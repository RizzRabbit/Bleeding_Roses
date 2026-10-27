"""Stake-style metrics from a lookUpTable CSV (id, weight, payout cents).

usage: python lut_metrics.py <lut.csv> <cost> [more lut cost pairs...]

Per-stake figures divide by the mode cost. ETL40 is the RTP, in cost units,
paid by wins above 40x cost (the figure that matched Stake on the sister
game). ETL10k is the same for wins of 10000x the base bet or more. CVaR is
the mean of the worst 0.1% of outcomes. The local CVaR gate is 540, under
Stake's 700, because a sister game's local read ran about 16% below Stake.
"""

import sys

import numpy as np

BANDS = [0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 15000, 1e18]

# Stake's published 3-star lines. Local CVaR is tighter on purpose.
STAKE_STD = 60.0
STAKE_CVAR = 700.0
LOCAL_CVAR = 540.0
STAKE_ETL40 = 0.9
STAKE_ETL10K = 0.8
STAKE_P5K = 0.01
STAKE_P10K = 0.005
STAKE_RTP_MAX = 0.967
TARGET_RTP = 0.96


def load(fn):
    table = np.loadtxt(fn, delimiter=",", dtype=np.float64)
    payouts = table[:, 2] / 100.0
    weights = table[:, 1]
    return payouts, weights / weights.sum()


def cvar(payouts, probs, quantile=0.001):
    """Mean payout of the worst `quantile` of probability."""
    order = np.argsort(-payouts, kind="stable")
    ranked_payouts = payouts[order]
    ranked_probs = probs[order]
    cumulative = np.cumsum(ranked_probs)
    cutoff = int(np.searchsorted(cumulative, quantile))
    taken = ranked_probs[: cutoff + 1].copy()
    if cumulative[cutoff] > quantile:
        taken[-1] -= cumulative[cutoff] - quantile
    return float((ranked_payouts[: cutoff + 1] * taken).sum() / taken.sum())


def metrics(payouts, probs, cost):
    mean = float((payouts * probs).sum())
    std = float(np.sqrt(((payouts - mean) ** 2 * probs).sum()))
    tail40 = payouts > 40.0 * cost
    tail10k = payouts >= 10000.0
    cap = payouts >= 15000.0 - 1e-6
    result = {
        "rtp": mean / cost,
        "hit": float(probs[payouts > 0].sum()),
        "std_raw": std,
        "std_cost": std / cost,
        "cvar_raw": cvar(payouts, probs),
        "cvar_cost": cvar(payouts, probs) / cost,
        "etl40": float((payouts * probs)[tail40].sum() / cost),
        "etl10k": float((payouts * probs)[tail10k].sum() / cost),
        "p5k": float(probs[payouts >= 5000].sum()),
        "p10k": float(probs[payouts >= 10000].sum()),
        "p_cap": float(probs[cap].sum()),
        "max": float(payouts.max()),
        "mean": mean,
    }
    result["cap_1_in"] = 1.0 / result["p_cap"] if result["p_cap"] else float("inf")
    return result


def star_checks(result):
    """Pass/fail against the 3-star lines. CVaR uses the local 540 gate."""
    checks = {
        "std_cost": result["std_cost"] <= STAKE_STD,
        "cvar_cost": result["cvar_cost"] <= LOCAL_CVAR,
        "etl40": result["etl40"] <= STAKE_ETL40,
        "etl10k": result["etl10k"] <= STAKE_ETL10K,
        "p5k": result["p5k"] < STAKE_P5K,
        "p10k": result["p10k"] < STAKE_P10K,
        "rtp": result["rtp"] <= STAKE_RTP_MAX and abs(result["rtp"] - TARGET_RTP) <= 0.0015,
        "max_win": result["max"] >= 15000.0 - 1e-6,
    }
    checks["pass"] = all(checks.values())
    return checks


def bands(payouts, probs, cost):
    mean = float((payouts * probs).sum())
    rows = []
    for low, high in zip(BANDS[:-1], BANDS[1:]):
        if low:
            mask = (payouts / cost >= low) & (payouts / cost < high)
        else:
            mask = (payouts > 0) & (payouts / cost < high)
        share = float((payouts * probs)[mask].sum() / mean) if mean else 0.0
        rows.append((low, high, float(probs[mask].sum()), share))
    return rows


def report(name, payouts, probs, cost):
    result = metrics(payouts, probs, cost)
    checks = star_checks(result)
    print(f"== {name} cost={cost} 3-star={'PASS' if checks['pass'] else 'FAIL'}")
    print("  " + "  ".join(f"{key}={value:.6g}" for key, value in result.items()))
    failed = [key for key, ok in checks.items() if key != "pass" and not ok]
    if failed:
        print("  failed:", ", ".join(failed))
    for low, high, prob, share in bands(payouts, probs, cost):
        print(f"   [{low:>6g},{high:>6g})x cost  prob={prob:.3e}  rtp_share={share * 100:6.2f}%")
    return result, checks


def evaluate_file(path, cost):
    payouts, probs = load(path)
    return report(path, payouts, probs, float(cost))


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2:
        raise SystemExit("usage: python lut_metrics.py <lut.csv> <cost> [more pairs...]")
    failed = 0
    for path, cost in zip(args[0::2], args[1::2]):
        _result, checks = evaluate_file(path, cost)
        failed += not checks["pass"]
    if failed:
        raise SystemExit(1)
