import dialog
import os
import configparser
import subprocess
import webbrowser
from time import time, sleep
from boto3.session import Session

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

        # Fetch sso-specific profile settings
        config_items = dict(config.items(section))
        # Fetch the sso session name
        sso_session_name = config_items.get("sso_session", None)
        sso_start_url = ""
        if not config.has_section(f"sso-session {sso_session_name}"):
            if "sso_start_url" not in config_items:
                continue  # We can't add anything to the list if we don't have a start url
            else:
                sso_start_url = config_items["sso_start_url"]
        else:
            sso_start_url = config.get(f"sso-session {sso_session_name}", "sso_start_url")

        profile_settings = {
            "name": profile_name,
            "browser": browser,
            "index": len(profiles),
            "tuple": ("%s" % len(profiles), profile_name),
            "settings": dict(config.items(section)),
            "sso_start_url": sso_start_url,
        }
        profiles.append(profile_settings)

my_dialog = dialog.Dialog(dialog="dialog", autowidgetsize=True)
my_dialog.set_background_title("AWS Profiles")
if not profiles:
    my_dialog.msgbox("No AWS profiles found in ~/.aws/config")
    exit(1)

button, choice = my_dialog.menu("Choose an AWS profile:", choices=[p["tuple"] for p in profiles])


def sso_login_with_cli(profile_name, browser):
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
    result = subprocess.run(f"aws configure export-credentials --profile {profile_name}", shell=True, text=True,
                            capture_output=True,
                            env=environ_copy)
    print(result)


def new_method():
    session = Session()
    sso_oidc = session.client("sso-oidc")
    client_creds = sso_oidc.register_client(clientName="AWS Profile Selector", clientType="public")
    device_authorization = sso_oidc.start_device_authorization(
        clientId=client_creds["clientId"],
        clientSecret=client_creds["clientSecret"],
        startUrl=selected_profile["sso_start_url"],
    )
    url = device_authorization['verificationUriComplete']
    device_code = device_authorization['deviceCode']
    expires_in = device_authorization['expiresIn']
    interval = device_authorization['interval']
    user_code = device_authorization['userCode']
    # TOOD: Make sure we open the right browser
    my_dialog.msgbox("Opening browser for authorization...\n\nCheck the following code:\n\n%s\n\n" % user_code)
    print(device_authorization)
    print(device_code)
    print(expires_in)
    print(interval)
    webbrowser.open(url, autoraise=True)
    for n in range(1, expires_in // interval + 1):
        # print("Waiting for authorization... %d seconds" % (n * interval))
        # my_dialog.gauge_update(int(100*((n * interval)/expires_in)))
        sleep(interval)
        try:
            token = sso_oidc.create_token(
                grantType='urn:ietf:params:oauth:grant-type:device_code',
                deviceCode=device_code,
                clientId=client_creds['clientId'],
                clientSecret=client_creds['clientSecret'],
            )
            break
        except sso_oidc.exceptions.AuthorizationPendingException:
            pass
    access_token = token['accessToken']
    sso = session.client('sso')
    account_roles = sso.list_account_roles(
        accessToken=access_token,
        accountId=selected_profile['settings']['sso_account_id'],
    )
    roles = account_roles['roleList']
    print(account_roles)
    # simplifying here for illustrative purposes
    role = roles[0]
    # earlier versions of the sso api returned the
    # role credentials directly, but now they appear
    # to be in a subkey called `roleCredentials`
    role_creds = sso.get_role_credentials(
        roleName=role['roleName'],
        accountId=selected_profile['settings']['sso_account_id'],
        accessToken=access_token,
    )['roleCredentials']
    session = Session(
        region_name=selected_profile["settings"]["region"],
        aws_access_key_id=role_creds['accessKeyId'],
        aws_secret_access_key=role_creds['secretAccessKey'],
        aws_session_token=role_creds['sessionToken'],
    )


if button == "ok":
    selected_profile = profiles[int(choice)]
    profile_name = selected_profile["name"]
    browser = selected_profile["browser"]

    sso_login_with_cli(profile_name, browser)
