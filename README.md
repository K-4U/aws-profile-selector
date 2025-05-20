# aws-profile-selector

A cli utility to select from profiles defined in your aws config.

## Requirements

### MacOS

```bash
brew install dialog
```

### Linux (Debian/Ubuntu)

```bash
sudo apt-get install dialog
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
