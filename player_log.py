"""
TODO:
- 1. Figure out how to run TF2 with launch parameters to dynamically set RCON password, port, etc.
- 2. We can pass multiple IDs at once to reduce Steam API calls. Get all IDs before making the calls.
"""
from rcon.source import Client
from shared_funcs import *
from Player import *
from clrprint import *
import random
import subprocess
import os
import winreg
import time
import requests

# For the program to work, copy the following (without quotes) into TF2's launch options:
# "-condebug -conclearlog -usercon +ip 0.0.0.0 +rcon_password Passw0rd +hostport 27015"
#
# Make sure RCON_PASSWORD's value is same as +rcon_password's value.
# RCON_PASSWORD can be up to 64 characters in length, letters a-Z and digits 0-9. Make sure it's a secure password.
RCON_PASSWORD = 'Passw0rd' # Temporary. Will be set with rand_string in future.

def rand_string(length=16, type='a'):
    """
    Generate a pseudo-random string of characters.
    
    Args:
        (int) length: Length of string.
        (string) type: Type of characters in string.
            l: English alphabet (a-z) + (A-Z).
            n: Decimal digits (0-9).
            s: Special characters (!"#$%&'()*+, -./:;<=>?@[\]^_`{|}~).
            l+n: English alphabet + Decimal digits.
            l+s: English alphabet + Special characters.
            n+s: Decimal digits + Special characters.
            a: English alphabet + Decimal digits + Special characters.
    Return:
        (string) random_string: Pseudo-random string of characters.
    """
    letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    numbers = '0123456789'
    special = '!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'

    match type:
        case 'l':
            characters = letters

        case 'n':
            characters = numbers

        case 's':
            characters = special

        case 'l+n':
            characters = letters + numbers
            
        case 'l+s':
            characters = letters + special
            
        case 'n+s':
            characters = numbers + special

        case 'a':
            characters = letters + numbers + special

    rand_string = ''.join(random.choice(characters) for character in range(length))
    return rand_string

# Load steam_api_key.
steam_api_key = get_api_key()

# Find Steam.exe.
steam_executable_path = None
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
    steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
    steam_exe_path = os.path.join(steam_path, "Steam.exe")
        
    if os.path.exists(steam_exe_path):
        steam_executable_path = steam_exe_path

# Launch tf2 with paramaters -condebug, -conclearlog, -usercon.
if steam_executable_path:
    steam_directory = f'{steam_executable_path[:-10]}'
    console_log_filepath = rf'{steam_directory}\steamapps\common\Team Fortress 2\tf\console.log' 

    # FIGURE OUT HOW THE FUCK TO RUN TF2 WITH PARAMETERS...
    #rcon_password = rand_string(13, 'l+n')
    #rcon_port = rand_string(4, 'n')
    subprocess.run([steam_executable_path, f'steam://run/440//'])
else:
    raise Exception(f"Error: Steam executable not found. Please download Steam.")

# Buffer to clear logs.
time.sleep(1)

# Wait until player joins server before connecting with RCON.
client_active = True
while client_active:
    console_output = None

    try:
        with open(console_log_filepath, 'r+') as console_log_file:
            console_output = console_log_file.read()

        # Connect to tf2.exe client with RCON if client in server.
        if "Connected to " in console_output or "*DEAD*" in console_output or "killed" in console_output:
            try: 
                with Client('127.0.0.1', 27015, passwd=RCON_PASSWORD) as client:
                    print("Connection to client made.")
                    connected = True
                    try:
                        while connected:
                        
                            # Check if client disconnected from server.
                            with open(console_log_filepath, 'r') as console_log_file:
                                console_output = console_log_file.read()
                                
                                if "Disconnecting from abandoned match server" in console_output:
                                    connected = False
                                    open(f'{console_log_filepath}', 'w').close() # Clears logs.
                                    
                        
                            client.run('status')

                            # Load player database each time to check for new additions from player_adder.
                            with open('database.txt', 'r') as database_file:
                                line_exists = True
                                while line_exists:
                                    line = database_file.readline().rstrip()

                                    if not line:
                                        line_exists = False

                                    substrings = line.split(";")
                                    if len(substrings) == 4:
                                        Player(substrings[0], substrings[1].split(".1.h"), int(substrings[2]), substrings[3].strip())
                                    elif len(substrings) == 1 and substrings[0] == '':
                                        pass
                                    else:
                                        print(f"Incomplete data in line: '{line}'. Please fix!")

                            server_players = []

                            with open(f'{console_log_filepath}', 'r', encoding='cp1252', errors='ignore') as console_log_file:
                                console_output = console_log_file.readlines()

                            # Create Player object for each player in match.
                            for line in console_output:
                                if "#    " in line:
                                    # Ignore username to pre-sanitise ID3.
                                    last_quote_index = line.rfind('"')
                                    after_name = line[last_quote_index + 1:]

                                    # ID3.
                                    start_id3 = after_name.find('[')
                                    end_id3 = after_name.rfind(']')
                                    steamid3 = after_name[start_id3+1:end_id3]

                                    # Get player info.
                                    steamid64 = convert_3_to_64(steamid3)
                                    api_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_api_key}&steamids={steamid64}"

                                    response = requests.get(api_url)
                                    
                                    if response.status_code == 200:
                                        data = response.json()
                                        friend_info = data["response"]["players"][0]
                                        unclean_persona_name = friend_info["personaname"]
                                        persona_name = unclean_persona_name.replace('.1.h', '').replace(';', '') # Removes delimiters to sanitise usernames for input.
                                    elif response.status_code == 504:
                                        print(f"Error: {response.status_code}. Ignoring player.")
                                        continue
                                    elif response.status_code == 403:
                                        print(f"Error: {response.status_code}. Ignoring player.")
                                        continue
                                    else:
                                        raise Exception(f"Error: {response.status_code}")

                                    # Check to see if player already exists in runtime by steamid64.
                                    if steamid64 in Player.player_dict:
                                        if persona_name not in Player.player_dict[steamid64].aliases:
                                            Player.player_dict[steamid64].aliases.append(persona_name)

                                        server_players.append(Player.player_dict[steamid64])
                                    else:
                                        player = Player(steamid64, [persona_name])
                                        server_players.append(player)

                            # Prints players in server.
                            for player in server_players:
                                if player.trust_level == 3:
                                    clrprint(f"[{player.steamid64}, {player.trust_level}, {player.aliases[-1]}]", clr='r')
                                elif player.trust_level == 2:
                                    clrprint(f"[{player.steamid64}, {player.trust_level}, {player.aliases[-1]}]", clr='y')
                                elif player.trust_level == 1:
                                    clrprint(f"[{player.steamid64}, {player.trust_level}, {player.aliases[-1]}]", clr='g')
                                else:
                                    print(f"[{player.steamid64}, {player.trust_level}, {player.aliases[-1]}]")
                            print("") # Why the fuck does this happen twice?

                            open(f'{console_log_filepath}', 'w').close() # Clears logs.
                            server_players = [] # Refreshes player list.

                            time.sleep(10)

                    except ConnectionAbortedError:
                        print("The game was closed during RCON connection. Exiting application.")
                        open(f'{console_log_filepath}', 'w').close() # Clears logs.
                        client_active = False

            except ConnectionRefusedError:
                print("Could not connect to the RCON client. Retrying.")
    
    except KeyboardInterrupt:
        print("Program forcefully closed. Clearing console.")
        open(f'{console_log_filepath}', 'w').close() # Clears logs.
        client_active = False

    else:
        print("Client not yet connected to a server. If in a server, port or password does not match that which is given in launch options.")
        time.sleep(30)