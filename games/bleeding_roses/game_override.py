"""Bleeding Roses game state overrides and special functionality."""

from game_executables import GameExecutables
from src.calculations.statistics import get_random_outcome


class GameStateOverride(GameExecutables):
    """
    Bleeding Roses specific game state overrides.
    Handles bleeding heart wild functionality and transformation mechanics.
    """
        
    def reset_book(self):
        """Reset game specific properties for new spin."""
        super().reset_book()
        
        # Initialize/Reset bleeding-specific properties
        if not hasattr(self, 'bleeding_events'):
            self.bleeding_events = []
            self.transformation_multiplier = 3
        
        self.bleeding_events = []
        self.transformation_events = []
        self.roses_transformed = False
        self.transformed_positions = []

    def assign_special_sym_function(self):
        """Assign special symbol functions for Bleeding Roses."""
        self.special_symbol_functions = {
            "BH": [self.assign_bleeding_heart_properties],  # Bleeding Heart
            "RP": [self.assign_reaper_properties],          # Reaper scatter
        }

    def assign_bleeding_heart_properties(self, symbol):
        """
        Assign properties to Bleeding Heart symbol.
        Functions as both wild and transformation trigger.
        """
        # Mark as wild symbol
        symbol.is_wild = True
        symbol.substitutes_for = self.config.rose_symbols + self.config.low_symbols + self.config.bloody_symbols
        
        # Mark as transformation trigger
        symbol.is_transformation_trigger = True
        symbol.trigger_type = "bleeding_transformation"
        
        # Visual properties for frontend
        symbol.animation_type = "bleeding_heart_pulse"
        symbol.blood_drip_effect = True

    def assign_reaper_properties(self, symbol):
        """Assign properties to Reaper scatter symbol."""
        symbol.is_scatter = True
        symbol.is_freespin_trigger = True
        symbol.animation_type = "reaper_glow"

    def evaluate_bleeding_transformation(self):
        """
        Enhanced bleeding transformation logic.
        Handles the core mechanic of transforming roses to bloody variants.
        """
        transformation_occurred = False
        
        # Find all Bleeding Heart positions
        bleeding_heart_positions = self.find_bleeding_heart_positions()
        
        # For each Bleeding Heart, transform roses on its reel
        for reel_idx, row_idx in bleeding_heart_positions:
            transformed_on_reel = self.transform_roses_on_reel(reel_idx)
            
            if transformed_on_reel:
                transformation_occurred = True
                
                # Create bleeding event for animation
                bleeding_event = {
                    "type": "bleeding_transformation",
                    "trigger_position": (reel_idx, row_idx),
                    "affected_reel": reel_idx,
                    "transformations": transformed_on_reel,
                    "blood_flow_direction": "downward",
                    "animation_duration": 2.0  # seconds
                }
                self.bleeding_events.append(bleeding_event)
        
        self.roses_transformed = transformation_occurred
        return transformation_occurred

    def find_bleeding_heart_positions(self):
        """Find all Bleeding Heart symbol positions."""
        positions = []
        
        # Only check reels where Bleeding Heart can appear (reels 2, 3, 4)
        valid_reels = self.config.transformation_config["trigger_reels"]
        
        for reel_idx in valid_reels:
            for row_idx in range(self.config.num_rows[reel_idx]):
                symbol = self.get_symbol_at_position(reel_idx, row_idx)
                if symbol == self.config.transformation_config["trigger_symbol"]:
                    positions.append((reel_idx, row_idx))
        
        return positions

    def transform_roses_on_reel(self, reel_idx):
        """Transform all roses on specified reel to bloody variants."""
        transformations = []
        
        for row_idx in range(self.config.num_rows[reel_idx]):
            symbol = self.get_symbol_at_position(reel_idx, row_idx)
            
            # Check if symbol is a transformable rose
            if self.config.is_rose_symbol(symbol):
                bloody_variant = self.config.transform_to_bloody(symbol)
                
                # Store transformation details
                transformation = {
                    "position": (reel_idx, row_idx),
                    "original_symbol": symbol,
                    "new_symbol": bloody_variant,
                    "multiplier_applied": self.transformation_multiplier
                }
                transformations.append(transformation)
                
                # Actually transform the symbol
                self.set_symbol_at_position(reel_idx, row_idx, bloody_variant)
                self.transformed_positions.append((reel_idx, row_idx))
        
        return transformations

    def handle_free_spins_transformation(self):
        """
        Enhanced transformation during free spins.
        ANY Bleeding Heart transforms ALL roses on ALL reels.
        """
        if not self.in_free_spins():
            return False
            
        # Find any Bleeding Heart on any reel
        bleeding_heart_positions = []
        for reel_idx in range(self.config.num_reels):
            for row_idx in range(self.config.num_rows[reel_idx]):
                symbol = self.get_symbol_at_position(reel_idx, row_idx)
                if symbol == self.config.transformation_config["trigger_symbol"]:
                    bleeding_heart_positions.append((reel_idx, row_idx))
        
        if not bleeding_heart_positions:
            return False
        
        # Transform ALL roses on ALL reels
        global_transformations = []
        for reel_idx in range(self.config.num_reels):
            reel_transformations = self.transform_roses_on_reel(reel_idx)
            global_transformations.extend(reel_transformations)
        
        if global_transformations:
            # Create global bleeding event
            global_bleeding_event = {
                "type": "global_bleeding_transformation",
                "trigger_positions": bleeding_heart_positions,
                "affected_reels": list(range(self.config.num_reels)),
                "transformations": global_transformations,
                "blood_flow_pattern": "cascade",
                "animation_duration": 3.0
            }
            self.bleeding_events.append(global_bleeding_event)
            return True
        
        return False

    def calculate_win_with_transformations(self):
        """
        Calculate wins accounting for rose transformations.
        This overrides the base win calculation.
        """
        # First, apply transformations
        if self.in_free_spins():
            transformation_occurred = self.handle_free_spins_transformation()
        else:
            transformation_occurred = self.evaluate_bleeding_transformation()
        
        # Then calculate wins with potentially transformed symbols
        win_result = self.evaluate_final_win()
        
        # Add transformation info to win result
        win_result["transformation_occurred"] = transformation_occurred
        win_result["bleeding_events"] = self.bleeding_events
        win_result["roses_transformed"] = self.roses_transformed
        
        return win_result

    def check_game_repeat(self):
        """
        Override repeat conditions for Bleeding Roses.
        May need to repeat if max win conditions aren't met.
        """
        if self.repeat == False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
                
            # Special case: if we're forcing max win and haven't achieved it
            if (hasattr(self, 'force_max_win') and self.force_max_win and 
                self.final_win < self.config.wincap):
                self.repeat = True

    def in_free_spins(self):
        """Check if currently in free spins mode."""
        return hasattr(self, 'gametype') and self.gametype == self.config.freegame_type

    def get_bleeding_animation_data(self):
        """
        Return animation data for frontend bleeding effects.
        """
        return {
            "bleeding_events": self.bleeding_events,
            "transformed_positions": self.transformed_positions,
            "roses_transformed": self.roses_transformed,
            "transformation_multiplier": self.transformation_multiplier
        }

    def create_game_events(self):
        """Create all game events for this spin."""
        events = []
        
        # Base game events
        events.extend(super().create_game_events())
        
        # Add bleeding-specific events
        for bleeding_event in self.bleeding_events:
            events.append({
                "event_type": bleeding_event["type"],
                "event_data": bleeding_event,
                "timing": "after_reel_stop",
                "duration": bleeding_event.get("animation_duration", 2.0)
            })
        
        return events

    def get_symbol_display_name(self, symbol):
        """Get display name for symbols (for frontend)."""
        display_names = {
            "WR": "White Rose",
            "RR": "Red Rose", 
            "BR": "Black Rose",
            "BWR": "Bloody White Rose",
            "BRR": "Bloody Red Rose",
            "BBR": "Bloody Black Rose",
            "BH": "Bleeding Heart",
            "RP": "Reaper"
        }
        return display_names.get(symbol, symbol)