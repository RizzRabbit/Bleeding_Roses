"""Generate Bleeding Roses books, lookup tables, and the PAR sheet.

Upload is intentionally not run. Nothing in this file sends files anywhere.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_config import GameConfig
from game_optimization import OptimizationSetup
from gamestate import GameState
from optimization_program.run_script import OptimizationExecution
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests


if __name__ == "__main__":
    num_threads = 4
    rust_threads = 4
    batching_size = 5000
    compression = True
    profiling = False

    run_conditions = {
        "run_sims": True,
        "run_optimization": True,
        "run_analysis": True,
        "run_format_checks": True,
        "upload_data": False,
    }

    config = GameConfig()
    gamestate = GameState(config)
    target_modes = [bet_mode.get_name() for bet_mode in config.bet_modes]

    num_sim_args = {name: int(1e4) for name in target_modes}

    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [
            {"tier": "bleeding_spins"},
            {"tier": "blood_moon"},
            {"tier": "reapers_harvest"},
        ]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)

    if run_conditions["upload_data"]:
        raise RuntimeError("Upload is disabled for Bleeding Roses. Do not send books anywhere.")
