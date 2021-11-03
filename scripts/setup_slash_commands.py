import requests
import yaml
import argparse

def execute():
    print("Initializing setting up Slash commands for Modmail...\r\n")
    print("-----------------------------------------------------\r\n")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--token", "-t", default="", help="Add the secret token to login to Discord."
    )

    args = parser.parse_args()
    if(not args.token):
        print("You need to provide a secret token with \"--token\" or \"-t\" ")
        return

    bot_token = args.token
    print("Token was successfully loaded from parameters.\r\n\r\n")

    try:
        config_file = open('../config.yaml', 'r')
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    except FileNotFoundError:
        print("\"config.yaml\" has to exist on root directory.")
        return

    except IOError:
        print("Sayo doesn't have the proper permissions to read \"config.yaml\".")
        return

    print("Application ID was successfully loaded from config file: {}.\r\n\r\n".format(config['discord']['application_id']))

    url = "https://discord.com/api/v8/applications/{}/commands".format(config['discord']['application_id'])

    # Create /modmail
    json = {
        "name": "modmail",
        "type": 1,
        "description": "Create a new modmail",
        "options": [
            {
                "name": "description",
                "description": "Description for the ticket",
                "type": 3
            }
        ]
    }

    # For authorization, you can use either your bot token
    headers = {
        "Authorization": "Bot {}".format(bot_token)
    }

    print("Attempting to create /modmail.\r\n")
    r = requests.post(url, headers=headers, json=json)
    print("Result was {} {}.\r\n\r\n".format(r.status_code, r.json()))

    # Create right click -> modmail
    json = {
        "name": "modmail",
        "type": 3
    }

    print("Attempting to create right click -> modmail.\r\n")
    r = requests.post(url, headers=headers, json=json)
    print("Result was {} {}.\r\n\r\n".format(r.status_code, r.json()))

    print("-----------------------------------------------------\r\n")
    print("Script for slash commands has finished.\r\n")

if __name__ == '__main__':
    execute()