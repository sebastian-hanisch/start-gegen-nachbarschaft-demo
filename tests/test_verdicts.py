"""Verdikte sind reine Funktionen: jede Zahl im Text stammt aus der Rechnung, Art und Wortlaut folgen den Schwellen."""

import pytest

import sgn_constants as C
import sgn_evaluation as ev


def test_run_verdict_for_the_hand_instance():
    s = ev.Settings()
    ch = ev.Choice(0, 5)
    run = ev.run_trace(s, ch)
    kind, text = ev.verdict_run(run, ch, 44.36230880544377)
    assert kind == "success" and "Aus Zufallsfolge + Split (62,60)" in text and "alle drei Züge" in text and "in 7 Zügen (Verschieben 7)" in text and "auf 44,36" in text
    assert "29,1 % kürzer als der Start" in text and "0,0 % gegen die Referenz" in text


def test_run_verdict_without_a_move_and_with_a_stuck_plan():
    s = ev.Settings()
    kind, text = ev.verdict_run(ev.run_trace(s, ev.Choice(0, 0)), ev.Choice(0, 0), 44.36230880544377)
    assert kind == "info" and "keinen verbessernden Zug" in text and "+41,1 % gegen die Referenz" in text
    run = ev.run_trace(s, ev.Choice(1, 5))
    kind, text = ev.verdict_run(run, ev.Choice(1, 5), 44.36230880544377)
    assert kind == "info" and "in 1 Zug (2-opt 1)" in text and "+23,0 % gegen die Referenz" in text


def test_live_verdict_spreads_for_a_mixed_instance():
    s = ev.Settings(25, 1, 0, 3, 90, 6)
    live = ev.live_matrix(s)
    kind, text = ev.verdict_live(live, ev.Choice())
    alle = {k: live.regret(live.cells[(k, "alle")].cost) for k in live.start_cost}
    rs = [live.regret(live.cells[("RS", nk)].cost) for nk in C.NEIGH_KEYS]
    best = min(alle, key=alle.get)
    gz = [live.regret(live.cells[(best, nk)].cost) for nk in C.NEIGH_KEYS]
    assert kind == "success" and f"zwischen {ev.pct(alle[best])} ({ev.start_name(best)})" in text and f"von {ev.pct(min(rs))} bis {ev.pct(max(rs))}" in text and f"von {ev.pct(min(gz))} bis {ev.pct(max(gz))}" in text
    assert ev.pct(max(rs)) == "65,2 %"


def test_random_verdict_levels():
    live = ev.live_matrix(ev.Settings(50, 1, 0, 3, 90, 1))
    for k in (1, 5, 20):
        kind, text = ev.verdict_random(live, k)
        best = min(live.rand[:k])
        assert f"Das beste von {k} Zufallsstarts mit Lokalsuche kostet {ev.de(best)}" in text
        sav = live.cells[("SAV", "alle")].cost
        assert ("verliert gegen" in text) == (best > sav + 1e-9) and kind == ("warning" if best > sav + 1e-9 else "success")
    kind, text = ev.verdict_random(live, 1)
    assert kind == "warning" and "verliert gegen Savings mit Lokalsuche" in text and "28,6 %" in text


def test_band_verdicts():
    for n in C.BAND_SIZES:
        for which in ("fest", "frisch"):
            kind, text = ev.verdict_bands(n, which)
            stats = ev.band_stats(n, which)
            if not stats:
                assert kind == "warning" and "keine Zeilen" in text
                continue
            good = stats["best_construction"]
            assert f"Bei {n} Kunden ({ev.instances_word(stats['count'])}" in text and f"um {ev.de(stats['start_span_alle'])} Prozentpunkte auseinander" in text
            assert f"{ev.pct(stats['mean'][good]['alle'])} für {ev.start_name(good)}" in text and "Ein Lauf je Start und Nachbarschaft" in text
            assert kind in ("success", "info")


def test_band_stats_are_consistent():
    for n in C.BAND_SIZES:
        s = ev.band_stats(n)
        assert s["count"] == len(ev.band_rows(n)) and s["rand"][20] <= s["rand"][5] <= s["rand"][1]
        assert all(s["mean"][k]["alle"] <= s["start"][k] + 1e-9 for k in s["keys"])
        assert s["start_span_alle"] == pytest.approx(max(s["mean"][k]["alle"] for k in s["keys"]) - min(s["mean"][k]["alle"] for k in s["keys"]))
    assert ev.band_stats(100, "frisch") == {} and ev.band_paired(25, "L9R", "RS") == ev.band_paired(25, "L9R", "RS", "alle", "fest")
    b, e, w = ev.band_paired(12, "SAV", "SAV")
    assert (b, e, w) == (0, 20, 0)
