# Home Assistant — fill logic, alerts and pumps

Exported from our Home Assistant (2026.10.1) on 2026-10-23. These are
**examples** — the real config we run, with private details replaced by
placeholders. The reasoning behind every rule is in
[fill-logic.md](../../docs/fill-logic.md).

| File | Contents |
|---|---|
| [`automations.yaml`](automations.yaml) | Automatic water fill (permissive + fill budget), level and valve alerts, the two supply-pump schedules |
| [`scripts.yaml`](scripts.yaml) | The metered water fill; valve test scripts for commissioning |
| [`helpers.yaml`](helpers.yaml) | Every helper: Brix/level/temperature scaling, the 1 h and 5-min means, rising trend, slope, conveyor-wash detection, run state, the fill permissive, the concentrate dose indicator, setpoints, schedule |

## About `helpers.yaml`

We built almost all of the helpers in the Home Assistant **UI**, so they have no
YAML of their own. `helpers.yaml` is the **YAML equivalent of the settings
stored in our Home Assistant**, with the template text copied exactly. You can
paste the sections into `configuration.yaml` (or a package), or recreate them
in the UI with the same settings. The run-state sensor (`UMC 500 Active`) is
the one piece we actually have in YAML.

## Placeholders to replace

| Placeholder | Replace with |
|---|---|
| `notify.mobile_app_your_phone` | Your notify service. The critical alerts use the iOS companion app's `push: sound: critical` format |
| `homemaster_miniplc_xxxxxx_` | Your MiniPLC's entity prefix (ours is MAC-derived) |
| `sensor.shellypro3em_xxxxxxxxxxxx_phase_c_current` | The current sensor you use for machine run state |
| `switch.shop_water_pump_switch`, `switch.coolant_concentrate_pump` | Your supply pump switches |
| `schedule.shop_staffed` | Your staffed hours |

Some entity IDs look odd for historical reasons and are kept so the files match
each other: `binary_sensor.fill_would_trigger_observe_only` is the **live** fill
permissive (it started as observe-only), and the `*_bench` sensors are the
permanent Brix and level scaling (they started as bench scaffolding).

## Numbers that are specific to our tank

Change these for yours: **0.55 gal/mm** (tank volume per mm, in the fill script
and predicted-trough sensor), the **123 mm** ceiling, the **5 gal** fill cap,
the alert thresholds **145 / 135 / 80 mm**, the **36 gal** 24-hour budget, the
setpoints (ours: trigger **109**, target **115** mm), the level span
**0–500 mm**, the Brix factor **2.3**, and the temperature offset **−0.9 °C**.

## Known issue

The fill script calculates its timeout from 4.8 L/min. Our measured flow is
4.2–4.4 L/min, and at the 5 gal cap the timeout (~384 s) is longer than the
MiniPLC's 6-minute valve watchdog. See
[fill-logic.md](../../docs/fill-logic.md#5-the-metered-fill).

## Not included

Dashboards, the retired one-shot supervised fill test, and unrelated
maintenance automations.
