"""
tf2-player-tracker: player_adder.py

Script which allows you to add players to 'database.txt' and visualise them in a node-based network. 
This allows users to make an informed decision when changing a player's trust level.
"""
from shared_funcs import *
from Player import *
from pyvis.network import Network
from IPython.display import display


if __name__ == "__main__":
    clear()

    # Load steam_api_key.
    steam_api_key = get_api_key()

    menu_choice = ""
    while menu_choice != 'X':
        print(f"tf2-player-tracker v{VERSION} by NORXONDOR\n")
        print("-------------------")
        print("Choose your option:")
        print("-------------------")
        print("1. Add Player")
        print("2. Populate Friends Lists")
        print("3. Load Database")
        print("4. Overwrite/Save Database")
        print("5. Show Players")
        print("6. Create Network (must populate friends first)")
        print("L. Player Lookup")
        print("X. Exit")
        menu_choice = input("> ").upper()

        match menu_choice:
            case '1':
                steamid64 = input("SteamID64 (without brackets): ")

                api_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_api_key}&steamids={steamid64}"
                response = requests.get(api_url)

                persona_name = None
                
                if response.status_code == 200:
                    data = response.json()
                    friend_info = data["response"]["players"][0]
                    persona_name_raw = friend_info["personaname"]
                    persona_name = persona_name_raw.replace('.1.h', '').replace(';', '') # Remove .1.h and ;, character combinations used to delimit database entry information.
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

                # Check to see if Player already exists by steamid64.
                if steamid64 in Player.player_dict:
                    print("Player already exists in database.")

                    choice_made = False
                    while not choice_made: 
                        print("Would you like to change their trust rating (y/n)?")
                        choice = input("> ").lower()

                        if choice == "y":
                            trust_level = int(input("Trust Level (0, 1, 2 or 3): "))
                            Player.player_dict[steamid64].trust_level = trust_level
                            choice_made = True
                        elif choice == "n":
                            choice_made = True
                        else:
                            print(f"'{choice}' is an invalid option!\n")

                    if persona_name not in Player.player_dict[steamid64].aliases:
                        Player.player_dict[steamid64].aliases.append(persona_name)
                        print(f"'{persona_name}' added to aliases!")
                    else:
                        print(f"'{persona_name}' already exists in aliases.")
                else:
                    aliases = [persona_name]
                    trust_level = int(input("Trust Level (0, 1, 2 or 3): "))
                    notes = input("Additional notes: ")

                    Player(steamid64, aliases, trust_level, notes)

            case '2':
                for player in Player.who():
                    # Get a list of a Player's Steam friends' IDs.
                    steamid64 = player.steamid64

                    api_url = f'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={steam_api_key}&steamid={steamid64}&relationship=friend'
                    response = requests.get(api_url)

                    if response.status_code == 200:
                        data = response.json()
                        friend_ids = [friend['steamid'] for friend in data['friendslist']['friends']]
                    elif response.status_code == 401:
                        print(f"Friends list of '{player.aliases[-1]}' is private. Skipping.")
                        continue
                    else:
                        raise Exception(response.status_code)
                
                    # If friend exists in database, add friend connection.
                    for friend_id in friend_ids:
                        if friend_id in Player.player_dict:
                            player.add_friends([f'{friend_id}'])

            case '3':
                # Clear current players in runtime.
                Player.clear_runtime()

                with open('database.txt', 'r') as text_file:
                    line_exists = True
                    while line_exists:
                        line = text_file.readline().rstrip()

                        if not line:
                            line_exists = False

                        substrings = line.split(";")
                        if len(substrings) == 4:
                            Player(substrings[0], substrings[1].split(".1.h"), int(substrings[2]), substrings[3].strip())
                        elif len(substrings) == 1 and substrings[0] == '':
                            pass
                        else:
                            print("Incomplete data in line: ", line)

                    print("Database loaded.")
                    time.sleep(1.5)

            case '4':
                with open('database.txt', 'w') as text_file:

                    for player in Player.who():
                        aliases = ""
                        for alias in range(len(player.aliases)-1):
                            aliases += f"{player.aliases[alias]}.1.h"
                        aliases += f"{player.aliases[-1]}"

                        text_file.write(f"{player.steamid64};{aliases};{player.trust_level};{player.notes}\n")

                    print("Database overwritten.")
                    time.sleep(1.5)                    

            case '5':
                for player in Player.who():
                    print(f"[{player.steamid64}, {player.aliases[-1]}, {player.trust_level}]")
                
                input("\nPress any button to continue.\n>")

            case '6':
                # Save friend connections to HTML.
                """
                1. decrease opacity of edges between nodes.
                2. increase opacity of edges coming from a node that has been clicked.
                3. make node labels all white
                """

                net = Network(height='1100px', width='100%', bgcolor='#000000', font_color='FFFFFF', select_menu=True)

                TRUST_COLOURS = {
                    0: 'rgb(255, 255, 255)', # Tracked.
                    1: 'rgb(0, 255, 0)', # Trusted.
                    2: 'rgb(255, 255, 0)', # Suspicious.
                    3: 'rgb(255, 0, 0)'  # Cheater/Bot.
                }

                for player in Player.who():
                    node_color = TRUST_COLOURS[player.trust_level]
                    net.add_node(player.steamid64, label=player.aliases[-1], color=node_color, shape="square")

                for player in Player.who():
                    for friend in player.friends:
                        net.add_edge(player.steamid64, friend.steamid64, width=3, smooth=False)

                net.show_buttons()

                net.show('player_network.html', local=True, notebook=False)
                print("Network saved to 'player_network.html'")

            case 'L':
                steamid64 = input("SteamID64: ")

                if steamid64 in Player.player_dict:
                    player = Player.player_dict[f'{steamid64}']
                    print(f"Player {steamid64}'s trust_level: '{player.trust_level}'")
                    friend_trusts = player.get_friend_trusts()
                    print(f"                         Friend trusts: [{friend_trusts[0]};{friend_trusts[1]};{friend_trusts[2]};{friend_trusts[3]}]")
                else:
                    print(f"Player {steamid64} does not exist in runtime!")
                
                input("\nPress any button to continue.\n>")

            case 'X':
                pass
    
        clear()

