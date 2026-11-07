"""Handwerte und Eigenschaften der Lokalsuche (DEMO-PLAYBOOK §1b): Quadrat, Linie, Tausch, Handinstanz, lokales Optimum, Zugfolge."""

import math

import pytest

import sgn_constants as C
import sgn_evaluation as ev
import sgn_ls as L
import sgn_starts as T
from sgn_scenario import Instance, make_instance

S2 = math.sqrt(2)
ALL = {"2opt", "move", "swap"}


def test_two_opt_on_the_crossed_square_by_roots(square):
    P = L.Prob(square)
    trace = []
    cost, routes, k = L.local_search(P, [[1, 3, 2, 4]], {"2opt"}, trace)
    assert L.plan_len(P, [[1, 3, 2, 4]]) == pytest.approx(6 * S2 + 2, abs=1e-9)        # 10,4853
    assert cost == pytest.approx(6 + 2 * S2, abs=1e-9) and k == len(trace) >= 1               # 8,8284: das Quadrat (mehrere Umkehrungen sind möglich, das Ende ist eindeutig)
    assert all(s["kind"] == "2-opt" for s in trace) and sum(s["gain"] for s in trace) == pytest.approx(4 * S2 - 4, abs=1e-9)   # Gewinn insgesamt 4 Wurzel 2 minus 4
    assert [c for r in routes for c in r] in ([1, 2, 3, 4], [4, 3, 2, 1], [2, 3, 4, 1], [3, 4, 1, 2], [4, 1, 2, 3], [1, 4, 3, 2], [2, 1, 4, 3], [3, 2, 1, 4])   # Umlauf um das Quadrat


def test_move_on_a_line_by_hand():
    inst = Instance(((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)), (1, 1, 1), 10)
    P = L.Prob(inst)
    trace = []
    cost, routes, k = L.local_search(P, [[1, 3], [2]], {"move"}, trace)
    assert L.plan_len(P, [[1, 3], [2]]) == pytest.approx(10.0) and cost == pytest.approx(6.0) and k == 1 and routes == [[1, 2, 3]]
    assert trace[0]["kind"] == "Verschieben" and trace[0]["customers"] == (2,) and trace[0]["gain"] == pytest.approx(4.0)


def test_swap_on_a_line_by_hand():
    inst = Instance(((0.0, 0.0), (10.0, 0.0), (-10.0, 0.0), (9.0, 0.0), (-9.0, 0.0)), (1, 1, 1, 1), 2)
    P = L.Prob(inst)
    trace = []
    cost, routes, k = L.local_search(P, [[1, 4], [2, 3]], {"swap"}, trace)
    assert L.plan_len(P, [[1, 4], [2, 3]]) == pytest.approx(76.0) and cost == pytest.approx(40.0) and k == 1
    assert trace[0]["kind"] == "Tauschen" and trace[0]["customers"] == (1, 2) and trace[0]["gain"] == pytest.approx(36.0)


def test_no_move_set_means_no_change():
    inst = make_instance(12, 1, 0, 3, 5, 90)
    P = L.Prob(inst)
    start = T.build_start(inst, P, "RS", 5)
    cost, routes, k = L.local_search(P, start, set())
    assert k == 0 and cost == pytest.approx(L.plan_len(P, start)) and routes == start


def test_the_hand_instance_with_the_random_start(hand):
    P = L.Prob(hand)
    start = T.build_start(hand, P, "RS", 0)
    assert start == [[5, 3, 2], [1], [6, 4]]
    by_hand = (S2 + math.sqrt(18) + math.sqrt(85) + math.sqrt(29)) + 2 * math.sqrt(72) + (math.sqrt(45) + math.sqrt(136) + 7)
    assert L.plan_len(P, start) == pytest.approx(by_hand, abs=1e-9) and by_hand == pytest.approx(62.6022, abs=5e-5)
    assert L.local_search(P, start, {"2opt"})[2] == 0                                      # 2-opt allein findet keinen Zug
    trace = []
    cost, routes, k = L.local_search(P, start, ALL, trace)
    optimum = (math.sqrt(72) + math.sqrt(37) + 7) + (math.sqrt(29) + math.sqrt(20) + math.sqrt(53) + math.sqrt(18) + math.sqrt(2))
    assert cost == pytest.approx(optimum, abs=1e-9) and k == 7 and all(s["kind"] == "Verschieben" for s in trace)
    assert sorted(map(sorted, routes)) == [[1, 4], [2, 3, 5, 6]]


def test_the_hand_instance_with_the_filled_random_start(hand):
    P = L.Prob(hand)
    start = T.build_start(hand, P, "RF", 0)
    assert start == [[3, 4, 6], [1, 5, 2]]
    trace = []
    cost, routes, k = L.local_search(P, start, ALL, trace)
    assert routes == [[4, 3, 6], [1, 5, 2]] and k == 1 and trace[0]["kind"] == "2-opt" and trace[0]["gain"] == pytest.approx(3.0386, abs=5e-5)
    assert cost == pytest.approx(54.5438, abs=5e-5)                                         # bleibt 23 % über dem Optimum hängen


@pytest.mark.parametrize("key", ["ES", "SAV", "SAVR", "L9R"])
def test_constructions_start_in_the_optimum_on_the_hand_instance(hand, key):
    P = L.Prob(hand)
    start = T.build_start(hand, P, key, 0)
    assert L.plan_len(P, start) == pytest.approx(44.3623, abs=5e-5) and L.local_search(P, start, ALL)[2] == 0


@pytest.mark.parametrize("n,family,seed", [(12, 1, 3), (25, 1, 6), (25, 2, 4), (30, 0, 2)])
def test_the_result_is_a_local_optimum_and_the_trace_adds_up(n, family, seed):
    inst = make_instance(n, family, seed % 2, 3, seed, 90)
    P = L.Prob(inst)
    for key in ("RS", "RF", "SAV"):
        start = T.build_start(inst, P, key, seed)
        trace = []
        cost, routes, k = L.local_search(P, start, ALL, trace)
        assert L.is_valid_plan(P, routes) and k == len(trace)
        assert L.local_search(P, routes, ALL)[2] == 0                                      # ein zweiter Lauf findet keinen Zug mehr
        assert sum(s["gain"] for s in trace) == pytest.approx(L.plan_len(P, start) - cost, abs=1e-7)
        if trace:
            assert trace[-1]["cost"] == pytest.approx(cost, abs=1e-7) and all(s["gain"] > 0 for s in trace)


def test_same_seed_same_result_and_a_different_seed_differs():
    inst = make_instance(25, 1, 0, 3, 11, 90)
    P = L.Prob(inst)
    a = L.local_search(P, T.build_start(inst, P, "RS", 11), ALL)
    b = L.local_search(P, T.build_start(inst, P, "RS", 11), ALL)
    assert a == b
    assert T.random_start_order(25, 11, 0) == T.random_start_order(25, 11, 0) and T.random_start_order(25, 11, 0) != T.random_start_order(25, 11, 1)
    assert sorted(T.random_start_order(25, 11, 3)) == list(range(1, 26))


def test_more_moves_are_on_average_not_worse():
    totals = {nk: 0.0 for nk in C.NEIGH_KEYS}
    for seed in range(8):
        inst = make_instance(25, 1, seed % 2, 3, seed + 40, 90)
        P = L.Prob(inst)
        start = T.build_start(inst, P, "RS", seed)
        for nk, (_, moves) in C.NEIGH.items():
            totals[nk] += L.local_search(P, start, set(moves))[0]
    assert totals["alle"] <= totals["2opt"] and totals["alle"] <= totals["swap"] and totals["move+swap"] <= totals["swap"] and totals["2opt+move"] <= totals["2opt"]


def test_renumbering_the_customers_keeps_the_split_cost():
    inst = make_instance(10, 1, 0, 3, 8, 90)
    perm = [3, 1, 2, 5, 4, 7, 6, 9, 8, 10]                                                  # Kunde i heißt danach perm[i - 1]
    xy = (inst.xy[0],) + tuple(inst.xy[perm.index(i + 1) + 1] for i in range(10))
    dem = tuple(inst.demand[perm.index(i + 1)] for i in range(10))
    other = Instance(xy, dem, inst.capacity)
    P, Q = L.Prob(inst), L.Prob(other)
    order = list(range(1, 11))
    mapped = [perm[c - 1] for c in order]
    assert L.split(P, order)[0] == pytest.approx(L.split(Q, mapped)[0], abs=1e-9)


def test_starts_are_valid_plans_and_deterministic():
    inst = make_instance(20, 2, 1, 3, 9, 90)
    P = L.Prob(inst)
    for key in C.START_KEYS:
        a = T.build_start(inst, P, key, 9)
        assert L.is_valid_plan(P, a) and a == T.build_start(inst, P, key, 9), key
    with pytest.raises(ValueError):
        T.build_start(inst, P, "XX", 9)
    assert ev.start_name("SAVR") == "Savings λ = 1 + Rundreise" and ev.neigh_name("alle") == "alle drei Züge"
