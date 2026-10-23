"""UMC 500 coolant panel — pin-level netlist, as confirmed at the panel 2026-10-23.
Generates: coolant_panel_wiring.svg (Graphviz preview) and coolant_panel_wiring.drawio (editable).
"""
import html, subprocess, xml.sax.saxutils as sx

# component id: (title, subtitle, column, [ports])
C = {
 "PSU":   ("Mean Well NDR-120-24", "24 VDC 5 A, DIN", 1, ["L", "N", "PE", "+V", "-V"]),
 "FUSE":  ("WAGO 281-611 fuse", "4 A — whole 24 V bus", 1, ["in", "out"]),
 "B24":   ("24 V bus", "single fused node", 1, ["bus"]),
 "B0":    ("0 V bus", "DC common", 1, ["bus"]),
 "FDH0":  ("FD-H 0 V bridge", "terminal, FD-H block", 1, ["node"]),
 "PT1":   ("PT flood upstream", "SPTD25-20-0100H · AI0.1", 0, ["+", "sig"]),
 "PT2":   ("PT flood downstream", "SPTD25-20-0100H · AI0.2", 0, ["+", "sig"]),
 "PT3":   ("PT conveyor upstream", "SPTD25-20-0100H · AI0.3", 0, ["+", "sig"]),
 "PT4":   ("PT conveyor downstream", "SPTD25-20-0100H · AI0.4", 0, ["+", "sig"]),
 "SH0":   ("MiniPLC shunt block", "4 × 499 Ω ¼ W → AGND", 1, ["AI0.1", "AI0.2", "AI0.3", "AI0.4", "AGND"]),
 "FDH1":  ("FD-H #1 — concentrate", "FD-H10 + FI-C20D (Multi-port) · FD-HCB2", 0, ["brown +24", "blue 0V", "black Ch1", "white Ch2", "grey Ch3", "pink Ch4"]),
 "FDH2":  ("FD-H #2 — water", "FD-H10 + FR-S01 via OP-88444 · FD-HCB2", 0, ["brown +24", "blue 0V", "black Ch1", "white Ch2", "grey Ch3", "pink Ch4"]),
 "PARK":  ("Parked terminals", "pink Ch4 ×2 — not connected", 1, ["park"]),
 "SH1":   ("AIO shunt block", "4 × 499 Ω ¼ W → AGND1", 1, ["AI1.1", "AI1.2", "AI1.3", "AI1.4", "AGND1"]),
 "SPARE": ("Spare bulkheads", "AI1.3, AI1.4 (capped)", 0, ["AI1.3", "AI1.4"]),
 "RTD":   ("RTD Pt100", "RTD1-25N-100-H · AIO RTD/1", 0, ["lead A", "lead B"]),
 "FLOAT": ("High-level float", "FLS-VL-600 · WLD I5", 0, ["black", "blue"]),
 "MINI":  ("MiniPLC", "HM-MINIPLC · RS-485 master", 2, ["V+", "0V", "AI1", "AI2", "AI3", "AI4", "AI GND", "B", "A", "COM", "Ethernet"]),
 "AIO":   ("AIO-422-R1", "Modbus address 3", 2, ["V+", "0V", "AI1", "AI2", "AI3", "AI4", "GND", "B", "A", "COM", "RTD1 1", "RTD1 2", "RTD1 3", "RTD1 4"]),
 "WLD":   ("WLD-521-R1", "Modbus address 4", 2, ["V+", "0V", "I1", "I2", "I3", "I4", "I5", "Gnd (ISO)", "B", "A", "COM", "R1 NO", "R1 C", "R2 NO", "R2 C", "5Vdc"]),
 "K1":    ("Interposer WLDR1", "Klemsan KPR-SCS-24VAC/DC", 3, ["A1", "A2", "11", "14"]),
 "K2":    ("Interposer WLDR2", "Klemsan KPR-SCS-24VAC/DC", 3, ["A1", "A2", "11", "14"]),
 "V1":    ("Concentrate valve", "Spartan 6100-6H001 · SC18-LS24-0", 4, ["+", "-"]),
 "V2":    ("Water valve", "Spartan 6100-6H001 · SC18-LS24-0", 4, ["+", "-"]),
 "ETH":   ("RJ45 bulkhead", "to shop network", 3, ["RJ45"]),
}

# (from, port, to, port, label, kind)  kind: p24 | p0 | sig | bus | out
E = [
 ("PSU", "+V", "FUSE", "in", "", "p24"),
 ("FUSE", "out", "B24", "bus", "", "p24"),
 ("PSU", "-V", "B0", "bus", "", "p0"),
 ("B24", "bus", "MINI", "V+", "", "p24"), ("B0", "bus", "MINI", "0V", "", "p0"),
 ("B24", "bus", "AIO", "V+", "", "p24"), ("B0", "bus", "AIO", "0V", "", "p0"),
 ("B24", "bus", "WLD", "V+", "", "p24"), ("B0", "bus", "WLD", "0V", "", "p0"),
 # pressure transmitters (2-wire loops)
 *[(f"PT{i}", "+", "B24", "bus", "", "p24") for i in range(1, 5)],
 *[(f"PT{i}", "sig", "SH0", f"AI0.{i}", f"AI0.{i}", "sig") for i in range(1, 5)],
 *[("SH0", f"AI0.{i}", "MINI", f"AI{i}", "", "sig") for i in range(1, 5)],
 ("SH0", "AGND", "MINI", "AI GND", "AGND (star)", "p0"),
 # FD-H #1 concentrate
 ("FDH1", "brown +24", "B24", "bus", "", "p24"),
 ("FDH1", "blue 0V", "FDH0", "node", "", "p0"),
 ("FDH1", "black Ch1", "WLD", "I1", "pulse 0.02 L, NPN", "sig"),
 ("FDH1", "white Ch2", "SH1", "AI1.1", "Brix 4–20 mA", "sig"),
 ("FDH1", "grey Ch3", "WLD", "I3", "error, N.C.", "sig"),
 ("FDH1", "pink Ch4", "PARK", "park", "", "out"),
 # FD-H #2 water
 ("FDH2", "brown +24", "B24", "bus", "", "p24"),
 ("FDH2", "blue 0V", "FDH0", "node", "", "p0"),
 ("FDH2", "black Ch1", "WLD", "I2", "pulse 0.02 L, NPN", "sig"),
 ("FDH2", "white Ch2", "SH1", "AI1.2", "level 4–20 mA", "sig"),
 ("FDH2", "grey Ch3", "WLD", "I4", "error, N.C.", "sig"),
 ("FDH2", "pink Ch4", "PARK", "park", "", "out"),
 # FD-H 0 V bridge: ties FD-H 0 V, WLD GND_ISO and supply 0 V into one node
 ("FDH0", "node", "WLD", "Gnd (ISO)", "GND_ISO (isolation bypassed)", "p0"),
 ("FDH0", "node", "B0", "bus", "", "p0"),
 # AIO analog
 *[("SH1", f"AI1.{i}", "AIO", f"AI{i}", "", "sig") for i in range(1, 5)],
 ("SPARE", "AI1.3", "SH1", "AI1.3", "", "out"), ("SPARE", "AI1.4", "SH1", "AI1.4", "", "out"),
 ("SH1", "AGND1", "AIO", "GND", "AGND1 (star)", "p0"),
 ("RTD", "lead A", "AIO", "RTD1 2", "2-wire, jumpers 1–2", "sig"),
 ("RTD", "lead B", "AIO", "RTD1 3", "2-wire, jumpers 3–4", "sig"),
 # float
 ("FLOAT", "black", "WLD", "I5", "", "sig"),
 ("FLOAT", "blue", "WLD", "5Vdc", "isolated 5 V", "sig"),
 # RS-485
 ("MINI", "B", "AIO", "B", "", "bus"), ("MINI", "A", "AIO", "A", "", "bus"), ("MINI", "COM", "AIO", "COM", "", "bus"),
 ("AIO", "B", "WLD", "B", "", "bus"), ("AIO", "A", "WLD", "A", "", "bus"), ("AIO", "COM", "WLD", "COM", "", "bus"),
 ("MINI", "Ethernet", "ETH", "RJ45", "", "bus"),
 # relays and valves
 ("B24", "bus", "WLD", "R1 C", "", "p24"), ("B24", "bus", "WLD", "R2 C", "", "p24"),
 ("WLD", "R1 NO", "K1", "A1", "", "sig"), ("WLD", "R2 NO", "K2", "A1", "", "sig"),
 ("K1", "A2", "B0", "bus", "", "p0"), ("K2", "A2", "B0", "bus", "", "p0"),
 ("B24", "bus", "K1", "11", "", "p24"), ("B24", "bus", "K2", "11", "", "p24"),
 ("K1", "14", "V1", "+", "white · bulkhead WLDR1", "sig"),
 ("K2", "14", "V2", "+", "white · bulkhead WLDR2", "sig"),
 ("V1", "-", "B0", "bus", "blue", "p0"), ("V2", "-", "B0", "bus", "blue", "p0"),
]

COLOR = {"p24": "#C0392B", "p0": "#1F5FA6", "sig": "#333333", "bus": "#7B5EA7", "out": "#9A9A9A"}

def pid(p):
    return "p" + "".join(ch if ch.isalnum() else "_" for ch in p)

NET = {}
def build_nets():
    keep = []
    for a, ap, b, bp, lab, kind in E:
        if b in ("B24", "B0") or a in ("B24", "B0"):
            other, op, bus = (a, ap, b) if b in ("B24", "B0") else (b, bp, a)
            if other in ("FUSE", "PSU"):
                NET[(other, op)] = "→ 24 V bus" if bus == "B24" else "→ 0 V bus"
            else:
                NET[(other, op)] = "→ 24 V" if bus == "B24" else "→ 0 V"
            continue
        keep.append((a, ap, b, bp, lab, kind))
    return keep

def plabel(k, p):
    return p + (f"  {NET[(k, p)]}" if (k, p) in NET else "")

def write_dot(path):
    L = ['digraph G {', 'graph [rankdir=LR, splines=spline, nodesep=0.3, ranksep=1.6, fontname="Helvetica", '
         'label="UMC 500 coolant panel — pin-level wiring (confirmed 2026-10-23)", labelloc=t, fontsize=18];',
         'node [shape=plaintext, fontname="Helvetica", fontsize=10];', 'edge [arrowhead=none, fontname="Helvetica", fontsize=8];']
    cols = {}
    for k, (t, s, c, ports) in C.items():
        if k in ("B24", "B0"):
            continue
        cols.setdefault(c, []).append(k)
        rows = "".join(f'<TR><TD PORT="{pid(p)}" ALIGN="LEFT">{html.escape(plabel(k, p))}</TD></TR>' for p in ports)
        L.append(f'{k} [label=<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">'
                 f'<TR><TD BGCOLOR="#EEEDFE"><B>{html.escape(t)}</B><BR/><FONT POINT-SIZE="8">{html.escape(s)}</FONT></TD></TR>{rows}</TABLE>>];')
    for c, ks in sorted(cols.items()):
        L.append("{rank=same; " + "; ".join(ks) + ";}")
    for a, ap, b, bp, lab, kind in EK:
        l = f' xlabel="{html.escape(lab)}"' if lab else ""
        L.append(f'{a}:{pid(ap)} -> {b}:{pid(bp)} [color="{COLOR[kind]}"{l}];')
    L.append("}")
    open(path, "w", encoding="utf-8").write("\n".join(L))

def write_drawio(path):
    colx = {0: 40, 1: 420, 2: 820, 3: 1220, 4: 1560}
    coly = {c: 60 for c in colx}
    cells, ids, n = [], {}, [2]
    def nid():
        n[0] += 1
        return f"c{n[0]}"
    W, H = 260, 20
    for k, (t, s, c, ports) in C.items():
        if k in ("B24", "B0"):
            continue
        x, y = colx[c], coly[c]
        gid = nid(); ids[k] = gid
        h = 40 + H * len(ports)
        cells.append(f'<mxCell id="{gid}" value="{sx.escape(t)}&lt;br&gt;&lt;font style=&quot;font-size:9px&quot;&gt;{sx.escape(s)}&lt;/font&gt;" '
                     f'style="swimlane;html=1;startSize=40;fillColor=#EEEDFE;strokeColor=#534AB7;whiteSpace=wrap;" vertex="1" parent="1">'
                     f'<mxGeometry x="{x}" y="{y}" width="{W}" height="{h}" as="geometry"/></mxCell>')
        for i, p in enumerate(ports):
            pidc = nid(); ids[(k, p)] = pidc
            cells.append(f'<mxCell id="{pidc}" value="{sx.escape(plabel(k, p))}" style="rounded=0;html=1;align=left;spacingLeft=4;fontSize=10;" vertex="1" parent="{gid}">'
                         f'<mxGeometry y="{40 + i * H}" width="{W}" height="{H}" as="geometry"/></mxCell>')
        coly[c] = y + h + 30
    for a, ap, b, bp, lab, kind in EK:
        eid = nid()
        cells.append(f'<mxCell id="{eid}" value="{sx.escape(lab)}" style="edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor={COLOR[kind]};fontSize=8;" '
                     f'edge="1" parent="1" source="{ids[(a, ap)]}" target="{ids[(b, bp)]}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    xml = ('<mxfile host="app.diagrams.net"><diagram name="UMC 500 coolant panel">'
           '<mxGraphModel grid="1" gridSize="10" page="1" pageWidth="1900" pageHeight="1600"><root>'
           '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>')
    open(path, "w", encoding="utf-8").write(xml)

EK = build_nets()

if __name__ == "__main__":
    # Writes next to this script. Needs Graphviz ("dot") on the PATH.
    import os
    out = os.path.dirname(os.path.abspath(__file__))
    dot = os.path.join(out, "panel.dot")
    write_dot(dot)
    subprocess.run(["dot", "-Tsvg", dot, "-o", os.path.join(out, "coolant_panel_wiring.svg")], check=True)
    subprocess.run(["dot", "-Tpng", "-Gdpi=110", dot, "-o", os.path.join(out, "coolant_panel_wiring.png")], check=True)
    write_drawio(os.path.join(out, "coolant_panel_wiring.drawio"))
    print("ok", len(C) - 2, "components", len(EK), "drawn wires,", len(NET), "power net labels")
