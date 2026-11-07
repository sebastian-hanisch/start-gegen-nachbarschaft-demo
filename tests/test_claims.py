"""Jede Zahl der README und der Preset-Hilfen wird aus den Bändern beziehungsweise der Rechnung nachgerechnet und muss im Text stehen (DEMO-PLAYBOOK §1b). Zeiten sind Daten der Bänder: sie werden gelesen, nie gemessen."""

import json
import statistics as st
from pathlib import Path

import sgn_constants as C
import sgn_evaluation as ev
import sgn_ls as L
import sgn_starts as T

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
ROWS = json.loads((ROOT / C.BAND_FILE).read_text(encoding="utf-8"))["rows"]
TIMES = json.loads((ROOT / C.BAND_FILE).read_text(encoding="utf-8"))["times"]
NAME = {k: v[0] for k, v in C.STARTS.items()}
NEIGH = {k: v[0] for k, v in C.NEIGH.items()}


def d(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def p(x, digits=1):
    return d(x, digits) + " %"


def rows(n, which="fest"):
    return [r for r in ROWS if r["n"] == n and r["set"] == which]


def best(r):
    vals = [r["ref"], r["other"]] + r["rand"]
    for e in r["starts"].values():
        vals += list(e["ls"].values())
    return min(vals)


def reg(r, c):
    return 100 * (c / best(r) - 1) if abs(c - best(r)) > 1e-9 else 0.0


def mean_ls(n, k, nk, which="fest"):
    rr = rows(n, which)
    if not rr or k not in rr[0]["starts"]:
        return None
    return st.mean(reg(r, r["starts"][k]["ls"][nk]) for r in rr)


def mean_rand(n, k, which="fest"):
    return st.mean(reg(r, min(r["rand"][:k])) for r in rows(n, which))


def cellp(n, k, nk, which="fest"):
    v = mean_ls(n, k, nk, which)
    return "–" if v is None else p(v)


def test_the_all_moves_table():
    for k in C.START_KEYS:
        row = f"| {NAME[k]} | " + " | ".join(cellp(n, k, "alle") for n in C.BAND_SIZES) + " |"
        assert row in README, row
    for kk in (5, 20):
        row = f"| Bestes von {kk} Zufallsstarts, je mit allen Zügen | " + " | ".join(p(mean_rand(n, kk)) for n in C.BAND_SIZES) + " |"
        assert row in README, row
    spans = [max(mean_ls(n, k, "alle") for k in C.START_KEYS if mean_ls(n, k, "alle") is not None) - min(mean_ls(n, k, "alle") for k in C.START_KEYS if mean_ls(n, k, "alle") is not None) for n in C.BAND_SIZES]
    assert f"um {d(spans[0])} / {d(spans[1])} / {d(spans[2])} / {d(spans[3])} Prozentpunkte auseinander" in README
    assert f"Savings mit nur 2-opt ({cellp(100, 'SAV', '2opt')} bei n = 100) ist besser als die Zufallsfolge mit allen Zügen ({cellp(100, 'RS', 'alle')})" in README
    assert mean_ls(100, "SAV", "2opt") < mean_ls(100, "RS", "alle")


def test_the_neighborhood_tables_and_spans():
    for start in ("RS", "SAVR"):
        for nk in C.NEIGH_KEYS:
            row = f"| {NEIGH[nk]} | " + " | ".join(cellp(n, start, nk) for n in C.BAND_SIZES) + " |"
            assert row in README, row
    for label, start in (("Nachbarschaften aus der Zufallsfolge + Split", "RS"), ("Nachbarschaften aus Savings + Rundreise", "SAVR"), ("Nachbarschaften aus dem besten von 9 λ + Rundreise", "L9R")):
        vals = []
        for n in C.BAND_SIZES:
            v = [mean_ls(n, start, nk) for nk in C.NEIGH_KEYS]
            vals.append(d(max(v) - min(v)))
        assert f"| {label} | " + " | ".join(vals) + " |" in README, label
    row = "| Startpläne bei allen Zügen | " + " | ".join(d(max(mean_ls(n, k, "alle") for k in C.START_KEYS if mean_ls(n, k, "alle") is not None) - min(mean_ls(n, k, "alle") for k in C.START_KEYS if mean_ls(n, k, "alle") is not None)) for n in C.BAND_SIZES) + " |"
    assert row in README


def test_gains_paired_counts_and_random_starts():
    for n in C.BAND_SIZES:
        for k in ("SAV", "L9R", "RS"):
            start = st.mean(reg(r, r["starts"][k]["start"]) for r in rows(n))
            assert f"{NAME[k]} {p(start)} → {p(mean_ls(n, k, 'alle'))}" in README, (n, k)
    for a in ("L9R", "SAVR"):
        cells = []
        for n in C.BAND_SIZES:
            diffs = [r["starts"][a]["ls"]["alle"] - r["starts"]["RS"]["ls"]["alle"] for r in rows(n)]
            cells.append(f"{sum(1 for x in diffs if x < -1e-9)} / {sum(1 for x in diffs if abs(x) <= 1e-9)} / {sum(1 for x in diffs if x > 1e-9)}")
        assert f"| {NAME[a]} gegen {NAME['RS']} | " + " | ".join(cells) + " |" in README
    for n, w in ((12, "bei n = 12 und 25"), ):
        assert w in README
    assert mean_rand(12, 20) < mean_ls(12, "SAV", "alle") and mean_rand(25, 20) < mean_ls(25, "SAV", "alle") and mean_rand(25, 20) < mean_ls(25, "L9R", "alle")       # 20 Zufallsstarts holen die Konstruktionen bei 12 und 25 ein
    assert mean_rand(50, 20) > mean_ls(50, "SAV", "alle") and mean_rand(100, 20) > mean_ls(100, "SAV", "alle") and mean_rand(100, 20) > mean_ls(100, "L9R", "alle")      # bei 50 und 100 nicht
    assert mean_rand(25, 5) > mean_ls(25, "SAV", "alle") and mean_rand(50, 5) > mean_ls(50, "SAV", "alle")                                                        # fünf reichen ab 25 nicht
    sentence = (f"Das beste von 20 Zufallsstarts liegt bei n = 12 und 25 bei {p(mean_rand(12, 20))} und {p(mean_rand(25, 20))} (Savings mit Lokalsuche {p(mean_ls(12, 'SAV', 'alle'))} und {p(mean_ls(25, 'SAV', 'alle'))}); "
                f"bei n = 50 und 100 bleibt es mit {p(mean_rand(50, 20))} und {p(mean_rand(100, 20))} hinter Savings ({p(mean_ls(50, 'SAV', 'alle'))} und {p(mean_ls(100, 'SAV', 'alle'))}) "
                f"und hinter dem besten von 9 λ mit Rundreise ({p(mean_ls(50, 'L9R', 'alle'))} und {p(mean_ls(100, 'L9R', 'alle'))})")
    assert sentence in README, sentence


def test_the_time_table_and_the_fresh_table():
    for k in C.START_KEYS:
        b50, l50 = ev.seconds_text(TIMES["50"]["build"][k]), ev.seconds_text(TIMES["50"]["ls_alle"][k])
        b100 = ev.seconds_text(TIMES["100"]["build"][k]) if k in TIMES["100"]["build"] else "–"
        l100 = ev.seconds_text(TIMES["100"]["ls_alle"][k]) if k in TIMES["100"]["ls_alle"] else "–"
        assert f"| {NAME[k]} | {b50} | {l50} | {b100} | {l100} |" in README, k
    assert f"| Ein Zufallsstart mit Lokalsuche | | {ev.seconds_text(TIMES['50']['rand_start_ls'])} | | {ev.seconds_text(TIMES['100']['rand_start_ls'])} |" in README
    assert f"Zwanzig Zufallsstarts mit Lokalsuche kosten bei n = 100 {ev.seconds_text(20 * TIMES['100']['rand_start_ls'])}" in README
    for k in C.START_KEYS:
        row = f"| {NAME[k]} | " + " | ".join(cellp(n, k, "alle", "frisch") for n in C.FRESH_SIZES) + " |"
        assert row in README, row
    for kk in (5, 20):
        assert f"| Bestes von {kk} Zufallsstarts | " + " | ".join(p(mean_rand(n, kk, "frisch")) for n in C.FRESH_SIZES) + " |" in README
    for n in C.FRESH_SIZES:
        assert len(rows(n, "frisch")) == 8


def test_the_hand_instance_and_the_hook():
    s = ev.Settings()
    rs, rf = ev.run_trace(s, ev.Choice(0, 5)), ev.run_trace(s, ev.Choice(1, 5))
    assert (d(rs.start_cost, 2), len(rs.steps), d(rf.start_cost, 2), d(rf.final_cost, 2), d(ev.live_matrix(s).exact, 2)) == ("62,60", 7, "57,58", "54,54", "44,36")
    for text in ("(Optimum 44,36)", "Der Zufallsstart (62,60) ist mit 2-opt allein ein lokales Optimum (kein Zug)", "findet die Lokalsuche das Optimum in 7 Zügen (alle Verschieben)", "(57,58) bleibt nach einem 2-opt-Zug bei 54,54 hängen"):
        assert text in README, text
    hook = (f"nur 2-opt {cellp(25, 'RS', '2opt')}, alle Züge {cellp(25, 'RS', 'alle')}); sobald der Start eine Konstruktion ist, entscheidet der Start ({cellp(25, 'SAVR', 'alle')} gegen {cellp(25, 'RS', 'alle')} bei n = 25)")
    assert hook in README, hook


# --- Presets -----------------------------------------------------------------------------------------------------------------------------

def _live(name):
    q = C.PRESETS[name]
    s = ev.Settings(q["n"], q["family"], q["depot"], q["routes"], q["fill"], q["seed"])
    return s, ev.Choice(q["start"], q["neigh"]), ev.live_matrix(s)


def test_hand_preset():
    name = "Zufallsstart und alle Züge (Handinstanz)"
    s, ch, live = _live(name)
    run = ev.run_trace(s, ch)
    assert (d(live.exact, 2), d(run.start_cost, 2), len(run.steps), ch.start_key, ch.neigh_key) == ("44,36", "62,60", 7, "RS", "alle")
    assert all(live.cells[(k, "alle")].moves == 0 for k in ("ES", "SAV", "SAVR", "L9R")) and live.cells[("RS", "2opt")].moves == 0
    for text in ("44,36", "62,60", "2-opt allein", "7 Zügen", "Savings oder Einfügen nach Split"):
        assert text in C.PRESET_HELP[name], text


def test_bad_start_and_good_start_presets():
    name = "Der schlechte Start braucht die Nachbarschaft (25 Kunden)"
    s, ch, live = _live(name)
    r = lambda k, nk: live.regret(live.cells[(k, nk)].cost)
    assert (ch.start_key, ch.neigh_key) == ("RS", "2opt") and (d(r("RS", "2opt")), d(r("RS", "alle")), d(live.reference, 2)) == ("65,2", "18,5", "542,41")
    for text in ("65,2 %", "18,5 %", "542,41", "Seed 6"):
        assert text in C.PRESET_HELP[name], text
    name = "Ein guter Start braucht sie kaum (25 Kunden)"
    s, ch, live = _live(name)
    assert (ch.start_key, ch.neigh_key) == ("SAVR", "2opt") and (d(r("SAVR", "2opt")), d(r("SAVR", "alle")), d(r("RS", "alle"))) == ("4,3", "4,1", "18,5")
    assert round(r("SAVR", "2opt") - r("SAVR", "alle"), 1) == 0.2
    for text in ("4,3 %", "4,1 %", "0,2 Prozentpunkte", "18,5 %", "Savings mit Rundreise"):
        assert text in C.PRESET_HELP[name], text


def test_random_starts_preset():
    name = "Zufallsstarts gegen Savings (50 Kunden)"
    s, ch, live = _live(name)
    assert (ch.start_key, ch.neigh_key) == ("SAV", "alle")
    got = (d(live.reference, 2), d(live.regret(live.cells[("SAV", "alle")].cost)), [d(live.regret(min(live.rand[:k]))) for k in (1, 5, 20)], d(live.regret(live.cells[("L9R", "alle")].cost)))
    assert got == ("642,37", "7,9", ["28,6", "16,6", "6,0"], "0,0")
    for text in ("7,9 %", "642,37", "28,6, 16,6, 6,0 %", "(0,0 %)", "Seed 1"):
        assert text in C.PRESET_HELP[name], text
