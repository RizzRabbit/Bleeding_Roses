"""Base spins, free-spin tiers, and retriggers for Bleeding Roses."""

from game_events import bonus_tier_event, retrigger_event
from game_override import GameStateOverride
from src.events.events import enter_bonus_event, fs_trigger_event


class GameState(GameStateOverride):
    """Handle a single simulation, including the repeat used to satisfy bet-mode criteria."""

    def run_spin(self, sim):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board(emit_event=True)
            self.resolve_board()
            self.win_manager.update_gametype_wins(self.gametype)
            if self._should_enter_bonus():
                self.run_freespin_from_base()
            self.evaluate_finalwin()
            self.check_repeat()
        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()
        self.sticky_reels = []
        self.sticky_multipliers = {}
        if self.bonus_tier == "reapers_harvest":
            self.global_multiplier = 1
        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.update_freespin()
            self.draw_board(emit_event=True)
            self.resolve_board()
            if self.check_fs_condition() and not self.wincap_triggered:
                self.update_fs_retrigger_amt()
            self.win_manager.update_gametype_wins(self.gametype)
        self.end_freespin()

    def run_freespin_from_base(self, scatter_key="scatter"):
        count = self._scatter_count(scatter_key)
        tier = self.config.tiers[count]
        self.bonus_tier = tier["id"]
        self.record(
            {
                "kind": count,
                "symbol": "scatter",
                "gametype": self.gametype,
                "tier": self.bonus_tier,
            }
        )
        self.tot_fs = tier["spins"]
        fs_trigger_event(self, basegame_trigger=True, freegame_trigger=False)
        self.bonus_type = self.bonus_tier
        enter_bonus_event(self)
        bonus_tier_event(self)
        self.run_freespin()

    def update_fs_retrigger_amt(self, scatter_key="scatter"):
        count = self._scatter_count(scatter_key)
        added = self.config.freespin_triggers[self.config.freegame_type][count]
        self.tot_fs += added
        fs_trigger_event(self, freegame_trigger=True, basegame_trigger=False)
        retrigger_event(self, added, count)

    def _should_enter_bonus(self):
        if self.betmode == self.config.full_bleed_mode or self.wincap_triggered:
            return False
        return self.check_fs_condition() and self.check_freespin_entry()

    def _scatter_count(self, scatter_key):
        count = self.count_special_symbols(scatter_key)
        max_count = max(self.config.tiers)
        return min(count, max_count)
