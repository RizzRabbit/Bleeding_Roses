"""Bleeding Roses configuration.

Tunable design numbers live in this file:

- `TIERS` — free-spin length and retrigger length per Reaper count.
- `BLEED_MULT_WEIGHTS` — 2x / 3x / 5x reel-multiplier weights in the base game
  and on the Full Bleed spin.
- `BLOOD_MOON_MULT_WEIGHTS` — the same ladder, drawn once when a Blood Moon
  reel locks and kept for the rest of that bonus. Bleeding Spins and
  Reaper's Harvest do not stamp reel multipliers.
- `BUY_*_COST` and `FULL_BLEED_COST` — price of each paid mode, in base bets.
  Buys are fixed at 100x / 300x / 600x. Full Bleed stays 100x. The free-spin
  strips are tuned so each buy returns 96% of that price.
- `SUPER_ANTE_VARIANTS` — published super-ante prices. Only the 20x ante is
  published. Remove a tuple to drop that mode from books, optimization, and
  the frontend config.

The max win is 15000x the base bet on every mode. It is not multiplied by the
mode cost. A 20x ante that caps still pays 15000x base (750x the debit).

Bet modes each draw their own free-spin strips where the shared strip cannot
serve both the 96% target and a real 15000x book:

- base and bloodlust share BR0 / FRB / FRM / FRH. Bloodlust only differs by
  how often the optimizer deals a bonus.
- super_ante_20 draws FRM20 and FRH20.
- each buy draws that tier's strip, and FRW when the book is a max win.
- full_bleed draws FB0, or FBW for a max-win book.
"""

import os

from src.config.betmode import BetMode
from src.config.config import Config
from src.config.distributions import Distribution


TIERS = {
    3: {
        "id": "bleeding_spins",
        "name": "Bleeding Spins",
        "spins": 10,
        "retrigger": 5,
        "board_bleed": True,
        "sticky": False,
        "global_mult": False,
    },
    4: {
        "id": "blood_moon",
        "name": "Blood Moon",
        "spins": 12,
        "retrigger": 6,
        "board_bleed": False,
        "sticky": True,
        "global_mult": False,
    },
    5: {
        "id": "reapers_harvest",
        "name": "Reaper's Harvest",
        "spins": 15,
        "retrigger": 8,
        "board_bleed": True,
        "sticky": False,
        "global_mult": True,
        # The global multiplier advances once per spin that bleeds, not once per heart.
        "global_step": "spin",
    },
}

# Only the 20x super ante is published.
SUPER_ANTE_VARIANTS = (("super_ante_20", 20.0),)

# Fixed prices, measured in base bets. At 96% RTP the buy pays about
# 96x, 288x, and 576x. The free-spin strips are tuned to those means.
BUY_BLEEDING_COST = 100.0
BUY_MOON_COST = 300.0
BUY_HARVEST_COST = 600.0
FULL_BLEED_COST = 100.0

BLEED_MULT_WEIGHTS = {2: 82, 3: 14, 5: 4}
# Drawn once per sticky reel and kept for the bonus. Cool enough that a
# 300x Blood Moon buy lands near 288x, above Bleeding Spins and under Harvest.
BLOOD_MOON_MULT_WEIGHTS = {2: 70, 3: 23, 5: 7}
WINCAP_BLEED_WEIGHTS = {2: 5, 3: 15, 5: 80}


def _pays():
    """Pays are on a 0.1x grid. Bloody roses are exactly 3x the plain rose."""
    plain = {
        (3, "10"): 0.1, (4, "10"): 0.2, (5, "10"): 0.5,
        (3, "J"): 0.1, (4, "J"): 0.2, (5, "J"): 0.5,
        (3, "Q"): 0.1, (4, "Q"): 0.3, (5, "Q"): 0.8,
        (3, "K"): 0.2, (4, "K"): 0.4, (5, "K"): 1.0,
        (3, "A"): 0.2, (4, "A"): 0.5, (5, "A"): 1.2,
        (3, "WR"): 0.4, (4, "WR"): 0.8, (5, "WR"): 2.0,
        (3, "RR"): 0.5, (4, "RR"): 1.2, (5, "RR"): 3.0,
        (3, "BR"): 0.6, (4, "BR"): 1.6, (5, "BR"): 4.0,
        (3, "BH"): 1.0, (4, "BH"): 4.0, (5, "BH"): 15.0,
    }
    roses = {"WR": "BWR", "RR": "BRR", "BR": "BBR"}
    paytable = dict(plain)
    for (kind, symbol), payout in list(plain.items()):
        if symbol in roses:
            paytable[(kind, roses[symbol])] = round(payout * 3, 2)
    return paytable


class GameConfig(Config):
    """Bleeding Roses, 5x4 ways."""

    def __init__(self):
        super().__init__()
        self.game_id = "bleeding_roses"
        self.provider_number = 1
        self.provider_name = "Rizzin Games"
        self.working_name = "Bleeding Roses"
        self.game_name = "Bleeding Roses"
        # 15000x the base bet. Antes and buys do not scale this number.
        self.wincap = 15000.0
        self.win_type = "ways"
        self.rtp = 0.96
        self.wincap_attempt_limit = 2500
        self.construct_paths()
        self._set_win_levels()

        self.num_reels = 5
        self.num_rows = [4] * self.num_reels
        self.paytable = _pays()
        self.include_padding = True

        self.low_symbols = ["10", "J", "Q", "K", "A"]
        self.rose_symbols = ["WR", "RR", "BR"]
        self.bloody_symbols = ["BWR", "BRR", "BBR"]
        self.wild_symbol = "BH"
        self.scatter_symbol = "RP"
        self.all_symbols = (
            self.low_symbols
            + self.rose_symbols
            + self.bloody_symbols
            + [self.wild_symbol, self.scatter_symbol]
        )
        self.special_symbols = {
            "wild": [self.wild_symbol],
            "scatter": [self.scatter_symbol],
            "multiplier": [],
            "bled": [],
        }
        self.all_valid_sym_names = set(self.all_symbols)

        self.tiers = TIERS
        self.bleed_reels = [1, 2, 3]
        self.full_bleed_mode = "full_bleed"
        self.bleed_mult_weights = dict(BLEED_MULT_WEIGHTS)
        self.blood_moon_mult_weights = dict(BLOOD_MOON_MULT_WEIGHTS)
        self.wincap_bleed_weights = dict(WINCAP_BLEED_WEIGHTS)
        self.rose_map = {"WR": "BWR", "RR": "BRR", "BR": "BBR"}

        self.freespin_triggers = {
            self.basegame_type: {count: info["spins"] for count, info in TIERS.items()},
            self.freegame_type: {count: info["retrigger"] for count, info in TIERS.items()},
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 2}

        reel_files = {
            "BR0": "BR0.csv",
            "FRB": "FRB.csv",
            "FRM": "FRM.csv",
            "FRH": "FRH.csv",
            "FRM20": "FRM20.csv",
            "FRH20": "FRH20.csv",
            "FRW": "FRW.csv",
            "FB0": "FB0.csv",
            "FBW": "FBW.csv",
        }
        self.reels = {}
        for reel_id, filename in reel_files.items():
            self.reels[reel_id] = self.read_reels_csv(os.path.join(self.reels_path, filename))
            self.validate_reel_symbols(self.reels[reel_id])

        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["FRB"]

        base_reels = {"BR0": 1}
        cap_reels = {"FRW": 1}
        standard_tiers = {
            "reapers_harvest": {"FRH": 1},
            "blood_moon": {"FRM": 1},
            "bleeding_spins": {"FRB": 1},
        }
        ante_tiers = {
            "super_ante_20": {
                "reapers_harvest": {"FRH20": 1},
                "blood_moon": {"FRM20": 1},
                "bleeding_spins": {"FRB": 1},
            },
        }

        self.bet_modes = [
            self._mode("base", 1.0, self._natural_distributions(standard_tiers, base_reels, cap_reels)),
            self._mode(
                "bloodlust", 3.0, self._natural_distributions(standard_tiers, base_reels, cap_reels)
            ),
            *[
                self._mode(
                    name,
                    cost,
                    self._super_distributions(ante_tiers[name], base_reels, cap_reels),
                )
                for name, cost in SUPER_ANTE_VARIANTS
            ],
            self._mode(
                "buy_bleeding",
                BUY_BLEEDING_COST,
                self._buy_distributions("bleeding_spins", 3, {"FRB": 1}, cap_reels, base_reels),
                buy=True,
            ),
            self._mode(
                "buy_blood_moon",
                BUY_MOON_COST,
                self._buy_distributions(
                    "blood_moon",
                    4,
                    {"FRM": 1},
                    cap_reels,
                    base_reels,
                    bleed_weights=self.blood_moon_mult_weights,
                ),
                buy=True,
            ),
            self._mode(
                "buy_harvest",
                BUY_HARVEST_COST,
                self._buy_distributions("reapers_harvest", 5, {"FRH": 1}, cap_reels, base_reels),
                buy=True,
            ),
            self._mode(
                "full_bleed",
                FULL_BLEED_COST,
                self._full_bleed_distributions(),
                feature=True,
            ),
        ]

    def _set_win_levels(self):
        cap = self.wincap
        self.win_levels = {
            "standard": {
                1: (0, 0.1),
                2: (0.1, 1.0),
                3: (1.0, 2.0),
                4: (2.0, 5.0),
                5: (5.0, 15.0),
                6: (15.0, 50.0),
                7: (50.0, 150.0),
                8: (150.0, 500.0),
                9: (500.0, cap),
                10: (cap, float("inf")),
            },
            "endFeature": {
                1: (0.0, 1.0),
                2: (1.0, 10.0),
                3: (10.0, 25.0),
                4: (25.0, 50.0),
                5: (50.0, 100.0),
                6: (100.0, 250.0),
                7: (250.0, 1000.0),
                8: (1000.0, 5000.0),
                9: (5000.0, cap),
                10: (cap, float("inf")),
            },
        }

    def _mode(self, name, cost, distributions, buy=False, feature=False):
        return BetMode(
            name=name,
            cost=float(cost),
            rtp=self.rtp,
            max_win=self.wincap,
            auto_close_disabled=buy,
            is_feature=feature or not buy,
            is_buybonus=buy,
            distributions=distributions,
        )

    def _distribution(
        self,
        criteria,
        quota,
        base_reels,
        free_reels=None,
        scatters=None,
        force_free=False,
        win_criteria=None,
        bleed_weights=None,
    ):
        conditions = {
            "reel_weights": {self.basegame_type: base_reels},
            "force_wincap": criteria == "wincap",
            "force_freegame": force_free,
            "bleed_mult_weights": bleed_weights or self.bleed_mult_weights,
        }
        if free_reels is not None:
            conditions["reel_weights"][self.freegame_type] = free_reels
        if scatters is not None:
            conditions["scatter_triggers"] = scatters
        return Distribution(
            criteria=criteria,
            quota=quota,
            win_criteria=win_criteria,
            conditions=conditions,
        )

    def _wincap_distribution(self, quota, base_reels, free_reels, scatter_count):
        return self._distribution(
            "wincap",
            quota,
            base_reels,
            free_reels=free_reels,
            scatters={scatter_count: 1},
            force_free=True,
            win_criteria=self.wincap,
            bleed_weights=self.wincap_bleed_weights,
        )

    def _tier_block(self, tier_reels, base_reels, quotas):
        """One distribution per tier, each pulling that tier's own free-spin strip."""
        block = []
        for tier, quota in quotas:
            count, _info = self.tier_by_id(tier)
            weights = self.blood_moon_mult_weights if tier == "blood_moon" else None
            block.append(
                self._distribution(
                    tier,
                    quota,
                    base_reels,
                    tier_reels[tier],
                    {count: 1},
                    force_free=True,
                    bleed_weights=weights,
                )
            )
        return block

    def _natural_distributions(self, tier_reels, base_reels, cap_reels):
        """Quotas oversample features. Published rates come from optimization weights."""
        return [
            self._wincap_distribution(0.01, base_reels, cap_reels, 5),
            *self._tier_block(
                tier_reels,
                base_reels,
                (("reapers_harvest", 0.06), ("blood_moon", 0.08), ("bleeding_spins", 0.12)),
            ),
            self._distribution("0", 0.33, base_reels, win_criteria=0.0),
            self._distribution("basegame", 0.40, base_reels),
        ]

    def _super_distributions(self, tier_reels, base_reels, cap_reels):
        return [
            self._wincap_distribution(0.015, base_reels, cap_reels, 5),
            *self._tier_block(
                tier_reels,
                base_reels,
                (("reapers_harvest", 0.14), ("blood_moon", 0.14), ("bleeding_spins", 0.07)),
            ),
            self._distribution("0", 0.275, base_reels, win_criteria=0.0),
            self._distribution("basegame", 0.36, base_reels),
        ]

    def _buy_distributions(self, criteria, scatter_count, free_reels, hot_reels, base_reels, bleed_weights=None):
        return [
            self._wincap_distribution(0.02, base_reels, hot_reels, scatter_count),
            self._distribution(
                criteria,
                0.98,
                base_reels,
                free_reels,
                {scatter_count: 1},
                force_free=True,
                bleed_weights=bleed_weights,
            ),
        ]

    def _full_bleed_distributions(self):
        return [
            self._distribution(
                "wincap",
                0.02,
                {"FBW": 1},
                win_criteria=self.wincap,
                bleed_weights=self.wincap_bleed_weights,
            ),
            self._distribution("0", 0.28, {"FB0": 1}, win_criteria=0.0),
            self._distribution("full_bleed", 0.70, {"FB0": 1}),
        ]

    def tier_by_id(self, tier_id):
        for count, info in self.tiers.items():
            if info["id"] == tier_id:
                return count, info
        raise KeyError(tier_id)

    def get_symbol_mapping(self):
        return dict(self.rose_map)

    def is_rose_symbol(self, symbol):
        return symbol in self.rose_symbols

    def is_bloody_rose(self, symbol):
        return symbol in self.bloody_symbols

    def transform_to_bloody(self, symbol):
        return self.rose_map.get(symbol, symbol)

    def get_ways_to_win(self):
        ways = 1
        for rows in self.num_rows:
            ways *= rows
        return ways
