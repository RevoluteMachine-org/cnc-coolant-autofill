# ESPHome — MiniPLC config

[`umc500-coolant-miniplc.yaml`](umc500-coolant-miniplc.yaml) is the config
running on our HomeMaster MiniPLC, published as an example. It was built with
**ESPHome 2025.12.5**.

## What it does

- **Modbus master** for the HomeMaster AIO-422-R1 (address 3, firmware v0.2.0)
  and WLD-521-R1 (address 4, firmware v0.1.0), using HomeMaster's own ESPHome
  packages. Each package path matches the firmware actually on that module.
- **Filter pressures** on the MiniPLC's four analog inputs: per-channel zero
  calibration through 499 Ω shunts, a ΔP per filter, and a 2-minute ΔP average
  taken only while that filter's pump is running (upstream > 5 psi). Below
  1.5 V reads as NaN (broken loop), never as zero.
- **Valve watchdog** (marked `ADDED 2026-10-16`): every 5 s, reads the WLD's
  *reported* relay states; forces the water valve (relay 2) off after
  **6 min** and the concentrate valve (relay 1) after **3 min**, re-sending
  "off" until the WLD confirms. Latches a *Valve watchdog tripped* binary sensor;
  a *Valve watchdog reset* button clears it. Works with Home Assistant down.
- **Both valves off on boot.**

## Before you use it

- **Add your own secrets.** Ours has no API encryption key or OTA password in
  the file (it's on wired Ethernet). Add both from your own `secrets.yaml` —
  see the comment at the top of the YAML.
- **Upgrading ESPHome past 2026.7.0?** Add `turnaround_time` and
  `send_wait_time` to the `modbus:` block in the same change, or the bus slows
  down silently. See the comment in the YAML and
  [lessons.md](../../docs/lessons.md#esphome-modbus-timing-options-are-tied-to-version-20267).
- **Calibration values are ours.** The four pressure zeros (1.986 / 1.996 /
  1.993 / 2.005 V) were measured on our panel; measure your own.
- **Known gaps:** the watchdog can't help if Modbus to the WLD is lost (its
  "off" can't land, and the WLD has no comm-loss failsafe). Valves are closed
  on boot but **not** when an over-the-air update starts. The fill sequence
  itself currently runs in Home Assistant, not here. See
  [safety.md](../../docs/safety.md#known-gaps-as-of-2026-10-23).
