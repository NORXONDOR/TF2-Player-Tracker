"""
tf2-player-tracker: shared_funcs.py

A shared set of imports, constants and functions used by player_adder.py and player_log.py.
"""
import os
import requests
import time


VERSION = "1.1.0"


def get_api_key():
    """
    Grabs the API key provided in api_key.txt.
    
    Returns:
        (string) steam_api_key: Key written in 'api_key.txt'
    """
    steam_api_key = None
    with open('api_key.txt', 'r+') as api_file:
        try:
            steam_api_key = api_file.read()[14:]
        except IndexError:
            api_file.write("STEAM_API_KEY=")
            raise Exception("FormattingError: Entry in 'api_key.txt' was improperly formatted. Overwriting 'api_key.txt'. Ensure key is placed directly after 'STEAM_API_KEY='.")
        
        if len(steam_api_key) != 32 or not all(char in "0123456789ABCDEF" for char in steam_api_key):
            raise Exception("APIKeyError: Key provided in 'api_key.txt' is invalid. Key must be a 32 character hex code (e.g 'CCA45C7367A7B52CF1E50E2096134082'). Ensure key is placed directly after 'STEAM_API_KEY='.")
    
    return steam_api_key
    

def clear():
    """
    Clears console.
    """
    os.system('cls' if os.name=='nt' else 'clear')