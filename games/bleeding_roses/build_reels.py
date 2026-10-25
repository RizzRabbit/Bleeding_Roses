"""Deterministic reel strips for Bleeding Roses.

Each bet mode draws the strips it needs. BH stays on reels 2-4 (indexes 1-3);
the ways calculator does not treat a wild on reel 1 as a starter. Reapers, where
they appear, sit at least five stops apart so a 4-row window never holds two.

    BR0     base spins (base, bloodlust, both antes, buy triggers)
    FRB     Bleeding Spins. Rose-heavy so the board-wide bleed pays well.
    FRM     Blood Moon. Richer than Bleeding Spins; sticky reel multipliers carry it.
    FRH     Reaper's Harvest. Leaner roses; the global multiplier carries it.
    FRM20   Blood Moon on the 20x super ante. Richer than FRM, leaner than FRH20.
    FRH20   Harvest on the 20x super ante
    FRW     Max-win free spins. Already-bloody premiums, every tier can cap.
    FB0     Full Bleed feature spin
    FBW     Full Bleed max-win spin
"""

import os
import random

LENGTH = 100
MIN_RP_GAP = 5
REEL_COUNT = 5
LOWS = ["10", "J", "Q", "K", "A"]


def _biased_lows(filler, remaining):
    primary = max(remaining // 2, 1)
    counts = {name: 0 for name in LOWS}
    counts[filler] = primary
    rest = remaining - primary
    others = [name for name in LOWS if name != filler]
    base, extra = divmod(rest, len(others))
    for name in others:
        counts[name] = base
    counts[others[0]] += extra
    if sum(counts.values()) != remaining:
        raise RuntimeError("low-symbol split does not fill the strip")
    return counts


def _rp_gaps_ok(strip):
    indexes = [i for i, symbol in enumerate(strip) if symbol == "RP"]
    n = len(strip)
    for i, left in enumerate(indexes):
        for right in indexes[i + 1 :]:
            distance = min(abs(left - right), n - abs(left - right))
            if distance < MIN_RP_GAP:
                return False
    return True


def _shuffle_valid(counts, seed):
    bag = []
    for symbol, count in counts.items():
        if count < 0:
            raise RuntimeError(f"negative count for {symbol}")
        bag.extend([symbol] * count)
    if len(bag) != LENGTH:
        raise RuntimeError(f"expected {LENGTH} symbols, got {len(bag)} from {counts}")
    rng = random.Random(seed)
    for _ in range(8000):
        rng.shuffle(bag)
        if _rp_gaps_ok(bag):
            return list(bag)
    raise RuntimeError("could not place Reapers with the required gap")


def _column(premiums, filler, seed):
    total = sum(premiums.values())
    if total > LENGTH - len(LOWS):
        raise RuntimeError(f"premiums leave no room for lows: {premiums}")
    counts = _biased_lows(filler, LENGTH - total)
    counts.update(premiums)
    return _shuffle_valid(counts, seed)


def _strip(seed, wr, rr, br, bh, bwr=1, brr=1, bbr=1, rp_edge=4, rp_mid=3):
    """Five reels. Hearts only on the middle three. Edges carry the extra Reapers."""
    columns = []
    fillers = ["10", "Q", "K", "A", "J"]
    for index, filler in enumerate(fillers):
        premiums = {"WR": wr, "RR": rr, "BR": br, "BWR": bwr, "BRR": brr, "BBR": bbr}
        premiums["RP"] = rp_edge if index in (0, 4) else rp_mid
        if index in (1, 2, 3):
            premiums["BH"] = bh
        columns.append(_column(premiums, filler, seed + index))
    return columns


def base_strips():
    """Each reel is dominated by a different low symbol, so 3-of-a-kind is uncommon.

    Hearts are a single stop on reels 2-4. The base spin has to leave most of
    the 96% return for the three bonuses.
    """
    specs = [
        ({"10": 65, "J": 13, "Q": 6, "K": 4, "A": 4, "WR": 2, "RR": 1, "BR": 1, "RP": 4}, 111),
        ({"Q": 63, "K": 11, "J": 8, "A": 5, "10": 4, "WR": 2, "RR": 1, "BR": 1, "BH": 2, "RP": 3}, 112),
        ({"K": 63, "A": 11, "Q": 8, "J": 5, "10": 4, "WR": 2, "RR": 1, "BR": 1, "BH": 2, "RP": 3}, 113),
        ({"A": 63, "J": 11, "Q": 8, "K": 5, "10": 4, "WR": 2, "RR": 1, "BR": 1, "BH": 2, "RP": 3}, 114),
        ({"J": 66, "Q": 11, "K": 7, "A": 5, "10": 3, "WR": 2, "RR": 1, "BR": 1, "RP": 4}, 115),
    ]
    columns = []
    for counts, seed in specs:
        if sum(counts.values()) != LENGTH:
            raise RuntimeError(f"base reel sums to {sum(counts.values())}: {counts}")
        columns.append(_shuffle_valid(dict(counts), seed))
    return columns


def full_bleed_strips():
    """One paid spin. Lots of plain roses; the mode bleeds every one of them."""
    columns = []
    specs = [
        ({"WR": 20, "RR": 14, "BR": 12, "RP": 2}, "10", 201),
        ({"WR": 20, "RR": 14, "BR": 12, "BH": 12, "RP": 2}, "Q", 202),
        ({"WR": 20, "RR": 14, "BR": 12, "BH": 12, "RP": 2}, "K", 203),
        ({"WR": 20, "RR": 14, "BR": 12, "BH": 12, "RP": 2}, "A", 204),
        ({"WR": 20, "RR": 14, "BR": 12, "RP": 2}, "J", 205),
    ]
    for premiums, filler, seed in specs:
        columns.append(_column(premiums, filler, seed))
    return columns


def full_bleed_wincap_strips():
    """Solid roses plus hearts. No Reapers: this spin never opens a bonus."""
    columns = []
    specs = [
        ({"BR": 72, "RR": 10, "WR": 8}, "10", 211),
        ({"BR": 52, "RR": 8, "WR": 6, "BH": 22}, "Q", 212),
        ({"BR": 50, "RR": 8, "WR": 6, "BH": 24}, "K", 213),
        ({"BR": 52, "RR": 8, "WR": 6, "BH": 22}, "A", 214),
        ({"BR": 72, "RR": 10, "WR": 8}, "J", 215),
    ]
    for premiums, filler, seed in specs:
        columns.append(_column(premiums, filler, seed))
    return columns


def wincap_strips():
    """Already-bloody black roses. Caps Bleeding Spins, Blood Moon, and Harvest."""
    columns = []
    specs = [
        ({"BBR": 74, "BRR": 8, "BR": 4, "RP": 4}, "10", 301),
        ({"BBR": 56, "BRR": 6, "BWR": 4, "BH": 20, "RP": 3}, "Q", 302),
        ({"BBR": 54, "BRR": 6, "BWR": 4, "BH": 22, "RP": 3}, "K", 303),
        ({"BBR": 56, "BRR": 6, "BWR": 4, "BH": 20, "RP": 3}, "A", 304),
        ({"BBR": 74, "BRR": 8, "BR": 4, "RP": 4}, "J", 305),
    ]
    for premiums, filler, seed in specs:
        columns.append(_column(premiums, filler, seed))
    return columns


def _write(path, columns):
    with open(path, "w", encoding="UTF-8") as handle:
        for row in range(LENGTH):
            handle.write(",".join(columns[reel][row] for reel in range(REEL_COUNT)) + "\n")


def main():
    folder = os.path.join(os.path.dirname(__file__), "reels")
    os.makedirs(folder, exist_ok=True)
    strips = {
        "BR0.csv": base_strips(),
        "FRB.csv": _strip(401, wr=12, rr=10, br=7, bh=12, bwr=4, brr=2, bbr=2),
        "FRM.csv": _strip(411, wr=14, rr=10, br=8, bh=11, bwr=3, brr=2, bbr=2),
        "FRH.csv": _strip(421, wr=12, rr=9, br=6, bh=9, bwr=3, brr=2, bbr=2),
        "FRM20.csv": _strip(451, wr=14, rr=10, br=8, bh=11, bwr=3, brr=2, bbr=2),
        "FRH20.csv": _strip(461, wr=12, rr=9, br=6, bh=9, bwr=3, brr=2, bbr=2),
        "FRW.csv": wincap_strips(),
        "FB0.csv": full_bleed_strips(),
        "FBW.csv": full_bleed_wincap_strips(),
    }
    for name, columns in strips.items():
        _write(os.path.join(folder, name), columns)
        print(f"wrote {name}")
    for stale in ("FR0.csv", "FRRICH.csv", "FRWCAP.csv", "FBWCAP.csv", "FRM10.csv", "FRH10.csv"):
        path = os.path.join(folder, stale)
        if os.path.exists(path):
            os.remove(path)
            print(f"removed {stale}")


if __name__ == "__main__":
    main()
