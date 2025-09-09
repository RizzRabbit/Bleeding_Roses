"""Optimization parameters for Bleeding Roses slot game."""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructConditions,
    verify_optimization_input,
)


class OptimizationSetup:
    """
    Bleeding Roses specific optimization setup.
    Configures RTP distribution and win balancing for 96% target.
    """

    def __init__(self, game_config: object):
        self.game_config = game_config
        
        # Configure optimization parameters for Bleeding Roses
        self.game_config.opt_params = {
            "base": {
                "conditions": {
                    # Max win condition (0.1% of simulations)
                    "wincap": ConstructConditions(
                        rtp=0.01,           # 1% of total RTP from max wins
                        av_win=5000,        # Average win when max win occurs
                        search_conditions=5000  # Search for 5000x+ wins
                    ).return_dict(),
                    
                    # Zero win condition (30% of simulations)
                    "0": ConstructConditions(
                        rtp=0,              # No RTP from losing spins
                        av_win=0,           # No average win
                        search_conditions=0 # Zero win condition
                    ).return_dict(),
                    
                    # Free game condition (8% of simulations)
                    "freegame": ConstructConditions(
                        rtp=0.35,           # 35% of total RTP from free spins
                        hr=200,             # Hit rate: 1 in 200 spins trigger free games
                        search_conditions={"symbol": "RP"}  # Reaper scatter triggers
                    ).return_dict(),
                    
                    # Base game wins condition (62% of simulations)
                    "basegame": ConstructConditions(
                        rtp=0.60,           # 60% of total RTP from base game
                        hr=3.0              # Hit rate: 1 in 3 spins wins
                    ).return_dict(),
                },
                
                "scaling": ConstructScaling([
                    # Base game scaling
                    {
                        "criteria": "basegame",
                        "scale_factor": 1.0,
                        "win_range": (1, 100),      # 1x to 100x wins
                        "probability": 0.8,         # 80% of base game wins
                    },
                    {
                        "criteria": "basegame", 
                        "scale_factor": 1.5,
                        "win_range": (100, 500),    # 100x to 500x wins
                        "probability": 0.15,        # 15% of base game wins
                    },
                    {
                        "criteria": "basegame",
                        "scale_factor": 2.0, 
                        "win_range": (500, 2000),   # 500x to 2000x wins
                        "probability": 0.05,        # 5% of base game wins
                    },
                    
                    # Free game scaling (higher volatility)
                    {
                        "criteria": "freegame",
                        "scale_factor": 1.0,
                        "win_range": (1, 200),      # 1x to 200x wins
                        "probability": 0.6,         # 60% of free spin wins
                    },
                    {
                        "criteria": "freegame",
                        "scale_factor": 2.0,
                        "win_range": (200, 1000),   # 200x to 1000x wins
                        "probability": 0.3,         # 30% of free spin wins
                    },
                    {
                        "criteria": "freegame", 
                        "scale_factor": 3.0,
                        "win_range": (1000, 10000), # 1000x to 10000x wins
                        "probability": 0.1,         # 10% of free spin wins
                    },
                ]).return_dict(),
                
                "parameters": ConstructParameters(
                    num_show=5000,          # Number of results to display
                    num_per_fence=10000,    # Simulations per optimization cycle
                    min_m2m=4,             # Minimum multiplier-to-multiplier ratio
                    max_m2m=8,             # Maximum multiplier-to-multiplier ratio
                    pmb_rtp=1.0,           # Perfect mathematical balance RTP
                    sim_trials=5000,       # Simulation trials for verification
                    test_spins=[50, 100, 200],  # Test spin counts
                    test_weights=[0.3, 0.4, 0.3],  # Weights for test results
                    score_type="rtp",      # Optimize for RTP accuracy
                ).return_dict(),
            },
        }

        # Bleeding Roses specific optimization constraints
        self.add_bleeding_roses_constraints()
        
        # Verify optimization input
        verify_optimization_input(self.game_config, self.game_config.opt_params)

    def add_bleeding_roses_constraints(self):
        """Add game-specific optimization constraints."""
        
        # Transformation frequency constraints
        self.game_config.transformation_constraints = {
            "bleeding_heart_frequency": {
                "min_per_1000_spins": 50,   # Minimum 50 bleeding hearts per 1000 spins
                "max_per_1000_spins": 150,  # Maximum 150 bleeding hearts per 1000 spins
                "target_reel_distribution": {
                    1: 0.33,  # 33% on reel 2 (0-indexed: reel 1)
                    2: 0.34,  # 34% on reel 3 (0-indexed: reel 2) 
                    3: 0.33,  # 33% on reel 4 (0-indexed: reel 3)
                }
            },
            
            "rose_transformation_rate": {
                "min_roses_per_transformation": 1,  # At least 1 rose transformed
                "max_roses_per_transformation": 4,  # Maximum 4 roses per reel
                "average_multiplier_benefit": 2.5,  # Average benefit from 3x multiplier
            },
            
            "free_spins_enhancement": {
                "global_transformation_rate": 0.8,  # 80% of free spins have transformation
                "average_roses_transformed": 8,     # Average roses per free spin round
                "max_win_contribution": 0.6,       # 60% of max wins come from free spins
            }
        }

        # RTP distribution verification
        self.game_config.rtp_verification = {
            "total_target": 96.0,
            "base_game_contribution": 52.8,    # 55% of 96% = 52.8%
            "free_spins_contribution": 33.6,   # 35% of 96% = 33.6%
            "transformation_bonus": 9.6,       # 10% of 96% = 9.6%
            "tolerance": 0.1,                   # ±0.1% tolerance
        }

        # Max win verification scenarios
        self.game_config.max_win_scenarios = [
            {
                "scenario": "full_screen_bloody_black_roses",
                "symbols": ["BBR"] * 20,  # 20 bloody black roses
                "expected_win": 8000,     # Expected ~8000x
                "probability": 1e-7,      # Very rare
            },
            {
                "scenario": "free_spins_with_global_transformation", 
                "description": "Multiple 5-of-a-kind bloody roses in free spins",
                "expected_win": 6000,     # Expected ~6000x
                "probability": 1e-6,      # Rare
            },
            {
                "scenario": "multiple_bleeding_hearts_with_roses",
                "description": "Base game with multiple transformations",
                "expected_win": 2000,     # Expected ~2000x
                "probability": 1e-5,      # Uncommon
            }
        ]

    def get_optimization_summary(self):
        """Return summary of optimization parameters."""
        return {
            "game_id": self.game_config.game_id,
            "target_rtp": self.game_config.rtp,
            "max_win": self.game_config.wincap,
            "hit_frequency_target": "30% (1 in 3.3 spins)",
            "free_spins_frequency": "0.5% (1 in 200 spins)",
            "transformation_mechanic": "Bleeding Heart transforms roses to 3x value",
            "volatility": "Medium-High",
            "ways_to_win": self.game_config.get_ways_to_win(),
        }

    def validate_optimization_results(self, results):
        """Validate that optimization results meet Bleeding Roses requirements."""
        validation_checks = {
            "rtp_accuracy": abs(results.get("actual_rtp", 0) - self.game_config.rtp) <= 0.1,
            "max_win_achievable": results.get("max_win_found", 0) >= self.game_config.wincap * 0.8,
            "hit_frequency_acceptable": 0.25 <= results.get("hit_frequency", 0) <= 0.35,
            "free_spins_frequency": 0.004 <= results.get("free_spins_rate", 0) <= 0.006,
        }
        
        all_passed = all(validation_checks.values())
        
        return {
            "passed": all_passed,
            "checks": validation_checks,
            "summary": self.get_optimization_summary()
        }
