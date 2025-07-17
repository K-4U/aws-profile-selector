import configparser
import json
import os
import subprocess
import sys
import dialog
import browsers

RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[m'


def read_profiles():
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.aws/config"))
    profiles = []
    found_browsers = set()
    idx = 0
    for section in config.sections():
        if section.startswith("profile "):
            profile_name = section.split(" ", 1)[1]
            browser = config.get(section, "browser") if config.has_option(section, "browser") else None
            if browser:
                found_browsers.add(browser.lower())
            profiles.append({
                "name": profile_name,
                "browser": browser,
                "index": idx,
                "tuple": (str(idx), profile_name),
            })
            idx += 1

    if found_browsers and not verify_browsers(list(found_browsers)):
        print(RED + "Please install the missing browsers or remove them from your AWS config." + RESET)
        exit(1)

    return profiles


def verify_browsers(found_browsers):
    all_browsers = list(browsers.browsers())
    installed_types = {b["browser_type"].lower() for b in all_browsers}
    installed_display_names = {b["display_name"].lower() for b in all_browsers}
    installed_paths = {b["path"].lower() for b in all_browsers}
    missing = set()
    for browser in found_browsers:
        browser_lc = browser.lower()
        # 1. Match by browser_type
        if browser_lc in installed_types:
            continue
        # 2. Match by display_name
        if browser_lc in installed_display_names:
            continue
        # 3. Match by substring in path (for custom installs like 'Firefox Werk')
        if any(browser_lc in p for p in installed_paths):
            continue
        # 4. Fallback: check if browser is a valid path
        if os.path.exists(browser) and os.access(browser, os.X_OK):
            continue
        missing.add(browser)
    if missing:
        for browser in missing:
            print(
                RED + f"Browser {browser} is not installed or not found. Please install it or remove it from your AWS config." + RESET)
        return False
    return True


def resolve_browser_path(browser):
    """Resolve the browser path using the browsers library, supporting type, display name, and custom installations."""
    browser_lc = browser.lower()
    all_browsers = list(browsers.browsers())
    # 1. Match by browser_type
    for b in all_browsers:
        if browser_lc == b["browser_type"].lower():
            return b["path"]
    # 2. Match by display_name
    for b in all_browsers:
        if browser_lc == b["display_name"].lower():
            return b["path"]
    # 3. Match by substring in path (for custom installs like 'Firefox Werk')
    for b in all_browsers:
        if browser_lc in b["path"].lower():
            return b["path"]
    # 4. Fallback: check if browser is a valid path
    if os.path.exists(browser) and os.access(browser, os.X_OK):
        return browser
    return None


def set_browser_env(environ_copy, browser):
    resolved = resolve_browser_path(browser)
    if resolved:
        environ_copy['BROWSER'] = resolved
    else:
        print(RED + f"Browser {browser} is not installed or not found." + RESET)
        exit(1)


def main(output_file):
    profiles = read_profiles()
    my_dialog = dialog.Dialog(dialog="dialog", autowidgetsize=True)
    my_dialog.set_background_title("AWS Profiles")

    if not profiles:
        print(RED + "No AWS profiles found in ~/.aws/config" + RESET)
        exit(1)

    button, choice = my_dialog.menu("Choose an AWS profile:", choices=[p["tuple"] for p in profiles])

    if button != "ok":
        return

    selected_profile = profiles[int(choice)]
    profile_name = selected_profile["name"]
    browser = selected_profile["browser"]

    environ_copy = os.environ.copy()
    environ_copy['AWS_PROFILE'] = profile_name
    if browser:
        set_browser_env(environ_copy, browser)

    print(GREEN + "Now forwarding your request to aws cli:" + RESET)
    # Wait for the user to log in to the SSO session
    subprocess.run("aws sso login", env=environ_copy, shell=True, text=True, check=True)

    # Export the credentials to a temp file
    result = subprocess.run(
        f"aws configure export-credentials --profile {profile_name} --format process --output json",
        shell=True, text=True, capture_output=True, env=environ_copy, check=True
    )

    try:
        aws_output = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(RED + "Failed to parse AWS credentials output." + RESET)
        exit(1)

    with open(output_file, "w") as f:
        f.write(f"export AWS_ACCESS_KEY_ID={aws_output['AccessKeyId']}\n")
        f.write(f"export AWS_SECRET_ACCESS_KEY={aws_output['SecretAccessKey']}\n")
        f.write(f"export AWS_SESSION_TOKEN={aws_output['SessionToken']}\n")
        f.write(f"export AWS_CREDENTIAL_EXPIRATION={aws_output['Expiration']}\n")
        f.write(f"export AWS_PROFILE={profile_name}\n")

    print(GREEN + f"Successfully logged in to AWS profile '{profile_name}'" + RESET)


# Do the __init__ thing:
if __name__ == "__main__":
    # Check if the output file is passed as an argument
    if len(sys.argv) != 2:
        print(RED + "Usage: python main.py <output_file>")
        exit(1)

    output_file = sys.argv[1]
    # Check if the output file is writable
    if not os.access(os.path.dirname(output_file), os.W_OK):
        print(RED + f"Error: Cannot write to {output_file}")
        exit(1)

    # Call the main function
    main(output_file)
