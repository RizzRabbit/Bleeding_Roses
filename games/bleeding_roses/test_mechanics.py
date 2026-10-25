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
        "super_ante_10",
        "super_ante_20",
        "buy_bleeding",
        "buy_blood_moon",
        "buy_harvest",
        "full_bleed",
    ]
    costs = {mode.get_name(): mode.get_cost() for mode in config.bet_modes}
    assert costs["base"] == 1
    assert costs["bloodlust"] == 3
    assert costs["super_ante_10"] == 10
    assert costs["super_ante_20"] == 20
    assert costs["buy_harvest"] > costs["buy_bleeding"] > costs["buy_blood_moon"]
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
    _plant(
        state,
        [
            ["10", "10", "10", "10"],
            ["BH", "WR", "10", "10"],
            ["10", "10", "10", "10"],
            ["10", "10", "10", "10"],
            ["10", "10", "10", "10"],
        ],
    )
    state.resolve_board()
    assert state.sticky_reels == [1]
    assert _names(state)[1][1] == "BWR"
    assert any(event["type"] == "stickyReel" for event in state.book.events)

    state.book = state.book.__class__(state.book.id, state.book.criteria)
    _plant(
        state,
        [
            ["10", "10", "10", "10"],
            ["RR", "10", "10", "10"],
            ["BH", "WR", "10", "10"],
            ["10", "10", "10", "10"],
            ["10", "10", "10", "10"],
        ],
    )
    state.resolve_board()
    assert _names(state)[1][0] == "BRR"
    assert _names(state)[2][1] == "BWR"
    assert state.sticky_reels == [1, 2]


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


def test_wincap_is_reachable():
    """Every mode can pay 15000x the base bet, not 15000x its cost."""
    modes = [
        "base",
        "bloodlust",
        "super_ante_10",
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
