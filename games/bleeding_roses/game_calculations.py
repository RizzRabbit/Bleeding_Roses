"""Bleeding Roses game calculations and logic."""

from src.executables.executables import Executables
from src.events.events import EventConstants


class GameCalculations(Executables):
    """Bleeding Roses specific game calculations."""

    def __init__(self, config):
        super().__init__(config)
        self.transformation_events = []

    def evaluate_bleeding_transformation(self):
        """
        Check for Bleeding Heart symbols and transform roses on same reels.
        This is the core mechanic of Bleeding Roses.
        """
        transformation_occurred = False
        
        # Check each reel for Bleeding Heart symbols
        for reel_idx in range(self.config.num_reels):
            if self.has_bleeding_heart_on_reel(reel_idx):
                # Transform all roses on this reel to bloody variants
                transformed_positions = self.transform_roses_on_reel(reel_idx)
                
                if transformed_positions:
                    transformation_occurred = True
                    # Create transformation event for frontend
                    self.add_transformation_event(reel_idx, transformed_positions)
        
        return transformation_occurred

    def has_bleeding_heart_on_reel(self, reel_idx):
        """Check if Bleeding Heart symbol appears on specified reel."""
        # Only check reels 1, 2, 3 (0-indexed) where Bleeding Heart can appear
        if reel_idx not in self.config.transformation_config["trigger_reels"]:
            return False
            
        for row in range(self.config.num_rows[reel_idx]):
            symbol = self.get_symbol_at_position(reel_idx, row)
            if symbol == self.config.transformation_config["trigger_symbol"]:
                return True
        return False

    def transform_roses_on_reel(self, reel_idx):
        """Transform all rose symbols on specified reel to bloody variants."""
        transformed_positions = []
        
        for row in range(self.config.num_rows[reel_idx]):
            symbol = self.get_symbol_at_position(reel_idx, row)
            
            if self.config.is_rose_symbol(symbol):
                # Transform to bloody variant
                bloody_symbol = self.config.transform_to_bloody(symbol)
                self.set_symbol_at_position(reel_idx, row, bloody_symbol)
                transformed_positions.append((reel_idx, row, symbol, bloody_symbol))
        
        return transformed_positions

    def add_transformation_event(self, reel_idx, transformed_positions):
        """Create event for bleeding transformation animation."""
        event = {
            "event_type": "bleeding_transformation",
            "data": {
                "trigger_reel": reel_idx,
                "transformations": transformed_positions,
                "blood_drip_animation": True
            }
        }
        self.transformation_events.append(event)

    def calculate_ways_wins(self):
        """
        Calculate wins using 1024 ways to win method.
        Symbols must appear on adjacent reels from left to right.
        """
        all_wins = []
        
        # Check for each symbol type
        for symbol in self.config.all_symbols:
            if symbol in [self.config.scatter_symbol]:  # Skip scatters for ways wins
                continue
                
            wins = self.find_ways_wins_for_symbol(symbol)
            all_wins.extend(wins)
        
        return all_wins

    def find_ways_wins_for_symbol(self, target_symbol):
        """Find all ways wins for a specific symbol."""
        wins = []
        
        # Start from leftmost reel and check consecutive reels
        for start_reel in range(self.config.num_reels):
            positions_by_reel = []
            
            # Find all positions of this symbol starting from start_reel
            for reel_idx in range(start_reel, self.config.num_reels):
                positions_on_reel = []
                
                for row in range(self.config.num_rows[reel_idx]):
                    symbol = self.get_symbol_at_position(reel_idx, row)
                    
                    # Wild substitution logic
                    if (symbol == target_symbol or 
                        (symbol == self.config.wild_symbol and target_symbol != self.config.wild_symbol) or
                        (target_symbol == self.config.wild_symbol and symbol == self.config.wild_symbol)):
                        positions_on_reel.append((reel_idx, row))
                
                if positions_on_reel:
                    positions_by_reel.append(positions_on_reel)
                else:
                    # No symbols on this reel, stop checking further reels
                    break
            
            # Calculate wins if we have 3+ consecutive reels with the symbol
            if len(positions_by_reel) >= 3:
                win_length = len(positions_by_reel)
                total_ways = 1
                
                # Calculate total ways for this win
                for reel_positions in positions_by_reel:
                    total_ways *= len(reel_positions)
                
                # Get payout multiplier
                payout = self.get_symbol_payout(target_symbol, win_length)
                total_payout = payout * total_ways
                
                if total_payout > 0:
                    win = {
                        "symbol": target_symbol,
                        "length": win_length,
                        "ways": total_ways,
                        "payout": total_payout,
                        "positions": positions_by_reel
                    }
                    wins.append(win)
        
        return wins

    def get_symbol_payout(self, symbol, length):
        """Get payout value for symbol with given length."""
        return self.config.paytable.get((length, symbol), 0)

    def calculate_scatter_wins(self):
        """Calculate scatter symbol wins (Reaper symbols)."""
        scatter_positions = []
        scatter_count = 0
        
        # Count scatter symbols across all reels
        for reel_idx in range(self.config.num_reels):
            for row in range(self.config.num_rows[reel_idx]):
                symbol = self.get_symbol_at_position(reel_idx, row)
                if symbol == self.config.scatter_symbol:
                    scatter_positions.append((reel_idx, row))
                    scatter_count += 1
        
        # Check for free spin triggers
        free_spins = 0
        if scatter_count >= 3:
            triggers = self.config.freespin_triggers[self.gametype]
            free_spins = triggers.get(scatter_count, 0)
        
        return {
            "count": scatter_count,
            "positions": scatter_positions,
            "free_spins": free_spins
        }

    def evaluate_final_win(self):
        """
        Main win evaluation function.
        1. First calculate initial wins
        2. Then apply bleeding transformation
        3. Recalculate wins after transformation
        """
        # Step 1: Calculate initial wins
        initial_ways_wins = self.calculate_ways_wins()
        scatter_result = self.calculate_scatter_wins()
        
        # Step 2: Apply bleeding transformation
        transformation_occurred = self.evaluate_bleeding_transformation()
        
        # Step 3: Recalculate wins after transformation
        if transformation_occurred:
            final_ways_wins = self.calculate_ways_wins()
        else:
            final_ways_wins = initial_ways_wins
        
        # Calculate total payout
        total_payout = sum(win["payout"] for win in final_ways_wins)
        
        # Store results
        self.ways_wins = final_ways_wins
        self.scatter_wins = scatter_result
        self.total_win = total_payout
        self.free_spins_awarded = scatter_result["free_spins"]
        
        return {
            "ways_wins": final_ways_wins,
            "scatter_wins": scatter_result,
            "total_win": total_payout,
            "free_spins": scatter_result["free_spins"],
            "transformation_events": self.transformation_events,
            "transformation_occurred": transformation_occurred
        }

    def get_symbol_at_position(self, reel, row):
        """Get symbol at specific reel and row position."""
        # This should interface with the reel data structure
        # Implementation depends on how symbols are stored
        pass  # To be implemented based on SDK structure

    def set_symbol_at_position(self, reel, row, symbol):
        """Set symbol at specific reel and row position."""
        # This should interface with the reel data structure
        # Implementation depends on how symbols are stored
        if hasattr(self, 'board') and self.board:
            if reel < len(self.board) and row < len(self.board[reel]):
                self.board[reel][row] = symbol
    
    def emit_transformation_events(self):
        """Emit events for bleeding heart transformations for frontend animation."""
        if hasattr(self, 'transformation_events') and self.transformation_events:
            for event in self.transformation_events:
                # Emit transformation event for frontend
                if hasattr(self, 'emit_event'):
                    self.emit_event(event["event_type"], event["data"])