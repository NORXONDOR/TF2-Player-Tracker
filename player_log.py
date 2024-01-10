"""
tf2-player-tracker: player_log.py

This script waits for the TF2 client to be connected to a server before showing a real-time log of all 
connected players. If said players are in your database, they will have a colour based on their 
trustworthiness. This checks 'database.txt' while its running so that new players can be added and 
represented in the log on the fly.
"""
from rcon.source import Client
from shared_funcs import *
from Player import *
from clrprint import *
import random
import subprocess
import winreg


# For the program to work, copy the following (without quotes) into TF2's launch options:
# "-condebug -conclearlog -usercon +ip 0.0.0.0 +rcon_password Passw0rd +hostport 27015"
#
# Make sure RCON_PASSWORD's value is same as +rcon_password's value.
# RCON_PASSWORD can be up to 64 characters in length, letters a-Z and digits 0-9. Make sure it's a secure password.
# This is a temporary workaround. Will be set dynamically in future.
RCON_PASSWORD = 'Passw0rd'

IN_SERVER_PHRASES = ["Connected to ", "*DEAD* ", "*SPEC* " " killed "]

API_CALL_DELAY = 5 # How many seconds the program waits before checking player info again. Rate limit sets in when API_CALL_DELAY <= 108/125.


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

        case 'ln':
            characters = letters + numbers
            
        case 'ls':
            characters = letters + special
            
        case 'ns':
            characters = numbers + special

        case 'a':
            characters = letters + numbers + special

    rand_string = ''.join(random.choice(characters) for character in range(length))
    return rand_string


def convert_3_to_64(steamid3):
    """
    Converts a steamID3 to steamID64.
    e.g U:1:1063092633 -> 76561199023358361.
    
    Args:
        (string) steamid3: steamID3.
    Return:
        (string) steamid64: steamID64.
    """
    steamid3_num = steamid3[4:]
    steamid64 = str(int(steamid3_num) + 76561197960265728)
    
    return steamid64


if __name__ == "__main__":
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
        #rcon_password = rand_string(64, 'ln')
        subprocess.run([steam_executable_path, f'steam://run/440//'])
    else:
        raise Exception(f"Error: Steam executable not found. Please download Steam.")

    # Clear logs in case anything residual before run.
    open(f'{console_log_filepath}', 'w').close()

    # Logging loop.
    while True:
        try:
            clear()
            print(f"tf2-player-tracker v{VERSION} by NORXONDOR\n")
            
            console_output = None

            with open(console_log_filepath, 'r+', errors='replace') as console_log_file:
                console_output = console_log_file.read()
                console_log_file.truncate(0)

            # Check if client in server.
            if any(phrase in console_output for phrase in IN_SERVER_PHRASES):
                try:
                    # Connect to tf2.exe client with RCON.
                    with Client('127.0.0.1', 27015, passwd=RCON_PASSWORD) as client:
                        try:
                            print("Connection to client made.\n")
                            while True:
                                # Check if client disconnected from server.
                                with open(console_log_filepath, 'r+', errors='replace') as console_log_file:
                                    console_output = console_log_file.read()
                                    console_log_file.truncate(0)

                                    if "Disconnecting from abandoned match server" in console_output:
                                        break

                                # Prints server info to console log.
                                client.run('status')
                                time.sleep(0.1)
                                
                                # Read server info.
                                with open(console_log_filepath, 'r', errors='replace') as console_log_file:
                                    console_output = console_log_file.readlines()

                                # Load player database each time to check for new additions from player_adder.py.
                                with open('database.txt', 'r') as database_file:
                                    while True:
                                        line = database_file.readline().rstrip()

                                        if not line:
                                            break

                                        substrings = line.split(";")
                                        if len(substrings) == 4:
                                            Player(substrings[0], substrings[1].split(".1.h"), int(substrings[2]), substrings[3].strip())
                                        elif len(substrings) == 1 and substrings[0] == '':
                                            pass
                                        else:
                                            print(f"Incomplete data in line: '{line}'. Please fix!")

                                # Get steamID64 of each player in match to pass into API call.
                                steamid64s = ""
                                is_valve_server = False
                                
                                for line in console_output:
                                    if "#   " in line:
                                        # Ignore username to pre-sanitise ID3.
                                        last_quote_idx = line.rfind('"')
                                        after_name = line[last_quote_idx + 1:]

                                        # Get ID3.
                                        start_id3 = after_name.find('[')
                                        end_id3 = after_name.rfind(']')
                                        steamid3 = after_name[start_id3+1:end_id3]

                                        # Append ID64 to comma-delimited string.
                                        steamid64 = convert_3_to_64(steamid3)
                                        steamid64s += steamid64 + ','
                                    elif "hostname: Valve Matchmaking Server " in line:
                                        # Check if Valve server.
                                        is_valve_server = True
                                    elif "udp/ip  : " in line:
                                        # Get IP.
                                        ip_start = line[10:]
                                        ip_end_idx = ip_start.rfind('\n')
                                        server_ip = ip_start[:ip_end_idx]
                                    elif "map     : " in line:
                                        # Get map name.
                                        map_start = line[10:]
                                        map_end_idx = map_start.find(' ')
                                        map_name = map_start[:map_end_idx]
                                    elif "players : " in line:
                                        # Get max players.
                                        if is_valve_server:
                                            max_players = '24'
                                        else: 
                                            players_start_idx = line.rfind('(') + 1
                                            players_start = line[players_start_idx:]
                                            players_end_idx = players_start.find(' ')
                                            max_players = players_start[:players_end_idx]

                                # Get info of all players in match.
                                players_info = []
                                
                                api_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_api_key}&steamids={steamid64s}"
                                response = requests.get(api_url)
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    for player_idx in range(len(data["response"]["players"])):
                                        player = data["response"]["players"][player_idx]
                                        
                                        steamid64 = player["steamid"]
                                        persona_name_raw = player["personaname"]
                                        persona_name = persona_name_raw.replace('.1.h', '').replace(';', '')
                                        
                                        players_info.append((steamid64, persona_name))
                                elif response.status_code == 504:
                                    print(f"Gateway received too many requests. Ignoring player.")
                                    continue
                                elif response.status_code == 502:
                                    print(f"Invalid gateway response. Ignoring player.")
                                    continue
                                elif response.status_code == 403:
                                    print(f"No authority to grab info. Ignoring player.")
                                    continue
                                else:
                                    raise Exception(response.status_code)
                                
                                # Sort players by steamid64.
                                players_info = sorted(players_info, key=lambda tup: tup[0])

                                # Create Player objects and add to server_players.
                                server_players = []

                                for player_info in players_info:
                                    steamid64 = player_info[0]
                                    persona_name = player_info[1]
                                    
                                    if steamid64 in Player.player_dict:
                                        # Adds newly discovered aliases.
                                        if persona_name not in Player.player_dict[steamid64].aliases:
                                            Player.player_dict[steamid64].aliases.append(persona_name)

                                        server_players.append(Player.player_dict[steamid64])
                                    else:
                                        player = Player(steamid64, [persona_name])
                                        server_players.append(player)
                                
                                # Prints info about server and its players.
                                if server_players:
                                    clear()
                                    print(f"tf2-player-tracker v{VERSION} by NORXONDOR\n")
                                    
                                    print("IP:", server_ip)
                                    print("Map:", map_name)
                                    print(f"{len(server_players)}/{max_players} players.\n")
                                    
                                    for player in server_players:
                                        if player.trust_level == 3:
                                            clrprint(f"[{player.steamid64}, {player.trust_level}, {player.aliases[-1]}]", clr='r')
                                        elif player.trust_level == 2:
                                            clrprint(f"[{player.steamid64}, {player.trust_level}, {player.aliases[-1]}]", clr='y')
                                        elif player.trust_level == 1:
                                            clrprint(f"[{player.steamid64}, {player.trust_level}, {player.aliases[-1]}]", clr='g')
                                        else:
                                            print(f"[{player.steamid64}, {player.trust_level}, {player.aliases[-1]}]")
                                
                                server_players = [] # Refreshes player list.
                                
                                time.sleep(API_CALL_DELAY)

                        except ConnectionAbortedError:
                            print("The game was closed during RCON connection. Exiting application.")
                            break

                except ConnectionRefusedError:
                    print("Could not connect to the RCON client. Retrying.")

            else:
                print("Client not yet connected to a server. If in a server, port or password does not match that which is given in launch options.")
                time.sleep(5)
        
        except KeyboardInterrupt:
            print("Program forcefully closed. Clearing console.")
            break

    open(f'{console_log_filepath}', 'w').close()
    clear()