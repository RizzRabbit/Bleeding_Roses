"""Natural return by criteria. Used to price buys and set optimization targets.

Does not upload anything. Prints conditional average payout (x bet) for each
distribution criteria. Wincap rows should sit on 15000.
"""

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_config import GameConfig
from gamestate import GameState
from src.state.run_sims import create_books


def _summarize(config):
    library = os.path.join(config.library_path, "lookup_tables")
    print("\nmode,criteria,n,avg,p50,p90,max,hit,cap_rate")
    for mode in config.bet_modes:
        name = mode.get_name()
        cost = mode.get_cost()
        segmented = os.path.join(library, f"lookUpTableSegmented_{name}.csv")
        lookup = os.path.join(library, f"lookUpTable_{name}.csv")
        by_id = {}
        with open(segmented, encoding="UTF-8") as handle:
            for line in handle:
                sim_id, criteria, base_win, free_win = line.strip().split(",")
                by_id[sim_id] = (criteria, float(base_win), float(free_win))
        grouped = defaultdict(list)
        with open(lookup, encoding="UTF-8") as handle:
            for line in handle:
                sim_id, _, payout = line.strip().split(",")
                total = int(payout) / 100.0
                criteria, base_win, free_win = by_id[sim_id]
                grouped[criteria].append(total)
        overall = []
        for criteria, wins in grouped.items():
            overall.extend(wins)
            ordered = sorted(wins)
            avg = sum(wins) / len(wins)
            hit = sum(1 for win in wins if win > 0) / len(wins)
            cap = sum(1 for win in wins if win >= config.wincap - 1e-6) / len(wins)
            print(
                f"{name},{criteria},{len(wins)},{avg:.3f},{ordered[len(ordered)//2]:.3f},"
                f"{ordered[int(len(ordered)*0.9)]:.3f},{ordered[-1]:.3f},{hit:.3f},{cap:.4f}"
            )
        if overall:
            print(f"{name},ALL,{len(overall)},{sum(overall)/len(overall):.3f},cost={cost}")


if __name__ == "__main__":
    sims = int(os.environ.get("PROBE_SIMS", "800"))
    config = GameConfig()
    gamestate = GameState(config)
    num_sim_args = {mode.get_name(): sims for mode in config.bet_modes}
    create_books(
        gamestate,
        config,
        num_sim_args,
        batch_size=sims,
        threads=4,
        compress=True,
        profiling=False,
    )
    _summarize(config)
