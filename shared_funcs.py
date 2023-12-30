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