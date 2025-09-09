from game_calculations import GameCalculations
from src.calculations.ways import Ways


class GameExecutables(GameCalculations):
    """Events and calculations specific to Bleeding Roses ways wins with transformation."""

    def evaluate_ways_board(self):
        """
        Populate win-data, record wins, transmit events for Bleeding Roses.
        This integrates with the bleeding transformation mechanics.
        """
        # Get ways win data using the standard Ways calculation
        self.win_data = Ways.get_ways_data(self.config, self.board)
        
        # Apply bleeding rose transformation logic from our game calculations
        transformation_result = self.evaluate_final_win()
        
        # Update win data with transformation results if any
        if transformation_result and transformation_result.get("transformation_occurred"):
            # Recalculate ways after transformation
            self.win_data = Ways.get_ways_data(self.config, self.board)
            
            # Add transformation events to win data
            if "transformation_events" not in self.win_data:
                self.win_data["transformation_events"] = []
            self.win_data["transformation_events"].extend(transformation_result["transformation_events"])
        
        # Record wins if any exist
        if self.win_data["totalWin"] > 0:
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
            
        # Emit events including transformation events
        Ways.emit_wayswin_events(self)
        self.emit_transformation_events()
