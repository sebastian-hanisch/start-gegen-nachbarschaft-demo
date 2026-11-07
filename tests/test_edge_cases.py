"""Randfälle: kleine und große Instanzen, Kapazität für alle, jeder Kunde allein, Seed 0, Live-Grenze."""

import pytest

import sgn_constants as C
import sgn_evaluation as ev
import sgn_ls as L
import sgn_starts as T
from sgn_scenario import Instance


@pytest.mark.parametrize("n", (1, 2, 3))
def test_tiny_instances_run_with_every_start_and_neighborhood(n):
    s = ev.Settings(n, 1, 0, 2, 90, 3)
    live = ev.live_matrix(s)
    assert set(live.start_cost) == set(C.START_KEYS) and len(live.cells) == len(C.START_KEYS) * len(C.NEIGH_KEYS)
    assert live.reference == pytest.approx(min(c.cost for c in live.cells.values()), abs=1e-9)


def test_capacity_for_all_gives_one_route_from_the_savings_start():
    inst = Instance(((0.0, 0.0), (1.0, 1.0), (2.0, 0.0), (1.0, -1.0)), (1, 1, 1), 100)
    P = L.Prob(inst)
    start = T.build_start(inst, P, "SAV", 0)
    assert len(start) == 1
    cost, routes, k = L.local_search(P, start, {"2opt", "move", "swap"})
    assert len(routes) == 1 and L.is_valid_plan(P, routes)


def test_every_customer_alone_has_no_move_that_fits():
    inst = Instance(((0.0, 0.0), (5.0, 0.0), (0.0, 5.0), (-5.0, 0.0)), (4, 4, 4), 4)
    P = L.Prob(inst)
    routes = [[1], [2], [3]]
    cost, final, k = L.local_search(P, routes, {"2opt", "move", "swap"})
    assert k == 0 and cost == pytest.approx(30.0) and final == routes                    # Last 4 gleich Kapazität: keine Route nimmt einen zweiten Kunden


def test_seed_zero_and_a_large_seed_work():
    for seed in (0, 999999):
        inst = ev.build_instance(ev.Settings(12, 2, 1, 3, 90, seed))
        P = L.Prob(inst)
        for key in C.START_KEYS:
            assert L.is_valid_plan(P, T.build_start(inst, P, key, seed))


def test_live_is_only_for_small_instances():
    with pytest.raises(ValueError):
        ev.live_matrix(ev.Settings(C.LIVE_N_MAX + 1, 1, 0, 3, 90, 1))


def test_the_reference_is_exact_up_to_twelve_customers_and_the_best_of_the_page_above():
    small = ev.live_matrix(ev.Settings(12, 1, 0, 3, 90, 5))
    big = ev.live_matrix(ev.Settings(14, 1, 0, 3, 90, 5))
    assert small.exact is not None and small.reference == small.exact and big.exact is None
    assert big.reference == pytest.approx(min([c.cost for c in big.cells.values()] + list(big.rand) + list(big.start_cost.values())), abs=1e-12)


def test_formats():
    assert ev.de(3.14159) == "3,14" and ev.pct(12.345) == "12,3 %" and ev.signed_pct(-0.04) == "0,0 %" and ev.signed_pct(2.5) == "+2,5 %" and ev.signed_pct(-2.5) == "−2,5 %"
    assert ev.routes_word(1) == "1 Route" and ev.routes_word(3) == "3 Routen" and ev.instances_word(1) == "1 Instanz" and ev.instances_word(8) == "8 Instanzen"
    assert [ev.seconds_text(t) for t in (0.0007, 0.0071, 0.05, 0.5, 2.34, 12.4, 100.0)] == ["0,7 ms", "7,1 ms", "50 ms", "0,50 s", "2,3 s", "12 s", "100 s"]
    assert ev.gap_percent(10.0, 10.0) == 0.0 and ev.gap_percent(11.0, 10.0) == pytest.approx(10.0)
    assert ev.routes_text(((1, 2), (3,))) == "(1 2) ‖ (3)"
