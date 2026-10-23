# Bill of materials

What one build uses, as on our Haas UMC-500. Machine-readable version:
[bom.csv](bom.csv).

## How to read this BOM

- **Qty** is per machine. We bought spares of most things.
- **Prices** are what we paid, or list price, in US dollars, with the date. They
  will drift — check before you order. Keyence sensors are shown as a set total
  only; get a quote from Keyence.
- **Not included** because we already had them as shop infrastructure: the
  water and concentrate supply pumps and their pressure tanks.
- Parts called out as "next build" are what we'd change; the panel in the photos
  doesn't have them yet.

## Cost summary

**About $4,000 per machine in parts, of which about $2,000 is the Keyence
sensors.**

| Group | Approx. |
|---|---|
| Keyence sensors (2 flow meters, refractometer, radar, cables, brackets) | ≈ $2,000 |
| Controller and I/O (HomeMaster MiniPLC, AIO, WLD; relays) | ≈ $480 |
| Other sensors (4 pressure transmitters, RTD, float) | ≈ $710 |
| Valves and valve plugs | ≈ $185 |
| Cables and connectors | ≈ $225 |
| Enclosure and panel hardware | ≈ $240 |
| **Priced subtotal** | **≈ $3,840** |
| Not priced here: 24 V supply, smart plugs, stainless nipples, fittings, brackets, consumables | brings it to ≈ $4,000 |

The **filter-pressure monitoring** (four transmitters, their bulkheads and
cables, ≈ $600) is optional if you only want auto-fill — but we use the
conveyor filter's upstream pressure to know the conveyor wash is running, which
is one of the fill criteria. You'd need some other way to detect that.

HomeMaster modules ship from Romania; customs and duties are payable on
arrival, and their terminals and DIN rail follow European standards. They are
**CE-marked but not UL listed or FCC certified** (vendor statement).

## Keyence sensors (≈ $2,000 as a set, Sept 2026)

| Item | Part number | Qty | Notes |
|---|---|---|---|
| Clamp-on flow sensor, ¼"–⅜" pipe | FD-H10 | 2 | One per line; each also hosts a Multi-port sensor |
| Flow sensor power/I/O cable, M12 8-pin, 2 m | FD-HCB2 | 2 | |
| Digital refractometer, probe type | FI-C20D | 1 | On FD-H #1's Multi-port |
| Refractometer bracket | FI-CDB1 | 1 | |
| Radar level sensor, short-range | FR-S01 | 1 | On FD-H #2's Multi-port |
| Radar side-mount bracket, SUS304 | OP-88873 | 1 | Open tanks |
| Cable, M12 8-pin → M12 4-pin, 2 m | OP-88444 | 1 | Radar to the FD-H Multi-port |

## Controller and I/O

| Item | Part number | Supplier | Unit price | Qty |
|---|---|---|---|---|
| MiniPLC — ESP32 DIN-rail PLC, Modbus RTU, Ethernet, ESPHome | HM-MINIPLC | HomeMaster (home-master.eu) | $260.00 (Sept 2026) | 1 |
| Analog I/O + RTD module (4 × 0–10 V in, 2 × 0–10 V out, 2 × RTD) | HM-AIO-422-R1 | HomeMaster | $120.00 | 1 |
| Water meter/leak module (5 inputs, 2 SPDT relays) | HM-WLD-521-R1 | HomeMaster | $80.00 | 1 |
| Interposing relay, SPDT, 24 VAC/DC coil, DIN | Klemsan KPR-SCS-24VACDC-1 | AutomationDirect | $9.50 | 2 |
| Shunt resistor, 499 Ω, 1%, **½ W** | Stackpole RNF12FTD499R | DigiKey | < $1 | 4 |
| 24 VDC supply, 5 A, DIN | Mean Well NDR-120-24 | — | not recorded | 1 |

Our panel has **¼ W** shunts (RNF14FTD499R), which are fine at normal signal
levels; we'd use ½ W next time for margin
([lessons.md](lessons.md#shunt-resistor-wattage)).

## Other sensors

| Item | Part number | Supplier | Unit price | Qty | Notes |
|---|---|---|---|---|---|
| Pressure transmitter, 0–100 psig, 4–20 mA, ¼" NPT, M12 | ProSense SPTD25-20-0100H | AutomationDirect | $133.00 | 4 | Optional; 2 per filter |
| RTD Pt100, 6 mm, ¼" NPT, M12, 150 mm | ProSense RTD1-25N-150-H | AutomationDirect | ~$82 | 1 | Our first build has the 100 mm version |
| Float level switch, ¼" NPT, reed | FLS-VL-600 | AutomationDirect | $96.00 | 1 | High-level backstop |

## Valves

| Item | Part number | Supplier | Unit price | Qty |
|---|---|---|---|---|
| Solenoid valve, 2-way **NC**, ¼" FNPT, brass/FKM, 24 VDC, 18 mm DIN plug | Spartan 6100-6H001-AAB3C-A | AutomationDirect | $80.00 | 2 |
| Valve plug, DIN 43650 Form A, LED + surge suppression | Murrelektronik SC18-LS24-0 | AutomationDirect | $12.50 | 2 |

## Cables and connectors

| Item | Part number | Supplier | Unit price | Qty | Notes |
|---|---|---|---|---|---|
| M12 bulkhead, 4-pin female → 1 m pigtail | Murrelektronik 7231-13541-9710100 | AutomationDirect | $13.50 | 10 | 8 bottom + 2 side. Some of ours are the 0.5 m version (‑9710050, $12.50) |
| M12 cable, 4-pole F–M, 1 m | CDP12-0B-010-AA | AutomationDirect | $12.50 | 4 | Pressure transmitters |
| M12 cable, 4-pole F–M, 3 m | CDP12-0B-030-AA | AutomationDirect | $12.50 | 1 | RTD |
| M12 male → pigtail, 4-pole, 5 m | Murrelektronik 7000-12021-2140500 | AutomationDirect | $11.50 | 2 | To the valve plugs |
| Ethernet bulkhead, RJ45 CAT6, waterproof | ANMBEST | Amazon | $39.89 per 10 (Oct 2026) | 1 | |

## Enclosure and panel

| Item | Part number | Supplier | Unit price | Qty | Notes |
|---|---|---|---|---|---|
| Enclosure, IP67 ABS, 20.1 × 16.1 × 7.9 in, with DIN rail + mounting plate | Joisyoya, ASIN B0F18ZLXS3 | Amazon | $109.99 (Oct 2026) | 1 | Smaller sizes in the same family if you need less space |
| Slotted wire duct with cover, 1.6 × 1.2 in, 6 × 16.5 in | ZhiYo, ASIN B0DG8WJ9YT | Amazon | $18.99 per 6 | 1 | ≈ 4 horizontal runs + 1 vertical |
| Push-in feed-through terminal blocks | e.g. Phoenix Contact 3211757 | DigiKey | $1.73 | ≈ 45 | See note below |
| Jumpers, 2-position | Phoenix Contact 3030336 | DigiKey | $0.57 | as needed | Must match the block family |
| Fuse terminal block | WAGO 281-611 | DigiKey | $21.15 | 1 (more next build) | 4 A fuse on ours |
| DIN rail, 35 mm slotted aluminium | Omron PFP-50N | DigiKey | $11.89 | as needed | |
| Ferrules (18 AWG single/twin, 20 AWG) | Z+F V30AE000013 / ‑608 / ‑006 | AutomationDirect | packs | — | |
| Adhesive-lined heat shrink, 3/16" and ½" | Sumitomo 115-10008 / 115-10079 | AutomationDirect | packs | — | ½" builds up the valve-plug gland |

**Terminal blocks aren't standardised yet.** Our panel mostly uses inexpensive
Amazon push-in blocks; the Phoenix Contact blocks are good but expensive, and
we don't want to specify the Amazon ones (long-term availability). We're leaning
toward an AutomationDirect line for future builds. Whatever you pick, buy the
jumpers from the same family.

## Pump control

| Item | Supplier | Qty | Notes |
|---|---|---|---|
| Shelly Plug US Gen4 | Amazon | 2 | One per supply pump. If several machines share the pumps, they share the plugs |

## Per-machine mechanical

Designed per machine; no fixed part numbers:

- **Measurement nipples:** ¼" NPT × 12", 304/304L, Sch 40, **seamless** (we used
  McMaster-Carr 4830K142), one per flow meter.
- **Float + RTD bracket** (planned 3D-printed PETG/ASA, hooks over the lip): RTD
  tip ≈ 50 mm off the bottom, float trip height relative to the full level and
  the lip.
- **Radar mount:** Keyence side bracket on open tanks; a PVC standoff tube with
  printed flange and cap for enclosed tanks with a lid port (≥ 300 mm above max
  level).
- **Refractometer mount** — the FI-CDB1 bracket plus an adapter to your tank.
- **Pressure transmitter taps** at each filter (side or top of the pipe, not the
  bottom; we're adding cleanable stainless Y-strainers and snubbers because the
  old sensing lines filled with fines).
- Plumbing fittings, tubing and tees.

## Bought but not used

- 24 V 4–20 mA signal isolators — replaced by 499 Ω shunts (panel space).
- HomeMaster ENM-223-R1 energy meter — energy metering belongs at the
  distribution panel, not the machine cabinet.
- A Phoenix Contact wire duct — not the one we used.
- Jumper bars from the wrong terminal block family.

## Changes for the next build

- **½ W shunts** (margin, not a fix).
- **A fuse per valve** (and probably separate sensor and controller feeds).
- **M12 8-pin bulkheads for the FD-H cables** instead of cord grips and loose
  2 m cables.
- **150 mm RTD.**
- **1 m bulkhead pigtails** throughout.
- **FD-H health outputs on N.O.** from the start.
- **A "COOLANT FILL STOP" button** ([safety.md](safety.md#planned-guardrails)).
- **Printed labels** on field cables (ours are red tape).
