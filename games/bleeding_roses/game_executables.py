"""Apply bleed rules, then score the board and emit win events."""

from game_calculations import GameCalculations
from game_events import (
    board_after_bleed_event,
    full_bleed_event,
    global_multiplier_event,
    reel_bleed_event,
    sticky_bleed_event,
    sticky_reel_event,
)
from src.calculations.ways import Ways


class GameExecutables(GameCalculations):
    """One reveal's worth of Bleeding Roses actions."""

    def resolve_board(self):
        """Transform the revealed board, then evaluate ways on the result."""
        self.reel_multipliers = [1] * self.config.num_reels
        self.pending_board_update = False
        feature = self._active_feature()

        if feature == "full_bleed":
            self._apply_full_bleed()
        if feature == "blood_moon":
            for reel, multiplier in self.sticky_multipliers.items():
                self.reel_multipliers[reel] = multiplier
            self._apply_sticky_roses()
        self._apply_bleed(feature)
        if self.pending_board_update:
            board_after_bleed_event(self)
        self.evaluate_ways_board()

    def evaluate_ways_board(self):
        """Record ways wins against the post-bleed board and emit the standard win events."""
        self.score_ways()
        if self.win_data["totalWin"] > 0:
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
        Ways.emit_wayswin_events(self)

    def _active_feature(self):
        if self.gametype == self.config.freegame_type and self.bonus_tier:
            return self.bonus_tier
        if self.betmode == self.config.full_bleed_mode:
            return "full_bleed"
        return "base"

    def _apply_full_bleed(self):
        changes = []
        for reel in range(self.config.num_reels):
            changes.extend(self.transform_roses_on_reel(reel))
        if changes:
            full_bleed_event(self, changes)
            self.pending_board_update = True

    def _apply_sticky_roses(self):
        changes = []
        for reel in self.sticky_reels:
            changes.extend(self.transform_roses_on_reel(reel))
        if changes:
            sticky_bleed_event(self, changes)
            self.pending_board_update = True

    def _apply_bleed(self, feature):
        heart_reels, rows_by_reel = self.bleeding_heart_reels()
        if not heart_reels:
            return

        assign_multiplier = feature in ("base", "full_bleed")
        if feature in ("bleeding_spins", "reapers_harvest"):
            transform_reels = list(range(self.config.num_reels))
            scope = "board"
        else:
            transform_reels = list(heart_reels)
            scope = "reel"

        if feature == "blood_moon":
            # A reel locks the first time a heart lands on it. The 2x/3x/5x drawn
            # then is the reel's multiplier for the rest of the bonus, including
            # this spin. Later hearts on that reel do not reroll it.
            newly_locked = []
            for reel in heart_reels:
                if reel in self.sticky_multipliers:
                    continue
                multiplier = self.draw_bleed_multiplier()
                self.sticky_multipliers[reel] = multiplier
                self.reel_multipliers[reel] = multiplier
                self.sticky_reels.append(reel)
                newly_locked.append(reel)
            if newly_locked:
                sticky_reel_event(self, newly_locked)

        changes_by_reel = {}
        for reel in transform_reels:
            changes_by_reel[reel] = self.transform_roses_on_reel(reel)

        for reel in range(self.config.num_reels):
            changes = changes_by_reel.get(reel, [])
            is_trigger = reel in rows_by_reel
            if not changes and not is_trigger:
                continue
            multiplier = None
            if assign_multiplier and is_trigger:
                multiplier = self.draw_bleed_multiplier()
                self.reel_multipliers[reel] = multiplier
            elif feature == "blood_moon" and is_trigger:
                multiplier = self.sticky_multipliers[reel]
            reel_bleed_event(
                self,
                reel,
                scope,
                rows_by_reel.get(reel, []),
                changes,
                multiplier,
            )
            self.pending_board_update = True

        if feature == "reapers_harvest":
            # One step per bleeding spin, not per heart. Per-heart steps pushed the
            # median Harvest onto the 15000x base cap; the cap stays a tail here,
            # and the dedicated max-win reel is what guarantees a 15000x book.
            self.global_multiplier += 1
            global_multiplier_event(
                self,
                increment=1,
                reel=heart_reels[0],
                heart_reels=heart_reels,
            )
