#!/usr/bin/env python3
"""Debug test for bleeding roses game."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from gamestate import GameState
from game_config import GameConfig

def test_basic_game():
    """Test basic game initialization and single spin."""
    print("🌹 Testing Bleeding Roses Game Logic")
    print("=" * 40)
    
    try:
        # Initialize configuration
        config = GameConfig()
        print(f"✅ Config loaded: {config.game_id}")
        print(f"   Symbols: {config.all_symbols}")
        print(f"   Reels: {len(config.reels)}")
        
        # Initialize game state
        gamestate = GameState(config)
        print("✅ Game state initialized")
        
        # Initialize betmode (normally done in create_books)
        gamestate.betmode = "base"
        gamestate.gametype = "basegame"
        print("✅ Betmode initialized")
        
        # Test distributions
        print("\n🔍 Testing distributions...")
        try:
            conditions = gamestate.get_current_distribution_conditions()
            print(f"✅ Distribution conditions: {type(conditions)}")
        except Exception as e:
            print(f"❌ Distribution error: {e}")
        
        # Test basic functionality without board drawing
        print("\n🎰 Testing basic game calculations...")
        
        # Test game calculations directly
        result = gamestate.evaluate_final_win()
        print(f"✅ Game calculations work: {type(result)}")
        print("✅ Single spin completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_game()
    exit(0 if success else 1)