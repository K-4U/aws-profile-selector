import dialog
import os
import configparser
import subprocess

# Check if AWS config file exists

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.aws/config"))

profiles = []

for section in config.sections():
    if section.startswith("profile"):
        profile_name = section.split(" ")[1]
        # Grab browser info if it exists
        browser = None
        if config.has_option(section, "browser"):
            browser = config.get(section, "browser")

        profiles.append({"name": profile_name, "browser": browser, "index": len(profiles),
                         "tuple": ("%s" % len(profiles), profile_name)})

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

    proc = subprocess.Popen(f"aws sso login --profile {profile_name}", env=environ_copy, shell=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    output = ""
    # TODO: Fetch the code from the output and display it in a dialog box
    for line in proc.stdout:
        print(line, end="")  # stream to terminal
        output += line  # collect output

    proc.wait()
    print("Process exited with code:", proc.returncode)

    result = subprocess.run(f"aws configure export-credentials", shell=True, text=True, capture_output=True,
                            env=environ_copy)
    print(result)
