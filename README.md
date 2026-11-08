# Start gegen Nachbarschaft – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-start-gegen-nachbarschaft-demo.streamlit.app/)** -->

Siebtes Stück (gelb) der **Tourenbildung**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel). Die Stücke 2 bis 6 haben Startpläne gebaut (Einfügen nach Split, Savings, Sweep, die Rundreise je Route), Stück 11 eine genetische Suche mit Lokalsuche. Hier die einfache Lokalsuche allein: **Zählt bei einem kapazitierten Tourenplan der Startplan oder die Nachbarschaft?** Die Hill-Climbing-Demo ([hill-climbing-demo](https://github.com/sebastian-hanisch/hill-climbing-demo)) und die [vrp-nachbarschaften-demo](https://github.com/sebastian-hanisch/vrp-nachbarschaften-demo) messen die Nachbarschaft ohne die Startpläne der Linie; deren Zahlen werden nicht übernommen.

## Kernfrage

Die Faustregel aus dem Hill Climbing lautet: Die Nachbarschaft zählt mehr als der Startplan. Gilt das bei Kapazität, wenn die Startpläne die Konstruktionen der Linie sind? Die Demo startet die Lokalsuche aus zwei Zufallsplänen und vier Konstruktionen mit je sechs Nachbarschaften (2-opt, Verschieben, Tauschen und ihre Kombinationen), zeigt eine Lokalsuche Zug für Zug, legt die Tabelle Start × Nachbarschaft über feste und frische Instanzen (live bis 50 Kunden, darüber die Bänder) und fragt, wie viele Zufallsstarts einen guten Start einholen.

## Modell

Wie in den Stücken 1 bis 11: ein Depot, n Kunden mit ganzzahliger Nachfrage, gleiche Fahrzeuge der Kapazität Q (ohne Flottengrenze), euklidische Entfernungen, keine Zeitfenster; die Kapazität folgt aus der Auslastung (90 %, drei Zielrouten). **Startpläne:** Zufallsfolge mit optimalem Split, Zufallsfolge mit „Füllen bis voll“, Einfügen nach Split (bis 50 Kunden), Savings (λ = 1), Savings mit Rundreise je Route, bestes von 9 λ mit Rundreise. **Lokalsuche:** erste Verbesserung; jeder Durchgang geht **2-opt** (ein Stück einer Route umkehren), **Verschieben** (ein Kunde an eine bessere Stelle, auch in eine andere Route, zu den acht nächsten Kunden) und **Tauschen** (zwei Kunden aus verschiedenen Routen) durch und führt jeden verbessernden Zug sofort aus; sie endet in einem lokalen Optimum.

## Methodik

- **Bedauern:** Abstand zum besten Wert auf der Instanz (Referenz, die Verfahren der Stücke 4 bis 11, alle Lokalsuchen und Zufallsstarts), in Prozent; im Mittel über die Instanzen einer Größe.
- **Daten:** 60 **feste** Instanzen (n = 12: 20, 25: 16, 50: 16, 100: 8) und **frische** (Seeds ab 200000, je 8 bei 25 und 50 Kunden); Instanzen, Referenzen (exakt bis 12 Kunden, darüber PyVRP 0.14.1) und die Kosten der Verfahren kommen aus den Bändern der Stücke 4 bis 11 und aus [tourenbildung-verfahrenswahl-demo](https://github.com/sebastian-hanisch/tourenbildung-verfahrenswahl-demo); Startpläne, Lokalsuchen und Zufallsstarts sind in dieser Demo gerechnet (`generate_precomputed.py`).
- **Je Instanz:** sechs Startpläne × sechs Nachbarschaften = 36 Lokalsuchen und 20 Zufallsstarts mit allen Zügen (Zufallsfolge `Random(Seed · 7 + k)`).
- **Zeiten:** einzeln gemessen (Median über wenige Instanzen je Größe, Zwischenspeicher der Rundreisen vor jeder Messung geleert); **Größenordnungen dieser Maschine** (parallel liefen weitere Rechnungen), in den Bändern gespeichert und von keinem Test nachgemessen.

## Befunde (gemessen, keine Behauptungen)

**1. Der Startplan zählt in diesen Messungen deutlich, bei n = 12 weniger.** Mittleres Bedauern nach der Lokalsuche mit allen Zügen, feste Instanzen:

| Startplan (Lokalsuche mit allen Zügen) | n = 12 | 25 | 50 | 100 |
|---|---|---|---|---|
| Zufallsfolge + Split | 3,9 % | 17,4 % | 19,3 % | 15,2 % |
| Zufallsfolge, Füllen bis voll | 5,4 % | 12,5 % | 14,3 % | 13,6 % |
| Einfügen nach Split | 2,2 % | 3,3 % | 5,1 % | – |
| Savings λ = 1 | 2,0 % | 2,2 % | 4,6 % | 6,2 % |
| Savings λ = 1 + Rundreise | 2,0 % | 2,1 % | 4,2 % | 6,0 % |
| Bestes von 9 λ + Rundreise | 0,9 % | 1,3 % | 2,2 % | 3,6 % |
| Bestes von 5 Zufallsstarts, je mit allen Zügen | 0,4 % | 3,6 % | 10,2 % | 14,3 % |
| Bestes von 20 Zufallsstarts, je mit allen Zügen | 0,0 % | 0,3 % | 6,8 % | 12,5 % |

Die Startpläne liegen bei allen Zügen um 4,5 / 16,2 / 17,0 / 11,6 Prozentpunkte auseinander (n = 12 / 25 / 50 / 100). Savings mit nur 2-opt (7,3 % bei n = 100) ist besser als die Zufallsfolge mit allen Zügen (15,2 %). Pro Instanz und pro Größe ist der Startplan weniger eindeutig: bei n = 12 ist Savings + Rundreise gegen die Zufallsfolge + Split nur in 9 von 20 Instanzen besser (9 / 6 / 5, Tabelle unter Befund 3), und das beste von 20 Zufallsstarts (0,0 % und 0,3 % bei n = 12 und 25) liegt vor allen Konstruktionen; bei kleinen Instanzen lässt sich der Startplan also durch Mehrfachstarts ersetzen (Befund 4).

**2. Die Nachbarschaft zählt beim schlechten Start; beim guten ändert sie das Bedauern um höchstens 1,1 Prozentpunkte.**

| Nachbarschaft (Start: Zufallsfolge + Split) | n = 12 | 25 | 50 | 100 |
|---|---|---|---|---|
| nur 2-opt | 31,2 % | 54,5 % | 69,7 % | 67,9 % |
| nur Verschieben | 9,9 % | 15,5 % | 22,3 % | 34,0 % |
| nur Tauschen | 21,5 % | 38,6 % | 93,5 % | 133,6 % |
| 2-opt + Verschieben | 7,6 % | 18,9 % | 19,2 % | 15,9 % |
| Verschieben + Tauschen | 4,7 % | 14,5 % | 22,3 % | 33,9 % |
| alle drei Züge | 3,9 % | 17,4 % | 19,3 % | 15,2 % |

| Nachbarschaft (Start: Savings λ = 1 + Rundreise) | n = 12 | 25 | 50 | 100 |
|---|---|---|---|---|
| nur 2-opt | 2,4 % | 3,2 % | 5,3 % | 6,5 % |
| nur Verschieben | 2,1 % | 2,3 % | 4,3 % | 6,1 % |
| nur Tauschen | 2,3 % | 2,6 % | 5,2 % | 6,5 % |
| 2-opt + Verschieben | 2,1 % | 2,3 % | 4,3 % | 6,0 % |
| Verschieben + Tauschen | 2,0 % | 2,2 % | 4,2 % | 6,1 % |
| alle drei Züge | 2,0 % | 2,1 % | 4,2 % | 6,0 % |

| Spannweite in Prozentpunkten | n = 12 | 25 | 50 | 100 |
|---|---|---|---|---|
| Startpläne bei allen Zügen | 4,5 | 16,2 | 17,0 | 11,6 |
| Nachbarschaften aus der Zufallsfolge + Split | 27,3 | 40,0 | 74,3 | 118,4 |
| Nachbarschaften aus Savings + Rundreise | 0,5 | 1,0 | 1,1 | 0,5 |
| Nachbarschaften aus dem besten von 9 λ + Rundreise | 0,5 | 0,2 | 0,4 | 0,5 |

Die Spannweite der Nachbarschaften wird von den absichtlich schwachen Nachbarschaften (nur Tauschen, nur 2-opt) bestimmt: Zwischen den Nachbarschaften mit Verschieben unterscheidet sich Savings + Rundreise um höchstens 0,2 Prozentpunkte, die Zufallsfolge + Split bei n = 100 aber noch um bis zu 19 Prozentpunkte (15,2 bis 34,0 %). Bei n = 50 sind 1,1 Prozentpunkte ein Viertel des Bedauerns von Savings + Rundreise (4,2 bis 5,3 %).

**3. Die Lokalsuche holt von einem guten Start absolut wenig heraus.** Startplan → nach der Lokalsuche mit allen Zügen (mittleres Bedauern): n = 12: Savings λ = 1 2,6 % → 2,0 %, Bestes von 9 λ + Rundreise 1,4 % → 0,9 %, Zufallsfolge + Split 47,6 % → 3,9 %; n = 25: Savings λ = 1 3,9 % → 2,2 %, Bestes von 9 λ + Rundreise 1,5 % → 1,3 %, Zufallsfolge + Split 123,1 % → 17,4 %; n = 50: Savings λ = 1 7,2 % → 4,6 %, Bestes von 9 λ + Rundreise 2,7 % → 2,2 %, Zufallsfolge + Split 249,2 % → 19,3 %; n = 100: Savings λ = 1 8,9 % → 6,2 %, Bestes von 9 λ + Rundreise 4,1 % → 3,6 %, Zufallsfolge + Split 427,9 % → 15,2 %. Aus der Zufallsfolge fällt das Bedauern von 428 % auf 15,2 % (n = 100), aus dem besten von 9 λ mit Rundreise von 4,1 % auf 3,6 %. Der Gewinn ist beim besten von 9 λ mit Rundreise 0,2 bis 0,5 Prozentpunkte, bei Savings λ = 1 0,6 bis 2,7; für Savings λ = 1 sind das 23 / 44 / 36 / 30 % seines Bedauerns (n = 12 / 25 / 50 / 100), relativ also nicht wenig.

| Gepaart, alle Züge: billiger / gleich / teurer | n = 12 | 25 | 50 | 100 |
|---|---|---|---|---|
| Bestes von 9 λ + Rundreise gegen Zufallsfolge + Split | 12 / 6 / 2 | 15 / 0 / 1 | 15 / 0 / 1 | 8 / 0 / 0 |
| Savings λ = 1 + Rundreise gegen Zufallsfolge + Split | 9 / 6 / 5 | 15 / 0 / 1 | 15 / 0 / 1 | 7 / 0 / 1 |

**4. 20 Zufallsstarts holen die Konstruktionen nur bei kleinen Instanzen ein.** Das beste von 20 Zufallsstarts liegt bei n = 12 und 25 bei 0,0 % und 0,3 % (Savings mit Lokalsuche 2,0 % und 2,2 %); bei n = 50 und 100 bleibt es mit 6,8 % und 12,5 % hinter Savings (4,6 % und 6,2 %) und hinter dem besten von 9 λ mit Rundreise (2,2 % und 3,6 %). Fünf Zufallsstarts reichen nicht über n = 12 hinaus. Mit mehr als 20 Zufallsstarts wurde nicht gemessen.

| Zeit (Median, einzeln gemessen) | n = 50: Bauen | Lokalsuche (alle Züge) | n = 100: Bauen | Lokalsuche (alle Züge) |
|---|---|---|---|---|
| Zufallsfolge + Split | 0,4 ms | 11 ms | 1,2 ms | 29 ms |
| Zufallsfolge, Füllen bis voll | 0,1 ms | 7,9 ms | 0,1 ms | 23 ms |
| Einfügen nach Split | 1,9 s | 3,1 ms | – | – |
| Savings λ = 1 | 3,4 ms | 4,7 ms | 13 ms | 12 ms |
| Savings λ = 1 + Rundreise | 0,18 s | 4,8 ms | 0,96 s | 4,3 ms |
| Bestes von 9 λ + Rundreise | 1,3 s | 2,7 ms | 8,8 s | 3,7 ms |
| Ein Zufallsstart mit Lokalsuche | | 7,1 ms | | 21 ms |

Die Lokalsuche kostet Millisekunden; der Preis liegt im Startplan (bestes von 9 λ mit Rundreise bei n = 100: 8,8 s, Savings 13 ms). Zwanzig Zufallsstarts mit Lokalsuche kosten bei n = 100 0,41 s.

**5. Frische Instanzen** (Seeds ab 200000, 8 je Größe) zeigen dasselbe Bild:

| Frische Instanzen, alle Züge | n = 25 | 50 |
|---|---|---|
| Zufallsfolge + Split | 8,1 % | 15,1 % |
| Zufallsfolge, Füllen bis voll | 9,4 % | 15,4 % |
| Einfügen nach Split | 3,3 % | 3,8 % |
| Savings λ = 1 | 1,9 % | 2,8 % |
| Savings λ = 1 + Rundreise | 1,9 % | 2,4 % |
| Bestes von 9 λ + Rundreise | 1,1 % | 1,3 % |
| Bestes von 5 Zufallsstarts | 2,9 % | 10,7 % |
| Bestes von 20 Zufallsstarts | 1,1 % | 8,3 % |
| Spannweite der Startpläne (Prozentpunkte) | 8,3 | 14,1 |
| Spannweite der Nachbarschaften aus Savings + Rundreise | 0,7 | 0,5 |

**Handinstanz** (Optimum 44,36): Der Zufallsstart (62,60) ist mit 2-opt allein ein lokales Optimum (kein Zug), mit allen Zügen findet die Lokalsuche das Optimum in 7 Zügen (alle Verschieben); die Zufallsfolge mit „Füllen bis voll“ (57,58) bleibt nach einem 2-opt-Zug bei 54,54 hängen. Aus Savings, Einfügen nach Split und der Rundreise-Variante startet die Lokalsuche schon im Optimum.

**Hook des Fachkanons** („Die Startlösung zählt bei Lokalsuche weniger als die Nachbarschaft, analog zur Hill-Climbing-Demo; prüfen, ob das bei Kapazität anders ist“): bei Kapazität und mit Konstruktionen als Start in diesen Messungen **nur für den Zufallsstart bestätigt**. Die Hill-Climbing-Aussage gilt für den Zufallsstart (aus der Zufallsfolge bei n = 25: nur 2-opt 54,5 %, alle Züge 17,4 %); ist der Start eine Konstruktion, liegen die Startpläne bei allen Zügen rund 1 bis 3 Prozentpunkte auseinander, die Nachbarschaften bei Savings + Rundreise und beim besten von 9 λ + Rundreise 0,2 bis 1,1: der Start zählt dort etwas mehr, aber nicht um ein Vielfaches. Der Vergleich 2,1 % gegen 17,4 % bei n = 25 stellt Savings + Rundreise der Zufallsfolge gegenüber, also einen guten Start einem Zufallsstart.

## Ehrliche Grenzen

- **Eine einfache Lokalsuche:** erste Verbesserung mit 2-opt, Verschieben und Tauschen (acht nächste Nachbarn je Kunde); kein 2-opt-Stern, kein CROSS, keine Strafen für Unzulässigkeit, keine ILS-, VNS- oder Tabu-Schicht. Mit reicheren Nachbarschaften schrumpft der Abstand der Startpläne eventuell weiter.
- **Eigene Instanzen:** Uchoa-artige Karten (zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke), höchstens 100 Kunden, Kapazität über die Auslastung (90 %), drei Zielrouten; die X-Instanzen der Literatur sind nicht geladen.
- **Ein Lauf je Start und Nachbarschaft:** die Konstruktionen sind deterministisch, die Zufallsstarts haben je Instanz feste Seeds; bei 100 Kunden gibt es nur 8 Instanzen, Mittelwerte tragen die Streuung der Instanz.
- **Referenz und Bedauern:** das Bedauern misst gegen den besten Wert auf der Instanz (Referenz, Verfahren der Stücke 4 bis 11, alle Lokalsuchen, Zufallsstarts); die Referenz ist bis 12 Kunden das Optimum, darüber PyVRP (5 Sekunden, Seed 1; bei frischen Instanzen der kleinere Wert von zwei Seeds) und keine Untergrenze.
- **Zeiten sind Daten:** eine Einzelmessung auf einer Maschine in Python (Median über wenige Instanzen), keine Zeit wird in einem Test gemessen; Einfügen nach Split fehlt bei 100 Kunden (rund 40 s je Start).
- **Mehrfachstarts:** je Instanz 20 feste Zufallsfolgen; „das Beste von k“ nimmt die ersten k. Das Ergebnis hängt an der Zahl der Starts und fällt bei kleinen Instanzen anders aus als bei großen.
- **Keine Flottengrenze, keine Fenster:** die Zahl der Routen ist frei, es gibt nur die Kapazität.

## Befunde und Korrekturen gegenüber dem Plan

- **Mehrfachstarts mit 20 statt 5:** Die Phase 0 rechnete mit fünf Zufallsstarts („Mehrfachstarts helfen kaum“). Mit 20 Zufallsstarts holt das Beste die Konstruktionen bei n = 12 und 25 ein (Befund 4); die Aussage gilt erst ab n = 50. Der Plan wird danach gelesen: Mehrfachstarts sind bei kleinen Instanzen ein Weg, bei großen nicht.
- **Bedauern gegen den besten Wert mit 20 Zufallsstarts:** Das Bezugsmaß enthält jetzt auch die 20 Zufallsstarts, die Zahlen weichen deshalb von der Phase 0 (fünf Zufallsstarts im Bezug) um Zehntel Prozentpunkte ab; die Wertung ist dieselbe.
- **Live bis 50 Kunden:** Der Plan sah live bis 25 Kunden vor; die Lokalsuche rechnet in Millisekunden, die teuerste Konstruktion (bestes von 9 λ mit Rundreise) bei n = 50 etwa 1,3 s, Einfügen nach Split 1,9 s.
- **Kein Lauf mit Einfügen nach Split bei 100 Kunden:** rund 40 s je Start; die Zeile fehlt.
- **Lehre:** Die Zufallsstarts müssen eine feste Reihenfolge haben (`Random(Seed · 7 + k)`), sonst ist „das Beste von k“ nicht nachrechenbar; Zeiten brauchen den geleerten Zwischenspeicher der Rundreisen.

## Verifikation

- **Handwerte:** 2-opt an einem Quadrat (10,4853 → 8,8284, Gewinn 4√2 − 4), die Handinstanz mit jedem Startplan und jeder Nachbarschaft, Verschieben und Tauschen an kleinen Plänen von Hand (`tests/test_ls.py`).
- **Orakel:** jede Lokalsuche aus jedem Startplan auf kleinen Instanzen (n = 5 bis 7) gegen die Aufzählung aller Zerlegungen mit allen Rundreisen: vollständige, kapazitätsgerechte Pläne, gemessene Länge gleich den Kosten, nie länger als der Start, nie unter dem Optimum; aus dem Optimum bewegt sich die Lokalsuche nicht (`tests/test_oracle.py`).
- **Eigenschaften:** nach der ersten Verbesserung ist der Plan ein lokales Optimum (ein zweiter Lauf findet keinen Zug); die Gewinne der Zugfolge ergeben genau Start minus Ende; gleicher Seed, gleiches Ergebnis; mehr erlaubte Züge sind im Mittel nicht schlechter, geprüft an vier Paaren und acht Instanzen mit 25 Kunden und Zufallsstart (allgemein gilt das nicht: aus der Zufallsfolge + Split ist bei n = 25 „alle drei Züge“ mit 17,4 % schlechter als „Verschieben + Tauschen“ mit 14,5 %); Umnummerieren der Kunden ändert die Aussagen nicht (`tests/test_ls.py`).
- **Randfälle:** n = 1, 2, 3, ein Kunde je Route, Kapazität für alle, leere Zugmenge, Seed 0 (`tests/test_edge_cases.py`).
- **Verdikte:** jede Verzweigung und jede Zahl im Text (`tests/test_verdicts.py`).
- **Zahlen der README und der Preset-Hilfen:** `tests/test_claims.py`; die vorberechneten Bänder auf Aufbau, Vollständigkeit und gegen eine frische Rechnung von Stichproben, alle Startpläne und Nachbarschaften bitgleich (`tests/test_bands.py`). **Zeiten werden nie gemessen:** sie sind Daten der Bänder.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), alle Startpläne und Nachbarschaften, Bänder, Zufallsstarts, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout, Laufzeit-Importe.

## Tests

102 Tests. Laufzeit lokal rund anderthalb Minuten (hier gemessen: 88 Sekunden).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Zwischenstände der Rechnung |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `generate_precomputed.py` | erzeugt `sgn_bands.json`: übernimmt Instanzen, Referenzen und Kosten aus Stück 15, rechnet Startpläne, Lokalsuchen, Zufallsstarts und Zeiten |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `sgn_algorithm.py` | Kern aus Stück 1: Split, Hilfsgraph, exakter Löser |
| `sgn_bands.json` | vorberechnete Bänder (76 Instanzzeilen mit 36 Lokalsuchen (30 bei den 8 Zeilen mit 100 Kunden, wo Einfügen nach Split fehlt) und 20 Zufallsstarts, Zeiten) |
| `sgn_constants.py` | Regler-Grenzen, Startpläne, Nachbarschaften, Presets, Annahmentext |
| `sgn_construct.py` | Einfügen nach Split |
| `sgn_evaluation.py` | Live-Rechnung, Bänder, Kennzahlen, Verdikt-Logik |
| `sgn_layout.py` | Fester Kopf und Tabellenregel (Stylesheet) |
| `sgn_ls.py` | Lokalsuche mit einzeln schaltbaren Zügen und Zugfolge, Split, Prüfer |
| `sgn_pdf_export.py` | PDF-Export des Ergebnisses |
| `sgn_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `sgn_routing.py` | Rundreise je Route (aus Stück 6) |
| `sgn_savings.py` | Savings (aus Stück 4) |
| `sgn_scenario.py` | Instanzen (aus Stück 1, mit Auslastung als Parameter) |
| `sgn_starts.py` | die sechs Startpläne und die Zufallsstarts |
| `sgn_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handinstanz, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Reichere Nachbarschaften und Metaheuristiken:** 2-opt-Stern, CROSS, ILS, VNS, Tabu, ALNS; Verweise auf die Trajektorien-Reihe und die [vrp-nachbarschaften-demo](https://github.com/sebastian-hanisch/vrp-nachbarschaften-demo).
- **Genetische Suche:** Stück 11; hier nur die einfache Lokalsuche.
- **Zeitfenster und Flottengrenze:** Stücke 8, 9 und 3.
- **Mehrere Läufe je Konstruktion:** die Konstruktionen sind deterministisch; nur die Zufallsstarts haben mehrere Seeds.
- **Einfügen nach Split bei 100 Kunden:** nicht gerechnet (rund 40 s je Start).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
