# WrecksShop Discord Ark Shop Bot

WrecksShop is a Discord-based bot for delivering items to players in-game. It is compatible with Tip4Serv donation shops, as well.

Description:
* Runs from a desktop GUI that will allow adding, removing & editing of shop items.
* GUI monitors both functional and error logs with optional saving to local files.
* Includes integration with SQL databases.
* Plug and play -- enter your information into the GUI (i.e., items to be sold, discord bot token, RCON credentials, discord channels/roles, etc.), and it will generate the appropriate files without you having to manually edit the code itself.
* Customizable -- set custom broadcast/in-game messages for shop functions, customize which logs to send where, etc.
* Skips the need for other tools -- no need to use companion plug-ins or bots! This tool is designed to be standalone to reduce the number of resources needed, but can still be integrated with certain plug-ins for Ark Ascended & Discord that allow seamless overall function.

## Setup

1. Copy `.env.example` to `.env` and fill in values.
2. Place `logo.png` & `icon.png` into `assets/`.
3. Install Python 3.11+ (if not using prebuilt `.exe`).
4. Run the launcher:
   ```bash
   python arkshopbot_launcher.py

Help:
* This is very much still a work-in-progress that will be changing frequently. Any questions about the bot, GUI, or suggestions can be directed to my discord: https://discord.gg/smXr7pQ37V

Authors/Contributors:
Bebe Watson -- unfortunate mastermind
ChatGPT -- file updates, recommendations for progression, integration of mass data input, other busy-work assistance

Version History:
* 1.01 -- Initial Release

License:
* This project is licensed under an MIT License -- see here: https://github.com/bebewat/wrecksshop?tab=MIT-1-ov-file

Acknowledgments:
* Thank you to Ark Legends PVE for the motivation to get this going & continual support along the way.
