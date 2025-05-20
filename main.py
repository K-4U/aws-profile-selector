import configparser
import json
import os
import subprocess
import sys
import dialog
import browsers


def read_profiles():
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.aws/config"))
    profiles = []
    found_browsers = []
    for section in config.sections():
        if section.startswith("profile"):
            profile_name = section.split(" ")[1]
            # Grab browser info if it exists
            browser = None
            if config.has_option(section, "browser"):
                browser = config.get(section, "browser")
                if browser not in found_browsers:
                    found_browsers.append(browser)

            profile_settings = {
                "name": profile_name,
                "browser": browser,
                "index": len(profiles),
                "tuple": ("%s" % len(profiles), profile_name),
            }
            profiles.append(profile_settings)

    if not verify_browsers(found_browsers):
        print("Please install the missing browsers or remove them from your AWS config.")
        exit(1)

    return profiles


def verify_browsers(found_browsers):
    installed_browsers_list = browsers.browsers()
    # Get all the browser_type from the installed_browsers_list
    installed_browsers = [browser["browser_type"] for browser in installed_browsers_list]
    browser_not_found = False
    for browser in found_browsers:
        if browser not in installed_browsers:
            print(f"Browser {browser} is not installed. Please install it or remove it from your AWS config.")
            browser_not_found = True
        else:
            print(f"Browser {browser} is installed.")

    return not browser_not_found


def main(output_file):
    profiles = read_profiles()
    my_dialog = dialog.Dialog(dialog="dialog", autowidgetsize=True)
    my_dialog.set_background_title("AWS Profiles")

    if not profiles:
        my_dialog.msgbox("No AWS profiles found in ~/.aws/config")
        exit(1)

    button, choice = my_dialog.menu("Choose an AWS profile:", choices=[p["tuple"] for p in profiles])

    if button == "ok":
        selected_profile = profiles[int(choice)]
        profile_name = selected_profile["name"]
        browser = selected_profile["browser"]

        environ_copy = os.environ.copy()
        environ_copy['AWS_PROFILE'] = profile_name
        if browser:
            environ_copy['BROWSER'] = browsers.get(browser)["path"]

        # Wait for the user to log in to the SSO session
        subprocess.run("aws sso login", env=environ_copy, shell=True, text=True)

        # Then export the credentials to a temp file
        result = subprocess.run(
            f"aws configure export-credentials --profile {profile_name} --format process --output json", shell=True,
            text=True,
            capture_output=True, env=environ_copy)
        stout = result.stdout
        print(f"STDOUT: {stout}")
        aws_output = json.loads(stout)

        # Open the temp file and write the credentials in env format to it
        with open(output_file, "w") as f:
            f.write(f"export AWS_ACCESS_KEY_ID={aws_output['AccessKeyId']}\n")
            f.write(f"export AWS_SECRET_ACCESS_KEY={aws_output['SecretAccessKey']}\n")
            f.write(f"export AWS_SESSION_TOKEN={aws_output['SessionToken']}\n")
            f.write(f"export AWS_CREDENTIAL_EXPIRATION={aws_output['Expiration']}\n")
            f.write(f"export AWS_PROFILE={profile_name}\n")


# Do the __init__ thing:
if __name__ == "__main__":
    # Check if the output file is passed as an argument
    if len(sys.argv) != 2:
        print("Usage: python main.py <output_file>")
        exit(1)

    output_file = sys.argv[1]
    # Check if the output file is writable
    if not os.access(os.path.dirname(output_file), os.W_OK):
        print(f"Error: Cannot write to {output_file}")
        exit(1)

    # Call the main function
    main(output_file)
