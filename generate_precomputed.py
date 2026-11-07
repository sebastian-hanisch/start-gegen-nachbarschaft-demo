"""Erzeugt sgn_bands.json: die Bänder der Messung „Start gegen Nachbarschaft“ (Stück 7 der Linie Tourenbildung).

Instanzen, Referenzen und die Kosten der Verfahren der Stücke 4 bis 11 kommen aus tvw_bands.json der Nachbarordner `tourenbildung-verfahrenswahl-demo` (Stück 15): die 60 festen Instanzen
(n = 12: 20, 25: 16, 50: 16, 100: 8) und die frischen (Seeds ab 200000) bei 25 und 50 Kunden (je 8). Je Instanz rechnet dieses Skript sechs Startpläne (zwei Zufallsstarts, Einfügen nach Split
bis 50 Kunden, Savings, Savings mit Rundreise, bestes von 9 λ mit Rundreise), jeden mit sechs Nachbarschaften (Lokalsuche mit erster Verbesserung, Züge einzeln schaltbar) und 20 Zufallsstarts mit allen Zügen.
Die Zeiten (Bauzeit je Start, Lokalsuche je Start) werden einzeln gemessen (Median über wenige Instanzen je Größe, Zwischenspeicher der Rundreisen vor jeder Messung geleert, höchstens vier Prozesse)
und sind Größenordnungen dieser Maschine; kein Test misst eine Zeit.

Aufruf (Reihenfolge):
    python generate_precomputed.py rows       # Zeilen (parallel, 12 Prozesse)
    python generate_precomputed.py times      # Zeiten (4 Prozesse)
    python generate_precomputed.py merge      # zu sgn_bands.json zusammenführen"""

import argparse
import json
import statistics as st
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import sgn_constants as C
import sgn_ls as L
import sgn_routing as W
import sgn_starts as T
from sgn_scenario import make_instance

HERE = Path(__file__).resolve().parent
TARGET = HERE / C.BAND_FILE
SOURCE = HERE.parent / "tourenbildung-verfahrenswahl-demo" / C.SOURCE_BANDS
TIME_INSTANCES = {12: 4, 25: 4, 50: 3, 100: 2}


def source_rows() -> list[dict]:
    rows = json.loads(SOURCE.read_text(encoding="utf-8"))["cvrp"]
    return [r for r in rows if r["set"] == "fest" or (r["set"] == "frisch" and r["n"] in C.FRESH_SIZES)]


def starts_of(n: int):
    return [k for k in C.START_KEYS if k != "ES" or n <= C.ES_MAX_N]


def row_job(src: dict) -> dict:
    n, seed = src["n"], src["seed"]
    inst = make_instance(n, src["family"], src["depot"], C.BAND_ROUTES, seed, C.BAND_FILL)
    P = L.Prob(inst)
    starts = {}
    for key in starts_of(n):
        routes = T.build_start(inst, P, key, seed)
        assert L.is_valid_plan(P, routes)
        entry = {"start": L.plan_len(P, routes), "ls": {}, "moves": {}}
        for nk, (_, moves) in C.NEIGH.items():
            cost, rr, k = L.local_search(P, routes, set(moves))
            assert L.is_valid_plan(P, rr)
            entry["ls"][nk], entry["moves"][nk] = cost, k
        starts[key] = entry
    rand = []
    for k in range(C.RANDOM_STARTS):
        routes = T.random_start_plan(P, seed, k)
        rand.append(L.local_search(P, routes, set(C.NEIGH["alle"][1]))[0])
    print("rows", n, src["set"], src["family"], src["depot"], seed, flush=True)
    return {"set": src["set"], "n": n, "family": src["family"], "depot": src["depot"], "seed": seed, "ref": src["ref"], "ref_kind": src["ref_kind"], "other": min(src["costs"].values()),
            "starts": starts, "rand": rand}


def time_job(args) -> dict:
    n, family, depot, seed = args
    inst = make_instance(n, family, depot, C.BAND_ROUTES, seed, C.BAND_FILL)
    P = L.Prob(inst)
    build, ls_all, ls_2opt = {}, {}, {}
    for key in starts_of(n):
        W._tsp_exact.cache_clear()            # jede Messung allein: der Zwischenspeicher der Rundreisen würde sonst spätere Startpläne begünstigen
        t = time.perf_counter()
        routes = T.build_start(inst, P, key, seed)
        build[key] = time.perf_counter() - t
        t = time.perf_counter()
        L.local_search(P, routes, set(C.NEIGH["alle"][1]))
        ls_all[key] = time.perf_counter() - t
        t = time.perf_counter()
        L.local_search(P, routes, {"2opt"})
        ls_2opt[key] = time.perf_counter() - t
    t = time.perf_counter()
    for k in range(C.RANDOM_STARTS):
        L.local_search(P, T.random_start_plan(P, seed, k), set(C.NEIGH["alle"][1]))
    rand_time = (time.perf_counter() - t) / C.RANDOM_STARTS
    print("times", n, seed, flush=True)
    return {"n": n, "build": build, "ls_alle": ls_all, "ls_2opt": ls_2opt, "rand_start_ls": rand_time}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["rows", "times", "merge"])
    args = ap.parse_args()
    parts = HERE / "parts"
    parts.mkdir(exist_ok=True)
    if args.kind == "rows":
        with ProcessPoolExecutor(max_workers=12) as pool:
            rows = list(pool.map(row_job, source_rows()))
        (parts / "rows.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    elif args.kind == "times":
        jobs = []
        for n in C.BAND_SIZES:
            fest = [r for r in source_rows() if r["set"] == "fest" and r["n"] == n]
            step = max(1, len(fest) // TIME_INSTANCES[n])
            jobs += [(n, r["family"], r["depot"], r["seed"]) for r in fest[::step][:TIME_INSTANCES[n]]]
        with ProcessPoolExecutor(max_workers=4) as pool:
            res = list(pool.map(time_job, jobs))
        (parts / "times.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    else:
        rows = json.loads((parts / "rows.json").read_text(encoding="utf-8"))
        res = json.loads((parts / "times.json").read_text(encoding="utf-8"))
        times = {}
        for n in C.BAND_SIZES:
            jobs = [j for j in res if j["n"] == n]
            times[str(n)] = {"build": {k: round(st.median(j["build"][k] for j in jobs), 5) for k in jobs[0]["build"]},
                             "ls_alle": {k: round(st.median(j["ls_alle"][k] for j in jobs), 5) for k in jobs[0]["ls_alle"]},
                             "ls_2opt": {k: round(st.median(j["ls_2opt"][k] for j in jobs), 5) for k in jobs[0]["ls_2opt"]},
                             "rand_start_ls": round(st.median(j["rand_start_ls"] for j in jobs), 5)}
        meta = {"counts": {s: {str(n): sum(1 for r in rows if r["set"] == s and r["n"] == n) for n in C.BAND_SIZES} for s in C.BAND_SETS},
                "time_instances": {str(n): v for n, v in TIME_INSTANCES.items()}, "random_starts": C.RANDOM_STARTS, "neighbors": C.NEIGHBORS,
                "source": "Instanzen, Referenzen und Kosten der Verfahren aus tvw_bands.json (tourenbildung-verfahrenswahl-demo, Stück 15); Startpläne, Lokalsuche und Zeiten mit den Kernen dieser Demo"}
        TARGET.write_text(json.dumps({"meta": meta, "rows": rows, "times": times}, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", TARGET.name, len(rows), "Zeilen")


if __name__ == "__main__":
    main()
