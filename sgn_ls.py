"""Lokalsuche mit einzeln schaltbaren Zügen (Stück 7 der Linie Tourenbildung).

Züge: 2-opt (eine Route: ein Stück umkehren), Verschieben (ein Kunde an eine bessere Stelle, auch in eine andere Route; Ziele: die acht nächsten Kunden), Tauschen (zwei Kunden aus verschiedenen Routen).
Erste Verbesserung: jeder Durchgang geht die Züge der Reihe 2-opt, Verschieben, Tauschen durch und führt jeden verbessernden Zug sofort aus; es endet, wenn ein Durchgang nichts findet (höchstens
MAX_ROUNDS Durchgänge). Alle Gleichstände und Schwellen: ein Zug zählt nur bei einem Gewinn von mehr als 1e-10. Die Instanz liegt als Listen vor (schneller als numpy im inneren Schleifenwerk)."""

import math
import random

import sgn_constants as C
from sgn_scenario import Instance, distance_matrix

INF = math.inf
MAX_ROUNDS = 100
EPS = 1e-10


class Prob:
    def __init__(self, inst: Instance):
        self.inst = inst
        self.n = inst.n
        self.D = [list(map(float, row)) for row in distance_matrix(inst)]
        self.dem = [0] + list(inst.demand)
        self.Q = inst.capacity
        self.near = [[]] + [sorted((c for c in range(1, self.n + 1) if c != u), key=lambda c: (self.D[u][c], c))[:C.NEIGHBORS] for u in range(1, self.n + 1)]


def route_len(P: Prob, r) -> float:
    if not r:
        return 0.0
    D = P.D
    return D[0][r[0]] + sum(D[a][b] for a, b in zip(r, r[1:])) + D[r[-1]][0]


def plan_len(P: Prob, routes) -> float:
    return sum(route_len(P, r) for r in routes)


def split(P: Prob, order):
    """Optimaler Split (Prins): kürzester Weg im Hilfsgraphen. Rückgabe (Kosten, Routen)."""
    n, D, dem, Q = P.n, P.D, P.dem, P.Q
    best = [INF] * (n + 1)
    pred = [0] * (n + 1)
    best[0] = 0.0
    for i in range(n):
        bi = best[i]
        load, inner = 0, 0.0
        for j in range(i, n):
            c = order[j]
            load += dem[c]
            if load > Q:
                break
            inner = D[0][c] if j == i else inner + D[order[j - 1]][c]
            v = bi + inner + D[c][0]
            if v < best[j + 1] - 1e-12:
                best[j + 1] = v
                pred[j + 1] = i
    routes, node = [], n
    while node > 0:
        routes.append(list(order[pred[node]:node]))
        node = pred[node]
    routes.reverse()
    return best[n], routes


def next_fit(P: Prob, order):
    """„Füllen bis voll“ nach der Last (Stück 3): eine neue Route beginnt, sobald der nächste Kunde nicht mehr passt."""
    out, cur, load = [], [], 0
    for c in order:
        if cur and load + P.dem[c] > P.Q:
            out.append(cur)
            cur, load = [], 0
        cur.append(c)
        load += P.dem[c]
    return out + ([cur] if cur else [])


def is_valid_plan(P: Prob, routes) -> bool:
    """Unabhängiger Prüfer: jeder Kunde genau einmal, keine Route über der Kapazität."""
    seen = sorted(c for r in routes for c in r)
    return seen == list(range(1, P.n + 1)) and all(sum(P.dem[c] for c in r) <= P.Q for r in routes)


def random_order(n: int, seed: int) -> list[int]:
    order = list(range(1, n + 1))
    random.Random(seed).shuffle(order)
    return order


def local_search(P: Prob, routes, moves, trace=None):
    """Erste Verbesserung mit den Zügen aus `moves` (Teilmenge von {"2opt", "move", "swap"}). Rückgabe (Kosten, Routen, Zahl der Züge). `trace`: eine Liste, an die je Zug ein Wörterbuch
    (Art, Kunden, Gewinn, Kosten danach, Routen danach) angehängt wird."""
    D, dem, Q = P.D, P.dem, P.Q
    routes = [list(r) for r in routes if r]
    load = [sum(dem[c] for c in r) for r in routes]
    where = {}
    cost = [plan_len(P, routes)]
    nmoves = [0]

    def reindex(ri):
        for pi, c in enumerate(routes[ri]):
            where[c] = (ri, pi)

    def note(kind, customers, delta):
        cost[0] += delta
        nmoves[0] += 1
        if trace is not None:
            trace.append({"kind": kind, "customers": tuple(customers), "gain": -delta, "cost": cost[0], "routes": tuple(tuple(r) for r in routes if r)})

    for ri in range(len(routes)):
        reindex(ri)
    for _ in range(MAX_ROUNDS):
        improved = False
        if "2opt" in moves:
            for ri, r in enumerate(routes):
                m = len(r)
                if m < 2:
                    continue
                path = [0] + r + [0]
                done = False
                while not done:
                    done = True
                    for i in range(1, m):
                        for j in range(i + 1, m + 1):
                            a, b, c, d = path[i - 1], path[i], path[j], path[j + 1]
                            delta = D[a][c] + D[b][d] - D[a][b] - D[c][d]
                            if delta < -EPS:
                                path[i:j + 1] = path[i:j + 1][::-1]
                                routes[ri] = path[1:-1]
                                note("2-opt", (b, c), delta)
                                done = False
                                improved = True
                routes[ri] = path[1:-1]
                reindex(ri)
        if "move" in moves:
            for u in range(1, P.n + 1):
                ru, pu = where[u]
                r = routes[ru]
                pa = r[pu - 1] if pu > 0 else 0
                nb = r[pu + 1] if pu + 1 < len(r) else 0
                gain = D[pa][u] + D[u][nb] - D[pa][nb]
                done = False
                for v in P.near[u]:
                    rv, pv = where[v]
                    if rv != ru and load[rv] + dem[u] > Q:
                        continue
                    for after in (True, False):
                        if rv == ru:
                            rest = r[:pu] + r[pu + 1:]
                            pos = rest.index(v) + (1 if after else 0)
                            a = rest[pos - 1] if pos > 0 else 0
                            b = rest[pos] if pos < len(rest) else 0
                            delta = D[a][u] + D[u][b] - D[a][b] - gain
                            if delta < -EPS:
                                rest.insert(pos, u)
                                routes[ru] = rest
                                reindex(ru)
                                note("Verschieben", (u,), delta)
                                done = True
                        else:
                            t = routes[rv]
                            pos = pv + (1 if after else 0)
                            a = t[pos - 1] if pos > 0 else 0
                            b = t[pos] if pos < len(t) else 0
                            delta = D[a][u] + D[u][b] - D[a][b] - gain
                            if delta < -EPS:
                                r.pop(pu)
                                t.insert(pos, u)
                                load[ru] -= dem[u]
                                load[rv] += dem[u]
                                reindex(ru)
                                reindex(rv)
                                note("Verschieben", (u,), delta)
                                done = True
                        if done:
                            break
                    if done:
                        break
                if done:
                    improved = True
        if "swap" in moves:
            for u in range(1, P.n + 1):
                ru, pu = where[u]
                for v in P.near[u]:
                    rv, pv = where[v]
                    if rv == ru or load[ru] - dem[u] + dem[v] > Q or load[rv] - dem[v] + dem[u] > Q:
                        continue
                    r, t = routes[ru], routes[rv]
                    a1, b1 = (r[pu - 1] if pu > 0 else 0), (r[pu + 1] if pu + 1 < len(r) else 0)
                    a2, b2 = (t[pv - 1] if pv > 0 else 0), (t[pv + 1] if pv + 1 < len(t) else 0)
                    delta = D[a1][v] + D[v][b1] - D[a1][u] - D[u][b1] + D[a2][u] + D[u][b2] - D[a2][v] - D[v][b2]
                    if delta < -EPS:
                        r[pu], t[pv] = v, u
                        load[ru] += dem[v] - dem[u]
                        load[rv] += dem[u] - dem[v]
                        reindex(ru)
                        reindex(rv)
                        note("Tauschen", (u, v), delta)
                        improved = True
                        break
        if not improved:
            break
    final = [r for r in routes if r]
    return plan_len(P, final), final, nmoves[0]
