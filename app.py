"""Start gegen Nachbarschaft - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 7 (gelb) der Reihe „Tourenbildung“: Zählt bei der Lokalsuche an einem kapazitierten Tourenplan die Startlösung oder die Nachbarschaft? Die Demo startet die Lokalsuche aus zwei Zufallsplänen und vier Konstruktionen
der Reihe (Einfügen nach Split, Savings, Savings mit Rundreise, bestes von 9 λ mit Rundreise) mit je sechs Nachbarschaften (2-opt, Verschieben, Tauschen und ihre Kombinationen) und zeigt Zug für Zug, was sie tut.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import sgn_constants as C
from sgn_evaluation import (
    Choice,
    Settings,
    band_paired,
    band_stats,
    band_times,
    best_of_first,
    build_instance,
    de,
    gap_percent,
    instances_word,
    live_matrix,
    neigh_name,
    pct,
    routes_text,
    routes_word,
    run_trace,
    seconds_text,
    signed_pct,
    start_name,
    verdict_bands,
    verdict_live,
    verdict_random,
    verdict_run,
)
from sgn_layout import dunkles_design, kopf_css
from sgn_pdf_export import build_pdf
from sgn_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from sgn_visualization import build_gain, build_heatmap, build_map

st.set_page_config(page_title="Start gegen Nachbarschaft – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _live(settings):
    return live_matrix(settings)


@st.cache_data(show_spinner=False)
def _trace(settings, choice):
    return run_trace(settings, choice)


def size_class(n: int) -> int:
    for size in C.BAND_SIZES[:-1]:
        if n <= size:
            return size
    return C.BAND_SIZES[-1]


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in sgn_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Start gegen Nachbarschaft")
st.markdown(
    """
**Zählt der Startplan oder die Nachbarschaft?** Eine **Lokalsuche** verbessert einen Tourenplan Zug für Zug: **2-opt** kehrt ein Stück einer Route um, **Verschieben** setzt einen Kunden an eine bessere Stelle (auch in eine andere Route),
**Tauschen** vertauscht zwei Kunden aus verschiedenen Routen. Die Demo startet sie aus zwei **Zufallsplänen** und vier **Konstruktionen** der Reihe (Einfügen nach Split, Savings, Savings mit Rundreise, bestes von 9 λ mit Rundreise)
mit je sechs **Nachbarschaften** und misst den Abstand zum besten Wert. Die Hill-Climbing-Faustregel „die Nachbarschaft zählt mehr als der Start“ stimmt in diesen Messungen nur für schlechte Startpläne.

Weiter unten: **🔬 Eine Lokalsuche Zug für Zug**, **🔬 Start × Nachbarschaft**, **🔬 Wie viel holt die Lokalsuche heraus?**, **🔬 Mehrfachstart gegen guten Start**, **🚧 Wo die Annahmen enden**,
der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So wird gemessen", expanded=True):
    st.markdown(
        """
1. **Startpläne:** Zufallsfolge mit optimalem Split, Zufallsfolge mit „Füllen bis voll“, Einfügen nach Split, Savings (λ = 1), Savings mit kürzester Rundreise je Route, das beste von neun λ-Werten mit Rundreise.
2. **Lokalsuche:** erste Verbesserung; jeder Durchgang geht 2-opt, Verschieben, Tauschen durch und führt jeden verbessernden Zug sofort aus; er endet in einem lokalen Optimum. Verschieben und Tauschen sehen die acht nächsten Kunden.
3. **Bedauern:** Abstand zum besten Wert auf der Instanz (Referenz, Verfahren der Stücke 4 bis 11, alle Lokalsuchen), in Prozent; im Mittel über die Instanzen einer Größe.
4. **Zeiten** sind Größenordnungen einer Einzelmessung in Python; sie stehen in den Bändern und werden nie nachgerechnet.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Lokalsuche**")
    start = st.selectbox("Startplan", list(range(len(C.START_KEYS))), key="start_select", format_func=lambda i: C.STARTS[C.START_KEYS[i]][0],
                         help="Womit die Lokalsuche beginnt. Einfügen nach Split gibt es live bis 50 Kunden.")
    neigh = st.selectbox("Nachbarschaft", list(range(len(C.NEIGH_KEYS))), key="neigh_select", format_func=lambda i: C.NEIGH[C.NEIGH_KEYS[i]][0],
                         help="Welche Züge die Lokalsuche ausführen darf: 2-opt, Verschieben, Tauschen oder eine Kombination.")
    st.markdown("**Instanz**")
    family = st.selectbox("Art der Karte", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="„Handinstanz“: die Instanz der Stücke 1 bis 4 (6 Kunden, Kapazität 7). „Kleine Karte“: ganze Koordinaten 0 bis 16, Nachfragen 1 bis 4. Die beiden anderen: Karte 0 bis 100, Nachfragen 1 bis 10; „In Gruppen“: drei Häufungen von Kunden.")
    hand = int(family) == C.HAND_FAMILY
    if hand:
        st.caption("Bei der Handinstanz gelten Kunden, Depot, Zielroutenzahl und Auslastung nicht (n = 6); der Seed legt nur den Zufall der Zufallsstarts fest.")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help=f"Live gerechnet wird bis n = {C.LIVE_N_MAX}; darüber zeigt die Seite die vorberechneten Bänder (Größenklassen 12, 25, 50, 100). Bei der Handinstanz gilt n = 6.")
    depot = st.selectbox("Lage des Depots", list(range(len(C.DEPOTS))), key="depot_select", format_func=lambda i: C.DEPOTS[i])
    routes = st.slider("Zielroutenzahl", *bounds("routes_slider"), key="routes_slider", help="Legt zusammen mit der Auslastung die Kapazität fest.")
    fill = st.slider("Auslastung (%)", *bounds("fill_slider"), step=C.FILL_STEP, key="fill_slider", help="Kapazität = aufgerundet Gesamtnachfrage geteilt durch (Zielroutenzahl mal Auslastung).")
    seed = st.number_input("Zufalls-Seed der Instanz und der Zufallsstarts", *bounds("seed_input"), key="seed_input", step=1, help="Der Seed legt die Instanz fest (außer bei der Handinstanz) und die Zufallsstarts.")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "family_select": int(family), "depot_select": int(depot), "routes_slider": int(routes), "fill_slider": int(fill), "seed_input": int(seed),
                   "start_select": int(start), "neigh_select": int(neigh)})

settings = Settings(int(n), int(family), int(depot), int(routes), int(fill), int(seed))
choice = Choice(int(start), int(neigh))
inst = build_instance(settings)
live_ok = inst.n <= C.LIVE_N_MAX
live = _live(settings) if live_ok else None
size = size_class(inst.n)
if live_ok and choice.start_key not in live.start_cost:
    choice = Choice(0, choice.neigh)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: eine Lokalsuche aus einem Startplan")
if live_ok:
    run = _trace(settings, choice)
    ref = live.reference
    gain = 100.0 * (run.start_cost - run.final_cost) / run.start_cost if run.start_cost > 0 else 0.0
    m1, m2, m3 = st.columns(3)
    m1.metric("Startplan " + start_name(choice.start_key), de(run.start_cost), delta=f"{signed_pct(gap_percent(run.start_cost, ref))} gegen Referenz", delta_color="inverse")
    m2.metric("Nach der Lokalsuche", de(run.final_cost), delta=f"{signed_pct(gap_percent(run.final_cost, ref))} gegen Referenz", delta_color="inverse")
    m3.metric("Gewinn der Lokalsuche", pct(gain), delta=f"{len(run.steps)} Züge", delta_color="off")
    st.caption(f"{inst.n} Kunden, Kapazität {inst.capacity}, Gesamtnachfrage {sum(inst.demand)}. Nachbarschaft: {neigh_name(choice.neigh_key)}. Referenz: {'exaktes Optimum' if live.exact is not None else 'bester Wert dieser Seite (keine Untergrenze)'} {de(ref)}.")
else:
    run = None
    bs = band_stats(size)
    m1, m2, m3 = st.columns(3)
    m1.metric("Startplan " + start_name(choice.start_key) + " (Mittel der Bänder)", pct(bs["start"][choice.start_key]))
    m2.metric("Nach der Lokalsuche (Mittel der Bänder)", pct(bs["mean"][choice.start_key][choice.neigh_key]))
    m3.metric("Größenklasse der Bänder", f"{size} Kunden")
    st.caption(f"{inst.n} Kunden: über {C.LIVE_N_MAX} Kunden zeigt die Seite die vorberechneten Bänder der Größenklasse {size} (Bedauern gegen den besten Wert, Mittel über {instances_word(bs['count'])}).")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, choice, live), file_name="start-gegen-nachbarschaft.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Zählt der Startplan oder die Nachbarschaft?")
if live_ok:
    kind, text = verdict_live(live, choice)
else:
    kind, text = verdict_bands(size)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Eine Lokalsuche Zug für Zug")
st.caption("Der Startplan der Seitenleiste wird mit der gewählten Nachbarschaft Zug für Zug verbessert. Die Karte zeigt den Plan nach dem gewählten Zug (0: der Startplan); die Tabelle jeden Zug mit Gewinn.")
if not live_ok:
    st.info(f"Live gerechnet wird nur bis {C.LIVE_N_MAX} Kunden. Für {inst.n} Kunden zeigen die Experimente 2 bis 4 die vorberechneten Bänder.")
else:
    steps = run.steps
    if steps:
        step = st.slider("Zug", 0, len(steps), len(steps), key=f"ls_step_{choice.start_key}_{choice.neigh_key}_{len(steps)}", help="0: der Startplan.")
    else:
        step = 0
    cur_routes = run.start if step == 0 else steps[step - 1]["routes"]
    cur_cost = run.start_cost if step == 0 else steps[step - 1]["cost"]
    l1, l2 = st.columns([1, 1])
    with l1:
        st.markdown(f"**Nach {step} von {len(steps)} Zügen: {de(cur_cost)}** ({routes_word(len(cur_routes))})")
        st.plotly_chart(build_map(inst, cur_routes), width="stretch", key="map_ls")
    with l2:
        rows = ["| Zug | Art | Kunden | Gewinn | Kosten danach |", "|---|---|---|---|---|"]
        shown = steps if len(steps) <= 40 else steps[:40]
        for i, stp in enumerate(shown, start=1):
            mark = "**" if i == step else ""
            rows.append(f"| {mark}{i}{mark} | {stp['kind']} | {' '.join(str(c) for c in stp['customers'])} | {de(stp['gain'])} | {de(stp['cost'])} |")
        st.markdown("\n".join(rows) if steps else "Kein verbessernder Zug.")
        if len(steps) > 40:
            st.caption(f"Die Tabelle zeigt die ersten 40 von {len(steps)} Zügen.")
    kind, text = verdict_run(run, choice, live.reference)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Start × Nachbarschaft")
st.caption("Zeilen: Startpläne, Spalten: Nachbarschaften, Zellen: Abstand zum besten Wert in Prozent nach der Lokalsuche. Oben die Instanz der Seitenleiste (live), unten die Bänder: die festen Instanzen der Stücke 4 bis 11 und frische (Seeds ab 200000).")
if live_ok:
    keys = list(live.start_cost)
    tab = ["| Startplan | Start selbst | " + " | ".join(C.NEIGH[nk][0] for nk in C.NEIGH_KEYS) + " |", "|---|---|" + "---|" * len(C.NEIGH_KEYS)]
    for k in keys:
        tab.append(f"| {start_name(k)} | {pct(live.regret(live.start_cost[k]))} | " + " | ".join(pct(live.regret(live.cells[(k, nk)].cost)) for nk in C.NEIGH_KEYS) + " |")
    st.markdown("**Diese Instanz** (Referenz " + ("exakt" if live.exact is not None else "bester Wert dieser Seite") + f" {de(live.reference)}):\n\n" + "\n".join(tab))
e1, e2 = st.columns(2)
with e1:
    band_n = int(st.radio("Kunden n (Bänder)", list(C.BAND_SIZES), index=C.BAND_SIZES.index(size), horizontal=True, key="band_n"))
with e2:
    band_set = st.radio("Instanzen", list(C.BAND_SETS), horizontal=True, key="band_set", format_func=lambda k: {"fest": "fest (Stücke 4 bis 11)", "frisch": "frisch (Seeds ab 200000)"}[k], help="Frische Instanzen gibt es für 25 und 50 Kunden.")
which = band_set if band_stats(band_n, band_set) else "fest"
if which != band_set:
    st.info("Für diese Größe gibt es keine frischen Instanzen; die Seite zeigt die festen.")
bstats = band_stats(band_n, which)
st.plotly_chart(build_heatmap(bstats), width="stretch", key="heatmap")
tab = ["| Startplan | Start selbst | " + " | ".join(C.NEIGH[nk][0] for nk in C.NEIGH_KEYS) + " | Randmittel |", "|---|---|" + "---|" * len(C.NEIGH_KEYS) + "---|"]
for k in bstats["keys"]:
    tab.append(f"| {start_name(k)} | {pct(bstats['start'][k])} | " + " | ".join(pct(bstats["mean"][k][nk]) for nk in C.NEIGH_KEYS) + f" | {pct(bstats['row_marginal'][k])} |")
tab.append("| **Randmittel** | | " + " | ".join(pct(bstats["col_marginal"][nk]) for nk in C.NEIGH_KEYS) + " | |")
st.markdown("\n".join(tab))
st.caption(f"{instances_word(bstats['count'])} ({'feste' if which == 'fest' else 'frische'} Menge), ein Lauf je Zelle. Spannweite der Startpläne bei allen Zügen: {de(bstats['start_span_alle'])} Prozentpunkte; "
           f"der Nachbarschaften im Randmittel: {de(bstats['neigh_span_total'])}.")
kind, text = verdict_bands(band_n, which)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wie viel holt die Lokalsuche heraus?")
st.caption("Je Startplan das mittlere Bedauern vor und nach der Lokalsuche mit allen Zügen (Größe und Menge wie oben), dazu die Zeit des Bauens und der Lokalsuche (Größenordnungen einer Einzelmessung).")
st.plotly_chart(build_gain(bstats), width="stretch", key="gain_chart")
times = band_times(band_n)
tab = ["| Startplan | Bedauern des Startplans | nach der Lokalsuche | Gewinn (Prozentpunkte) | Bauzeit | Zeit der Lokalsuche |", "|---|---|---|---|---|---|"]
for k in bstats["keys"]:
    tab.append(f"| {start_name(k)} | {pct(bstats['start'][k])} | {pct(bstats['mean'][k]['alle'])} | {de(bstats['start'][k] - bstats['mean'][k]['alle'], 1)} | {seconds_text(times['build'][k])} | {seconds_text(times['ls_alle'][k])} |")
st.markdown("\n".join(tab))

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Mehrfachstart gegen guten Start")
st.caption("Wie viele Zufallsstarts (je mit allen Zügen) braucht es, um einen guten Start einzuholen? Live auf der Instanz der Seitenleiste (bis 50 Kunden), darunter die Bänder.")
if live_ok:
    k_rand = int(st.slider("Zufallsstarts", 1, C.LIVE_RANDOM_MAX, 5, key="k_random"))
    kind, text = verdict_random(live, k_rand)
    getattr(st, kind)(text)
    tab = ["| Verfahren | Kosten | Abstand zur Referenz |", "|---|---|---|"]
    for k in ("SAV", "SAVR", "L9R"):
        c = live.cells[(k, "alle")].cost
        tab.append(f"| {start_name(k)} + Lokalsuche | {de(c)} | {signed_pct(live.regret(c))} |")
    for k in (1, 5, C.RANDOM_STARTS):
        c = best_of_first(live.rand, k)
        tab.append(f"| Bestes von {k} Zufallsstarts + Lokalsuche | {de(c)} | {signed_pct(live.regret(c))} |")
    st.markdown("\n".join(tab))
bs4 = band_stats(band_n, which)
tab = ["| Verfahren (alle Züge) | Mittleres Bedauern | Zeit |", "|---|---|---|"]
for k in ("SAV", "SAVR", "L9R"):
    tab.append(f"| {start_name(k)} + Lokalsuche | {pct(bs4['mean'][k]['alle'])} | {seconds_text(times['build'][k] + times['ls_alle'][k])} |")
for k in (1, 5, C.RANDOM_STARTS):
    tab.append(f"| Bestes von {k} Zufallsstarts + Lokalsuche | {pct(bs4['rand'][k])} | {seconds_text(k * times['rand_start_ls'])} |")
st.markdown(f"**Bänder, {band_n} Kunden ({instances_word(bs4['count'])}):**\n\n" + "\n".join(tab))
b, e, w = band_paired(band_n, "L9R", "RS", "alle", which)
st.caption(f"Gepaart mit allen Zügen: bestes von 9 λ mit Rundreise gegen Zufallsfolge + Split billiger / gleich / teurer: {b} / {e} / {w}.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Einfache Lokalsuche** | Mit 2-opt-Stern, CROSS oder einer Iterated Local Search schrumpft der Abstand der Startpläne eventuell weiter | `vrp-nachbarschaften-demo`, Trajektorien-Reihe |
| **Eigene Instanzen** | Uchoa-artige Karten bis 100 Kunden, nicht die X-Instanzen | CVRPLIB (nicht geladen) |
| **Ein Lauf je Zelle** | Konstruktionen sind deterministisch, Zufallsstarts haben feste Seeds; bei 100 Kunden nur 8 Instanzen | mehr Instanzen |
| **Zufallsstarts begrenzt** | Das Beste von 20 Starts hängt an der Zahl; bei kleinen Instanzen holt es die Konstruktionen ein | mehr Starts |
| **Keine Flottengrenze, keine Fenster** | Die Zahl der Routen ist frei | Stücke 3 und 8 |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Ein Depot $0$, Kunden $1, \dots, n$ mit Nachfragen $q_i$, Kapazität $Q$, euklidische Entfernungen $d_{ij}$; ein Plan ist eine Menge von Routen, jede Route eine Folge von Kunden mit Last höchstens $Q$.

**2-opt.** In einer Route mit Kanten $(a, b)$ und $(c, d)$ ersetze sie durch $(a, c)$ und $(b, d)$ (das Stück $b \dots c$ wird umgekehrt), wenn $d_{ac} + d_{bd} < d_{ab} + d_{cd}$.

**Verschieben.** Nimm den Kunden $u$ aus seiner Route (Gewinn $g_u = d_{pu} + d_{un} - d_{pn}$ für Vorgänger $p$ und Nachfolger $n$) und setze ihn vor oder hinter einen der acht nächsten Kunden $v$ (zwischen $a$ und $b$), wenn $d_{au} + d_{ub} - d_{ab} < g_u$ und die Zielroute die Kapazität einhält.

**Tauschen.** Vertausche $u$ und $v$ aus verschiedenen Routen, wenn die Summe der Umwege sinkt und beide Routen die Kapazität einhalten.

**Bedauern.** Für eine Instanz $i$ und ein Ergebnis $c$ sei $b_i$ der beste Wert auf der Instanz (Referenz, Verfahren der Stücke 4 bis 11, alle Lokalsuchen, Zufallsstarts). Das Bedauern ist $100\,(c / b_i - 1)$, im Mittel über die Instanzen einer Größe.

**Spannweite.** Für ein Verfahren $s$ (Startplan) und eine Nachbarschaft $m$ sei $\bar\rho_{sm}$ das mittlere Bedauern. Die Spannweite der Startpläne bei allen Zügen ist $\max_s \bar\rho_{s,\mathrm{alle}} - \min_s \bar\rho_{s,\mathrm{alle}}$, die Spannweite der Nachbarschaften bei festem Start $s$ ist $\max_m \bar\rho_{sm} - \min_m \bar\rho_{sm}$.

**Literatur.** Savings: Clarke und Wright (1964); Split: Prins (2004); 2-opt: Croes (1958); Verschieben und Tauschen als Nachbarschaften des VRP: Übersicht in Toth und Vigo (2014). Nur als Titel oder Abstract gesehen; die Demo übernimmt keine Zahl daraus.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
