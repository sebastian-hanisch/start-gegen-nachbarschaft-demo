"""Orakel (ORACLE-PLAYBOOK §5): ein unabhängiger Rechenweg gegen die Lokalsuche aus jedem Startplan auf kleinen Instanzen.

Das Orakel zählt alle Zerlegungen der Kunden in Gruppen auf (Mengenpartitionen) und nimmt je Gruppe die kürzeste Rundreise aus allen Reihenfolgen (n <= 7). Jede Lokalsuche muss einen vollständigen,
kapazitätsgerechten Plan liefern, dessen Länge der gemeldeten Kosten entspricht, nie länger als der Start und nie unter dem Optimum; aus dem Optimum bewegt sie sich nicht."""

import itertools
import math

import pytest

import sgn_algorithm as A
import sgn_constants as C
import sgn_evaluation as ev
import sgn_ls as L
import sgn_starts as T


def _route_len(inst, route):
    pts = [inst.xy[0]] + [inst.xy[c] for c in route] + [inst.xy[0]]
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def _partitions(items):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in _partitions(rest):
        yield [[first]] + part
        for i in range(len(part)):
            yield part[:i] + [[first] + part[i]] + part[i + 1:]


def brute_optimum(inst):
    best = math.inf
    for part in _partitions(list(range(1, inst.n + 1))):
        if all(inst.load(g) <= inst.capacity for g in part):
            best = min(best, sum(min(_route_len(inst, p) for p in itertools.permutations(g)) for g in part))
    return best


def test_the_brute_force_oracle_on_the_hand_instance(hand):
    assert brute_optimum(hand) == pytest.approx(44.3623, abs=5e-5)


@pytest.mark.parametrize("n,family,seed", [(5, 0, 1), (6, 1, 2), (7, 2, 3), (7, 0, 4), (6, 1, 9)])
def test_every_start_and_every_neighborhood_gives_a_valid_plan_between_the_start_and_the_optimum(n, family, seed):
    s = ev.Settings(n, family, seed % 2, 2, 90, seed)
    inst = ev.build_instance(s)
    opt = brute_optimum(inst)
    assert A.exact_cvrp(inst).cost == pytest.approx(opt, abs=1e-9)
    P = L.Prob(inst)
    for key in C.START_KEYS:
        start = T.build_start(inst, P, key, seed)
        assert L.is_valid_plan(P, start)
        for nk, (_, moves) in C.NEIGH.items():
            cost, routes, k = L.local_search(P, start, set(moves))
            flat = sorted(c for r in routes for c in r)
            assert flat == list(range(1, inst.n + 1)) and all(inst.load(r) <= inst.capacity for r in routes), (key, nk)
            assert sum(_route_len(inst, r) for r in routes) == pytest.approx(cost, abs=1e-9), (key, nk)
            assert cost <= L.plan_len(P, start) + 1e-9 and cost >= opt - 1e-9, (key, nk)
            assert (k == 0) == (abs(cost - L.plan_len(P, start)) < 1e-12), (key, nk)


@pytest.mark.parametrize("n,family,seed", [(6, 1, 2), (7, 2, 3), (7, 0, 4)])
def test_from_the_optimum_the_local_search_does_not_move(n, family, seed):
    inst = ev.build_instance(ev.Settings(n, family, seed % 2, 2, 90, seed))
    P = L.Prob(inst)
    opt_plan = [list(r) for r in A.exact_cvrp(inst).routes]
    for nk, (_, moves) in C.NEIGH.items():
        cost, routes, k = L.local_search(P, opt_plan, set(moves))
        assert k == 0 and cost == pytest.approx(brute_optimum(inst), abs=1e-9), nk


def test_the_split_of_a_random_order_matches_the_enumeration_of_its_blocks():
    inst = ev.build_instance(ev.Settings(7, 1, 0, 2, 90, 6))
    P = L.Prob(inst)
    order = T.random_start_order(7, 6, 0)
    cost, routes = L.split(P, order)
    best = math.inf                                                                          # alle Schnitte der festen Folge von Hand aufzählen
    for cuts in itertools.product((0, 1), repeat=6):
        blocks, cur = [], [order[0]]
        for c, cut in zip(order[1:], cuts):
            if cut:
                blocks.append(cur)
                cur = []
            cur.append(c)
        blocks.append(cur)
        if all(inst.load(b) <= inst.capacity for b in blocks):
            best = min(best, sum(_route_len(inst, b) for b in blocks))
    assert cost == pytest.approx(best, abs=1e-9)
