"""Bleeding Roses game configuration file."""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.config import BetMode


class GameConfig(Config):
    """Bleeding Roses configuration class."""

    def __init__(self):
        super().__init__()
        
        # Game Identity
        self.game_id = "bleeding_roses"
        self.provider_number = 1
        self.working_name = "Bleeding Roses"
        self.wincap = 1000  # 1000x max win (more reasonable for 96% RTP)
        self.win_type = "ways"  # 1024 ways to win
        self.rtp = .96  # 96% RTP
        self.construct_paths()

        # Game Dimensions - 5x4 reels
        self.num_reels = 5
        self.num_rows = [4, 4, 4, 4, 4]  # 4 rows per reel
        
        # Symbol Definitions
        # Low paying symbols (cards)
        self.low_symbols = ["10", "J", "Q", "K", "A"]
        # Medium paying symbols (roses)
        self.rose_symbols = ["WR", "RR", "BR"]  # White Rose, Red Rose, Black Rose
        # High paying symbols (bloody roses)
        self.bloody_symbols = ["BWR", "BRR", "BBR"]  # Bloody variants (3x value)
        # Special symbols
        self.wild_symbol = "BH"  # Bleeding Heart (wild + transformation)
        self.scatter_symbol = "RP"  # Reaper (scatter)

        # All symbols list
        self.all_symbols = (self.low_symbols + self.rose_symbols + 
                           self.bloody_symbols + [self.wild_symbol, self.scatter_symbol])

        # Paytable (for $1 bet) - format: (length, symbol): payout  
        self.paytable = {
            # Low paying symbols (calibrated for 96% RTP)
            (3, "10"): 0.08, (4, "10"): 0.22, (5, "10"): 0.41,
            (3, "J"):  0.08, (4, "J"):  0.22, (5, "J"):  0.49,
            (3, "Q"):  0.14, (4, "Q"):  0.33, (5, "Q"):  0.60,
            (3, "K"):  0.14, (4, "K"):  0.41, (5, "K"):  0.68,
            (3, "A"):  0.22, (4, "A"):  0.49, (5, "A"):  0.82,
            
            # Rose symbols (scaled up)
            (3, "WR"): 0.33, (4, "WR"): 0.68, (5, "WR"): 1.37,   # White Rose
            (3, "RR"): 0.49, (4, "RR"): 0.96, (5, "RR"): 2.05,   # Red Rose
            (3, "BR"): 0.68, (4, "BR"): 1.37, (5, "BR"): 2.74,   # Black Rose
            
            # Bloody roses (scaled up)
            (3, "BWR"): 0.96, (4, "BWR"): 2.05, (5, "BWR"): 4.11,    # Bloody White Rose
            (3, "BRR"): 1.37, (4, "BRR"): 2.74, (5, "BRR"): 6.16,    # Bloody Red Rose  
            (3, "BBR"): 2.05, (4, "BBR"): 4.11, (5, "BBR"): 8.22,    # Bloody Black Rose
            
            # Wild symbol (scaled up but controlled)
            (3, "BH"): 3.42, (4, "BH"): 13.7, (5, "BH"): 34.3,  # Bleeding Heart Wild
        }

        self.include_padding = True
        
        # Special symbol properties
        self.special_symbols = {
            "wild": ["BH"],  # Bleeding Heart is wild
            "scatter": ["RP"],  # Reaper is scatter
            "multiplier": []
        }

        # Free spin triggers (scatter count: free spins awarded)
        self.freespin_triggers = {
            self.basegame_type: {3: 10, 4: 15, 5: 20},  # 3+ reapers = 10/15/20 free spins
            self.freegame_type: {3: 5, 4: 10, 5: 15}    # Retrigger with fewer spins
        }
        
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 2}

        # Reel files
        reels = {
            "BR0": "bleeding_roses_base.csv",    # Base game reels
            "FR0": "bleeding_roses_free.csv"     # Free spins reels
        }
        
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(str.join("/", [self.reels_path, f]))

        # Bet modes configuration
        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    # Simple base game distribution (100% of spins)
                    Distribution(
                        criteria="basegame",
                        quota=1.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "scatter_triggers": {},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            # Bonus Buy Mode - 200x cost to guarantee free spins
            BetMode(
                name="bonus",
                cost=200.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    # Bonus buy - single spin then enter free spins
                    Distribution(
                        criteria="basegame",
                        quota=1.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "scatter_triggers": {3: 1.0},  # Always trigger with 3 scatters
                            "force_wincap": False,
                            "force_freegame": False,  # Let scatter_triggers handle it
                        },
                    ),
                ],
            ),
        ]

        # Bleeding transformation configuration
        self.transformation_config = {
            "trigger_symbol": "BH",  # Bleeding Heart triggers transformation
            "target_symbols": ["WR", "RR", "BR"],  # Regular roses to transform
            "result_symbols": ["BWR", "BRR", "BBR"],  # Bloody rose results
            "trigger_reels": [1, 2, 3],  # Bleeding Heart appears on reels 2,3,4 (0-indexed: 1,2,3)
            "multiplier": 3  # Bloody roses pay 3x original value
        }

    def get_symbol_mapping(self):
        """Return mapping of regular roses to bloody roses."""
        return {
            "WR": "BWR",   # White Rose -> Bloody White Rose
            "RR": "BRR",   # Red Rose -> Bloody Red Rose  
            "BR": "BBR"    # Black Rose -> Bloody Black Rose
        }

    def is_rose_symbol(self, symbol):
        """Check if symbol is a regular rose that can be transformed."""
        return symbol in self.rose_symbols

    def is_bloody_rose(self, symbol):
        """Check if symbol is already a bloody rose."""
        return symbol in self.bloody_symbols

    def transform_to_bloody(self, symbol):
        """Transform a regular rose to its bloody variant."""
        mapping = self.get_symbol_mapping()
        return mapping.get(symbol, symbol)

    def get_ways_to_win(self):
        """Calculate total ways to win for 5x4 grid."""
        return 4 * 4 * 4 * 4 * 4  # 1024 ways