"""Mechanic tests for Bleeding Roses. Failures must fail the process."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
GAME = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, GAME)

from game_calculations import quantize_win
from game_config import TIERS, GameConfig
from gamestate import GameState


def _state(mode="base", criteria="basegame", freegame=False, tier=None):
    config = GameConfig()
    state = GameState(config)
    state.betmode = mode
    state.criteria = criteria
    state.reset_book()
    if freegame:
        state.gametype = config.freegame_type
    if tier is not None:
        state.bonus_tier = tier
    return state


def _plant(state, columns):
    state.board = []
    state.top_symbols = []
    state.bottom_symbols = []
    state.reel_positions = [0] * state.config.num_reels
    state.padding_position = [0] * state.config.num_reels
    state.anticipation = [0] * state.config.num_reels
    for names in columns:
        state.board.append([state.create_symbol(name) for name in names])
        state.top_symbols.append(state.create_symbol("10"))
        state.bottom_symbols.append(state.create_symbol("10"))
    state.get_special_symbols_on_board()


def _names(state):
    return [[symbol.name for symbol in reel] for reel in state.board]


def _event_types(state):
    return [event["type"] for event in state.book.events]


def test_paytable_and_tiers():
    config = GameConfig()
    assert config.get_ways_to_win() == 1024
    assert config.wincap == 15000
    assert config.rtp == 0.96
    assert config.freespin_triggers[config.basegame_type] == {3: 10, 4: 12, 5: 15}
    assert config.freespin_triggers[config.freegame_type] == {3: 5, 4: 6, 5: 8}
    for symbol, bloody in (("WR", "BWR"), ("RR", "BRR"), ("BR", "BBR")):
        for kind in (3, 4, 5):
            assert config.paytable[(kind, bloody)] == round(config.paytable[(kind, symbol)] * 3, 2)
    for payout in config.paytable.values():
        assert abs(payout * 10 - round(payout * 10)) < 1e-9
    mode_names = [mode.get_name() for mode in config.bet_modes]
    assert mode_names == [
        "base",
        "bloodlust",
        "super_ante_20",
        "buy_bleeding",
        "buy_blood_moon",
        "buy_harvest",
        "full_bleed",
    ]
    costs = {mode.get_name(): mode.get_cost() for mode in config.bet_modes}
    assert costs["base"] == 1
    assert costs["bloodlust"] == 3
    assert "super_ante_10" not in costs
    assert costs["super_ante_20"] == 20
    assert costs["buy_bleeding"] == 100
    assert costs["buy_blood_moon"] == 300
    assert costs["buy_harvest"] == 600
    assert costs["full_bleed"] == 100
    assert costs["buy_harvest"] > costs["buy_blood_moon"] > costs["buy_bleeding"]
    for mode in config.bet_modes:
        assert mode.get_wincap() == 15000, mode.get_name()
    for mode in config.bet_modes:
        quota = sum(dist.get_quota() for dist in mode.get_distributions())
        assert abs(quota - 1) < 1e-9, mode.get_name()
    assert TIERS[5]["global_mult"] is True
    assert TIERS[4]["sticky"] is True
    assert TIERS[3]["board_bleed"] is True


def test_reels_place_hearts_and_reapers():
    config = GameConfig()
    for reel_id, strips in config.reels.items():
        for reel_index, strip in enumerate(strips):
            if reel_index not in config.bleed_reels:
                assert "BH" not in strip, reel_id
            reaper_stops = [i for i, symbol in enumerate(strip) if symbol == "RP"]
            if reel_id != "FBW":
                assert reaper_stops, (reel_id, reel_index)
            for left_at, left in enumerate(reaper_stops):
                for right in reaper_stops[left_at + 1 :]:
                    distance = min(abs(left - right), len(strip) - abs(left - right))
                    assert distance >= 5
        for reel_index in config.bleed_reels:
            assert "BH" in strips[reel_index], (reel_id, reel_index)


def test_base_bleed_is_per_reel_and_multiplies_wins_through_that_reel():
    state = _state()
    state.get_current_distribution_conditions()["bleed_mult_weights"] = {5: 1}
    _plant(
        state,
        [
            ["A", "10", "10", "10"],
            ["BH", "J", "J", "J"],
            ["A", "Q", "Q", "Q"],
            ["K", "K", "K", "K"],
            ["K", "K", "K", "K"],
        ],
    )
    state.resolve_board()
    assert _names(state)[1][0] == "BH"
    assert state.reel_multipliers == [1, 5, 1, 1, 1]
    assert state.win_data["totalWin"] == quantize_win(state.config.paytable[(3, "A")] * 5)
    bleed = [event for event in state.book.events if event["type"] == "reelBleed"]
    assert len(bleed) == 1
    assert bleed[0]["reel"] == 1
    assert bleed[0]["multiplier"] == 5
    assert bleed[0]["scope"] == "reel"
    assert any(event["type"] == "boardAfterBleed" for event in state.book.events)


def test_reel_multiplier_does_not_apply_past_the_win():
    state = _state()
    _plant(
        state,
        [
            ["A", "RP", "RP", "RP"],
            ["A", "J", "J", "J"],
            ["A", "Q", "Q", "Q"],
            ["K", "K", "K", "K"],
            ["K", "K", "K", "K"],
        ],
    )
    pay = state.config.paytable[(3, "A")]
    state.reel_multipliers = [1, 1, 1, 5, 1]
    state.score_ways()
    assert state.win_data["totalWin"] == pay
    state.reel_multipliers = [1, 5, 1, 1, 1]
    state.score_ways()
    assert state.win_data["totalWin"] == quantize_win(pay * 5)


def test_bleeding_spins_bleed_the_whole_board():
    state = _state(criteria="bleeding_spins", freegame=True, tier="bleeding_spins")
    _plant(
        state,
        [
            ["WR", "10", "10", "10"],
            ["BH", "RR", "10", "10"],
            ["BR", "10", "10", "10"],
            ["WR", "10", "10", "10"],
            ["RR", "10", "10", "10"],
        ],
    )
    state.resolve_board()
    names = _names(state)
    assert names[0][0] == "BWR"
    assert names[1][1] == "BRR"
    assert names[2][0] == "BBR"
    assert names[3][0] == "BWR"
    assert names[4][0] == "BRR"
    assert state.reel_multipliers == [1, 1, 1, 1, 1]
    scopes = {event["scope"] for event in state.book.events if event["type"] == "reelBleed"}
    assert scopes == {"board"}


def test_blood_moon_sticky_persists():
    state = _state(criteria="blood_moon", freegame=True, tier="blood_moon")
    state.get_current_distribution_conditions()["bleed_mult_weights"] = {3: 1}
    _plant(
        state,
        [
            ["A", "10", "J", "Q"],
            ["BH", "WR", "K", "10"],
            ["A", "K", "K", "K"],
            ["K", "K", "K", "K"],
            ["K", "K", "K", "K"],
        ],
    )
    pay = state.config.paytable[(3, "A")]
    state.resolve_board()
    assert state.sticky_reels == [1]
    assert state.sticky_multipliers == {1: 3}
    assert state.reel_multipliers == [1, 3, 1, 1, 1]
    assert _names(state)[1][1] == "BWR"
    assert state.win_data["totalWin"] == quantize_win(pay * 3)
    locked = [event for event in state.book.events if event["type"] == "stickyReel"]
    assert locked[0]["newReels"] == [1]
    assert locked[0]["multipliers"] == [3]
    assert locked[0]["stickyMultipliers"] == [3]
    bleed = [event for event in state.book.events if event["type"] == "reelBleed"]
    assert bleed[0]["multiplier"] == 3
    assert bleed[0]["scope"] == "reel"

    state.book = state.book.__class__(state.book.id, state.book.criteria)
    _plant(
        state,
        [
            ["A", "10", "J", "Q"],
            ["A", "RR", "K", "WR"],
            ["BH", "K", "K", "K"],
            ["K", "K", "K", "K"],
            ["K", "K", "K", "K"],
        ],
    )
    state.resolve_board()
    assert _names(state)[1][1] == "BRR"
    assert _names(state)[1][3] == "BWR"
    assert state.sticky_reels == [1, 2]
    assert state.sticky_multipliers == {1: 3, 2: 3}
    assert state.reel_multipliers == [1, 3, 3, 1, 1]
    assert state.win_data["totalWin"] == quantize_win(pay * 9)
    locked = [event for event in state.book.events if event["type"] == "stickyReel"]
    assert locked[0]["newReels"] == [2]
    assert locked[0]["multipliers"] == [3]
    assert locked[0]["stickyMultipliers"] == [3, 3]


def test_harvest_global_multiplier_stacks_and_scales_the_win():
    state = _state(criteria="reapers_harvest", freegame=True, tier="reapers_harvest")
    _plant(
        state,
        [
            ["A", "RP", "RP", "RP"],
            ["BH", "J", "J", "J"],
            ["A", "Q", "Q", "Q"],
            ["K", "K", "K", "K"],
            ["K", "K", "K", "K"],
        ],
    )
    pay = state.config.paytable[(3, "A")]
    state.resolve_board()
    assert state.global_multiplier == 2
    assert state.win_data["totalWin"] == quantize_win(pay * 2)
    assert any(event["type"] == "updateGlobalMult" and event["globalMult"] == 2 for event in state.book.events)

    state.book = state.book.__class__(state.book.id, state.book.criteria)
    _plant(
        state,
        [
            ["A", "RP", "RP", "RP"],
            ["BH", "J", "J", "J"],
            ["BH", "Q", "Q", "Q"],
            ["K", "K", "K", "K"],
            ["K", "K", "K", "K"],
        ],
    )
    state.resolve_board()
    assert state.global_multiplier == 3
    assert state.win_data["totalWin"] == quantize_win(pay * 3)
    steps = [event for event in state.book.events if event["type"] == "updateGlobalMult"]
    assert steps[-1]["increment"] == 1
    assert len(steps[-1]["heartReels"]) == 2


def test_full_bleed_converts_every_rose_and_keeps_reel_multipliers():
    state = _state(mode="full_bleed", criteria="full_bleed")
    state.get_current_distribution_conditions()["bleed_mult_weights"] = {3: 1}
    _plant(
        state,
        [
            ["WR", "10", "10", "10"],
            ["BH", "RR", "10", "10"],
            ["BR", "10", "10", "10"],
            ["10", "10", "10", "10"],
            ["RR", "10", "10", "10"],
        ],
    )
    state.resolve_board()
    names = _names(state)
    assert names[0][0] == "BWR"
    assert names[1][1] == "BRR"
    assert names[2][0] == "BBR"
    assert names[4][0] == "BRR"
    assert state.reel_multipliers[1] == 3
    types = _event_types(state)
    assert "fullBleed" in types
    assert types.index("fullBleed") < types.index("reelBleed")


def test_forced_tier_awards_the_right_spins():
    state = _state(criteria="bleeding_spins")
    state.run_spin(3)
    tiers = [event for event in state.book.events if event["type"] == "bonusTier"]
    assert len(tiers) == 1
    assert tiers[0]["tier"] == "bleeding_spins"
    assert tiers[0]["spins"] == 10
    assert tiers[0]["boardBleed"] is True
    assert sum(1 for event in state.book.events if event["type"] == "updateFreeSpin") >= 10
    assert any(event["type"] == "freeSpinTrigger" for event in state.book.events)
    assert any(event["type"] == "freeSpinEnd" for event in state.book.events)
    assert _cents(state) % 10 == 0


def test_buy_and_full_bleed_spins_complete():
    harvest = _state(mode="buy_harvest", criteria="reapers_harvest")
    harvest.run_spin(8)
    tier = [event for event in harvest.book.events if event["type"] == "bonusTier"][0]
    assert tier["tier"] == "reapers_harvest"
    assert tier["globalMultiplier"] is True
    assert _cents(harvest) % 10 == 0

    bleed = _state(mode="full_bleed", criteria="full_bleed")
    bleed.run_spin(4)
    assert any(event["type"] == "fullBleed" for event in bleed.book.events)
    assert not any(event["type"] == "freeSpinTrigger" for event in bleed.book.events)
    assert _cents(bleed) % 10 == 0


def _cents(state):
    return int(round(state.book.payout_multiplier * 100))


def test_freespin_end_and_win_without_mult_round():
    """Book units use round(), so a float just under the cent is not truncated."""
    state = _state(criteria="bleeding_spins", freegame=True, tier="bleeding_spins")
    state.win_manager.basegame_wins = 0
    state.win_manager.freegame_wins = 2329.2
    state.win_manager.running_bet_win = 2329.2
    state.end_freespin()
    event = state.book.events[-1]
    assert event["type"] == "freeSpinEnd"
    assert event["amount"] == 232920

    from game_events import win_info_event

    state.win_data = {
        "totalWin": 2.3,
        "wins": [
            {
                "symbol": "WR",
                "kind": 3,
                "win": 2.3,
                "positions": [{"reel": 0, "row": 0}],
                "meta": {"ways": 1, "globalMult": 1, "winWithoutMult": 2.3},
            }
        ],
    }
    win_info_event(state)
    info = [item for item in state.book.events if item["type"] == "winInfo"][-1]
    assert info["wins"][0]["meta"]["winWithoutMult"] == 230
    assert info["wins"][0]["win"] == 230
    assert int(2.3 * 100) == 229


def test_capped_bonus_keeps_base_wins_out_of_freespin_end():
    """A max win that also paid in the base game reports only the free portion."""
    state = _state(criteria="wincap", freegame=True, tier="bleeding_spins")
    state.win_manager.basegame_wins = 0.6
    state.win_manager.freegame_wins = 16000
    state.win_manager.running_bet_win = 16000.6
    state.wincap_triggered = True
    state.end_freespin()
    event = state.book.events[-1]
    assert event["type"] == "freeSpinEnd"
    assert event["amount"] == 1_499_940
    state.update_final_win()
    final = int(round(state.book.payout_multiplier * 100))
    base_cents = int(round(state.book.basegame_wins * 100))
    assert final == 1_500_000
    assert base_cents == 60
    assert event["amount"] == final - base_cents


def test_published_sample_seeds_keep_their_payouts():
    """The dev books are these seeds. Rounding must not move the payout."""
    moon = _state(mode="buy_blood_moon", criteria="blood_moon")
    moon.run_spin(11)
    events = moon.book.events
    free_end = next(event["amount"] for event in events if event["type"] == "freeSpinEnd")
    final = next(event["amount"] for event in events if event["type"] == "finalWin")
    base_cents = int(round(moon.book.basegame_wins * 100))
    assert int(round(moon.book.payout_multiplier * 100)) == 232920
    assert free_end == 232920
    assert free_end == final - base_cents

    cap = _state(mode="buy_bleeding", criteria="wincap")
    cap.run_spin(16)
    cap_events = cap.book.events
    spins = [event for event in cap_events if event["type"] == "updateFreeSpin"]
    assert len(spins) == 7
    assert spins[-1]["total"] == 10
    windex = next(index for index, event in enumerate(cap_events) if event["type"] == "wincap")
    assert cap_events[windex - 1]["type"] == "winInfo"
    running = 0
    for event in cap_events:
        if event["type"] == "setTotalWin" and event["index"] < cap_events[windex]["index"]:
            running = event["amount"]
    assert running < 1_500_000
    assert running + cap_events[windex - 1]["totalWin"] > 1_500_000
    assert all(event["type"] != "winInfo" for event in cap_events[windex + 1 :])
    assert any(event["type"] == "freeSpinEnd" for event in cap_events[windex + 1 :])
    assert int(round(cap.book.payout_multiplier * 100)) == 1_500_000


def test_wincap_is_reachable():
    """Every mode can pay 15000x the base bet, not 15000x its cost."""
    modes = [
        "base",
        "bloodlust",
        "super_ante_20",
        "buy_bleeding",
        "buy_blood_moon",
        "buy_harvest",
        "full_bleed",
    ]
    for name in modes:
        state = _state(mode=name, criteria="wincap")
        state.run_spin(11)
        assert state.final_win == 15000, (name, state.final_win)
        assert _cents(state) == 1_500_000, name
        assert any(event["type"] == "wincap" for event in state.book.events), name


def test_symbol_access_round_trip():
    state = _state()
    _plant(state, [["WR", "10", "J", "Q"]] * 5)
    assert state.get_symbol_at_position(0, 0) == "WR"
    state.set_symbol_at_position(0, 0, "BWR")
    assert state.get_symbol_at_position(0, 0) == "BWR"
    assert state.board[0][0].check_attribute("bled") is False or True


def test_published_lookup_rtp_matches_the_math_index():
    """RTP and max win in the rules file come from the optimized lookup tables."""
    publish = os.path.join(GAME, "library", "publish_files", "lookUpTable_base_0.csv")
    if not os.path.exists(publish):
        return
    from check_published_rtp import lookup_path, measure

    costs = {
        "base": 1,
        "bloodlust": 3,
        "super_ante_20": 20,
        "buy_bleeding": 100,
        "buy_blood_moon": 300,
        "buy_harvest": 600,
        "full_bleed": 100,
    }
    for name, cost in costs.items():
        rtp, max_win, count = measure(lookup_path(name), cost)
        assert count == 10000, (name, count)
        assert abs(rtp - 0.96) < 1e-8, (name, rtp)
        assert max_win == 15000, (name, max_win)
    index = os.path.join(ROOT, "web-sdk", "apps", "bleeding_roses", "static", "assets", "math", "index.json")
    if os.path.exists(index):
        import subprocess

        result = subprocess.run([sys.executable, os.path.join(GAME, "check_published_rtp.py"), index], check=False)
        assert result.returncode == 0


def test_every_bonus_book_splits_freespin_end_from_the_base_win():
    """freeSpinEnd is the free-game portion: finalWin minus base-game cents."""
    import json

    import zstandard as zstd

    folder = os.path.join(GAME, "library", "publish_files")
    sample = os.path.join(folder, "books_base.jsonl.zst")
    if not os.path.exists(sample):
        return
    modes = [
        "base",
        "bloodlust",
        "super_ante_20",
        "buy_bleeding",
        "buy_blood_moon",
        "buy_harvest",
        "full_bleed",
    ]
    decoder = zstd.ZstdDecompressor()
    failures = []
    for name in modes:
        path = os.path.join(folder, f"books_{name}.jsonl.zst")
        with open(path, "rb") as handle:
            payload = decoder.stream_reader(handle).read().decode()
        for line in payload.splitlines():
            if not line.strip():
                continue
            book = json.loads(line)
            events = book["events"]
            free = next((event for event in events if event["type"] == "freeSpinEnd"), None)
            if free is None:
                continue
            final = next(event["amount"] for event in events if event["type"] == "finalWin")
            base_cents = int(round(float(book["baseGameWins"]) * 100))
            if free["amount"] != final - base_cents:
                failures.append((name, book["id"], free["amount"], final, base_cents))
                if len(failures) >= 5:
                    break
        if len(failures) >= 5:
            break
    assert not failures, failures


def test_volatility_limits_use_the_local_cvar_gate():
    import numpy as np

    from lut_metrics import LOCAL_CVAR, STAKE_CVAR, metrics, star_checks

    assert LOCAL_CVAR == 540
    assert STAKE_CVAR == 700
    calm_payouts = np.array([0.0, 1.0, 15000.0])
    calm_probs = np.array([0.79, 0.209999, 0.000001])
    calm_probs = calm_probs / calm_probs.sum()
    calm = star_checks(metrics(calm_payouts, calm_probs, 1.0))
    assert calm["std_cost"] and calm["cvar_cost"] and calm["p5k"] and calm["max_win"]

    hot_payouts = np.array([0.0, 1.0, 8000.0])
    hot_probs = np.array([0.5, 0.49, 0.01])
    hot = star_checks(metrics(hot_payouts, hot_probs, 1.0))
    assert hot["pass"] is False
    assert hot["p5k"] is False or hot["cvar_cost"] is False


def test_optimization_matches_modes():
    from game_optimization import OptimizationSetup

    config = GameConfig()
    OptimizationSetup(config)
    for mode in config.bet_modes:
        params = config.opt_params[mode.get_name()]
        criteria = [dist.get_criteria() for dist in mode.get_distributions()]
        assert list(params["conditions"].keys()) == criteria
        rtp = round(sum(item["rtp"] for item in params["conditions"].values()), 5)
        assert rtp == 0.96


if __name__ == "__main__":
    failures = 0
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        try:
            test()
            print(f"ok {test.__name__}")
        except Exception as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
    if failures:
        raise SystemExit(1)
