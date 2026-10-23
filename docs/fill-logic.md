# Fill logic — the criteria and why each one exists

This is the most important page in the repo. Every rule below is there because
of something we saw go wrong (or nearly go wrong) on our Haas UMC-500. If you
adapt this to your machine, the *reasons* matter more than our numbers.

The Home Assistant config that implements this is in
[`config/home-assistant/`](../config/home-assistant/); the valve watchdog is in
[`config/esphome/`](../config/esphome/). Safety and failure modes are covered
in more depth in [safety.md](safety.md).

**Contents**

1. [The problem: a level that won't sit still](#1-the-problem-a-level-that-wont-sit-still)
2. [Setpoints and the drain-back envelope](#2-setpoints-and-the-drain-back-envelope)
3. [The permissive, criterion by criterion](#3-the-permissive-criterion-by-criterion)
4. [Fill budget](#4-fill-budget)
5. [The metered fill](#5-the-metered-fill)
6. [Overshoot](#6-overshoot)
7. [Alerts](#7-alerts)
8. [Concentrate dosing — designed, not automated](#8-concentrate-dosing--designed-not-automated)
9. [How we got here](#9-how-we-got-here)

---

## 1. The problem: a level that won't sit still

Our level sensor is a radar (Keyence FR-S01) looking down at the coolant tank,
reporting millimetres from the tank bottom. Before we automated anything, we
expected "level" to be a slow number that falls as coolant evaporates. It
isn't. Three things move it:

- **The conveyor wash sawtooth.** While the machine runs, the chip conveyor's
  filter disc slowly clogs with chips and coolant backs up *inside the machine*.
  Every few minutes the conveyor wash pump fires (about 16 psi for about a
  minute, every 4–5 min on our programs), clears the disc, and the backed-up
  coolant rushes back — the tank level jumps 15–20 mm, then sags until the next
  wash. So the *lowest* reading is exactly when the most coolant is held up in
  the machine and about to come back.
- **Drain-back.** When the machine stops, coolant sitting in the enclosure, chip
  pan, conveyor and sumps drains back into the tank. There's a lower "running"
  level and a higher "stopped" level.
- **Raw spikes.** While running, the radar sometimes reads 25–40 mm above the
  real surface for about 30 s, occasionally reporting "no valid echo", when the
  wash return lands near the beam (churned or foamy surface). We've seen raw
  readings up to ~158 mm on a surface sitting around 120 mm.

On top of that, coolant actually leaves at roughly **0.7–0.9 gal/h**
(1.2–1.6 mm/h on our tank) while running — mostly evaporation, much of it
through the mist collector.

So any rule written as "fill when the level is below X" will fill at the wrong
time. Everything below is about deciding *when the level number means what it
says*.

Our tank, for reference:

| | Value |
|---|---|
| Volume per mm | **≈ 0.55 gal/mm** (1.81 mm/gal), measured by metering 5.15 gal into a settled tank (±10%) |
| What we call "full" (100%) | 153 mm (≈ 84 gal) |
| Tank lip (overflow) | ≈ 197 mm (7¾ in) above the bottom |
| System volume (tank + machine) | ≈ 70 gal, estimated from how much a metered fill diluted the coolant |

## 2. Setpoints and the drain-back envelope

Fills are sized in the **running frame**: both setpoints are compared against
the level *while the machine is running*. Today:

| Setpoint | Value | Where it lives |
|---|---|---|
| Fill trigger (1 h mean below this) | **109 mm** | `input_number.coolant_fill_trigger` |
| Fill target | **115 mm** | `input_number.coolant_fill_target` |
| Fill ceiling (never fill above this) | **123 mm** | hard-coded in the permissive template |

**The envelope that matters is fill-then-stop.** The scenario that worries us
most: a fill finishes, then the machine stops, and everything held up inside it
drains back into a tank we just topped up. No valve can help after the fact, so
the setpoints have to leave room for it:

> target (115 mm) + worst-case drain-back (30 mm) = **145 mm idle**, still
> ≈ 52 mm (≈ 29 gal) below the 197 mm lip.

The ceiling is the same idea from the other side: 153 mm "full" − 30 mm
worst-case holdup = **123 mm**. Whatever the trigger is set to, we never fill
above that.

**How we arrived at 30 mm.** The design started at 25 mm (the biggest
drain-back seen in the first days of data). Then we watched a program run for
2 hours without the conveyor washing and saw ≈ 23–30 mm held up (see the
conveyor-wash criterion below), so the design worst case went to 30 mm. What
we've measured since:

| When | Drain-back |
|---|---|
| Early runs | 11 mm, ~18 mm, 25 mm worst case |
| Monday after the first unattended weekend | ≈ **6 mm** (idle level settled rock-steady) |
| Fill at 23:56, machine stopped at 00:30 — the exact scenario above, for real | ≈ **10 mm**, then a slow creep of another ~2 mm over 4 h as sumps kept draining. Highest 5-min average 127.2 mm, ≈ 72 mm below the lip |

Drain-back clearly depends on what the machine was doing. We keep 30 mm as the
design figure.

**Setpoint history**, because the numbers moved for reasons:

| Date | Trigger / target | Why |
|---|---|---|
| 2026-10-14 | 79 / 95 mm | First design, conservative 20 mm running offset |
| 2026-10-16 | 99 / 105 mm | 79 mm looked "alarmingly low" by eye; pump intake heights unknown. (The Haas's own float read 64% at the same moment our radar read 65% of 153 mm — two independent sensors agreeing.) |
| 2026-10-18 | **109 / 115 mm** | The Haas's own low-coolant warning flashed with our 1 h mean around 100 mm, so the machine's threshold sits about there |

A narrow band (6 mm ≈ 3.3 gal per fill) means small, frequent top-ups, far from
the lip. That's deliberate.

## 3. The permissive, criterion by criterion

A fill is allowed only when **all** of these are true at once. In Home
Assistant this is one template binary sensor,
`binary_sensor.fill_would_trigger_observe_only` (displayed as *Water fill
permitted*; the ID kept its name from when it was observe-only). The automatic
fill fires when it has been on for 2 minutes, and re-checks every 15 minutes.

### 3.1 Fill on the 1-hour mean, not the raw level

**Rule:** compare `sensor.coolant_level_1h_mean` — a time-weighted rolling
1-hour average of the level (`average_step`, 5,000-sample buffer; the level
reports ~1,600 times an hour) — against the trigger.

**Failure it prevents:** filling on a sawtooth trough or a raw spike. The
1-hour window spans a dozen or so wash cycles, so the sawtooth averages out,
and a 30-second spike barely moves it.

**The cost:** it lags by roughly 30 minutes. That's fine for deciding to fill
(nothing about consumption is fast), but it means any fill it triggers needs a
lockout — which the "not rising" rule below provides. It also turned out to be
far too slow for overflow alarms; see [Alerts](#7-alerts).

### 3.2 Machine running for at least 1 hour

**Rule:** `binary_sensor.umc_500_active` has been continuously on for ≥ 1 h.
Run state comes from current on one phase of the machine's supply (Shelly Pro
3EM): on above 5 A for 20 s, off below 3 A for 90 s.

**Failures it prevents:**
- Filling at idle, when the tank is holding drain-back and reads high-and-steady
  — or worse, sizing a fill to an idle level and then starting the machine.
- Filling in the first hour after a start, when coolant is still being pulled
  up into the machine and the 1 h mean is a blend of idle and running.

This collapses everything into one frame: the level is only meaningful with
coolant circulating, and the setpoints are running-frame numbers. Idle never
needs a fill.

**Known limitation (accepted):** with manual part loading, gaps over 90 s drop
"active", so "running ≥ 1 h" may never be met and no fill happens. That fails
safe — the tank drifts low and the low-level alert covers it. On automated runs
(we've seen it hold solidly through an 18-hour run) it's reliable.

### 3.3 Conveyor wash seen in the last 10 minutes

**Rule:** the conveyor filter's upstream pressure has gone above 5 psi (wash
pump running) at some point in the last 10 minutes
(`sensor.conveyor_wash_time_last_10_min` > 0).

**Failure it prevents:** filling a tank that reads low only because coolant is
trapped in the machine. This one we found the hard way, and it's the rule
we're most glad we have.

On 2026-10-14 a program ran for about 2 hours with flood coolant on but **no
conveyor wash at all** (the conveyor's upstream pressure sat flat at zero).
With the return choked, the 1 h mean slid from ~146 to ~123 mm (raw troughs
~113) — about **23–30 mm, ≈ 13–16 gal, held up in the machine**. When washing
resumed, the level recovered toward 140. It happened again the next night with
the same fingerprint.

Without this rule, our permissive would have allowed a fill (running > 1 h,
mean falling, not rising) right before ~15 gal came back. It's also why the
fill budget exists (section 4): that run looked like ~15 gal "consumed" in 2 h
against ~1 gal of real consumption.

**Root cause was in the CAM output, not the machine.** The no-wash program had
been posted from a selection that skipped the manual-NC operations at the top
of the job — start chip conveyor, start mist collector, set job info — so the
NC code simply never turned the conveyor on. Our programs have probably run
like this more often than we knew. The real fix is making the post-processor
always emit those commands (planned); this rule is the guard for when it
doesn't happen.

**Why 10 minutes:** the normal wash cadence on our programs is every 3–5 min,
so 10 minutes is 2–3 missed washes.

**Does it starve the tank?** We worried about it, then realised it's mostly
self-correcting: fills are blocked exactly while the level reads *falsely* low
(coolant held up, not consumed), and the coolant comes back when washing
resumes. Genuine starvation during long no-wash programs is caught by the
low-level alert.

**It also blocks concentrate dosing.** During the second no-wash run, Brix (the
concentration reading) had been climbing steadily and then went flat for the
whole no-wash period while the level kept falling. Our theory: most
evaporation happens *in the machine* (spray over hot tools and chips, mist,
mist-collector airflow), and the tank only gets richer when that coolant drains
back. We predicted Brix would step up when washing resumed — and when it did,
Brix spiked 7.10 → 7.22 at the same moment the level jumped. So during a
blocked return, the tank's Brix doesn't represent the system either.

**A related hazard it doesn't cover:** a long, chip-heavy program with no
conveyor can plug the filter disc and overflow the *machine enclosure* onto the
floor, with the tank reading low the whole time. That has happened to us before
this project. See [safety.md](safety.md#machine-side-overflow-blocked-return).

### 3.4 Not rising

**Rule:** `binary_sensor.coolant_level_rising` is off — a Trend helper on the
1 h mean that turns on above +0.5 mm/h over a 30-minute window.

**Failures it prevents:**
- Filling while drain-back or held-up coolant is still arriving.
- Filling on top of a chip barrel being poured back (see
  [results.md](results.md#chip-barrel-returns)).
- **Double fills.** Because the 1 h mean lags, it keeps rising for a while
  after every fill. The rising flag doubles as the post-fill lockout.

### 3.5 Below the ceiling

**Rule:** 1 h mean < 123 mm, regardless of the trigger setting.

**Failure it prevents:** someone (us) raising the trigger setpoint without
thinking about drain-back. The ceiling is the envelope from section 2 written
directly into the logic.

### 3.6 Sensor health inputs — and the fail-safe gap we found

**Rule:** both Keyence FD-H units report healthy on their error outputs
(WLD inputs I3 and I4).

**Failure it prevents:** acting on a reading the sensor itself knows is bad.
One FD-H "Error" output covers settings and memory errors, the refractometer's
dry/low-liquid detection, and the **radar's stability alarm** — the only way a
knocked or blinded radar becomes visible to us, because a stability alarm does
not move the analog level signal.

This matters because of a specific radar failure: if a knock swings the beam
off the surface, the radar may pick up a bounce off a wall or pipe that reads
*long* — so the level reads *low* — so we'd fill. That's the dangerous
direction. (A radar that sees nothing at all outputs 21.5 mA, which clips our
input and reads as very high. That's safe for filling, but it also means our
"> 20.5 mA = fault" check can never fire — so radar health *has* to come from
I4.)

We proved the health chain works by unplugging the radar: I4 dropped within
seconds and recovered when it was reconnected (done twice).

**The gap (open):** the FD-H error outputs are configured **N.C.**, so
"healthy" = output conducting = 0 V at the WLD input. We later learned the WLD's
inputs read **on with no voltage applied** (see
[lessons.md](lessons.md#the-wld-521-inputs-need-voltage-applied)). Result: a
real FD-H error reads correctly, but **a cut wire or an unpowered FD-H also
reads 0 V = "healthy"**. Not fail-safe. The planned fix is to switch both
outputs to **N.O.** and invert the meaning in Home Assistant (on = fault), then
re-prove it with the radar-unplug test. Until then, I3/I4 protect against
faults the FD-H detects, not against wiring faults.

### 3.7 High-level float (I5) — wired, not yet in the permissive

A stainless float switch (AutomationDirect FLS-VL-600) is wired to WLD input I5
and proven in both directions: **off = clear, on = high level**, and a cut
cable, unplugged connector or lost 5 V rail all read **on** (fills blocked).
It isn't mounted on the tank yet, so it isn't in the permissive. It will be
added after mounting, with the trip height chosen relative to the 153 mm
"full" level and the lip.

Its one undetectable failure is a **stuck-closed** switch (jammed by sludge, or
mounted too high) — it would read "clear" while the tank rises. Planned
mitigations: a radar cross-check (level above the float's height while I5 still
reads clear → "float may be stuck") and a 30-day reminder if I5 hasn't changed
state.

## 4. Fill budget

Even with every criterion above, the level sensor could still be wrong in a way
none of them catch — a constant offset, a frozen value, a mis-set *Bottom
distance* on the radar. The fill budget is the guard that doesn't trust the
level sensor at all.

**Rules (in the automatic fill automation):**
- At least **2 hours** since the fill script last ran.
- Less than **36 gal** of water added in the last 24 hours (from the water
  meter's total; nominal budget 40 gal, so a 4-gal-ish fill can't push past it).

A blocked fill sends a phone notification instead of filling.

**Why:** physics caps how fast coolant can leave. Our fastest observed
consumption is about 32 gal/day. If the logic asks for more water than that,
the *measurement* is wrong, not the tank. The budget limits how much a lying
level sensor can overfill before a person looks. On the no-wash run in section
3.3, the level made it look like ~15 gal had gone in 2 hours — the budget alone
would have stopped a runaway.

**The long-term version** (not built) scales with use instead of a fixed 24 h
cap: water added over a window may not exceed (highest observed consumption
rate × hours run) + margin. Large legitimate deficits — after a tank clean-out
or a long idle — are human-initiated fills that bypass the budget on purpose,
never automatic ones.

## 5. The metered fill

`script.coolant_metered_water_fill`, in order:

1. **Compute the volume once:** (target − 1 h mean) × 0.55 gal/mm, **capped at
   5 gal (18.9 L)**. Skip if under 1 L.
2. Turn the shop water pump on; wait 5 s for pressure.
3. Open the water valve (WLD relay 2).
4. **No-flow abort:** if the meter hasn't counted 0.1 L after 20 s, close the
   valve, notify, stop.
5. Wait until the metered volume is delivered **or a timeout** of 1.5 × the
   expected time + 30 s.
6. Close the valve. Outside staffed hours, turn the pump back off.
7. Notify the phone at start and end (planned vs delivered).

**Compute once, deliver it.** We size the fill at the moment of the trigger and
deliver that volume, rather than "fill until the level reaches X". A level-based
stop would be chasing a sawtooth and a lagging mean. And because the volume was
sized in the running frame, a machine stopping mid-fill doesn't matter — the
envelope in section 2 already allows for it.

**Metered by volume, never timed.** Supply flow isn't constant (the
concentrate line in particular surges when its valve opens), so time is a poor
proxy for volume.

**Why the cap went from 10 gal to 5.** The MiniPLC has a hardware-independent
valve watchdog that forces the water valve closed after **6 minutes** no matter
what Home Assistant is doing (section 7 and [safety.md](safety.md)). We had
assumed 4.8 L/min. Measured flow turned out to be ~4.2–4.4 L/min, and a 6-gal
fill ran **5 min 28 s — only 32 s inside the watchdog**. A cap that close to the
watchdog means a slightly slow supply turns every big fill into a watchdog
trip. At 5 gal a fill takes ~4.5 min, leaving ~1.5 min of margin. In normal
running a fill is ~3 gal and takes ~3 min.

> ⚠️ **Known gap:** the script still calculates its timeout from the old
> 4.8 L/min. At the 5 gal cap that's 18.9 ÷ 4.8 × 60 × 1.5 + 30 ≈ **384 s**,
> longer than the 360 s watchdog. If the meter under-reads on a full-cap fill,
> the watchdog — not the script — closes the valve (and sends a critical
> alert). That's still safe, but it's not the clean timeout we intended. Fix:
> base the timeout on the measured rate, or clamp it under the watchdog.

**Where this runs.** Today the fill script runs in **Home Assistant**, with the
**valve watchdog in ESPHome** on the MiniPLC as the backstop that works with
Home Assistant down. The original plan (and still the goal) was to move the
whole fill sequence into ESPHome, so it doesn't depend on Home Assistant at all.

## 6. Overshoot

Fills deliver about **6% more** than planned (first overnight fill: 3.47 gal
planned, 3.66 delivered). Two causes:
- The WLD module updates its flow total roughly every 10 s (~0.7 L at our flow
  rate), so the script sees the target late.
- The FD-H flow meter's 5 s response time adds a tail after the valve closes.

Harmless for water. It matters for concentrate, where doses are small
(~1.5 L) and the same lag could mean ~20% overshoot. The fix is anticipation —
close early by the expected overshoot, self-calibrated from logged fills — and
we deliberately haven't changed it during steady running.

## 7. Alerts

`automation.coolant_level_and_valve_alerts` — tiered since 2026-10-19:

| Alert | Signal | Level | Why |
|---|---|---|---|
| **Overflow risk** | 5-min average of the raw level > **145 mm** for 3 min | Critical (breaks through Do Not Disturb) | See below |
| **Valve watchdog tripped** | MiniPLC forced a valve closed | Critical | Something kept a valve open — someone needs to look |
| Above band | 1 h mean > **135 mm** for 5 min | Normal | Unusual but not dangerous (e.g. a barrel return on top of drain-back) |
| Low | 1 h mean < **80 mm** for 5 min, repeats every 30 min | Normal | Fills may be blocked — go and look why |
| Fill blocked by budget | Section 4 | Normal | Possible lying level sensor or leak |

**Why the 1 h mean was too slow for overflow.** The first version raised a
critical alert when the 1 h mean passed 125 mm. On 2026-10-19 it fired about an
**hour after** a real (harmless) rise. For an actual overflow, an hour is
useless. So overflow now watches a **5-minute average of the raw level** — long
enough to ride over the 25–40 mm, ~30 s raw spikes, short enough to flag a real
rise within about 8 minutes. 145 mm leaves ≈ 52 mm (≈ 29 gal) below the lip to
react.

**Why "above band" moved from 125 to 135 mm.** With the 109/115 band, an
ordinary end-of-run stop parks the tank at ~120–131 mm after drain-back. The
125 mm note was arriving in the middle of the night for a normal stop. 135 keeps
it for genuinely unusual levels.

## 8. Concentrate dosing — designed, not automated

Concentrate is **not** dosed automatically yet. The design is written down and
an observe-only indicator (`binary_sensor.concentrate_dose_indicated_observe_only`)
runs on the dashboard; the first doses will be manual, following this logic,
until it's proven.

**Why it's harder than water.** An over-dose can't be undone. Concentrate only
leaves by carry-out on chips and parts, which is slow (we measure about
1 gal/day equivalent), so one over-dose lingers for weeks. Water can always be
added; concentrate can't be taken out. So dosing approaches the target **from
below**.

**The floor: 4.9 Brix (≈ 11.3%) at the trough.** The leanest moment is just
after a water fill. Setpoints are anchored in Brix because that's what the
refractometer measures; percent is display-only (Brix × 2.3, our coolant
maker's refractometer factor), so changing the factor never touches the logic.

**When to dose: at each water fill.** Just before a fill, Brix is at its
sawtooth peak, at the same level every time — a repeatable checkpoint — and the
incoming water helps mix the dose.

**Decision:** predict this fill's trough (peak × V ÷ (V + fill volume)). If it
would fall below the floor, dose with this fill, aiming the trough at ≈ 12%.

**Sizing:** mass balance ≈ (target % − current %) × system volume (~70 gal),
then **deliberately under-dose** (~50–70% of computed) with a per-dose cap
(~0.5 gal). Converge from below; an under-dose just means the next dose comes
sooner.

**Permissives (all):**
- The water-fill permissives are green (running ≥ 1 h, conveyor washing, etc.).
- **Brix settled** — 15-min standard deviation < 0.03 Brix — so we're not
  reading mid-slug from drain-back or a barrel return.
- Predicted trough below the floor.
- Lockout: ≥ 4–6 h (or ≥ 2 water fills) since the last dose.
- **No recent unlogged addition.** A chip-barrel return is itself a concentrate
  dose — one return delivered ≈ 1.3 gal of concentrate.
- Daily concentrate cap (≈ 1 gal/day).
- Concentrate pump available and the valve watchdog clear.

**Why idle Brix can't be trusted.** One night the machine sat idle for six
hours and the Brix-derived concentration climbed 16.0 → 16.7%, then fell back
within two hours of running. The only inflow was ~1 gal of slow drain-back,
which would have had to be ~45 points richer than the tank to cause that. It's
stratification around the refractometer with no circulation — a measurement
artefact. Hence "running ≥ 1 h with the conveyor washing" before Brix is
trusted, and for manual doses: read Brix during steady running, never off an
idle tank.

**A caution about Brix in general.** On used coolant, a refractometer reads
everything dissolved or suspended — tramp oil, fines, hard-water salts — so a
dirty sump reads "too strong". A loop that trusts it blindly would add water to
a sump that's contaminated rather than rich. We validated the refractometer
against a handheld (identical readings on a carefully mixed batch) and keep
comparing, but this is why dosing stays manual for now.

## 9. How we got here

The decision history, where it explains the design:

- **Automate the spreadsheet we already used.** For years we topped up by tape
  measure, a handheld refractometer and a spreadsheet. The first design
  automated exactly that: measure, compute water and concentrate, fill.
- **Phase 1 was manual-trigger only** — a button in Home Assistant, watched by a
  person. The cheap safety layers (stop at metered volume, max fill time, valves
  closed on boot) went in from the start anyway, for the moment the watcher
  walks away.
- **Our first idea for where the "stop" lives was wrong.** We planned to put
  the fill target in the WLD module's own "irrigation" function so a lost bus
  couldn't leave a valve open. Reading the module's firmware source showed that
  function doesn't exist (the README describes it; the code doesn't contain it).
  So the logic moved to the controller, and the valve watchdog was added to
  cover a controller or Home Assistant failure.
- **First data changed everything.** The sawtooth, drain-back and holdup
  (section 1) all came from the first nights of watching the radar. The
  permissive criteria were written in response, then **red-teamed** for the
  two outcomes that matter — running dry and overflow. The rule was: no
  unattended filling until every failure mode was closed or consciously
  accepted ([safety.md](safety.md)).
- **First metered fill (supervised), 2026-10-16.** Planned 11.4 L, delivered
  11.6 L. The concentration dropped by an amount implying ~70 gal in the system
  — an independent cross-check of our gal/mm figure.
- **Why automatic fills beat approve-from-phone for unattended weekends.** We
  considered having the system ask permission by phone before each fill. Over a
  weekend that's 15–25 prompts at all hours; asleep or in Do Not Disturb, Brad
  would miss some, and at the fast evaporation rate one missed fill could put
  the sawtooth troughs dangerously low. Automatic fills fail more rarely, and
  each failure is bounded (≤ 5 gal per fill, pump off after hours, budget,
  watchdog). So we chose automatic, with notifications — consciously passing the
  red-team gate with the residual risks written down, not pretending they were
  closed.
- **It worked.** The first unattended weekend ran fills of ~3 min each, the
  watchdog never tripped and the 1 h mean held in the band. Since then:
  setpoints raised (section 2), fill cap cut (section 5), alerts tiered
  (section 7).
