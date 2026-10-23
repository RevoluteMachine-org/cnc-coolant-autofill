# Safety — failure modes and what catches them

This system opens valves that put water (and eventually concentrate) into a
running machine, unattended, overnight. Before we let it do that, we
red-teamed it: for each way it could break, what happens, and what stops it.
This page is that exercise, kept current.

Two outcomes matter:

- **Running dry** — the machine cuts without coolant.
- **Overflow** — worse. Coolant on the floor, and potentially a lot of it.

**The gate we set ourselves:** no unattended filling until every row below was
*closed* or *accepted with a reason*. On 2026-10-16 we passed that gate
**consciously, not by satisfying it** — we turned on automatic fills for a
weekend with the residual risks written down (see
[fill-logic.md](fill-logic.md#9-how-we-got-here)). This page says plainly which
rows are still open.

Status key: **Mitigated** (something real covers it) · **Partial** ·
**Open** (known, not yet covered) · **Accepted** (we decided to live with it).

## Overflow

| Failure | How it overfills | What catches it | Status |
|---|---|---|---|
| **Valve stuck open** (debris in the solenoid, welded relay or interposer contact) | Continuous flow with no command | Supply pumps run only while the shop is staffed or during a fill (smart plugs), so a stuck valve is bounded by the small pressure tank (water ~5–8 gal, concentrate ~1–2 gal). An after-hours pump limit turns a pump off 30 min after any after-hours turn-on. | **Mitigated** — depends on Home Assistant running. Future: fail-closed motorized ball valves downstream of the pressure tanks |
| **MiniPLC or Home Assistant dies mid-fill** | Relay left on | **Valve watchdog in ESPHome on the MiniPLC** — forces the water valve off after 6 min, concentrate after 3 min, and closes both on boot. Runs without Home Assistant. Tested: forced off at 6 min 5 s. Critical alert if it ever trips. | **Mitigated.** Gap: if Modbus to the WLD is lost, the watchdog's "off" can't land — the WLD has no comm-loss failsafe of its own |
| **Flow meter under-reads** (fouling, wrong span, false zero) | Delivers more than it counts | Script timeout (1.5 × expected time) and no-flow abort at 20 s, with notification | **Mitigated** (but see the timeout note in [fill-logic.md](fill-logic.md#5-the-metered-fill)) |
| **Level reads falsely low** (radar knocked or seeing a bounce, *Bottom distance* reset to its default, analog frozen) | Repeated fills | Fill budget (≥ 2 h between fills, < 36 gal/24 h); critical overflow alert; FD-H health input (stability alarm) | **Partial** — the post-fill level-rise check (below) is the real guard against a constant offset and isn't built |
| **Holdup larger than designed** (conveyor wash failed or not programmed, heavy through-spindle use) | Tank reads low while coolant is up in the machine, then it all returns | Conveyor-wash-in-last-10-min rule; ceiling; not-rising rule; design holdup raised to 30 mm after seeing ~23–30 mm | **Mitigated** |
| **Chip barrel poured back right after a fill** | 5–10 gal on top | The band leaves room; not-rising rule blocks the next fill | **Mitigated** by design |
| **Concentrate valve stuck** | As above, plus a concentration spike | Same as the water valve; 3-min watchdog | **Mitigated** (same fixes) |
| **Float stuck closed** (jammed by chips or sludge, or mounted too high) | Float reads "clear" while the tank rises | Planned: radar cross-check, 30-day "hasn't changed state" reminder | **Open** — and the float isn't in the permissive yet anyway |

### Machine-side overflow (blocked return)

This one is **independent of the fill system** and existed before it. A long
program making fine chips with the conveyor not running: the conveyor's filter
disc plugs, flood coolant keeps being pumped in, and the machine enclosure
fills like a bathtub and overtops onto the floor. The tank reads *low* the whole
time. **This has happened to us before.**

- **Prevention is the main defence.** Most of these runs are unattended, so an
  alert reaches nobody who can press the conveyor button. The fix is making the
  post-processor always start the conveyor (and mist collector) — planned.
- **Proposed alert, buildable with signals we already have:** machine active +
  flood pressure up + no conveyor-wash pulse for 15–20 min (optionally the
  1 h mean sloping steadily down) → phone notification and dashboard warning.
  Our 2-hour no-wash run would have alerted about 15 min in. **Open** — useful
  for staffed runs and conveyor faults.
- Risk scales with chip volume: a light finishing program without the conveyor
  is harmless; heavy roughing is the dangerous case.

## Running dry

| Failure | How it starves | What catches it | Status |
|---|---|---|---|
| **Permissive stuck blocking** (false health trip, a criterion never met) | No fills, silently | Repeating low-level alert below 80 mm, independent of the permissive | **Partial** |
| **Level reads falsely high** (foam, chips in the beam, *Bottom distance* too large, frozen value) | Never fills | ⚠️ The low-level alert is blind here — it uses the same radar. Needs an independent "no fill in X hours of running" watchdog. Brix rising steadily with no water fills is a second tell | **Open** |
| **Supply empty or failed** (tank, pump, plug, clogged strainer) | Fill attempted, no flow | No-flow abort at 20 s plus notification; no endless retry | **Mitigated** |
| **Leak** (hose, tank seam) | Loss outruns capped fills | Planned leak alarm (level falling while idle); fills more frequent than usual | **Open** |
| **Home Assistant or the MiniPLC down** | No fills — and no alerts either | Planned: a heartbeat checked from *outside* Home Assistant | **Open** |

We chose **not** to fit a floor leak sensor: an overflow runs away from a
machine along one unpredictable path, so there's no good place to put one. A
float at the tank lip catches the same event earlier, where it starts.

## The safety ladder

Each layer covers failures the others don't. Where each stands today:

1. **Control logic** — stop at metered volume; timeout; no-flow abort; fill
   budget; valves closed on controller boot. ✅ Built (fill script in Home
   Assistant, watchdog and boot-close in ESPHome).
2. **Valve watchdog on the controller** — independent of Home Assistant.
   ✅ Built and tested.
3. **Supply pumps on only during demand** — caps a stuck valve at the pressure
   tank's drawdown, and fails safe: with Home Assistant down, fills simply
   don't happen. ✅ Built (staffed hours + 30-min after-hours limit).
4. **Hardware high-level float** on WLD I5. 🟡 Wired and proven, not mounted,
   not in the permissive. It's a *software* cutout: on the WLD's current
   firmware an input can't force a Modbus-controlled relay off, so the
   controller has to act on it.
5. **A second normally-closed valve per supply run**, driven from a different
   output — the only full cover for a valve stuck *mechanically* open.
   ❌ Not built; planned as fail-closed motorized ball valves for our new
   building.

Both solenoid valves are **normally closed**, so losing power closes them.

## What's accepted

These are known and we've decided to live with them, with the reason:

- **Run-state latch with manual loading.** "Running ≥ 1 h" may never be met
  when parts are loaded by hand with long gaps. Fails safe (no fill → low alert).
- **A radar fault reads "high", not "fault".** The radar's no-detection output
  (21.5 mA) clips our analog input, so it looks like a very full tank. Safe for
  filling (it blocks fills), but radar health must come from the FD-H error
  input — which the fill logic checks.
- **For the first unattended weekend**, these residual risks were explicitly
  accepted: no per-fill level-rise check; no float; no external heartbeat; and
  the ~3-minute window per fill where a mid-fill Home Assistant failure is
  bounded only by the 6-minute watchdog (≈ 8 gal).

## Known gaps (as of 2026-10-23)

Plainly, what isn't done:

- **Post-fill level-rise check** — not built (see below).
- **Float** — wired and proven, not mounted, not in the permissive.
- **FD-H health inputs aren't fail-safe** — a cut wire or unpowered FD-H reads
  "healthy". Fix planned: switch to N.O.
- **No "no fill in X hours" watchdog** for a level stuck high.
- **No heartbeat from outside Home Assistant.**
- **The WLD module has no comm-loss failsafe** — if the bus drops with a relay
  on, the relay stays on until something else intervenes.
- **The fill logic runs in Home Assistant**, not on the controller. The
  watchdog bounds a mid-fill failure; moving the fill into ESPHome is planned.
- **The fill timeout at the 5 gal cap is longer than the watchdog** (384 s vs
  360 s). Safe, but the watchdog rather than the script ends that case.
- **Valves are not closed when an over-the-air firmware update starts** — only
  on boot. A fill running during an update would stay open until the
  controller restarts or the watchdog trips.
- **Pump limits depend on Home Assistant.** If Home Assistant is down after
  hours with a pump on, nothing turns it off.
- **One fuse for the whole cabinet.** A single fault blows it and the cabinet
  goes dark — monitoring, alerts and the watchdog included (valves close, since
  they're normally closed). Future builds fuse each valve separately.
- **Uncommanded-flow alarm** (flow counted while both valves are commanded
  closed → alarm and lock the pump) — designed, not built.
- **"COOLANT FILL STOP" button** — designed, not built (below).

## Planned guardrails

- **Physical "COOLANT FILL STOP" button.** A red latching mushroom-head stop
  (push to stop, twist to release) on the cabinet door or near the tank, so
  *anyone* in the shop can stop a fill that won't stop — no app, no knowledge
  of the system. Its **N.C. contact breaks the +24 V feeding the valve coils**
  (after everything software controls), so both normally-closed valves close
  even if a relay contact has welded or a module has locked up. Its **N.O.
  contact goes to a spare controller input** so Home Assistant knows: abort the
  fill, pumps off, notify. Kept **separate from the machine's E-stop chain** —
  it stops the coolant system, not the machine. It can't close a valve jammed
  open mechanically; the pump limits cover that. Today the only fast answer is
  unplugging the whole cabinet, which also kills monitoring.
- **Post-fill level-rise check.** The counterpart of the no-flow abort: the
  valve opened and flow was metered, but the level didn't rise. Expected rise =
  metered volume ÷ 0.55 gal/mm (4 gal ≈ 7 mm). Compare the 1 h mean about an
  hour after the fill (it lags) with the pre-fill mean, adjusted for that
  hour's normal consumption; a shortfall beyond a generous tolerance → latch
  out and alert. This is the real guard against a radar with a constant offset.
- **Coolant ledger.** A running mass balance: level change × gal/mm vs metered
  water + metered concentrate − estimated evaporation and carry-out. The
  residual is diagnostic — persistently negative = leak, meter reading high, or
  radar drifting low; positive = unlogged additions (chip-barrel returns, hand
  fills); a slow trend = sensor drift, caught long before it causes a bad fill.
- **Scaled fill budget** — (highest observed consumption rate × hours run) +
  margin, instead of a fixed 24 h cap.
- **Heartbeat** from outside Home Assistant.
