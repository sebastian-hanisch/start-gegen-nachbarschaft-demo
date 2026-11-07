"""Konstanten: Regler-Grenzen, Startpläne, Nachbarschaften, Bänder, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 100, 6
SEED_MAX, DEFAULT_SEED = 999999, 0
ROUTES_MIN, ROUTES_MAX, DEFAULT_ROUTES = 2, 4, 3
FILL_MIN, FILL_MAX, FILL_STEP, DEFAULT_FILL = 60, 100, 2, 90   # Auslastung in Prozent: Kapazität = aufgerundet Gesamtnachfrage / (Zielroutenzahl · Auslastung)
CLUSTERS, CLUSTER_SIGMA = 3, 7.0              # Familie „In Gruppen“
FAMILIES = ("Kleine Karte (ganze Zahlen)", "Zufällig verteilt (0 bis 100)", "In Gruppen (0 bis 100)", "Handinstanz (n = 6)")
FAMILY_KEYS = ("small", "random", "clustered")   # Familie 3 (Handinstanz) hat keinen Generator
HAND_FAMILY = 3
DEFAULT_FAMILY = HAND_FAMILY
DEPOTS = ("In der Mitte", "In der Ecke")
DEFAULT_DEPOT = 0
EXACT_MAX = 12                                # bis zu dieser Größe rechnet die App das exakte Optimum
TOL = 1e-9                                    # Gleichstände und Gleichheit von Kosten: absolut
TIE = 1e-12                                   # Beim Einfügen zählt ein Kandidat nur als besser, wenn er um mehr als TIE besser ist
LEVEL_PP = 0.5                                # „gleichauf“: Unterschied unter einem halben Prozentpunkt

# Handinstanz aus den Stücken 1 bis 4 (Depot (0,0), Kapazität 7, Optimum 44,3623 mit den Routen (1 4) und (2 6 3 5))
HAND_XY = ((0.0, 0.0), (6.0, -6.0), (-2.0, 5.0), (-4.0, -4.0), (0.0, -7.0), (-1.0, -1.0), (-6.0, 3.0))
HAND_DEMAND = (3, 2, 2, 4, 2, 1)
HAND_CAPACITY = 7

NEIGHBORS = 8                                 # Nachbarn je Kunde für Verschieben und Tauschen

# Startpläne: Schlüssel -> (Name, Art, Farbe). Reihenfolge = Reihenfolge der Tabellen.
STARTS = {
    "RS": ("Zufallsfolge + Split", "Zufall", "#9aa5b1"),
    "RF": ("Zufallsfolge, Füllen bis voll", "Zufall", "#c9b6e4"),
    "ES": ("Einfügen nach Split", "Konstruktion", "#d8a13a"),
    "SAV": ("Savings λ = 1", "Konstruktion", "#8fb8b3"),
    "SAVR": ("Savings λ = 1 + Rundreise", "Konstruktion", "#5f9d96"),
    "L9R": ("Bestes von 9 λ + Rundreise", "Konstruktion", "#2F6B65"),
}
START_KEYS = tuple(STARTS)
ES_MAX_N = 50                                  # Einfügen nach Split wird nur bis zu dieser Größe gerechnet (bei 100 Kunden rund 40 s)
# Nachbarschaften: Schlüssel -> (Name, Züge)
NEIGH = {
    "2opt": ("nur 2-opt", ("2opt",)),
    "move": ("nur Verschieben", ("move",)),
    "swap": ("nur Tauschen", ("swap",)),
    "2opt+move": ("2-opt + Verschieben", ("2opt", "move")),
    "move+swap": ("Verschieben + Tauschen", ("move", "swap")),
    "alle": ("alle drei Züge", ("2opt", "move", "swap")),
}
NEIGH_KEYS = tuple(NEIGH)
DEFAULT_START, DEFAULT_NEIGH = 0, 5
RANDOM_STARTS = 20                             # Zufallsstarts je Instanz in den Bändern (Experiment 4)
LAMS = (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0)

# Bänder
BAND_SIZES = (12, 25, 50, 100)
FRESH_SIZES = (25, 50)
BAND_FILE = "sgn_bands.json"
BAND_SETS = ("fest", "frisch")
BAND_ROUTES, BAND_FILL = 3, 90
SOURCE_BANDS = "tvw_bands.json"                # Instanzen, Referenzen und Kosten der Verfahren aus tourenbildung-verfahrenswahl-demo (Stück 15)

# Live-Rechnung der App
LIVE_N_MAX = 50
LIVE_RANDOM_MAX = 20

ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b", "#17becf", "#e377c2")
COLOR_REF = "#c0504d"

# Presets (die Zahlen in den Hilfetexten prüft tests/test_claims.py); das erste ist die Voreinstellung
_H = {"n": 6, "family": 3, "depot": 0, "routes": 3, "fill": 90, "seed": 0, "start": 0, "neigh": 5}
_K = {"n": 25, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 6}
PRESETS = {
    "Zufallsstart und alle Züge (Handinstanz)": dict(_H),
    "Der schlechte Start braucht die Nachbarschaft (25 Kunden)": {**_K, "start": 0, "neigh": 0},
    "Ein guter Start braucht sie kaum (25 Kunden)": {**_K, "start": 4, "neigh": 0},
    "Zufallsstarts gegen Savings (50 Kunden)": {"n": 50, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 1, "start": 3, "neigh": 5},
}
PRESET_HELP = {
    "Zufallsstart und alle Züge (Handinstanz)": "Die Handinstanz der Stücke 1 bis 4 (Optimum 44,36). Der Zufallsstart (62,60) ist mit 2-opt allein ein lokales Optimum: kein Zug. Mit allen Zügen findet die Lokalsuche in 7 Zügen (alle Verschieben) das Optimum 44,36. "
                                                "Aus Savings oder Einfügen nach Split startet sie schon im Optimum.",
    "Der schlechte Start braucht die Nachbarschaft (25 Kunden)": "25 Kunden, Karte zufällig, Depot in der Mitte, Seed 6. Aus der Zufallsfolge mit Split bleibt die Lokalsuche mit 2-opt allein 65,2 % über der Referenz (542,41), mit allen drei Zügen 18,5 %: "
                                                                  "hier entscheidet die Nachbarschaft.",
    "Ein guter Start braucht sie kaum (25 Kunden)": "Dieselbe Instanz, Start Savings mit Rundreise: 2-opt allein 4,3 %, alle Züge 4,1 % über der Referenz. Die Nachbarschaft ändert 0,2 Prozentpunkte, der Start (4,1 gegen 18,5 % mit allen Zügen) ändert viel mehr.",
    "Zufallsstarts gegen Savings (50 Kunden)": "50 Kunden, Seed 1. Savings mit allen Zügen liegt 7,9 % über der Referenz (642,37); das beste von 1, 5, 20 Zufallsstarts mit allen Zügen 28,6, 16,6, 6,0 %. Das beste von 9 λ mit Rundreise und Lokalsuche trifft den besten Wert (0,0 %). "
                                                "20 Zufallsstarts sind 20 Lokalsuchen, Savings braucht einen Start und eine.",
}
ASSUMPTIONS_MARKDOWN = """- **Eine einfache Lokalsuche:** erste Verbesserung mit 2-opt, Verschieben und Tauschen (acht nächste Nachbarn je Kunde); kein 2-opt-Stern, kein CROSS, keine Strafen für Unzulässigkeit, keine ILS-, VNS- oder Tabu-Schicht. Mit reicheren Nachbarschaften schrumpft der Abstand der Startpläne eventuell weiter.
- **Eigene Instanzen:** Uchoa-artige Karten (zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke), höchstens 100 Kunden, Kapazität über die Auslastung (90 %), drei Zielrouten; die X-Instanzen der Literatur sind nicht geladen.
- **Ein Lauf je Start und Nachbarschaft:** die Konstruktionen sind deterministisch, die Zufallsstarts haben je Instanz feste Seeds; bei 100 Kunden gibt es nur 8 Instanzen, Mittelwerte tragen die Streuung der Instanz.
- **Referenz und Bedauern:** das Bedauern misst gegen den besten Wert auf der Instanz (Referenz, Verfahren der Stücke 4 bis 11, alle Lokalsuchen, Zufallsstarts); die Referenz ist bis 12 Kunden das Optimum, darüber PyVRP (5 Sekunden, Seed 1) und keine Untergrenze.
- **Zeiten sind Daten:** eine Einzelmessung auf einer Maschine in Python (Median über wenige Instanzen), keine Zeit wird in einem Test gemessen; Einfügen nach Split fehlt bei 100 Kunden (rund 40 s je Start).
- **Mehrfachstarts:** je Instanz 20 feste Zufallsfolgen; „das Beste von k“ nimmt die ersten k. Das Ergebnis hängt an der Zahl der Starts und fällt bei kleinen Instanzen anders aus als bei großen.
- **Keine Flottengrenze, keine Fenster:** die Zahl der Routen ist frei, es gibt nur die Kapazität.
"""
