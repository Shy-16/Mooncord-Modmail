# Moonmail

Moderation bot for Mooncord

## Install Instructions

### Install latest version of Python 3.

Moonmail uses latest version of Python3, at the very least higher than 3.8
Once ready install all modules:
- `pip install -r requirements.txt`

## Install MongoDB

Moonmail uses latest version of MongoDB. 
- Configure access user with admin privileges.

By default mongoDB will create non-existing resources on first read, that means you don't need to configure anything. However for the sake of explanation here is the MongoDB structure:
- Create a new database. By default Moonmail uses `moon2web`
- Create a 4 new collections. The name of these cannot be changed:
- - `discord_config`
- - `users`
- -  `users_bans`
- -  `users_strikes`

## Copy config.yaml and edit it.

Copy `config.yaml` from `config_example` to root folder (where `main.py` is located).
Open it and configure the file.

## Run the bot

The bot requires discord token from a **Bot** user to run, which will be provided within the command parameters. 
To get your token create a new Application in the [Discord developer portal](https://discord.com/developers/applications) and then make sure you activate the `Bot` under `Bot` configuration.

Once you have the token, run the bot:
- `python3 main.py -t <token>`

## Invite the bot to your server

To invite the bot to your server you have to copy both the `Applcation ID` and `Permissions` from the bot, and edit them into the invite link.

The `Application ID` can be found on top of the `General Information` of the application.

The bot uses the following permissions:
- Permissions number is: `535529122902`
- `Manage Roles`
- `Kick Members`
- `Ban Members`
- `View Channels`
- `Send Messages`
- `Manage Messages`
- `Embed Links`
- `Attack Files`
- `Read Message History`
- `Mention Everyone`
- `Add Reactions`

Once ready, edit the following link with `client_id`, and open it in a new tab.

[https://discord.com/oauth2/authorize?client_id=893906869184237588&permissions=535529253974&scope=bot%20applications.commands](https://discord.com/oauth2/authorize?client_id=893906869184237588&permissions=535529253974&scope=bot%20applications.commands)