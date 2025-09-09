"""Bleeding Roses game state management and spin logic."""

from game_override import GameStateOverride


class GameState(GameStateOverride):
    """Handle all game-logic and event updates for Bleeding Roses game."""

    def run_spin(self, sim):
        """Execute a single simulation spin for Bleeding Roses."""
        self.reset_seed(sim)
        self.repeat = True
        
        while self.repeat:
            self.reset_book()
            self.draw_board(emit_event=True)
            
            # Evaluate ways wins with bleeding transformation
            self.evaluate_bleeding_roses_board()
            
            self.win_manager.update_gametype_wins(self.gametype)
            
            # Check scatter condition and trigger free spins
            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()
            
            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        """Execute free spins with enhanced bloody rose frequency."""
        self.reset_fs_spin()
        
        while self.fs < self.tot_fs:
            self.update_freespin()
            self.draw_board(emit_event=True)
            
            # Evaluate with bleeding transformation
            self.evaluate_bleeding_roses_board()
            
            # Check for free spin retrigger
            if self.check_fs_condition():
                self.update_fs_retrigger_amt()
            
            self.win_manager.update_gametype_wins(self.gametype)
            
        self.end_freespin()
    
    def evaluate_bleeding_roses_board(self):
        """
        Evaluate the board with bleeding transformation mechanics.
        First calculates initial wins, then applies transformations, then recalculates.
        """
        # Use the bleeding roses specific evaluation logic
        self.evaluate_ways_board()
        
        # Apply bleeding transformation if Bleeding Heart symbols are present
        if hasattr(self, 'game_calculations'):
            transformation_result = self.game_calculations.evaluate_bleeding_transformation()
            if transformation_result:
                # Recalculate wins after transformation
                self.evaluate_ways_board()
