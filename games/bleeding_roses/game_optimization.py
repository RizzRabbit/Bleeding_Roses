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
# set a few percent under the probed natural means (Bleeding ~109x, Blood Moon
# ~311x, Harvest ~701x) so the optimizer overweights the smaller books.
# RTP values sum to 0.96 with the wincap and base-game fences.
#
# Cap is always 15000x the base bet. Its hit rate is 15000 / wincap_rtp / cost.
# Hit rates are "1 in N". Each extra Reaper is rarer than the tier below it.
# Bloodlust is several times more often than base. The 20x ante is more often
# still, and its Moon and Harvest are boosted more than Bleeding Spins.
FEATURE_TARGETS = {
    "base": {
        "bleeding_spins": (580, 0.18172),
        "blood_moon": (1856, 0.16252),
        "reapers_harvest": (5939, 0.11450),
        "basegame_hr": 4.72,
        "basegame_rtp": 0.49126,
    },
    "bloodlust": {
        "bleeding_spins": (112, 0.31369),
        "blood_moon": (358, 0.28085),
        "reapers_harvest": (1146, 0.19779),
        "basegame_hr": 4.72,
        "basegame_rtp": 0.15767,
    },
    "super_ante_20": {
        "bleeding_spins": (19, 0.27737),
        "blood_moon": (44, 0.34276),
        "reapers_harvest": (108, 0.31482),
        "basegame_hr": 4.81,
        "basegame_rtp": 0.00505,
        "wincap_rtp": 0.02,
    },
}

# Scale weights inside a fence. Higher values favour that win range. The fence
# mean stays the target above; this only stops the far tail from carrying it.
# Ranges are base-bet multiples.
_TAIL_BIAS = (
    (1, 20, 6.0),
    (20, 100, 5.0),
    (100, 500, 2.5),
    (500, 2000, 0.45),
    (2000, 15000, 0.08),
)
_ANTE_BIAS = (
    (1, 20, 3.0),
    (20, 100, 4.0),
    (100, 500, 4.0),
    (500, 2000, 1.4),
    (2000, 15000, 0.1),
)
_BUY_BIAS = {
    "buy_bleeding": (
        (1, 20, 4.0),
        (20, 100, 6.0),
        (100, 500, 1.6),
        (500, 2000, 0.25),
        (2000, 15000, 0.05),
    ),
    "buy_blood_moon": (
        (1, 20, 2.0),
        (20, 100, 4.0),
        (100, 500, 5.0),
        (500, 2000, 0.7),
        (2000, 15000, 0.08),
    ),
    "buy_harvest": (
        (1, 20, 2.0),
        (20, 100, 3.0),
        (100, 500, 5.0),
        (500, 2000, 2.2),
        (2000, 15000, 0.12),
    ),
}

def _parameters():
    return ConstructParameters(
        num_show=800,
        num_per_fence=1600,
        min_m2m=1,
        max_m2m=12,
        pmb_rtp=1.0,
        sim_trials=800,
        test_spins=[50, 100, 200],
        test_weights=[0.3, 0.4, 0.3],
        score_type="rtp",
    ).return_dict()


def _scaling(criteria_names, bands):
    rows = []
    for name in criteria_names:
        for win_range in bands:
            lo, hi, scale = win_range
            rows.append(
                {
                    "criteria": name,
                    "scale_factor": scale,
                    "win_range": (lo, hi),
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
                bands = _ANTE_BIAS if name == "super_ante_20" else _TAIL_BIAS
            elif name == "full_bleed":
                conditions = _full_bleed_block()
                scalable = ["full_bleed"]
                bands = tuple((lo, hi, 1.0) for lo, hi, _scale in _TAIL_BIAS)
            elif name in _BUY_BIAS:
                criteria = {
                    "buy_bleeding": "bleeding_spins",
                    "buy_blood_moon": "blood_moon",
                    "buy_harvest": "reapers_harvest",
                }[name]
                wincap_rtp = 0.02 if name == "buy_harvest" else Wincap_RTP
                conditions = _buy_block(criteria, wincap_rtp=wincap_rtp)
                scalable = [criteria]
                bands = _BUY_BIAS[name]
            else:
                raise RuntimeError(f"no optimization block for mode {name}")
            opt[name] = {
                "conditions": conditions,
                "scaling": _scaling(scalable, bands),
                "parameters": params,
            }
        game_config.opt_params = opt
        verify_optimization_input(game_config, game_config.opt_params)
