import argparse
import json
import sys
import secrets
import webbrowser
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
import requests
from flask import Flask, request, redirect, render_template
import threading
import time
import os
import logging
from . import smee

# Silence Flask development server
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Disable Flask's .env loading
os.environ['FLASK_SKIP_DOTENV'] = '1'

console = Console()
app = Flask(__name__)
app.config.update(
    ENV='production',  # Silence .env message
    PROPAGATE_EXCEPTIONS=True
)
callback_data = {"code": None}
SERVER_PORT = 3000

DEFAULT_PERMISSIONS = {
    "contents": "write",
    "issues": "write",
    "checks": "write",
    "metadata": "read",
    "pull_requests": "write",
    "workflows": "write",
    "members": "read",
    "deployments": "write"
}

DEFAULT_EVENTS = [
    "push",
    "pull_request",
    "issues",
    "deployment",
    "workflow_run",
    "check_run",
    "check_suite"
]

class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        if isinstance(action, argparse._SubParsersAction):
            # Keep the command list but hide the metavar
            parts = []
            for name, subparser in action._name_parser_map.items():
                parts.append("  {:<10} {}".format(name, subparser.description.split('\n', 1)[0]))
            return "\n".join(parts) + "\n"
        if action.option_strings == ['-h', '--help']:
            return ""
        return super()._format_action(action)

def load_config(path):
    """Load configuration from a JSON file."""
    try:
        with open(path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        console.print(f"[red]Error loading config file: {e}[/red]")
        sys.exit(1)

def show_help():
    """Show help message."""
    console.print("\n[yellow]Skyline - GitHub App Onboarding CLI[/yellow]")
    console.print("\nCreate a GitHub App using:")
    console.print("1. Interactive mode:")
    console.print("   [dim]github-app-onboarding --org YOUR_ORG[/dim]")
    console.print("\n2. Config file:")
    console.print("   [dim]github-app-onboarding --config app_config.json --org YOUR_ORG[/dim]")
    sys.exit(1)

def prompt_config():
    """Prompt the user interactively to input GitHub App configuration details."""
    config = {}
    console.print("[bold cyan]Welcome to Skyline - GitHub App Onboarding CLI![/bold cyan]")
    console.print("\n[yellow]This tool will help you create a GitHub App.[/yellow]\n")
    
    # Basic settings
    config["name"] = Prompt.ask("Enter the GitHub App name")
    config["url"] = Prompt.ask("Enter the homepage URL of your app")
    config["description"] = Prompt.ask("Enter the GitHub App description")
    
    # These are required by GitHub
    config["public"] = True
    config["default_permissions"] = {
        "contents": "write",
        "issues": "write",
        "checks": "write",
        "metadata": "read",
        "pull_requests": "write",
        "workflows": "write",
        "members": "read",
        "deployments": "write"
    }
    config["default_events"] = [
        "push",
        "pull_request",
        "issues",
        "deployment",
        "workflow_run",
        "check_run",
        "check_suite"
    ]
    
    return config

@app.route('/callback')
def callback():
    """Handle the GitHub App creation callback."""
    # Verify state parameter to prevent CSRF
    if request.args.get('state') != app.config.get('state'):
        return 'Invalid state parameter', 400
        
    # Get the temporary code from GitHub
    code = request.args.get('code')
    if not code:
        return 'No code parameter', 400
        
    # Exchange code for app configuration
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    response = requests.post(
        'https://api.github.com/app-manifests/' + code + '/conversions',
        headers=headers
    )
    
    if response.status_code == 201:
        app_config = response.json()
        
        # Store config for later use
        app.config['app_credentials'] = app_config
        
        # Show success page first
        console.print("\n[green]✓ GitHub App created successfully![/green]")
        console.print("\n[yellow]Check the CLI for next steps to save your credentials.[/yellow]")
        
        # Schedule credential saving after response is sent
        def save_credentials():
            time.sleep(1)  # Give time for response to be sent
            
            # Prompt for credential locations
            console.print("\n[bold]Where would you like to save your credentials?[/bold]")
            env_path = Prompt.ask("Environment file location", default=".env")
            key_path = Prompt.ask("Private key location", default=".github/app-private-key.pem")
            
            # Create directories if needed
            key_dir = Path(key_path).parent
            key_dir.mkdir(exist_ok=True, parents=True)
            
            # Save private key
            with open(key_path, 'w') as f:
                f.write(app_config['pem'])
            
            # Save environment variables
            with open(env_path, 'w') as f:
                f.write(f"# GitHub App Credentials\n")
                f.write(f"GITHUB_APP_ID={app_config['id']}\n")
                f.write(f"GITHUB_APP_CLIENT_ID={app_config['client_id']}\n")
                f.write(f"GITHUB_APP_WEBHOOK_SECRET={app_config['webhook_secret']}\n")
                f.write(f"GITHUB_APP_PRIVATE_KEY_PATH={key_path}\n")
            
            # Show success messages
            console.print(f"\n[green]✓ Credentials saved to {env_path}[/green]")
            console.print(f"[green]✓ Private key saved to {key_path}[/green]")
            
            # Add to gitignore if it exists
            gitignore_path = Path(".gitignore")
            if gitignore_path.exists():
                with open(gitignore_path, 'a') as f:
                    f.write(f"\n# GitHub App credentials\n")
                    f.write(f"{env_path}\n")
                    f.write(f"{key_path}\n")
                console.print(f"[green]✓ Added credentials to .gitignore[/green]")
            else:
                console.print("\n[yellow]Remember to add these files to your .gitignore:[/yellow]")
                console.print(f"  {env_path}")
                console.print(f"  {key_path}")
            
            # Exit after saving
            os._exit(0)
            
        threading.Thread(target=save_credentials).start()
        
        return render_template('success.html')
    else:
        error = f"Failed to create GitHub App: {response.text}"
        console.print(f"\n[red]✗ {error}[/red]")
        return error, 400

@app.route('/')
def index():
    """Show the app configuration and GitHub button."""
    manifest = app.config.get('manifest', {})
    state = app.config.get('state', '')
    org = app.config.get('org', '')
    
    # Create the form action URL with state parameter
    form_url = f"https://github.com/organizations/{org}/settings/apps/new?state={state}" if org else f"https://github.com/settings/apps/new?state={state}"
    
    return render_template('index.html', 
                         manifest=json.dumps(manifest, indent=2),
                         form_url=form_url,
                         manifest_json=json.dumps(manifest))

@app.route('/create', methods=['POST'])
def create():
    """Redirect to the index page which has the form."""
    return redirect('/')

def start_local_server():
    """Start the local Flask server in a separate thread."""
    threading.Thread(target=lambda: app.run(port=SERVER_PORT, host='localhost')).start()
    time.sleep(1)  # Give the server a moment to start

def create_smee_client():
    """Create a new smee.io channel and start the client."""
    try:
        # Create smee client pointing to our callback endpoint
        client = smee.SmeeClient(f"http://localhost:{SERVER_PORT}/callback")
        
        # Create a new channel
        smee_url = client.create_channel()
        console.print(f"\n[green]✓ Created one-off Smee.io channel:[/green] {smee_url}")
        
        # Start listening for events
        console.print("\n[yellow]Connecting to Smee.io...[/yellow]")
        if client.start(smee_url):
            console.print("[green]✓ Connected to Smee.io[/green]")
            return smee_url
        else:
            console.print("[red]Error: Could not connect to Smee.io[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error setting up Smee.io client: {e}[/red]")
        sys.exit(1)

def create_github_app(config, org):
    """Create a GitHub App using GitHub's manifest flow."""
    # Generate a random state parameter for security
    state = secrets.token_urlsafe(16)
    
    # Start local server to handle the callback
    start_local_server()
    
    # Create smee channel for webhook forwarding
    smee_url = create_smee_client()
    console.print(f"\n[green]✓ Created one-off Smee.io channel for webhook forwarding:[/green] {smee_url}")
    
    # Update the config with smee URL for webhooks, but use our callback endpoint for the redirect
    config["hook_attributes"] = {"url": smee_url}
    config["redirect_url"] = f"http://localhost:{SERVER_PORT}/callback"
    
    # Store config in Flask app
    app.config['manifest'] = config
    app.config['state'] = state
    app.config['org'] = org
    
    # Open browser to our local server
    url = f"http://localhost:{SERVER_PORT}"
    console.print("\n[green]✓ Opening browser to review your app configuration...[/green]")
    console.print("\nPlease review the settings and click 'Create GitHub App' when ready.")
    webbrowser.open(url)
    
    console.print("\n[yellow]Waiting for GitHub authorization...[/yellow]")

def main():
    parser = argparse.ArgumentParser(
        description="""
Commands:
  create    Create a new GitHub App (interactive or via config)

Usage: skyline create [options]
   or: skyline create --org org [--config file]

EXAMPLES
    skyline create                                 Create app interactively
    skyline create --config config.json            From config, will prompt for org
    skyline create --org acme                      Create for specific org
    skyline create --config conf.json --org acme   Create from config for org

Note: Only supports creating GitHub Apps under organizations.
""",
        formatter_class=CustomHelpFormatter,
        add_help=False,
        usage=argparse.SUPPRESS
    )
    
    parser.add_argument('-h', '--help', action='help', help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest='command', help=argparse.SUPPRESS)
    
    # Create command
    create_parser = subparsers.add_parser('create', 
        help='Create a new GitHub App',
        description="""Create a new GitHub App with automated webhook forwarding

Configuration:
  You can provide a JSON config file with these fields:
    {
      "name": "My GitHub App",          # Required
      "url": "https://example.com",     # Required
      "description": "App description",  # Optional
      "public": true                    # Optional, default: true
    }

  On success, credentials are saved to:
    • .env file with app credentials
    • .github/app-private-key.pem

Arguments:
  --config    Path to JSON configuration file. If not provided, will use interactive mode
  --org       GitHub organization name. If not provided, will prompt for it
""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    create_parser.add_argument('--config', 
        help='Path to JSON configuration file. If not provided, will use interactive mode')
    create_parser.add_argument('--org', 
        help='GitHub organization name. If not provided, will prompt for it')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    if args.command == 'create':
        # Get org name if not provided
        org = args.org
        if not org:
            org = Prompt.ask("\nWhat organization should own this app?")
            if not org:
                console.print("[red]Organization name is required[/red]")
                sys.exit(1)
        
        if args.config:
            try:
                with open(args.config) as f:
                    config = json.load(f)
            except Exception as e:
                console.print(f"[red]Error reading config file: {e}[/red]")
                sys.exit(1)
        else:
            # Interactive mode
            console.print("\n[bold]Skyline - GitHub App Creation[/bold]")
            
            # Get app name
            name = Prompt.ask("\nWhat should we name your GitHub App?")
            url = Prompt.ask("\nWhat's the homepage URL for your app?", default="https://example.com")
            description = Prompt.ask("\nProvide a brief description of your app")
            
            config = {
                "name": name,
                "url": url,
                "description": description,
                "public": True,
                "default_permissions": DEFAULT_PERMISSIONS,
                "default_events": DEFAULT_EVENTS
            }
        
        create_github_app(config, org)

if __name__ == "__main__":
    main()
