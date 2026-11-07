"""Rundreise je Route (aus Stück 6 der Linie Tourenbildung, gekürzt): die kürzeste Rundreise durch das Depot und alle Kunden einer Route, exakt bis EXACT_MAX Kunden (Teilmengen-DP), darüber 2-opt und Or-opt.
Dieselbe Rundreise ordnet die Routen von Savings und Einfügen nach Split neu (`reoptimize`)."""

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import sgn_algorithm as A
from sgn_scenario import Instance, distance_matrix

EXACT_MAX = 12                              # bis zu dieser Clustergröße rechnet die Rundreise exakt


@dataclass(frozen=True)
class Plan:
    cost: float
    routes: tuple[tuple[int, ...], ...]


# ----------------------------------------------------------------------------------------------------------------------------------------- Rundreise je Cluster

def tour_length(inst: Instance, route) -> float:
    return A.route_length(inst, route)


@lru_cache(maxsize=200_000)
def _tsp_exact(inst: Instance, nodes: tuple[int, ...]) -> tuple[float, tuple[int, ...]]:
    D = distance_matrix(inst)
    k = len(nodes)
    if k == 1:
        return float(2 * D[0][nodes[0]]), (nodes[0],)
    d = np.array([[D[a][b] for b in nodes] for a in nodes])
    d0 = np.array([D[0][a] for a in nodes])
    size = 1 << k
    dp = np.full((size, k), np.inf)
    parent = np.full((size, k), -1, dtype=int)
    for i in range(k):
        dp[1 << i, i] = d0[i]
    for mask in range(1, size):
        cand = dp[mask][:, None] + d
        vals, args = cand.min(axis=0), cand.argmin(axis=0)
        for nxt in range(k):
            if mask >> nxt & 1 or vals[nxt] == np.inf:
                continue
            nm = mask | (1 << nxt)
            if vals[nxt] < dp[nm, nxt] - 1e-12:
                dp[nm, nxt] = vals[nxt]
                parent[nm, nxt] = args[nxt]
    full = size - 1
    total = dp[full] + d0
    last = int(np.argmin(total))
    best = float(total[last])
    order, mask = [], full
    while last != -1:
        order.append(nodes[last])
        prev = int(parent[mask, last])
        mask ^= 1 << last
        last = prev
    return best, tuple(order[::-1])


def tsp_exact(inst: Instance, cluster) -> tuple[float, tuple[int, ...]]:
    """Kürzeste Rundreise Depot - Kunden - Depot durch alle Kunden des Clusters (Teilmengen-DP; höchstens EXACT_MAX Kunden). Gleichstand: bestimmt die Rechnung, nicht die Eingabereihenfolge."""
    if len(cluster) > EXACT_MAX:
        raise ValueError(f"mehr als {EXACT_MAX} Kunden")
    return _tsp_exact(inst, tuple(sorted(cluster)))


def tsp_heuristic(inst: Instance, cluster, start_order=None) -> tuple[float, tuple[int, ...]]:
    """2-opt und Or-opt (Segmente bis 3, beide Richtungen) ab der Folge `start_order` (Voreinstellung: die Reihenfolge von `cluster`), bis keine Verbesserung mehr gefunden wird. Eine Heuristik: die Länge liegt nie unter der Rundreise."""
    D = distance_matrix(inst)
    route = list(start_order if start_order is not None else cluster)
    n = len(route)
    if n <= 2:
        return float(tour_length(inst, route)), tuple(route)
    improved = True
    while improved:
        improved = False
        path = [0] + route + [0]
        for i in range(1, n):
            for j in range(i + 1, n + 1):
                a, b, c, d = path[i - 1], path[i], path[j], path[j + 1]
                if D[a][c] + D[b][d] < D[a][b] + D[c][d] - 1e-10:
                    path[i:j + 1] = path[i:j + 1][::-1]
                    improved = True
        route = path[1:-1]
        for seg in (1, 2, 3):
            for i in range(n - seg + 1):
                moved = route[i:i + seg]
                rest = route[:i] + route[i + seg:]
                best = (tour_length(inst, route), None)
                for p in range(len(rest) + 1):
                    for cand in (moved, moved[::-1]):
                        trial = rest[:p] + cand + rest[p:]
                        value = tour_length(inst, trial)
                        if value < best[0] - 1e-10:
                            best = (value, trial)
                if best[1] is not None:
                    route = best[1]
                    improved = True
    return float(tour_length(inst, route)), tuple(route)


def route_of(inst: Instance, cluster, hint=None) -> tuple[float, tuple[int, ...]]:
    """Kürzeste Rundreise des Clusters: exakt bis EXACT_MAX Kunden, sonst die Heuristik ab `hint` (Voreinstellung: die Reihenfolge von `cluster`)."""
    if len(cluster) <= EXACT_MAX:
        return tsp_exact(inst, cluster)
    return tsp_heuristic(inst, cluster, hint)


def with_routing(inst: Instance, clusters) -> Plan:
    """Jedes Cluster als kürzeste Rundreise (Winkelfolge als Startfolge der Heuristik)."""
    routes, total = [], 0.0
    for cl in clusters:
        c, r = route_of(inst, cl, cl)
        total += c
        routes.append(r)
    return Plan(total, tuple(routes))


def reoptimize(inst: Instance, routes) -> Plan:
    """Jede Route eines fremden Plans (Savings, Einfügen nach Split) mit derselben Regel neu als kürzeste Rundreise (Startfolge: die vorhandene Route)."""
    return with_routing(inst, [list(r) for r in routes])
