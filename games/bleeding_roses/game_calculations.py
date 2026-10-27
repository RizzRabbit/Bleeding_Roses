"""Board transforms and ways scoring for Bleeding Roses."""

from src.calculations.statistics import get_random_outcome
from src.calculations.ways import Ways
from src.executables.executables import Executables


def quantize_win(amount):
    """Snap a win onto the 0.1x grid the RGS lookup table requires."""
    cents = int(round(float(amount) * 100))
    snapped = int(round(cents / 10.0)) * 10
    if snapped < 0:
        snapped = 0
    return snapped / 100.0


class GameCalculations(Executables):
    """Symbol access, rose transforms, and multiplier application."""

    def get_symbol_at_position(self, reel, row):
        """Return the symbol name at a visible board position."""
        symbol = self.board[reel][row]
        if symbol is None or symbol == 0 or symbol == []:
            return None
        return symbol.name

    def set_symbol_at_position(self, reel, row, symbol_name):
        """Replace one board position with a freshly built symbol."""
        self.board[reel][row] = self.create_symbol(symbol_name)
        return self.board[reel][row]

    def transform_roses_on_reel(self, reel):
        """Turn every plain rose on `reel` into its bloody version. Returns the changes."""
        changes = []
        for row in range(self.config.num_rows[reel]):
            name = self.get_symbol_at_position(reel, row)
            if not self.config.is_rose_symbol(name):
                continue
            bloody = self.config.transform_to_bloody(name)
            symbol = self.set_symbol_at_position(reel, row, bloody)
            symbol.assign_attribute({"bled": True})
            changes.append({"reel": reel, "row": row, "from": name, "to": bloody})
        return changes

    def bleeding_heart_reels(self):
        """Reels (restricted to the trigger reels) that currently show a Bleeding Heart."""
        reels = []
        rows_by_reel = {}
        for reel in self.config.bleed_reels:
            rows = []
            for row in range(self.config.num_rows[reel]):
                if self.get_symbol_at_position(reel, row) == self.config.wild_symbol:
                    rows.append(row)
            if rows:
                reels.append(reel)
                rows_by_reel[reel] = rows
        return reels, rows_by_reel

    def draw_bleed_multiplier(self):
        """2x, 3x or 5x, using the active distribution's weights."""
        weights = self.config.bleed_mult_weights
        conditions = self.get_current_distribution_conditions()
        if isinstance(conditions, dict) and conditions.get("bleed_mult_weights"):
            weights = conditions["bleed_mult_weights"]
        return int(get_random_outcome(weights))

    def score_ways(self):
        """Score left-to-right ways, then apply reel multipliers and the harvest global multiplier."""
        win_data = Ways.get_ways_data(
            self.config,
            self.board,
            global_multiplier=1,
            multiplier_strategy="global",
        )
        global_mult = max(int(self.global_multiplier), 1)
        kept = []
        for win in win_data["wins"]:
            reel_mult = 1
            touched = []
            for reel in range(win["kind"]):
                mult = int(self.reel_multipliers[reel])
                if mult > 1:
                    reel_mult *= mult
                    touched.append({"reel": reel, "multiplier": mult})
            base = quantize_win(win["meta"]["winWithoutMult"])
            amount = quantize_win(base * global_mult * reel_mult)
            if amount <= 0:
                continue
            win["win"] = amount
            win["meta"]["winWithoutMult"] = base
            win["meta"]["globalMult"] = global_mult
            win["meta"]["reelMult"] = reel_mult
            win["meta"]["reelMultipliers"] = touched
            kept.append(win)
        total = round(sum(win["win"] for win in kept), 2)
        self.win_data = {"totalWin": total, "wins": kept}
