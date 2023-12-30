# TF2-Player-Tracker by NORXONDOR
A CLI which allows you to add Steam users to a local database, visualise them with a friendship network and get a live log of the players on the server you are connected to, showing the trustworthiness of said players as determined by your database, among other information. 

It works well for building a catalogue of information on players in your servers of choice, so that dealing with said players in future situations becomes quick and easy (e.g the decision to kick/mute 😉).

This set of scripts was designed with the intention of keeping track of cheaters/bots, but it can be modified to go beyond that. This code should give you a framework for tracking whatever you want about a Steam user.

The two scripts function alone, but are designed to be run together: 
- 'player_adder.py' allows you to add players to 'database.txt' and visualise them in a node-based network. This allows users to make an informed decision when changing a player's trust level, e.g if they have more than three untrusted/suspicious friends.
- 'player_log.py' waits for the TF2 client to be connected to a server before showing a real-time log of all connected players. If said players are in your database, they will have a colour based on their trustworthiness. This checks 'database.txt' while its running so that new players can be added and represented in the log on the fly.


# Running the program
Ensure your Steam Web API Key (https://steamcommunity.com/dev/apikey) is set in 'api_key.txt' before running.

TEMPORARY: Ensure RCON_PASSWORD is changed in 'player_log.py' and matches that of +rcon_password in TF2's launch options. More information is listed underneath the imports in player_log.py.

Installing dependencies:
```
pip install pyvis ipython requests rcon clrprint
```

To run player adder:
```
cd "path/to/folder"
python player_adder.py
```

To run player log:
```
cd "path/to/folder"
python player_log.py
```


# Samples images
White (0) represents tracked, green (1) - trusted, yellow (2) - suspicious and red (3) - bot/cheater.

Server player log using local database.

![player_log](https://github.com/NORXONDOR/TF2-Player-Tracker/assets/100261200/0028c1cf-35cb-47e7-8c75-679b356624d5)


Player friendship network loaded from database (names removed for preserving anonymity).

![friendship_network](https://github.com/NORXONDOR/TF2-Player-Tracker/assets/100261200/47ebae60-54cd-4048-9f78-14a89eb42614)


