# skyline 🌃

CLI tool for easily creating GitHub Apps. Ideal for repeatable and automated local dev setup. If your app
integrates with GitHub via GitHub Apps, you'll want this.

* Use either a JSON config file or an interactive CLI interface for app configuration (great for repeatable local dev setup)
* Works with the obscure but useful GitHub App Manifest semi-automated creation flow
* `skyline` automatically handles one-off webhook forwarding to handle the app creation callback (via smee.io), no configuration needed
* Lastly, securely stores the newly-created app credentials so developers can get right to work

## Features

- 🚀 **Easy for Local Development**: Developers do not need to manually setup their own apps, fill in permission details, etc. Also no need for shared dev apps.
- 🔐 **Secure Credential Management**: Automatically saves the new app credentials and private key in the right places, so you can get right to work
- ⚡️ **Flexible Configuration**: Use interactive prompts or JSON config files for reproducible app creation
- 🔄 **GitHub App Manifest Flow**: Implements GitHub's manifest flow for automated app creation with pre-filled permissions
- 🏢 **Organization Apps**: Create GitHub Apps for your organizations

## Installation

```bash
curl -sSL https://raw.githubusercontent.com/cased/skyline/main/install.sh | bash
```

The script will install `skyline` using pip, making it available in your PATH.

## Usage

After installation, you can run `skyline` from any directory:

### Config File Mode (Great for Automation)

Create a config file:
```json
{
    "name": "My GitHub App",
    "url": "https://example.com",
    "description": "A description of my app",
    "public": true
}
```

Then run one of these commands:
```bash
# Specify org via CLI flag (recommended for automation)
skyline create --config config.json --org my-org-name

# Or let it prompt for org interactively
skyline create --config config.json
```

### Interactive Mode (Good to try out skyline)

```bash
skyline create
```

You'll be prompted for:
1. Organization name/username
2. App name
3. Homepage URL
4. Description

## What happens when you run it?

1. **Configuration**: `skyline` either prompts you for details or reads from config file

2. **Temporary Webhook**: Creates a temporary smee.io channel just for the app creation callback
   - This is only used during app creation
   - Your actual app can use whatever webhook setup you prefer (ngrok, smee, etc.)

3. **GitHub flow**: 
   - Opens GitHub's app manifest creation flow page, which requires just the app name (will be pre-filled)
   - User returns to local server with a success message 
   - Tool saves your credentials

4. **Credential storage**:
   You'll be prompted in the local terminal where to save:
   ```bash
   # .env file (customizable location)
   GITHUB_APP_ID=123456
   GITHUB_APP_CLIENT_ID=Iv1.abcd1234
   GITHUB_APP_WEBHOOK_SECRET=your-webhook-secret
   GITHUB_APP_PRIVATE_KEY_PATH=.github/app-private-key.pem
   ```

   And your private key will be saved to `.github/app-private-key.pem`

   ⚠️ **Important**: These files contain sensitive information. Make sure to:
   - Add them to your `.gitignore`
   - Never commit them to version control
   - Follow your organization's security practices for credential management

Note that `skyline` does not handle the webhooks for your GitHub App itself, only
the creation of the app. You'll still need a smee or ngrok channel for that. 
However, I have a couple ideas to make that more automatable as 
well and may fold them into `skyline`.

## Default settings

### Permissions
The tool sets up common permissions needed for GitHub Apps (customize as needed in your config file):
```python
{
    "contents": "write",    # For repo content access
    "issues": "write",      # For issue management
    "checks": "write",      # For CI/CD integration
    "metadata": "read",     # Required for basic app function
    "pull_requests": "write", # For PR automation
    "workflows": "write",   # For GitHub Actions
    "members": "read",      # For org member access
    "deployments": "write"  # For deployment automation
}
```

### Events
Default webhook events (customize as needed in your config file):
```python
[
    "push",           # Code pushes
    "pull_request",   # PR activities
    "issues",         # Issue activities
    "deployment",     # Deployment events
    "workflow_run",   # Action workflow events
    "check_run",      # CI check events
    "check_suite"     # CI suite events
]
```

## For development of `skyline`

If you're working on `skyline` itself:

```bash
# Clone the repo
git clone https://github.com/cased/skyline.git
cd skyline

# Set up development environment
./dev-install.sh
```

This will:
1. Create a virtual environment in `.venv`
2. Install the package in editable mode (`pip install -e .`)
3. Create a global `skyline` command that reflects your local changes

Now you can:
- Make changes to the code and they'll be immediately reflected when you run `skyline`
- Run `skyline create` from any directory and it'll use your local development version
- No need to reinstall unless you change dependencies in `pyproject.toml`

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
