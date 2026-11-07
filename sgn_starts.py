"""Die Startpläne der Wahl: zwei Zufallsstarts und vier Konstruktionen der Linie (Stück 2 bis 6)."""

import random

import sgn_algorithm as A
import sgn_constants as C
import sgn_construct as K
import sgn_ls as L
import sgn_routing as W
import sgn_savings as S
from sgn_scenario import Instance


def random_start_order(n: int, seed: int, k: int) -> list[int]:
    """Die k-te Zufallsfolge zu einem Seed (für die Mehrfachstarts): `sample` aus Random(seed * 7 + k)."""
    return random.Random(seed * 7 + k).sample(range(1, n + 1), n)


def random_start_plan(P: L.Prob, seed: int, k: int):
    """Plan eines Zufallsstarts: die k-te Zufallsfolge, optimal zerlegt."""
    return L.split(P, random_start_order(P.n, seed, k))[1]


def build_start(inst: Instance, P: L.Prob, key: str, seed: int) -> list[list[int]]:
    """Startplan als Liste von Routen. RS: Zufallsfolge (Random(seed)) + Split; RF: Zufallsfolge (Random(seed + 1)) + Füllen bis voll; ES: Einfügen nach Split; SAV: Savings mit λ = 1;
    SAVR: Savings mit Rundreise je Route; L9R: das beste von neun λ-Werten, jede Route neu als kürzeste Rundreise."""
    if key == "RS":
        return L.split(P, L.random_order(inst.n, seed))[1]
    if key == "RF":
        return L.next_fit(P, L.random_order(inst.n, seed + 1))
    if key == "ES":
        return [list(r) for r in A.split(inst, K.insert_split_order(inst)).routes]
    sav = S.savings_routes(inst)
    if key == "SAV":
        return [list(r) for r in sav]
    if key == "SAVR":
        return [list(r) for r in W.reoptimize(inst, sav).routes]
    if key == "L9R":
        best = min((W.reoptimize(inst, S.savings_routes(inst, S.Params(lam))) for lam in C.LAMS), key=lambda p: p.cost)
        return [list(r) for r in best.routes]
    raise ValueError(f"unbekannter Startplan {key!r}")
