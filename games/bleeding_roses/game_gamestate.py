"""Bleeding Roses game state management and simulation logic."""

from game_override import GameStateOverride


class GameState(GameStateOverride):
    """
    Handle all game-logic and event updates for Bleeding Roses.
    Manages base game spins, free spins, and bleeding transformations.
    """

    def __init__(self, config):
        super().__init__(config)
        self.spin_results = []
        self.current_spin_data = {}
        
    def run_spin(self, sim):
        """
        Execute a single simulation spin for Bleeding Roses.
        
        Args:
            sim: Simulation number for this spin
        """
        # Initialize spin with simulation seed
        self.reset_seed(sim)
        self.current_simulation = sim
        self.repeat = True
        
        # Execute spin until win criteria are met
        while self.repeat:
            # Reset for this spin attempt
            self.reset_book()
            
            # Generate reel outcome
            self.generate_reel_outcome()
            
            # Evaluate wins and transformations
            self.evaluate_spin_outcome()
            
            # Check if we need to repeat (for specific win targets)
            self.check_game_repeat()

        # Finalize and record results
        self.imprint_wins()
        self.record_spin_data()

    def generate_reel_outcome(self):
        """Generate the reel symbols for this spin."""
        # This would interface with the reel data to select symbols
        # based on the current game mode (base game vs free spins)
        
        current_reel_set = self.get_current_reel_set()
        
        # Generate symbols for each reel position
        for reel_idx in range(self.config.num_reels):
            for row_idx in range(self.config.num_rows[reel_idx]):
                # Get random symbol from appropriate reel strip
                symbol = self.select_symbol_from_reel(current_reel_set, reel_idx, row_idx)
                self.set_symbol_at_position(reel_idx, row_idx, symbol)

    def get_current_reel_set(self):
        """Get the appropriate reel set for current game mode."""
        if self.in_free_spins():
            return "FR0"  # Free spins reels
        else:
            return "BR0"  # Base game reels

    def evaluate_spin_outcome(self):
        """
        Evaluate the complete spin outcome including transformations and wins.
        This is the core evaluation logic for Bleeding Roses.
        """
        # Step 1: Record initial reel state
        initial_state = self.capture_reel_state()
        
        # Step 2: Calculate initial wins (before transformation)
        initial_wins = self.calculate_ways_wins()
        initial_scatter_result = self.calculate_scatter_wins()
        
        # Step 3: Apply bleeding transformation
        if self.in_free_spins():
            transformation_result = self.handle_free_spins_transformation()
        else:
            transformation_result = self.evaluate_bleeding_transformation()
        
        # Step 4: Calculate final wins (after transformation)
        if transformation_result:
            final_wins = self.calculate_ways_wins()
        else:
            final_wins = initial_wins
            
        # Step 5: Calculate total win amount
        total_ways_win = sum(win["payout"] for win in final_wins)
        
        # Step 6: Handle free spins triggers
        free_spins_awarded = initial_scatter_result["free_spins"]
        if free_spins_awarded > 0 and not self.in_free_spins():
            self.trigger_free_spins(free_spins_awarded)
        
        # Step 7: Store results
        self.final_win = total_ways_win
        self.ways_wins = final_wins
        self.scatter_result = initial_scatter_result
        self.transformation_occurred = transformation_result
        
        # Step 8: Create events for frontend
        self.create_spin_events()

    def run_freespin(self):
        """
        Execute free spins bonus round.
        Enhanced transformation rules apply during free spins.
        """
        self.reset_fs_spin()
        
        while self.fs < self.tot_fs:
            # Execute individual free spin
            self.execute_free_spin()
            
            # Update free spin counter
            self.update_freespin()
            
            # Check for retrigger
            if self.check_free_spin_retrigger():
                self.add_retrigger_spins()

        # Complete free spins round
        self.end_freespin()

    def execute_free_spin(self):
        """Execute a single free spin with enhanced transformation rules."""
        # Generate reel outcome
        self.generate_reel_outcome()
        
        # Apply enhanced free spin transformations
        # ANY bleeding heart transforms ALL roses on ALL reels
        transformation_occurred = self.handle_free_spins_transformation()
        
        # Calculate wins
        ways_wins = self.calculate_ways_wins()
        scatter_result = self.calculate_scatter_wins()
        
        # Accumulate free spin wins
        spin_win = sum(win["payout"] for win in ways_wins)
        self.fs_total_win += spin_win
        
        # Record free spin data
        self.record_free_spin_data(ways_wins, transformation_occurred)

    def check_free_spin_retrigger(self):
        """Check if additional free spins are triggered."""
        if hasattr(self, 'scatter_result') and self.scatter_result:
            return self.scatter_result["free_spins"] > 0
        return False

    def add_retrigger_spins(self):
        """Add retriggered free spins to current total."""
        additional_spins = self.scatter_result["free_spins"]
        self.tot_fs += additional_spins
        
        # Create retrigger event
        retrigger_event = {
            "type": "free_spin_retrigger",
            "additional_spins": additional_spins,
            "new_total": self.tot_fs
        }
        self.add_event(retrigger_event)

    def trigger_free_spins(self, num_spins):
        """Initialize free spins bonus round."""
        self.tot_fs = num_spins
        self.fs = 0
        self.fs_total_win = 0
        self.gametype = self.config.freegame_type
        
        # Create free spins trigger event
        trigger_event = {
            "type": "free_spins_trigger",
            "num_spins": num_spins,
            "trigger_symbols": self.scatter_result["positions"]
        }
        self.add_event(trigger_event)

    def capture_reel_state(self):
        """Capture current state of all reel positions."""
        state = {}
        for reel_idx in range(self.config.num_reels):
            state[reel_idx] = {}
            for row_idx in range(self.config.num_rows[reel_idx]):
                symbol = self.get_symbol_at_position(reel_idx, row_idx)
                state[reel_idx][row_idx] = symbol
        return state

    def create_spin_events(self):
        """Create all events for this spin to send to frontend."""
        events = []
        
        # Base reel spin event
        events.append({
            "type": "reel_spin",
            "final_symbols": self.capture_reel_state(),
            "spin_id": self.current_simulation
        })
        
        # Add bleeding transformation events
        if hasattr(self, 'bleeding_events'):
            events.extend(self.bleeding_events)
        
        # Add win events
        if self.ways_wins:
            events.append({
                "type": "ways_wins",
                "wins": self.ways_wins,
                "total_win": self.final_win
            })
        
        # Add scatter events
        if self.scatter_result["count"] >= 3:
            events.append({
                "type": "scatter_trigger",
                "scatter_count": self.scatter_result["count"],
                "free_spins": self.scatter_result["free_spins"],
                "positions": self.scatter_result["positions"]
            })
        
        self.spin_events = events

    def record_spin_data(self):
        """Record comprehensive data for this spin."""
        self.current_spin_data = {
            "simulation_id": self.current_simulation,
            "game_mode": self.gametype,
            "final_symbols": self.capture_reel_state(),
            "ways_wins": self.ways_wins,
            "scatter_result": self.scatter_result,
            "total_win": self.final_win,
            "transformation_occurred": getattr(self, 'transformation_occurred', False),
            "bleeding_events": getattr(self, 'bleeding_events', []),
            "free_spins_triggered": self.scatter_result["free_spins"] > 0,
            "events": self.spin_events
        }
        
        self.spin_results.append(self.current_spin_data)

    def record_free_spin_data(self, ways_wins, transformation_occurred):
        """Record data for individual free spin."""
        free_spin_data = {
            "free_spin_number": self.fs + 1,
            "symbols": self.capture_reel_state(),
            "ways_wins": ways_wins,
            "transformation_occurred": transformation_occurred,
            "spin_win": sum(win["payout"] for win in ways_wins)
        }
        
        if not hasattr(self, 'free_spin_details'):
            self.free_spin_details = []
        self.free_spin_details.append(free_spin_data)

    def get_simulation_summary(self):
        """Get summary of all simulations run."""
        return {
            "total_spins": len(self.spin_results),
            "total_wins": sum(1 for spin in self.spin_results if spin["total_win"] > 0),
            "free_spins_triggered": sum(1 for spin in self.spin_results if spin["free_spins_triggered"]),
            "transformations_occurred": sum(1 for spin in self.spin_results if spin["transformation_occurred"]),
            "max_win": max((spin["total_win"] for spin in self.spin_results), default=0),
            "average_win": sum(spin["total_win"] for spin in self.spin_results) / len(self.spin_results) if self.spin_results else 0
        }

    def export_for_stake_engine(self):
        """Export simulation data in Stake Engine format."""
        export_data = {
            "game_id": self.config.game_id,
            "simulations": self.spin_results,
            "summary": self.get_simulation_summary(),
            "configuration": {
                "rtp": self.config.rtp,
                "max_win": self.config.wincap,
                "ways_to_win": self.config.get_ways_to_win(),
                "reels": f"{self.config.num_reels}x{self.config.num_rows[0]}",
                "special_features": [
                    "Bleeding Heart Wild + Transformation",
                    "Rose to Bloody Rose (3x multiplier)",
                    "Free Spins with Enhanced Transformation",
                    "Reaper Scatter Triggers"
                ]
            }
        }
        
        return export_data