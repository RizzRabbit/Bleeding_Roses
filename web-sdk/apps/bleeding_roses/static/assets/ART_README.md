# Bleeding Roses: art v6

v6 is built from v5, and the v5 folder is untouched. The layout goes back to **v1**: the "BLEEDING ROSES / RIZZIN GAMES" logo sits centred above the reels with a rose on each side, and there is an angel statue on the left and on the right. All v5 cleanups are kept: 172px cells at 1920, Cinzel type, the clean iron frame, the oval Bonus Buy/Ante plaques with captions, the round rose Spin button and the bottom bar. The Reaper and the bloody symbols are relit so they read at 172px, and the portrait backgrounds and a mobile mockup are new.

## Deliverables
| File | What it is |
|---|---|
| `mockup_desktop_v6.png` / `.jpg` | 1920x1080 desktop mockup (v1 layout) |
| `mockup_mobile_v6.png` / `.jpg` | 1080x1920 mobile portrait mockup |
| `br_v6_contact_sheet.jpg` | Symbols, letters, melt keyframes, heart idle/win |
| `preview/br_v6_board_preview.mp4` | 16s, 1920x1080, 30fps, 480 frames. Plain board → melts → bloody idle → heart win → idle |
| `scene/reel_frame.png` + `.json` | Frame art at 1182x1005 with a transparent 5x4 window (x141 y134, cell 180). The `mockup_1920` and `mockup_portrait_1080` keys give the v6 placements |
| `scene/bg_v6_1920.png`, `bg_v6_2560.png` | Cleaned 16:9 background with both angels brightened |
| `scene/bg_v6_portrait_1080.png`, `bg_v6_portrait_1440.png` | 9:16 background, cleaned in the same style (new in v6) |
| `scene/ui/logo.png` (1892x267), `logo_text.png`, `plaque_*.png` | UI set in real type |
| `atlas/` + `atlas/manifest.json` | Pixi/TexturePacker JSON-hash sheets at 1x (256px) and @2x (512px). Every sheet is ≤4096. 30fps |
| `pixi_test/index.html` | Atlas playback test with screenshots `shot_*.png` and `shots_grid.jpg` |

## Layout
**Desktop (1920x1080):**
- Logo: w=960, centred at (960, 72).
- Frame: at (395, 70), scale 0.9556; grid at (530, 198), 860x688, cell 172.
- Bar: top at y≈904. Spin is centred.
- Plaques: left side, centre y 690 and 880, w 250, with captions under them.
- Sound/Info/Menu: top right. Autoplay/Turbo: bottom right.

**Mobile (1080x1920):**
- Logo: w=1020 at y 410.
- Plaques: side by side at y 610.
- Grid: at (140, 899), cell 160, 800x640.
- Bar: 820 wide, top at ≈1733, with Autoplay/Turbo either side.
- Sound/Info/Menu: top right.

## Contrast relight (`relight.py`)
This is a pointwise pass `f(frame, plain)` on the v5 frames, which gives two properties:
- Every frame identity is preserved exactly (melt0 == plain, melt_last == idle0 == bloody still, win0 == idle0).
- The loops stay seamless.

**Liquid:** a weight `w` comes from the difference against the plain symbol and is guarded so the black ink stays black. The liquid is lifted per channel toward brighter crimson. The red channel rises by +43% on the bloody red rose, +48% on the bloody black and +54% on the heart. The heart gets an extra global lift, and its V band is kept. There is no glow, no bloom and no added specular.

**Reaper:**
- The pink AI rim inside the silhouette is replaced with dark robe.
- The robe is lifted, with a cold ambient fill.
- A cold upper-left moonlight rim is added on the hood, shoulder and scythe.
- The eyes are reduced to small ember cores with the red halo removed.
- Mean luminance goes from 0.038 to 0.124.

Plain red and black roses are unchanged, so bloody vs plain stays distinct: the liquid sheets and pools appear only on the bloody versions.

## Animation (30fps)
| Symbol | melt | idle (loop) | win |
|---|---|---|---|
| white/red/black rose | 81 | 180 | – |
| bleeding_heart | 81 | 180 | 90 |

## QA (`melt_qa.py` on the v6 finished frames, `_qa/qa6_*.txt`)
| | melt0 vs plain | melt last vs idle0 | melt pop (max, frame) | idle pop (cyclic) | idle seam (median step) | win |
|---|---|---|---|---|---|---|
| white | 0 | 0 | 1.05 @15 | 1.26 | 0.0096 (0.013) | – |
| red | 0 | 0 | 2.07 @8* | 1.25 | 0.0136 (0.0143) | – |
| black | 0 | 0 | 1.63 @76* | 1.28 | 0.0141 (0.0174) | – |
| heart | 0 | 0 | 1.21 @12 | 1.35 @85* | 0.0098 (0.0085) | win0==idle0, end→rest 0.0172, pop 1.39 @44* |

\* These ratios are over 1.3:
- **Red @8 is the melt onset.** The surrounding steps are below 0.01 grey levels (0–255 scale), so the ratio is quantisation noise and not a visible jump. A softer liquid weight ramp was tested and only reached 1.85.
- **Black @76 is settling.** It is the same as v5 (1.61).
- **Heart idle @85 is a droplet detaching:** 0.052 → 0.067 → 0.047 grey levels. v5 was 1.28 at the same frame; the relight scales the step.
- **Heart win @44 is the pulse peak.** v5 was 1.37.

`alpha_never_below_plain` = -64. This is the same as v5: it comes from the anti-aliased liquid edge over the outline and is not visible on dark cells.

## Fonts (SIL OFL 1.1)
- Cinzel: logo, "RIZZIN GAMES", plaques, UI.
- Cinzel Decorative Black: logo initials and the 10/J/Q/K/A letters.

## Copy
- Bonus Buy: "3 bonuses · from 100x".
- Ante: "Bloodlust 3x · Super 20x".

## Still weak
- The base paintings are still AI-derived under the paint-over.
- The left angel is softer and darker than the right.
- The logo is smaller than in v1, so the cells can stay at 172px.
- The Reaper's eyes still read slightly ember-like.
- Bloody red vs plain red is clear in the liquid and pool, but the rose heads are similar.
- The four QA ratios above are over 1.3.
