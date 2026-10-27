"""Compare each mode's published lookup table with the frontend math index.

RTP is the weighted mean payout divided by the mode cost. Payouts in the table
are cents of the base bet. max win is the largest payout, in base bets.

Exit 1 if index.json disagrees. Pass --write to store the table values.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
GAME = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INDEX = os.path.join(
    ROOT, "web-sdk", "apps", "bleeding_roses", "static", "assets", "math", "index.json"
)


def load_rows(path):
    rows = []
    with open(path, encoding="UTF-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            _sim_id, weight, payout = line.split(",")
            rows.append((float(weight), int(payout)))
    if not rows:
        raise RuntimeError(f"empty lookup table: {path}")
    return rows


def measure(path, cost):
    rows = load_rows(path)
    weight = sum(item[0] for item in rows)
    mean = sum(item[0] * (item[1] / 100.0) for item in rows) / weight
    rtp = mean / cost
    max_win = max(item[1] for item in rows) / 100.0
    return rtp, max_win, len(rows)


def lookup_path(mode):
    library = os.path.join(GAME, "library")
    published = os.path.join(library, "publish_files", f"lookUpTable_{mode}_0.csv")
    if os.path.exists(published):
        return published
    return os.path.join(library, "lookup_tables", f"lookUpTable_{mode}.csv")


def main(argv):
    write = "--write" in argv
    index_path = DEFAULT_INDEX
    for arg in argv[1:]:
        if arg != "--write":
            index_path = arg
    with open(index_path, encoding="UTF-8") as handle:
        payload = json.load(handle)
    failures = []
    print(f"{'mode':16} {'cost':8} {'rtp':12} {'maxWin':10} lookup")
    for mode in payload["modes"]:
        name = mode["name"]
        cost = float(mode["cost"])
        path = lookup_path(name)
        rtp, max_win, count = measure(path, cost)
        rtp_text = f"{rtp * 100:.3f}%"
        print(f"{name:16} {cost:<8g} {rtp_text:12} {max_win:<10g} {count} rows  {path}")
        if write:
            mode["rtp"] = round(rtp, 6)
            mode["maxWin"] = max_win
        else:
            if abs(float(mode["rtp"]) - rtp) > 5e-7:
                failures.append(f"{name} rtp index={mode['rtp']} table={rtp:.6f}")
            if abs(float(mode["maxWin"]) - max_win) > 1e-6:
                failures.append(f"{name} maxWin index={mode['maxWin']} table={max_win}")
    if write:
        with open(index_path, "w", encoding="UTF-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        print(f"wrote {index_path}")
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
