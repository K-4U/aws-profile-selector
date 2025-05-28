# aws-profile-selector

A cli utility to select from profiles defined in your aws config.

I created this script because I often have to log in to different AWS accounts and I wanted a simple way to select the
right profile, without having to remember the profile names.

## Requirements

Note: this already assumes you have the AWS CLI and Python 3 installed and configured.

## Installation

```bash
pip install -r requirements.txt
```

This script also requires `dialog` to be installed on your system:
### MacOS

```bash
brew install dialog
```

### Linux (Debian/Ubuntu)

```bash
sudo apt install dialog
```

### Windows

Sorry, I don't know of a package for this. You can use WSL and install the Linux version.

## Usage

Make sure the script is executable and in your PATH.
Then add the following alias to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`):

```bash
alias aws-login='. aws-login.sh'
```

Attention! The period in front of the command is important. It makes sure that the environment variables are set in the
current shell session.

## Useful functions to include in your shell configuration file

```bash
function aws-logoff() {
    unset AWS_ACCESS_KEY_ID
    unset AWS_SECRET_ACCESS_KEY
    unset AWS_SESSION_TOKEN
    unset AWS_PROFILE
    unset AWS_REGION
    unset AWS_CREDENTIAL_EXPIRATION
}
```

## Changes to your aws config (optional)

You can add a `browser` to your profiles in `~/.aws/config`. This will tell aws cli to open the sign-in page in your
preferred browser.
For me as a consultant this is very useful, because I have to log in to different AWS accounts all the time and I often
use different browsers for different clients.

For example:

```ini
[profile my-profile]
sso_session = my-sso-session
sso_account_id = 123456789012
sso_start_url = https://my-sso-portal.awsapps.com/start
sso_role_name = my-role
region = us-east-1
browser = chrome

[profile my-other-profile]
sso_session = my-other-sso-session
sso_account_id = 210987654321
sso_start_url = https://my-other-sso-portal.awsapps.com/start
sso_role_name = my-role
region = eu-central-1
browser = firefox
```

