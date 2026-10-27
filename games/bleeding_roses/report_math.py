"""Summarise optimized Bleeding Roses books. Does not upload anything.

Joins the published lookup table (id, weight, payout in cents of the base bet)
to the segmented criteria file. The cap is 15000x the base bet on every mode.
"""

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_config import GameConfig


WINCAP_TIER = {
    "base": "reapers_harvest",
    "bloodlust": "reapers_harvest",
    "super_ante_20": "reapers_harvest",
    "buy_bleeding": "bleeding_spins",
    "buy_blood_moon": "blood_moon",
    "buy_harvest": "reapers_harvest",
}

TIERS = ("bleeding_spins", "blood_moon", "reapers_harvest")


def _load(config, mode):
    library = config.library_path
    published = os.path.join(library, "publish_files", f"lookUpTable_{mode}_0.csv")
    segmented = os.path.join(library, "lookup_tables", f"lookUpTableSegmented_{mode}.csv")
    criteria = {}
    with open(segmented, encoding="UTF-8") as handle:
        for line in handle:
            sim_id, name, base_win, free_win = line.strip().split(",")
            criteria[sim_id] = (name, float(base_win), float(free_win))
    rows = []
    with open(published, encoding="UTF-8") as handle:
        for line in handle:
            sim_id, weight, payout = line.strip().split(",")
            name, base_win, free_win = criteria[sim_id]
            rows.append(
                {
                    "id": sim_id,
                    "weight": float(weight),
                    "payout": int(payout) / 100.0,
                    "criteria": name,
                    "base": base_win,
                    "free": free_win,
                }
            )
    return rows


def _tier_of(mode, row):
    if row["criteria"] == "wincap":
        return WINCAP_TIER.get(mode, "wincap")
    if row["criteria"] in TIERS:
        return row["criteria"]
    return None


def summarise(config):
    print(
        "mode,cost,rtp,hit_rate,std_x,max_x,p_cap,"
        "hr_bleeding,hr_moon,hr_harvest,"
        "rtp_base,rtp_bleeding,rtp_moon,rtp_harvest,"
        "avg_bleeding,avg_moon,avg_harvest"
    )
    for mode in config.bet_modes:
        name = mode.get_name()
        cost = mode.get_cost()
        rows = _load(config, name)
        total_w = sum(row["weight"] for row in rows)
        mean = sum(row["weight"] * row["payout"] for row in rows) / total_w
        second = sum(row["weight"] * row["payout"] ** 2 for row in rows) / total_w
        std = (max(second - mean ** 2, 0.0)) ** 0.5
        hit_w = sum(row["weight"] for row in rows if row["payout"] > 0)
        cap_w = sum(row["weight"] for row in rows if abs(row["payout"] - config.wincap) < 1e-6)
        max_win = max(row["payout"] for row in rows)
        tier_w = defaultdict(float)
        tier_pay = defaultdict(float)
        base_pay = 0.0
        for row in rows:
            tier = _tier_of(name, row)
            if tier is None:
                base_pay += row["weight"] * row["payout"]
            else:
                tier_w[tier] += row["weight"]
                tier_pay[tier] += row["weight"] * row["payout"]

        def hr(tier):
            if tier_w[tier] <= 0:
                return ""
            return f"{total_w / tier_w[tier]:.1f}"

        def rtp(pay):
            return pay / total_w / cost

        def avg(tier):
            if tier_w[tier] <= 0:
                return ""
            return f"{tier_pay[tier] / tier_w[tier]:.2f}"

        print(
            f"{name},{cost:.0f},{mean / cost:.4f},{hit_w / total_w:.4f},{std:.2f},{max_win:.1f},"
            f"{cap_w / total_w:.8f},{hr('bleeding_spins')},{hr('blood_moon')},{hr('reapers_harvest')},"
            f"{rtp(base_pay):.4f},{rtp(tier_pay['bleeding_spins']):.4f},"
            f"{rtp(tier_pay['blood_moon']):.4f},{rtp(tier_pay['reapers_harvest']):.4f},"
            f"{avg('bleeding_spins')},{avg('blood_moon')},{avg('reapers_harvest')}"
        )


if __name__ == "__main__":
    summarise(GameConfig())
