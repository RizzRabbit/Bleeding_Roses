"""Optimization fences for every Bleeding Roses bet mode.

Fence RTP values are fractions of the mode RTP (they sum to 0.96). `hr` is the
published "1 in N" rate. For a fence with an explicit hit rate the average
payout of those books is `hr * rtp * cost`. Wincap uses the 15000x cap directly.
The `0` fence is the remainder, so its hit rate is left unset.
"""

from optimization_program.optimization_config import (
    ConstructConditions,
    ConstructParameters,
    ConstructScaling,
    verify_optimization_input,
)


Wincap_RTP = 0.01

# (hr, rtp) per feature fence. The average win of that fence is `hr * rtp * cost`,
# set next to the probed conditional mean so the optimizer is not asked to
# invent return that the books do not contain. RTP values sum to 0.96 with the
# wincap and base-game fences.
#
# Cap is always 15000x the base bet. Its hit rate is 15000 / wincap_rtp / cost.
FEATURE_TARGETS = {
    "base": {
        "bleeding_spins": (615, 0.260),
        "blood_moon": (720, 0.050),
        "reapers_harvest": (3512, 0.205),
        "basegame_hr": 4.72,
        "basegame_rtp": 0.435,
    },
    "bloodlust": {
        "bleeding_spins": (135, 0.39506),
        "blood_moon": (150, 0.08000),
        "reapers_harvest": (730, 0.32994),
        "basegame_hr": 4.72,
        "basegame_rtp": 0.145,
    },
    "super_ante_10": {
        "bleeding_spins": (280, 0.05350),
        "blood_moon": (40, 0.16250),
        "reapers_harvest": (228, 0.69180),
        "basegame_hr": 4.81,
        "basegame_rtp": 0.04220,
    },
    "super_ante_20": {
        "bleeding_spins": (275, 0.02723),
        "blood_moon": (45, 0.11667),
        "reapers_harvest": (174, 0.77500),
        "basegame_hr": 4.81,
        "basegame_rtp": 0.02110,
        "wincap_rtp": 0.02,
    },
}

TAIL_RANGES = (
    (1, 20),
    (20, 100),
    (100, 500),
    (500, 2000),
    (2000, 15000),
)


def _parameters():
    return ConstructParameters(
        num_show=800,
        num_per_fence=1600,
        min_m2m=1,
        max_m2m=80,
        pmb_rtp=1.0,
        sim_trials=800,
        test_spins=[50, 100, 200],
        test_weights=[0.3, 0.4, 0.3],
        score_type="rtp",
    ).return_dict()


def _scaling(criteria_names):
    rows = []
    for name in criteria_names:
        for win_range in TAIL_RANGES:
            rows.append(
                {
                    "criteria": name,
                    "scale_factor": 1.0,
                    "win_range": win_range,
                    "probability": 1.0,
                }
            )
    return ConstructScaling(rows).return_dict()


def _wincap(rtp):
    return ConstructConditions(rtp=rtp, av_win=15000, search_conditions=15000).return_dict()


def _zero():
    return ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict()


def _feature_block(spec, wincap_rtp):
    """Ordered fences: cap, three tiers, dead spins, base-game wins."""
    assigned = wincap_rtp
    conditions = {"wincap": _wincap(wincap_rtp)}
    for tier in ("reapers_harvest", "blood_moon", "bleeding_spins"):
        hr, rtp = spec[tier]
        conditions[tier] = ConstructConditions(
            rtp=rtp, hr=hr, search_conditions={"tier": tier}
        ).return_dict()
        assigned += rtp
    base_rtp = spec["basegame_rtp"]
    assigned = round(assigned + base_rtp, 5)
    if abs(assigned - 0.96) > 1e-9:
        raise RuntimeError(f"fence RTP sums to {assigned}, not 0.96: {spec}")
    conditions["0"] = _zero()
    conditions["basegame"] = ConstructConditions(rtp=base_rtp, hr=spec["basegame_hr"]).return_dict()
    return conditions


def _buy_block(criteria, wincap_rtp=Wincap_RTP):
    feature_rtp = round(0.96 - wincap_rtp, 5)
    return {
        "wincap": _wincap(wincap_rtp),
        criteria: ConstructConditions(
            rtp=feature_rtp, hr="x", search_conditions={"tier": criteria}
        ).return_dict(),
    }


def _full_bleed_block():
    return {
        "wincap": _wincap(Wincap_RTP),
        "0": _zero(),
        "full_bleed": ConstructConditions(rtp=round(0.96 - Wincap_RTP, 5), hr=1.37).return_dict(),
    }


class OptimizationSetup:
    """Attach `opt_params` for every bet mode on the config."""

    def __init__(self, game_config):
        self.game_config = game_config
        params = _parameters()
        opt = {}
        for bet_mode in game_config.bet_modes:
            name = bet_mode.get_name()
            if name in FEATURE_TARGETS:
                spec = FEATURE_TARGETS[name]
                conditions = _feature_block(spec, spec.get("wincap_rtp", Wincap_RTP))
                scalable = ["reapers_harvest", "blood_moon", "bleeding_spins", "basegame"]
            elif name == "full_bleed":
                conditions = _full_bleed_block()
                scalable = ["full_bleed"]
            elif name == "buy_bleeding":
                conditions = _buy_block("bleeding_spins")
                scalable = ["bleeding_spins"]
            elif name == "buy_blood_moon":
                conditions = _buy_block("blood_moon")
                scalable = ["blood_moon"]
            elif name == "buy_harvest":
                conditions = _buy_block("reapers_harvest", wincap_rtp=0.02)
                scalable = ["reapers_harvest"]
            else:
                raise RuntimeError(f"no optimization block for mode {name}")
            opt[name] = {
                "conditions": conditions,
                "scaling": _scaling(scalable),
                "parameters": params,
            }
        game_config.opt_params = opt
        verify_optimization_input(game_config, game_config.opt_params)
