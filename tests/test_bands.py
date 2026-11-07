"""Die Bänder: Aufbau, Vollständigkeit, Stichproben gegen eine frische Rechnung mit den Kernen dieser Demo (Zeiten werden nie gerechnet, nur gelesen)."""

import pytest

import sgn_constants as C
import sgn_evaluation as ev
import sgn_ls as L
import sgn_starts as T
from sgn_scenario import make_instance

B = ev.load_bands()


def test_counts():
    assert {n: len(ev.band_rows(n)) for n in C.BAND_SIZES} == {12: 20, 25: 16, 50: 16, 100: 8}
    assert {n: len(ev.band_rows(n, "frisch")) for n in C.BAND_SIZES} == {12: 0, 25: 8, 50: 8, 100: 0}
    assert B["meta"]["counts"]["fest"] == {"12": 20, "25": 16, "50": 16, "100": 8} and B["meta"]["counts"]["frisch"] == {"12": 0, "25": 8, "50": 8, "100": 0}
    assert B["meta"]["random_starts"] == C.RANDOM_STARTS


def test_every_row_has_every_start_neighborhood_and_random_start():
    for r in B["rows"]:
        assert set(r["starts"]) == set(ev.live_starts(r["n"])) and ("ES" in r["starts"]) == (r["n"] <= C.ES_MAX_N)
        assert len(r["rand"]) == C.RANDOM_STARTS and r["ref"] > 0 and r["other"] > 0 and r["ref_kind"]
        for k, entry in r["starts"].items():
            assert set(entry["ls"]) == set(C.NEIGH_KEYS) == set(entry["moves"]), (r["n"], r["seed"], k)
            assert all(c <= entry["start"] + 1e-9 for c in entry["ls"].values()), (r["n"], r["seed"], k)       # die Lokalsuche macht den Plan nie länger
            assert all((m == 0) == (abs(c - entry["start"]) < 1e-12) for (nk, c), m in zip(entry["ls"].items(), (entry["moves"][nk] for nk in entry["ls"]))), (r["n"], r["seed"], k)


def test_exact_references_are_lower_bounds_for_up_to_twelve_customers():
    for r in B["rows"]:
        if r["n"] <= C.EXACT_MAX:
            assert r["ref_kind"] == "exakt"
            assert all(c >= r["ref"] - 1e-9 for e in r["starts"].values() for c in e["ls"].values()) and min(r["rand"]) >= r["ref"] - 1e-9


def test_the_best_value_never_exceeds_any_result():
    for r in B["rows"]:
        best = ev.row_best(r)
        assert best <= r["ref"] and best <= r["other"] and best <= min(r["rand"]) and ev.row_regret(r, best) == 0.0


def test_the_sets_do_not_overlap():
    fest = {(r["n"], r["family"], r["depot"], r["seed"]) for r in B["rows"] if r["set"] == "fest"}
    fresh = {(r["n"], r["family"], r["depot"], r["seed"]) for r in B["rows"] if r["set"] == "frisch"}
    assert not fest & fresh and all(s[3] >= 200000 for s in fresh) and all(s[3] >= 300000 for s in fest)


def test_times_exist_for_every_start_of_every_size_and_follow_the_amount_of_work():
    for n in C.BAND_SIZES:
        t = ev.band_times(n)
        keys = set(ev.live_starts(n))
        assert set(t["build"]) == keys == set(t["ls_alle"]) == set(t["ls_2opt"]) and t["rand_start_ls"] > 0
        assert all(v > 0 for part in ("build", "ls_alle", "ls_2opt") for v in t[part].values())
        assert t["build"]["SAV"] <= t["build"]["SAVR"] <= t["build"]["L9R"]                                      # mehr Arbeit, mehr Zeit (Daten, kein Maß)


def _recompute(row):
    inst = make_instance(row["n"], row["family"], row["depot"], C.BAND_ROUTES, row["seed"], C.BAND_FILL)
    P = L.Prob(inst)
    out = {"starts": {}, "rand": []}
    for key in ev.live_starts(row["n"]):
        routes = T.build_start(inst, P, key, row["seed"])
        entry = {"start": L.plan_len(P, routes), "ls": {}, "moves": {}}
        for nk, (_, moves) in C.NEIGH.items():
            cost, _, k = L.local_search(P, routes, set(moves))
            entry["ls"][nk], entry["moves"][nk] = cost, k
        out["starts"][key] = entry
    out["rand"] = [L.local_search(P, T.random_start_plan(P, row["seed"], k), set(C.NEIGH["alle"][1]))[0] for k in range(C.RANDOM_STARTS)]
    return out


@pytest.mark.parametrize("n,which,idx", [(12, "fest", 0), (12, "fest", 11), (25, "frisch", 0), (25, "fest", 3), (50, "frisch", 1), (100, "fest", 0)])
def test_samples_are_reproduced_for_every_start_and_neighborhood(n, which, idx):
    row = ev.band_rows(n, which)[idx]
    fresh = _recompute(row)
    for key, entry in row["starts"].items():
        assert fresh["starts"][key]["start"] == pytest.approx(entry["start"], abs=1e-7), key
        assert fresh["starts"][key]["moves"] == entry["moves"], key
        assert all(fresh["starts"][key]["ls"][nk] == pytest.approx(entry["ls"][nk], abs=1e-7) for nk in C.NEIGH_KEYS), key
    assert all(a == pytest.approx(b, abs=1e-7) for a, b in zip(fresh["rand"], row["rand"]))
