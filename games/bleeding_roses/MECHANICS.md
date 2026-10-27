# Bleeding Roses: mechanics spec and event contract

Source: `games/bleeding_roses` on `cursor/bleeding-roses-math-8e18` (PR #1) and
`web-sdk/apps/bleeding_roses` on `cursor/bleeding-roses-frontend-dd36` (PR #2).
All amounts in book events are integer cents of the base bet (100 = 1x).
Rows in book events are padded: visible rows are 1..4.

## 1. Game

- 5 reels x 4 rows, 1024 ways, left to right, pays on a 0.1x grid.
- Symbols: lows `10 J Q K A`; roses `WR RR BR`; bloody roses `BWR BRR BBR`
  (exactly 3x the plain rose); `BH` Bleeding Heart (wild, pays 1/4/15x for 3/4/5);
  `RP` Reaper (scatter).
- Max win 15000x the base bet in every mode. Antes and buys do not scale it.
- RTP 96% target in every mode.

## 2. Bleed (core mechanic)

A Bleeding Heart can only act on reels 2, 3, 4 (`bleed_reels = [1,2,3]`).
Wins are always scored on the board **after** all bleeds.

| Context | What a heart does | Reel multiplier |
|---|---|---|
| Base / ante | Turns every plain rose on **its own reel** bloody | Draws 2x/3x/5x (82/14/4) for that reel |
| Full Bleed (100x) | Every plain rose on the board turns bloody first, then hearts bleed their reel | Same draw as base |
| Bleeding Spins (3 RP, 10 spins, +5) | Turns every rose on the **whole board** bloody | None |
| Blood Moon (4 RP, 12 spins, +6) | First heart on a reel locks it bloody for the bonus; roses landing there later turn bloody | Drawn once at lock (70/23/7), kept for the bonus, applies from that spin |
| Reaper's Harvest (5+ RP, 15 spins, +8) | Whole-board bleed | Global multiplier +1 per spin that bleeds (not per heart), applied to that same spin; starts at 1 |

A way's win = base pay x product of reel multipliers on the reels it covers x global multiplier,
snapped to 0.1x.

## 3. Bet modes

| Mode | Cost | Notes |
|---|---|---|
| base | 1x | |
| bloodlust | 3x | Same strips as base, bonus dealt more often |
| super_ante_20 | 20x | Own Blood Moon / Harvest strips |
| buy_bleeding | 100x | Starts Bleeding Spins |
| buy_blood_moon | 300x | Starts Blood Moon |
| buy_harvest | 600x | Starts Reaper's Harvest |
| full_bleed | 100x | One spin with Full Bleed; never enters a bonus |

## 4. Event order per spin

Base spin: `reveal` -> [`fullBleed`] -> [`stickyReel`] -> [`stickyBleed`] -> `reelBleed`* ->
[`updateGlobalMult`] -> [`boardAfterBleed`] -> [`winInfo` -> `wincap`? -> `setWin`] -> `setTotalWin`.
Bonus entry: `freeSpinTrigger` -> `enterBonus` -> `bonusTier`, then per free spin
`updateFreeSpin` + the spin events above, with `freeSpinRetrigger` + `retrigger` on a retrigger.
Round end: `freeSpinEnd` (if bonus) -> `finalWin`.

## 5. Event contract

| Event | Fields | Frontend must |
|---|---|---|
| `reveal` | `board` (6 rows incl. padding), `paddingPositions`, `anticipation`, `gameType` | Stop reels on rows 1..4; play anticipation per reel |
| `fullBleed` | `transformations[{reel,row,from,to}]` | Melt every listed rose before anything else |
| `reelBleed` | `reel`, `scope` (`reel`/`board`), `multiplierApplied`, `multiplier`, `triggers[]`, `transformations[]` | Melt listed roses; if `multiplierApplied`, show the reel multiplier badge |
| `stickyReel` | `newReels`, `multipliers`, `stickyReels`, `stickyMultipliers` | Lock reel visuals and badges for the rest of the bonus |
| `stickyBleed` | `stickyReels`, `transformations[]` | Melt roses landing on locked reels |
| `updateGlobalMult` | `globalMult`, `increment`, `reel`, `heartReels`, `reason` | Update the Harvest meter **before** wins present |
| `boardAfterBleed` | `board`, `reelMultipliers`, `globalMult`, `tier`, `stickyReels` | Authoritative state: snap board and badges to this |
| `winInfo` | `totalWin`, `wins[{symbol,kind,win,positions,meta{ways,winWithoutMult,reelMult,globalMult,reelMultipliers}}]` | Highlight ways; sum of `win` = `totalWin` |
| `setWin` | `amount`, `winLevel` | Spin win banner (not emitted after wincap) |
| `setTotalWin` | `amount` | Round running total |
| `wincap` | `amount` | Stop the round's presentation at 15000x |
| `freeSpinTrigger` / `freeSpinRetrigger` | `totalFs`, `positions` | Highlight Reapers; update spin count |
| `enterBonus` | `reason` | Switch to bonus scene |
| `bonusTier` | `tier`, `tierName`, `scatterCount`, `spins`, `boardBleed`, `sticky`, `globalMultiplier` | Tier intro |
| `retrigger` | `tier`, `addedSpins`, `totalFs`, `scatterCount` | "+N spins" |
| `updateFreeSpin` | `amount` (0-based spin index), `total` | Counter shows `amount+1 / total` |
| `freeSpinEnd` | `amount`, `winLevel` | Bonus total (free-game wins only) |
| `finalWin` | `amount` | Equals `payoutMultiplier` and the RGS payout |

**Invariant the frontend relies on:** the last `setTotalWin` = `finalWin` = book `payoutMultiplier`,
and `freeSpinEnd.amount` = free-game wins exactly.
