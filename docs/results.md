# Results — what the data showed

From about ten days of logged data on one Haas UMC-500, October 2026. These are
observations from our machine, our programs and our coolant — useful as a
sense of scale, not as constants for yours.

## Consumption

| Period | Rate |
|---|---|
| First steady evening (7-hour straight-line fit, ±0.2 mm) | 1.19 mm/h ≈ **0.65 gal/h** (~16 gal per 24 h of running) |
| Rougher running | ~1.5 mm/h |
| An overnight run with the mist collector on all night | 2.4 mm/h |
| An 18-hour steady run | 1.3–1.6 mm/h ≈ **0.7–0.9 gal/h** |
| Fastest seen (used for the fill budget) | ~32 gal/day |

We wrote down an 18-hour prediction (1 h mean would fall to 94–100 mm) before
relying on the rate. It landed at ~98 mm.

The mist collector looks like a major driver: the night it ran continuously,
consumption was markedly faster.

## Tank gallons per mm

Metering 5.15 gal into a settled, machine-off tank raised it 142.5 → 151.8 mm:
**1.81 mm/gal, ≈ 0.55 gal/mm (±10%)**, given the radar's 1 mm steps. Our old
spreadsheet assumed a plain rectangle and was ~7% off. A metered fill later
diluted the coolant by an amount implying ~70 gal in the whole system (tank
plus machine), an independent cross-check.

## Drain-back

When the machine stops, coolant held in the enclosure, chip pan, conveyor and
sumps drains back:

| Event | Rise |
|---|---|
| Early runs | 11 mm, ~18 mm, 25 mm worst case |
| Monday after the first unattended weekend | ~6 mm |
| Fill at 23:56, stop at 00:30 (the fill-then-stop case) | ~10 mm, then ~2 mm more creeping in over 4 hours |

It depends heavily on what the machine was doing. We design for 30 mm.

## Holdup when the conveyor doesn't wash

Two runs with flood coolant but no conveyor wash: the 1 h mean slid ~23–30 mm
(≈ 13–16 gal held up in the machine) and recovered when washing resumed.
Normal wash cadence on our programs is every 3–5 min, each wash lifting the
level 15–20 mm. Details in
[fill-logic.md](fill-logic.md#33-conveyor-wash-seen-in-the-last-10-minutes).

## Carry-out

Comparing Brix at the same pre-fill level (so the same volume) over successive
fills:

- Pre-fill concentration peaks stepped down ~0.4–0.8 points/day over the first
  weekend.
- On an 18-hour run: ~0.1 Brix per 4-hour fill cycle, roughly **1 gal of
  concentrate per day** carried out on chips and parts.

Concentrate only leaves this way, slowly — which is why an over-dose lingers
for weeks, and part of why our shop had been running rich (this tank read
15–19% during the project against an ~11% target, and is drifting down with
water-only fills).

## Chip-barrel returns

Chips dump into a barrel that drains through holes into a second one; that
coolant gets poured back into the tank.

| Return | Detected by | Added |
|---|---|---|
| #1 | Level jump at idle with no fill | ~7 gal; Brix step implied the barrel was ~19% concentration, ≈ **1.3 gal of concentrate** |
| #2 | **Fill timing** — the next fill came hours late (6 mm used in 11½ h where ~15 mm was expected) | ~5 gal; barely moved Brix, because that barrel had been carried out recently at tank strength |

On busy runs, returns are ~5–7 gal a day — about a third of consumption. A
barrel return is a concentrate dose, which is why the dosing design requires
"no recent unlogged addition".

## Shop humidity

With two temperature/humidity sensors (machining room vs the other side of the
shop), the machining room's dew point rose about 45.6 → 51 °F overnight while
the other room stayed flat — the evaporating coolant (~0.7–0.9 gal/h, much of
it through the mist collector) going into the room air. On a second night with
two machines running, the rise was bigger, but outdoor dew point had also risen,
and relative to outdoors the excess was about the same: no clear second-machine
signal yet. Coolant settles ~4 °F above shop air.

## Radar spikes

While running, raw radar readings sometimes jump 25–40 mm above the real
surface for ~30 s. Dissecting one event second by second: ~19 mm was a **real**
rise as a conveyor wash released held-up coolant; ~35 mm on top of that lasted
~30 s and included a moment of "no valid echo". That's consistent with a
churned or foamy surface where the return lands. Spike size varied with the
part being run. Absent at idle (the idle level is steady to ~1 mm).

The fill logic uses the 1 h mean and the overflow alarm a 5-min mean, so
neither is fooled. We plan an anti-foam test to separate foam from splash.

## Why idle Brix can't be trusted

Six hours idle: concentration "rose" 16.0 → 16.7% with only ~1 gal of
drain-back coming in, then fell back to 15.5–16.0% within two hours of running.
Stratification around the probe, not chemistry.

## Unattended weekends

First unattended weekend (from 2026-10-16): fills of ~3 min each, notifications
received, valve watchdog never tripped, 1 h mean held inside the band. Two
overnight fills on the first night came ~5 h 50 min apart (≈ 1.0 mm/h).

An 18-hour steady run later: three fills (~3 min each), watchdog never tripped,
conveyor washing every ~4 min.

The scenario we designed hardest for — a fill, then the machine stopping half
an hour later — happened for real on 2026-10-22. Drain-back was ~10 mm, the
highest 5-minute average was 127.2 mm, the overflow alert correctly stayed
silent, and the tank sat ~72 mm below the lip.
