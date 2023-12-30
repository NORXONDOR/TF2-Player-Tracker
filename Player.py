class Player:
    """
    Stores information about TF2 players in a match or loaded from a database.
    
    Global variables:
        (list[Player]) player_list: List of TF2 players in memory.
        (dict{string: Player}) player_dict: Maps Player objects to steamID64 for efficient lookup.
    """
    player_list = [] # List of TF2 players in the database.
    player_dict = {} # Maps player objects to steamID64s for efficient lookup.

    def __init__(self, steamid64, aliases, trust_level=0, notes=" "):
        """
        Initialises a Player object.
        
        Args:
            (string) steamid64: e.g 76561199023358361. Used as primary key in Player lookups.
            (list[string]) aliases: List of each username a Player has been seen with. aliases[-1] represents their current name.
            (int) trust_level: Percieved trustworthiness of player.
                0: Tracked; Player is in the database/memory without a status. Default value.
                1: Trusted; Player is not a cheater/bot.
                2: Suspicious; Player might be a cheater/bot.
                3: Cheater/bot; Player is a cheater/bot.
            (string) notes: Additional subjective information about a player, optional.
            
        Object variables:
            (string) steamid64: See eponym.
            (list[string]) aliases: See eponym.
            (int) trust_level: See eponym.
            (string) notes: See eponym.
            (list[Player]) friends: A list of all Players in a database who are Steam friends with the Player.
        """
        self.steamid64 = steamid64

        for alias in aliases:
            if len(alias.encode('utf8')) > 32: # Steam alias byte limit.
                raise Exception(f"Alias '{alias}' in aliases is larger than 32 bytes (UTF-8)! Aborting.")

        self.aliases = aliases

        if trust_level >= 0 or trust_level <= 3:
            self.trust_level = trust_level
        else:
            print(f"trust_level {trust_level} invalid! Value must be between 0-3. Defaulting to 0.")
            self.trust_level = 0

        self.notes = notes
        self.friends = []

        Player.player_dict[steamid64] = self
        Player.player_list.append(self)
        
    def add_friends(self, friends):
        """
        Populates a Players friends list, assuming they are not already in the list.
        
        Args:
            (list[Player]) friends: A list of all Players in a database who are Steam friends with the Player.
        """
        for friend in friends:
            friend_obj = Player.player_dict[friend]

            if friend_obj not in self.friends:
                self.friends.append(friend_obj)
                friend_obj.friends.append(self)
            else:
                print(f"Player with steamid64 '{friend}' already in '{self.steamid64}''s friends list! Player is not being added.")

    def get_friend_trusts(self):
        """
        Returns the counts of a Player's friends' trusts.
        
        Return:
            (list[int]) trusts: Counts of Player's friends' trusts.
        """
        friend_trusts = []
        for friend in self.friends:
            friend_trusts.append(friend.trust_level)

        count_0 = 0
        count_1 = 0
        count_2 = 0
        count_3 = 0
        for trust in friend_trusts:
            match trust:
                case 0:
                    count_0 += 1
                case 1:
                    count_1 += 1
                case 2:
                    count_2 += 1
                case 3:
                    count_3 += 1
        
        # [5, 2, 1, 3]; [0] = 5 trackeds, [1] = 2 trusteds, [2] = 1 susses, [3] = 3 bots/cheaters.
        trusts = [count_0, count_1, count_2, count_3]
        return trusts

    @classmethod
    def who(cls):
        """
        Returns list containing all Player object.
        """
        return cls.player_list
        
    @classmethod
    def clear_runtime(cls):
        """
        Removes references to Players in memory.
        """
        cls.player_list = []
        cls.player_dict = {}