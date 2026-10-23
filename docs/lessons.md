# Lessons — things that bit us

In roughly the order they'll bite you.

## The WLD-521 inputs need voltage applied

The HomeMaster WLD-521-R1's README describes its inputs as having a 100 kΩ
pull-down, "held low" when open, and its wiring diagram shows a passive contact
wired from an input to GND_ISO. On our hardware the opposite is true:

- **No voltage applied** (open, floating, or shorted to GND_ISO) → input reads
  **on**.
- **~3.5–5 V applied** (relative to GND_ISO) → input reads **off**.

A dry contact to GND_ISO can never switch it. We spent most of two days on this,
and we went wrong in instructive ways:

- Our "+5 V jumper" test used the module's **top-row logic 5 V**, not the
  **isolated 5 Vdc** at the bottom right, which is the one referenced to
  GND_ISO.
- The first retry had the float still plugged in, so its closed contact shorted
  the jumper to ground.
- Short test pulses were missed by Home Assistant's polling.
- Reading 0 V on a bare input and calling it "dead" — that's normal behaviour.

What finally settled it was benching **the spare module** with factory settings:
same behaviour, so no fault. **Lessons:** test a known-good unit first; one
variable at a time; write down the exact terminal; hold each test state ≥ 20 s.

Consequences: the float is wired from the isolated 5 Vdc through the contact to
the input (fail-safe for wiring faults), and our FD-H health inputs, wired as
N.C., are **not** fail-safe for a cut wire (fix: N.O.). See
[wiring.md](wiring.md#wld-inputs-they-need-voltage-applied).

## The WLD module has no "irrigation" logic and no comm-loss failsafe

We designed the fill-stop around the WLD's described irrigation/zone feature, so
a lost bus couldn't leave a valve open. Reading the firmware source showed the
feature isn't in the code — in either version. There's also no Modbus
comm-loss failsafe: if the bus drops with a relay on, it stays on. Read the
source, not the README, before you design safety around a feature.

## Firmware and config-tool versions must match

HomeMaster modules ship with whatever firmware was loaded at manufacture, often
a version behind the vendor's current one. The default config-tool link points
at the newest tool, which fails confusingly against older firmware (greyed-out
fields, blank status, `Unknown command: hello`). Try the legacy tool under "All
versions & firmware". Likewise, **the ESPHome package path must match each
module's actual firmware**, not the version in the docs — register maps differ
and aren't drop-in. Our AIO runs v0.2.0, our WLD v0.1.0, and each is imported
with its own package version.

## The WLD config tool relay-pair trap

The legacy WLD config tool writes **both relays'** Enabled/Inverted settings
together, from whatever its page is displaying — and the page has shown
checkboxes that didn't match the module. Editing one relay's card silently
disabled both. Rule: **after any relay-card edit, verify both relays from Home
Assistant.**

## ESPHome Modbus timing options are tied to version 2026.7+

`turnaround_time` and `send_wait_time` on the `modbus:` block don't exist
before ESPHome 2026.7.0 (they're a config error on our 2025.12.5). The same
release **raised the defaults** to 600 ms / 2000 ms — enough to starve modules
on a multi-module bus, with no error logged. **When upgrading past 2026.7.0,
add both options, set to the old defaults, in the same change.** (Also: the
Ethernet `clk_mode` option is deprecated as of 2026.1.)

## Read module addresses from the module

Every HomeMaster module we bought arrived at a different Modbus address from
the one its README states. Read it from the module's config tool.

## Fill overshoot: response time and polling

Fills run ~6% over: the WLD updates its flow total about every 10 s, and the
FD-H's 5 s response time adds a tail. Fine for water; for small concentrate
doses it could be ~20%. Plan on anticipation (close early by the expected
overshoot) before automating anything small.

## The RTD must be fully immersed

Our temperature probe swung 68–73 °F in lockstep with the level. It was coming
out of the coolant at each running drawdown and reading wet, cooled air. Fix the
tip ~50 mm off the bottom and immerse 60–90 mm of the sheath.

## Idle Brix can't be trusted

With no circulation, coolant stratifies around the refractometer. Overnight
idle, concentration "rose" from 16.0 to 16.7% with nothing added, then fell back
within two hours of running. Only trust Brix during steady running with the
conveyor washing.

## Chip-barrel returns are unlogged additions

Coolant drained off chips and poured back into the tank is both water *and*
concentrate. One return added ~7 gal including ~1.3 gal of concentrate; on busy
runs they're ~5–7 gal a day, about a third of consumption. They confuse
consumption estimates and dosing unless you account for them. The robust
detector turned out to be **fill timing**: when the level lasts longer than
consumption allows, something was added.

## Shunt resistor wattage

Not a failure — a margin note. Our ¼ W shunts are fine at normal signal levels
(7–10 mA ≈ 0.02–0.05 W). But a 499 Ω shunt at 20 mA dissipates 0.2 W, 80% of a
¼ W rating, and a sensor stuck at a fault current runs it near its limit. We'd
use ½ W next time; it costs pennies. Check the wattage on the order, not just
the value.

## Jumper bars are series-specific

The "2.5" in a terminal block or bridge part number is the conductor size in
mm². It says nothing about whether the bridge fits. Our jumpers were from a
screw-clamp family and our blocks were push-in; they don't fit. Buy bridges
against the block's own family, and order them together.

## Fuse the valves separately

One 4 A fuse feeds our whole 24 V bus. A valve or cable fault takes out the
controller, monitoring and alerts along with it. Next build: a separate fuse per
valve feed at least.

## The 1-hour mean is too slow for overflow alarms

Great for deciding when to fill; useless for a "the tank is overflowing" alarm.
Ours alerted about an hour after a real rise. Use a short average (we use 5 min)
for anything urgent.

## Look at what's upstream of the data

Our biggest surprise — tank level sliding 25+ mm with nothing wrong with the
tank — turned out to be NC programs posted without their conveyor command. The
fix belongs in the CAM post-processor, not the coolant system.

## Old sensors can lie about the baseline

The cheap pressure sensors we replaced had drifting zeros, so everything they
reported as "normal" (30–60 psi) was suspect. A mechanical max-reading gauge
showed under 20 psi on clean filters. Verify a baseline with an independent
instrument before you spec a replacement off old data.
