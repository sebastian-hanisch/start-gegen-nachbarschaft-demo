"""Formate, Live-Rechnung, Bänder und Verdikte. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import json
import statistics as st
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import sgn_algorithm as A
import sgn_constants as C
import sgn_ls as L
import sgn_routing as W
import sgn_starts as T
from sgn_scenario import Instance, make_instance


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    family: int = C.DEFAULT_FAMILY
    depot: int = C.DEFAULT_DEPOT
    routes: int = C.DEFAULT_ROUTES
    fill: int = C.DEFAULT_FILL
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Choice:
    """Startplan (Index in C.START_KEYS) und Nachbarschaft (Index in C.NEIGH_KEYS)."""
    start: int = C.DEFAULT_START
    neigh: int = C.DEFAULT_NEIGH

    @property
    def start_key(self) -> str:
        return C.START_KEYS[self.start]

    @property
    def neigh_key(self) -> str:
        return C.NEIGH_KEYS[self.neigh]


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def signed_pct(x: float, digits: int = 1) -> str:
    """Mit Vorzeichen (echtes Minus); -0,0 wird zu 0,0."""
    text = de(abs(x), digits)
    if float(text.replace(",", ".")) == 0.0:
        return f"{text} %"
    return f"{'+' if x > 0 else '−'}{text} %"


def seconds_text(t: float) -> str:
    """Zeit als Größenordnung: Millisekunden unter 0,1 s, sonst Sekunden mit sinnvoller Stellenzahl."""
    if t < 0.1:
        return f"{de(t * 1000, 1 if t < 0.01 else 0)} ms"
    if t < 10:
        return f"{de(t, 2 if t < 1 else 1)} s"
    return f"{de(t, 0)} s"


def routes_word(k: int) -> str:
    return f"{k} Route" if k == 1 else f"{k} Routen"


def moves_word(k: int) -> str:
    return "1 Zug" if k == 1 else f"{k} Zügen"


def instances_word(k: int) -> str:
    return f"{k} Instanz" if k == 1 else f"{k} Instanzen"


def gap_percent(cost: float, reference: float) -> float:
    if reference <= 0 or abs(cost - reference) <= C.TOL:
        return 0.0
    return 100.0 * (cost - reference) / reference


def routes_text(routes) -> str:
    return " ‖ ".join("(" + " ".join(str(c) for c in r) + ")" for r in routes)


def start_name(key: str) -> str:
    return C.STARTS[key][0]


def neigh_name(key: str) -> str:
    return C.NEIGH[key][0]


# ----------------------------------------------------------------------------------------------------------------------------------- Live

def hand_instance() -> Instance:
    return Instance(C.HAND_XY, C.HAND_DEMAND, C.HAND_CAPACITY)


def build_instance(s: Settings) -> Instance:
    if s.family == C.HAND_FAMILY:
        return hand_instance()
    return make_instance(s.n, s.family, s.depot, s.routes, s.seed, s.fill)


def live_starts(n: int) -> list[str]:
    return [k for k in C.START_KEYS if k != "ES" or n <= C.ES_MAX_N]


@dataclass(frozen=True, eq=False)
class LiveCell:
    cost: float
    moves: int
    seconds: float


@dataclass(frozen=True, eq=False)
class Live:
    """Alle Startpläne mit allen Nachbarschaften auf einer Instanz (höchstens LIVE_N_MAX Kunden) und die Mehrfachstarts."""
    inst: Instance
    start_cost: dict          # Startplan -> Kosten des Startplans
    start_routes: dict        # Startplan -> Routen
    cells: dict               # (Startplan, Nachbarschaft) -> LiveCell
    rand: list                # Kosten der Zufallsstarts nach Lokalsuche mit allen Zügen (Reihenfolge der Starts)
    exact: float | None       # exaktes Optimum bis EXACT_MAX Kunden

    @property
    def reference(self) -> float:
        """Das exakte Optimum oder, darüber, der beste Wert dieser Seite (kein Beweis)."""
        if self.exact is not None:
            return self.exact
        return min([c.cost for c in self.cells.values()] + list(self.rand) + list(self.start_cost.values()))

    def regret(self, cost: float) -> float:
        return gap_percent(cost, self.reference)


def live_matrix(s: Settings) -> Live:
    inst = build_instance(s)
    if inst.n > C.LIVE_N_MAX:
        raise ValueError(f"live nur bis {C.LIVE_N_MAX} Kunden")
    P = L.Prob(inst)
    start_cost, start_routes, cells = {}, {}, {}
    for key in live_starts(inst.n):
        routes = T.build_start(inst, P, key, s.seed)
        start_routes[key] = tuple(tuple(r) for r in routes)
        start_cost[key] = L.plan_len(P, routes)
        for nk, (_, moves) in C.NEIGH.items():
            t = time.perf_counter()
            cost, _, k = L.local_search(P, routes, set(moves))
            cells[(key, nk)] = LiveCell(cost, k, time.perf_counter() - t)
    rand = [L.local_search(P, T.random_start_plan(P, s.seed, k), set(C.NEIGH["alle"][1]))[0] for k in range(C.RANDOM_STARTS)]
    exact = A.exact_cvrp(inst).cost if inst.n <= C.EXACT_MAX else None
    return Live(inst, start_cost, start_routes, cells, rand, exact)


@dataclass(frozen=True, eq=False)
class Run:
    """Eine Lokalsuche Zug für Zug: Startplan, Zugfolge, Endplan."""
    inst: Instance
    start: tuple
    start_cost: float
    steps: list
    final: tuple
    final_cost: float


def run_trace(s: Settings, ch: Choice) -> Run:
    inst = build_instance(s)
    P = L.Prob(inst)
    routes = T.build_start(inst, P, ch.start_key, s.seed)
    trace: list = []
    cost, final, _ = L.local_search(P, routes, set(C.NEIGH[ch.neigh_key][1]), trace)
    return Run(inst, tuple(tuple(r) for r in routes), L.plan_len(P, routes), trace, tuple(tuple(r) for r in final), cost)


def best_of_first(costs, k: int) -> float:
    """Das Beste der ersten k Zufallsstarts."""
    return min(costs[:k])


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

@lru_cache(maxsize=1)
def load_bands() -> dict:
    path = Path(__file__).with_name(C.BAND_FILE)
    if not path.exists():
        return {"meta": {}, "rows": [], "times": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def band_rows(n: int, which: str = "fest") -> list[dict]:
    return [r for r in load_bands()["rows"] if r["n"] == n and r["set"] == which]


def row_best(row: dict) -> float:
    """Bester Wert auf der Instanz: Minimum über die Referenz, die Verfahren der Stücke 4 bis 11, alle Lokalsuchen und die Zufallsstarts."""
    vals = [row["ref"], row["other"]] + list(row["rand"])
    for entry in row["starts"].values():
        vals += list(entry["ls"].values())
    return min(vals)


def row_regret(row: dict, cost: float) -> float:
    return gap_percent(cost, row_best(row))


def band_starts(n: int) -> list[str]:
    return live_starts(n)


def band_stats(n: int, which: str = "fest") -> dict:
    """Mittleres Bedauern je (Startplan, Nachbarschaft), je Startplan vor der Lokalsuche, der Zufallsstarts (1, 5, 20) und die Spannweiten; leer, wenn es keine Zeilen gibt."""
    rows = band_rows(n, which)
    if not rows:
        return {}
    keys = band_starts(n)
    cell = {k: {nk: [] for nk in C.NEIGH_KEYS} for k in keys}
    start = {k: [] for k in keys}
    for r in rows:
        for k in keys:
            start[k].append(row_regret(r, r["starts"][k]["start"]))
            for nk in C.NEIGH_KEYS:
                cell[k][nk].append(row_regret(r, r["starts"][k]["ls"][nk]))
    mean = {k: {nk: st.mean(v) for nk, v in d.items()} for k, d in cell.items()}
    rand = {k: st.mean(row_regret(r, min(r["rand"][:k])) for r in rows) for k in (1, 5, C.RANDOM_STARTS)}
    row_marg = {k: st.mean(mean[k].values()) for k in keys}
    col_marg = {nk: st.mean(mean[k][nk] for k in keys) for nk in C.NEIGH_KEYS}
    alle = {k: mean[k]["alle"] for k in keys}
    out = {"count": len(rows), "keys": keys, "mean": mean, "start": {k: st.mean(v) for k, v in start.items()}, "rand": rand, "cells": cell,
           "row_marginal": row_marg, "col_marginal": col_marg, "start_span_alle": max(alle.values()) - min(alle.values()),
           "neigh_span": {k: max(mean[k].values()) - min(mean[k].values()) for k in keys}, "neigh_span_total": max(col_marg.values()) - min(col_marg.values()),
           "start_span_total": max(row_marg.values()) - min(row_marg.values())}
    out["best_construction"] = min((k for k in keys if C.STARTS[k][1] == "Konstruktion"), key=lambda k: alle[k])
    return out


def band_paired(n: int, a: str, b: str, neigh: str = "alle", which: str = "fest") -> tuple[int, int, int]:
    """Gepaart nach dem Bedauern nach der Lokalsuche: Startplan a billiger / gleich / teurer als Startplan b (Gleichheit bis 1e-9)."""
    better = equal = worse = 0
    for r in band_rows(n, which):
        d = r["starts"][a]["ls"][neigh] - r["starts"][b]["ls"][neigh]
        if d < -C.TOL:
            better += 1
        elif d > C.TOL:
            worse += 1
        else:
            equal += 1
    return better, equal, worse


def band_times(n: int) -> dict:
    return load_bands()["times"].get(str(n), {})


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_run(run: Run, ch: Choice, ref: float) -> tuple[str, str]:
    """Eine Lokalsuche: Gewinn, Zugarten, Abstand zur Referenz."""
    gain = 100.0 * (run.start_cost - run.final_cost) / run.start_cost if run.start_cost > 0 else 0.0
    if not run.steps:
        return "info", (f"Aus {start_name(ch.start_key)} ({de(run.start_cost)}) findet die Lokalsuche ({neigh_name(ch.neigh_key)}) keinen verbessernden Zug: der Plan ist schon ein lokales Optimum "
                        f"({signed_pct(gap_percent(run.start_cost, ref))} gegen die Referenz).")
    kinds = {}
    for stp in run.steps:
        kinds[stp["kind"]] = kinds.get(stp["kind"], 0) + 1
    kind_text = ", ".join(f"{name} {k}" for name, k in sorted(kinds.items()))
    gap = gap_percent(run.final_cost, ref)
    text = (f"Aus {start_name(ch.start_key)} ({de(run.start_cost)}) bringt die Lokalsuche ({neigh_name(ch.neigh_key)}) den Plan in {moves_word(len(run.steps))} ({kind_text}) auf {de(run.final_cost)}: "
            f"{pct(gain)} kürzer als der Start, {signed_pct(gap)} gegen die Referenz.")
    return ("success" if gap <= C.LEVEL_PP else "info"), text


def verdict_live(live: Live, ch: Choice) -> tuple[str, str]:
    """Die Instanz: wie viel hängt vom Start, wie viel von der Nachbarschaft ab (Spannweiten des mittleren Bedauerns über die Zeilen und Spalten der Seite)."""
    keys = list(live.start_cost)
    reg = {(k, nk): live.regret(live.cells[(k, nk)].cost) for k in keys for nk in C.NEIGH_KEYS}
    alle = {k: reg[(k, "alle")] for k in keys}
    best_start = min(keys, key=lambda k: alle[k])
    worst_start = max(keys, key=lambda k: alle[k])
    zz = {nk: reg[("RS", nk)] for nk in C.NEIGH_KEYS}
    good = best_start
    gz = {nk: reg[(good, nk)] for nk in C.NEIGH_KEYS}
    text = (f"Mit allen Zügen liegen die Startpläne zwischen {pct(alle[best_start])} ({start_name(best_start)}) und {pct(alle[worst_start])} ({start_name(worst_start)}) über der Referenz ({de(live.reference)}). "
            f"Aus der Zufallsfolge reichen die Nachbarschaften von {pct(min(zz.values()))} bis {pct(max(zz.values()))}, aus {start_name(good)} nur von {pct(min(gz.values()))} bis {pct(max(gz.values()))}.")
    spread_start = max(alle.values()) - min(alle.values())
    spread_neigh = max(gz.values()) - min(gz.values())
    return ("success" if spread_start > spread_neigh else "info"), text


def verdict_random(live: Live, k: int) -> tuple[str, str]:
    """k Zufallsstarts mit Lokalsuche gegen Savings und bestes von 9 λ mit Rundreise (je mit allen Zügen)."""
    best_rand = best_of_first(live.rand, k)
    sav = live.cells[("SAV", "alle")].cost
    l9r = live.cells[("L9R", "alle")].cost
    better = "schlägt" if best_rand < sav - C.TOL else ("gleicht" if abs(best_rand - sav) <= C.TOL else "verliert gegen")
    text = (f"Das beste von {k} Zufallsstarts mit Lokalsuche kostet {de(best_rand)} ({signed_pct(live.regret(best_rand))} gegen die Referenz) und {better} Savings mit Lokalsuche ({de(sav)}, {signed_pct(live.regret(sav))}); "
            f"das beste von 9 λ mit Rundreise und Lokalsuche kostet {de(l9r)} ({signed_pct(live.regret(l9r))}).")
    return ("warning" if best_rand > sav + C.TOL else "success"), text


def verdict_bands(n: int, which: str = "fest") -> tuple[str, str]:
    stats = band_stats(n, which)
    if not stats:
        return "warning", "Für diese Größe gibt es keine Zeilen in den Bändern."
    mean = stats["mean"]
    good = stats["best_construction"]
    from_rs = {nk: mean["RS"][nk] for nk in C.NEIGH_KEYS}
    from_good = {nk: mean[good][nk] for nk in C.NEIGH_KEYS}
    text = (f"Bei {n} Kunden ({instances_word(stats['count'])}, {'feste' if which == 'fest' else 'frische'} Menge): Mit allen Zügen liegen die Startpläne um {de(stats['start_span_alle'])} Prozentpunkte auseinander "
            f"({pct(mean[good]['alle'])} für {start_name(good)}, {pct(mean['RS']['alle'])} für die Zufallsfolge). Aus der Zufallsfolge ändert die Nachbarschaft das Bedauern um {de(max(from_rs.values()) - min(from_rs.values()), 1)} Prozentpunkte, "
            f"aus {start_name(good)} um {de(max(from_good.values()) - min(from_good.values()), 1)}. Ein Lauf je Start und Nachbarschaft; Referenz bis {C.EXACT_MAX} Kunden exakt, darüber PyVRP (keine Untergrenze).")
    return ("success" if stats["start_span_alle"] > max(from_good.values()) - min(from_good.values()) else "info"), text
