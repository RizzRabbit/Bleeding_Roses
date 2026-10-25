"""Per-spin state for Bleeding Roses."""

from game_calculations import quantize_win
from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Reset bleed state and fail loudly if a max-win search cannot land."""

    def reset_book(self):
        super().reset_book()
        self.bonus_tier = None
        self.sticky_reels = []
        self.reel_multipliers = [1] * self.config.num_reels
        self.pending_board_update = False

    def assign_special_sym_function(self):
        self.special_symbol_functions = {}

    def update_final_win(self):
        """Snap the published payout onto the 0.1x grid before the base/free split is checked."""
        cap = quantize_win(self.config.wincap)
        total = quantize_win(min(self.win_manager.running_bet_win, cap))
        base = quantize_win(min(self.win_manager.basegame_wins, total))
        free = quantize_win(max(total - base, 0))
        if quantize_win(base + free) != total:
            free = quantize_win(total - base)
        self.win_manager.running_bet_win = total
        self.win_manager.basegame_wins = base
        self.win_manager.freegame_wins = quantize_win(total - base)
        super().update_final_win()

    def check_repeat(self):
        super().check_repeat()
        if self.criteria == "wincap" and self.repeat and self.repeat_count > self.config.wincap_attempt_limit:
            raise RuntimeError(
                f"{self.betmode} wincap was not reached after {self.repeat_count} attempts "
                f"(sim {self.sim}). The max-win reel is not producing the cap."
            )
