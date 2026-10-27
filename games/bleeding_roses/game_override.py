"""Per-spin state for Bleeding Roses."""

from game_calculations import quantize_win
from game_events import freespin_end_event
from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Reset bleed state and fail loudly if a max-win search cannot land."""

    def reset_book(self):
        super().reset_book()
        self.bonus_tier = None
        self.sticky_reels = []
        self.sticky_multipliers = {}
        self.reel_multipliers = [1] * self.config.num_reels
        self.pending_board_update = False

    def assign_special_sym_function(self):
        self.special_symbol_functions = {}

    def _publish_capped_split(self):
        """Put running, base, and free wins on the capped 0.1x split the book will publish.

        end_freespin runs before update_final_win. Without this snap, a capped round
        that also won in the base game still reports the full cap as the free-spin total.
        """
        cap = quantize_win(self.config.wincap)
        total = quantize_win(min(self.win_manager.running_bet_win, cap))
        base = quantize_win(min(self.win_manager.basegame_wins, total))
        free = quantize_win(max(total - base, 0))
        if quantize_win(base + free) != total:
            free = quantize_win(total - base)
        self.win_manager.running_bet_win = total
        self.win_manager.basegame_wins = base
        self.win_manager.freegame_wins = quantize_win(total - base)

    def update_final_win(self):
        """Snap the published payout onto the 0.1x grid before the base/free split is checked."""
        self._publish_capped_split()
        super().update_final_win()

    def end_freespin(self) -> None:
        """Transmit the capped freegame portion with rounded book units."""
        self._publish_capped_split()
        freespin_end_event(self)

    def check_repeat(self):
        super().check_repeat()
        if self.criteria == "wincap" and self.repeat and self.repeat_count > self.config.wincap_attempt_limit:
            raise RuntimeError(
                f"{self.betmode} wincap was not reached after {self.repeat_count} attempts "
                f"(sim {self.sim}). The max-win reel is not producing the cap."
            )
