"""Frontend events for Bleeding Roses.

Row indexes follow the Stake web-sdk convention: when the board is padded, row 0
is the padding symbol above the window, so visible rows are reported as 1..4.
"""

from src.events.event_constants import EventConstants
from src.events.events import json_ready_sym


def _row(gamestate, row):
    if gamestate.config.include_padding:
        return row + 1
    return row


def _positions(gamestate, positions):
    return [{"reel": pos["reel"], "row": _row(gamestate, pos["row"])} for pos in positions]


def _transformations(gamestate, changes):
    padded = []
    for change in changes:
        padded.append(
            {
                "reel": change["reel"],
                "row": _row(gamestate, change["row"]),
                "from": change["from"],
                "to": change["to"],
            }
        )
    return padded


def _board_client(gamestate):
    special_attributes = list(gamestate.config.special_symbols.keys())
    board_client = []
    for reel, _ in enumerate(gamestate.board):
        board_client.append([])
        for row in range(len(gamestate.board[reel])):
            board_client[reel].append(json_ready_sym(gamestate.board[reel][row], special_attributes))
    if gamestate.config.include_padding:
        for reel, _ in enumerate(board_client):
            board_client[reel] = [json_ready_sym(gamestate.top_symbols[reel], special_attributes)] + board_client[reel]
            board_client[reel].append(json_ready_sym(gamestate.bottom_symbols[reel], special_attributes))
    return board_client


def full_bleed_event(gamestate, changes):
    """Every plain rose on a Full Bleed spin turns bloody before wins are scored."""
    event = {
        "index": len(gamestate.book.events),
        "type": "fullBleed",
        "transformations": _transformations(gamestate, changes),
    }
    gamestate.book.add_event(event)


def reel_bleed_event(gamestate, reel, scope, triggers, changes, multiplier):
    """One reel's bleed. `multiplier` is null when this tier does not stamp a reel multiplier."""
    event = {
        "index": len(gamestate.book.events),
        "type": "reelBleed",
        "reel": reel,
        "scope": scope,
        "multiplierApplied": multiplier is not None,
        "multiplier": multiplier if multiplier is not None else 1,
        "triggers": [{"reel": reel, "row": _row(gamestate, row)} for row in triggers],
        "transformations": _transformations(gamestate, changes),
    }
    gamestate.book.add_event(event)


def sticky_bleed_event(gamestate, changes):
    """Roses landing on an already-bloody reel during Blood Moon."""
    event = {
        "index": len(gamestate.book.events),
        "type": "stickyBleed",
        "stickyReels": list(gamestate.sticky_reels),
        "transformations": _transformations(gamestate, changes),
    }
    gamestate.book.add_event(event)


def sticky_reel_event(gamestate, new_reels):
    """A Blood Moon reel locks bloody, with the multiplier it keeps for the bonus."""
    event = {
        "index": len(gamestate.book.events),
        "type": "stickyReel",
        "newReels": list(new_reels),
        "multipliers": [gamestate.sticky_multipliers[reel] for reel in new_reels],
        "stickyReels": list(gamestate.sticky_reels),
        "stickyMultipliers": [gamestate.sticky_multipliers[reel] for reel in gamestate.sticky_reels],
    }
    gamestate.book.add_event(event)


def global_multiplier_event(gamestate, increment, reel, heart_reels=None):
    """Reaper's Harvest global multiplier. Same `type` as the SDK event, plus the step that caused it.

    One event per bleeding spin. `heartReels` lists every Bleeding Heart on that
    spin; the multiplier still advances by `increment` (one), not by the heart count.
    """
    hearts = list(heart_reels if heart_reels is not None else [reel])
    event = {
        "index": len(gamestate.book.events),
        "type": EventConstants.UPDATE_GLOBAL_MULT.value,
        "globalMult": int(gamestate.global_multiplier),
        "increment": int(increment),
        "reel": reel,
        "heartReels": hearts,
        "reason": "bleed",
    }
    gamestate.book.add_event(event)


def board_after_bleed_event(gamestate):
    """Authoritative board once every transformation this spin has been applied."""
    event = {
        "index": len(gamestate.book.events),
        "type": "boardAfterBleed",
        "board": _board_client(gamestate),
        "reelMultipliers": list(gamestate.reel_multipliers),
        "globalMult": int(gamestate.global_multiplier),
        "tier": gamestate.bonus_tier,
        "stickyReels": list(gamestate.sticky_reels),
    }
    gamestate.book.add_event(event)


def bonus_tier_event(gamestate):
    """Which free-spin tier was just entered, and the rules the frontend should play."""
    count, info = gamestate.config.tier_by_id(gamestate.bonus_tier)
    event = {
        "index": len(gamestate.book.events),
        "type": "bonusTier",
        "tier": info["id"],
        "tierName": info["name"],
        "scatterCount": count,
        "spins": info["spins"],
        "boardBleed": info["board_bleed"],
        "sticky": info["sticky"],
        "globalMultiplier": info["global_mult"],
    }
    gamestate.book.add_event(event)


def retrigger_event(gamestate, added, scatter_count):
    """Extra spins. The tier does not change."""
    event = {
        "index": len(gamestate.book.events),
        "type": "retrigger",
        "tier": gamestate.bonus_tier,
        "addedSpins": int(added),
        "totalFs": int(gamestate.tot_fs),
        "scatterCount": int(scatter_count),
    }
    gamestate.book.add_event(event)
