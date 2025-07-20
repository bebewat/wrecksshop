# WrecksShop Discord Ark Shop Bot

WrecksShop is a Discord-based bot for delivering items to players in-game. It is compatible with Tip4Serv donation shops, as well.

## Description:
* Runs from a desktop GUI that will allow adding, removing & editing of shop items.
* GUI monitors both functional and error logs with optional saving to local files.
* Includes integration with SQL databases.
* Plug and play -- enter your information into the GUI (i.e., items to be sold, discord bot token, RCON credentials, discord channels/roles, etc.), and it will generate the appropriate files without you having to manually edit the code itself.
* Customizable -- set custom broadcast/in-game messages for shop functions, customize which logs to send where, etc.
* Skips the need for other tools -- no need to use companion plug-ins or bots! This tool is designed to be standalone to reduce the number of resources needed, but can still be integrated with certain plug-ins for Ark Ascended & Discord that allow seamless overall function.


# Setup:

1. Clone privately so that you can enter all private credentials.
2. Configure .env:

- Replace all placeholders with your credentials.
- Not completing this step will cause shop bot launch failure.
- To get channel IDs in Discord, you will need to enter Developer Mode. Then you'll have the option to copy the channel ID in the right-click menu of each channel.
- When configuring your discord bot in the Discord Developer interface, enable all intents; this will allow the bot to do everything that it needs to do.
<img width="373" height="154" alt="Screenshot 2025-07-20 151049" src="https://github.com/user-attachments/assets/42a54eda-b277-4fe2-9217-2d1b03d064b9" />

- Use the following format to add multiple servers (use this to replace the RCON port, password & host lines :
<img width="823" height="117" alt="Screenshot 2025-07-20 152536" src="https://github.com/user-attachments/assets/20ffff75-1a56-4825-92b7-6974a4f24e85" />

3. Once GitHub finishes running your updates to the file(s), click on the green checkmark & go to "Upload EXE Artifact". Save & extract the .exe file that was populated. 

- The .exe compiler will be automatically updated in GitHub when updates are applied; so keep an eye on update notifications for the bot in GitHub and/or Discord announcements.

4. Double-click the .exe in the folder you'd like the files to be populated. It will automatically populate your SQL file and all other pertinent files that are needed to run the bot. 
5. If you start the program & it automatically closes, you will need to re-visit the .env file to enter the appropriate credentials.

- If, after putting your credentials into the .env file, your program still does not run, please open a ticket in the discord so that I can troubleshoot with you & get you up and running.



## Shop Items Configuration
* Edit via GUI or directly in `shop_items.json`

## Help:
* This is very much still a work-in-progress that will be changing frequently. Any questions about the bot, GUI, or suggestions can be directed to my discord: https://discord.gg/smXr7pQ37V

## Authors/Contributors:
* Bebe Watson -- unfortunate mastermind
* ChatGPT -- file updates, recommendations for progression, integration of mass data input, other busy-work assistance

## Version History:
* 1.01 -- Initial Release

## License:
* This project is licensed under an MIT License -- see here: https://github.com/bebewat/wrecksshop?tab=MIT-1-ov-file

## Acknowledgments:
* Thank you to Ark Legends PVE for the motivation to get this going & continual support along the way.
