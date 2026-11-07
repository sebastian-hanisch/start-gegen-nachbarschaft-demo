"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import sgn_constants as C
from sgn_evaluation import Choice, Settings, build_instance, de, gap_percent, neigh_name, pct, run_trace, start_name

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2", "λ": "lambda", "‖": "|", "←": "<-", "✔": "x"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, ch: Choice, live) -> bytes:
    inst = build_instance(s)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Start gegen Nachbarschaft"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    where = "Handinstanz (6 Kunden)" if s.family == C.HAND_FAMILY else f"{s.n} Kunden, Karte: {C.FAMILIES[s.family]}, Depot: {C.DEPOTS[s.depot].lower()}, Zielroutenzahl {s.routes}, Auslastung {s.fill} %, Seed {s.seed}"
    pdf.multi_cell(0, 5, _s(f"{where}. Kapazität {inst.capacity}, Gesamtnachfrage {sum(inst.demand)}. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    if live is not None:
        run = run_trace(s, ch)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _s(f"Lokalsuche aus: {start_name(ch.start_key)}; Nachbarschaft: {neigh_name(ch.neigh_key)}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, _s(f"Startplan {de(run.start_cost)}, nach der Lokalsuche {de(run.final_cost)} in {len(run.steps)} Zügen; Referenz {de(live.reference)} "
                              f"({'exakt' if live.exact is not None else 'bester Wert der Seite'}), Abstand {pct(gap_percent(run.final_cost, live.reference))}."), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        keys = list(live.start_cost)
        widths = [50, 20] + [20] * len(C.NEIGH_KEYS)
        pdf.set_font("Helvetica", "B", 7)
        for w, h in zip(widths, ["Startplan", "Start"] + [C.NEIGH[nk][0] for nk in C.NEIGH_KEYS]):
            pdf.cell(w, 6, _s(h[:22]), border=1)
        pdf.ln()
        pdf.set_font("Helvetica", "", 8)
        for k in keys:
            vals = [start_name(k), pct(live.regret(live.start_cost[k]))] + [pct(live.regret(live.cells[(k, nk)].cost)) for nk in C.NEIGH_KEYS]
            for w, v in zip(widths, vals):
                pdf.cell(w, 5.5, _s(v), border=1)
            pdf.ln()
    else:
        pdf.multi_cell(0, 5, _s(f"Über {C.LIVE_N_MAX} Kunden zeigt die App nur die vorberechneten Bänder."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Bedauern: Abstand zum besten Wert auf der Instanz. Eine einfache Lokalsuche (erste Verbesserung, 2-opt, Verschieben, Tauschen). Quelle: start-gegen-nachbarschaft-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
