# Robustheit – Zufall gegen gezielten Angriff, Perkolationsschwelle – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-robustheit-demo.streamlit.app/)**

Achtes Stück der **Graphen-und-Netzwerke-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Kind von Stück 7 (Strukturkennzahlen, [strukturkennzahlen-demo](https://github.com/sebastian-hanisch/strukturkennzahlen-demo)): dort wurde die Struktur eines Netzes vermessen (Clustering, Gradverteilung), jetzt geht es darum, was diese Struktur für den AUSFALL bedeutet. Vier Entfernungsstrategien: **Zufall**, **Grad statisch** (Rangfolge einmal aus dem Ausgangsnetz), **Grad adaptiv** (Cohen, Erez, ben-Avraham & Havlin 2001: nach jeder Entfernung neu der aktuell höchstgradige Restknoten), **Betweenness adaptiv** (dieselbe Idee mit der aktuellen Betweenness, Brandes 2001). Der klassische Befund (Albert, Jeong & Barabási 2000, Nature 406, 378–382): **skalenfreie Netze sind erstaunlich robust gegen zufälligen Ausfall, aber sehr verwundbar gegen gezielten Angriff auf ihre Hubs**. Als **Perkolationsschwelle** wird gemessen, ab welchem entfernten Anteil die größte Komponente stark schrumpft; für Erdős-Rényi-artige Netze unter zufälligem Ausfall gibt es eine geschlossene Vorhersage (Cohen, Erez, ben-Avraham & Havlin 2000: f_c = 1 − 1/⟨k⟩). Als zusammenfassende Kennzahl je Strategie/Netz dient der **Robustheitsindex** R = (1/n)·Σ S(k)/n (Schneider, Moreira, Andrade, Herrmann & Havlin 2011).

Abgrenzung: Stück 1 ([bfs-dfs-demo](https://github.com/sebastian-hanisch/bfs-dfs-demo)) hat schon einmal eine Perkolationsschwelle gemessen, aber dort wurden zufällig **Kanten** gesperrt (Bond-Perkolation) – hier werden **Knoten** entfernt (Site-Perkolation), eine verwandte, aber eigene Frage.

**Einordnung in die Reihe:** die Reihe hat zwölf Stücke, dies ist das achte (Details in `graphen-planung/PLAN.md` des Portfolio-Ordners):

```
1 BFS und DFS (Wurzel)                                                        [gebaut: bfs-dfs-demo]
 ├─ 2 Brücken und Artikulationspunkte ─ 4 Euler-Touren                        [gebaut: bridges-demo, euler-tour-demo]
 ├─ 3 Starke Zusammenhangskomponenten, topologische Sortierung                [gebaut: scc-demo]
 ├─ 5 Graphfärbung                                                            [gebaut: graph-coloring-demo]
 ├─ 6 Zentralität ─ 7 Strukturkennzahlen ─ 8 Robustheit                       [gebaut: centrality-demo, strukturkennzahlen-demo, robustheit-demo ─ DIESES STÜCK]
 │        │        └─ 9 Kaskaden und Ausbreitung                              [nicht gebaut]
 │        └─ 10 Kritische Knoten härten                                       [nicht gebaut]
 └─ 11 Bandbreite ─ 12 Bandbreite von G(n,k,b) und Cliquenüberdeckung         [nicht gebaut]
```

Ergebnis in Kürze: Auf dem **skalenfreien Netz** (Barabási-Albert) fällt der Robustheitsindex von R=0.4065 (Zufall) auf **R=0.1112 (Grad-adaptiv)** – der mit Abstand größte Zufall/gezielt-Kontrast aller drei Vehikel, genau der Albert-Jeong-Barabási-Befund. Eine **echte Überraschung**: schon auf dem Betriebsnetz (Straßenraster, 20 % gesperrt) ist der Unterschied MESSBAR (R=0.3198 gegen R=0.2055), nicht "kaum vorhanden", wie die Ausgangs-Hypothese vermutete – und dort schlägt **Betweenness-adaptiv sogar den Grad-Angriff** (R=0.1679), während auf dem skalenfreien Netz und dem Barbell-Graphen umgekehrt Grad-adaptiv knapp die Nase vorn hat. Kein einheitlicher Sieger zwischen Grad und Betweenness – gemessen, nicht angenommen.

## Warum dieses Problem

Ein Netz mit hoher Gradheterogenität (wenige Knoten mit sehr vielen Verbindungen, viele mit wenigen – ein skalenfreies Netz) verhält sich unter Ausfall fundamental anders, je nachdem WER ausfällt: fällt ein zufälliger Knoten aus, trifft es meist einen der vielen schwachgradigen Knoten, kaum Schaden. Fällt gezielt der höchstgradige Knoten aus – und danach wieder der NEUE höchstgradige (Cohen u. a. 2001) –, bricht das Netz überproportional schnell zusammen. Das ist der Kern der Internet-/Infrastruktur-Robustheitsdebatte der frühen 2000er (Albert, Jeong & Barabási 2000). Diese Demo macht den Kontrast an drei konkreten Netzen, vier Entfernungsstrategien und einer geschlossenen Vorhersage (Cohen-Formel) messbar.

## Design-Entscheidung: zwei verschiedene Perkolationsschwellen

`percolation_threshold(sizes, n, frac)` misst, ab welchem entfernten Anteil `S(k) < frac·n` gilt. Die App zeigt standardmäßig **frac=0.5** ("Riesenkomponente auf die Hälfte gefallen") – eine griffige, aber NICHT mit Cohens asymptotischer f_c-Definition vergleichbare Schwelle: f_c beschreibt, wann die Riesenkomponente im Grenzwert VERSCHWINDET (ihr Anteil geht gegen 0), während "auf 50 % gefallen" strukturell viel FRÜHER eintritt, weil die Riesenkomponente kontinuierlich schrumpft (kein Sprung, zweite-Ordnung-Phasenübergang). Nachgerechnet mit der Mean-Field-Selbstkonsistenzgleichung: bei ⟨k⟩=3..8 liegt die 50 %-Schwelle 0.30–0.38 UNTER f_c – ein **struktureller Unterschied der Definitionen, kein Rauschen**. Für den Vergleich MIT der Cohen-Formel verwendet `threshold_check()` darum eine viel kleinere Schwelle (`PERCOLATION_FRAC_VANISH=0.05`, "auf einen kleinen Rest gefallen"), bei der die Restabweichung tatsächlich ein endliche-Größe-Effekt ist (schrumpft mit kleinerem `frac`, s. Tests).

## Vorab-Hypothesen (vor der Messung notiert, hier geprüft)

| Hypothese | Ergebnis |
|---|---|
| **H1** S(k), Perkolationsschwelle, Robustheitsindex stimmen mit unabhängiger networkx-Neuberechnung überein. | ✅ Bestätigt: S(k) gegen `networkx.connected_components` nach JEDER Entfernungsstufe auf >380 Instanzen, alle vier Strategien. |
| **H2** Auf dem Betriebsnetz (enge, fast reguläre Gradverteilung) macht es kaum einen Unterschied, welchen Knoten man entfernt. | ❌ **Widerlegt (Überraschung):** R(Zufall)=0.3198 gegen R(Grad-adaptiv)=0.2055 – ein MESSBARER Unterschied (Gap 0.09), weil das Sperren von 20 % der Straßen die Gradverteilung uneinheitlich macht. Kleiner als beim skalenfreien Netz (Gap 0.30), aber klar vorhanden. |
| **H3** Das skalenfreie Netz ist robust gegen Zufall, aber fragil gegen gezielten Angriff (Albert, Jeong & Barabási 2000). | ✅ Bestätigt, der größte Kontrast aller drei Vehikel: R fällt von 0.4065 (Zufall) auf 0.1112 (Grad-adaptiv). |
| **H4** Grad-adaptiv entfernt bei jedem Schritt exakt den aktuell höchstgradigen Restknoten (kein Rescan-Ersatz mit Fehlern). | ✅ Bestätigt als Satz, gegen Brute-Force-Neuberechnung auf kleinen Instanzen und auf einer konstruierten Instanz, die Grad-statisch nachweislich hereinlegt. |
| **H5** Betweenness-adaptiv ist grundsätzlich verheerender als Grad-adaptiv (Betweenness ist die "bessere" Zentralität). | ❌ **Widerlegt:** kein einheitlicher Sieger. Betweenness gewinnt auf dem Betriebsnetz (R=0.1679 gegen 0.2055), verliert aber knapp auf dem skalenfreien Netz (0.1148 gegen 0.1112) und deutlich auf dem Barbell (0.3320 gegen 0.2500 – nach dem Kappen der Brücke bleibt keine Betweenness-Information mehr übrig). |
| **H6** Die gemessene Perkolationsschwelle eines ER-Netzes liegt nahe an Cohens f_c=1−1/⟨k⟩. | ⚠️ **Nur bei der richtigen Definition:** bei der kleinen 5 %-Schwelle ja (Abweichung 0.004–0.03, endliche Größe). Bei der allgemeinen 50 %-Schwelle NEIN (Abweichung >0.28, strukturell – s. Design-Entscheidung oben). |
| **H7** Der Barbell-Graph zeigt den Zufall/gezielt-Kontrast am dramatischsten (ein einziger Treffer zerlegt ihn). | ✅ Bestätigt als Satz: der gezielte Angriff trennt den Graphen nach GENAU 1 Entfernung in Stücke der Größe k−1 und k; eine zufällige Reihenfolge trifft ein Brückenende erst im Mittel nach (n−2)/3 Entfernungen. |
| **H8** R(Grad-adaptiv) ist nie größer als der Mittelwert von R(Zufall) über viele Zufallsreihenfolgen. | ✅ Bestätigt (Mittelwert-Aussage) auf jeder gemessenen Instanz – NICHT als Aussage über jede einzelne Zufallsfolge behauptet, da eine einzelne glückliche zufällige Ziehung gelegentlich auch früh Hubs treffen kann. |

## Befunde (gemessen, keine Behauptungen)

Seed 35, Standardeinstellungen sofern nicht anders angegeben; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem Seed.

| Frage | Ergebnis |
|---|---|
| **Stimmt das Verfahren?** | ✅ S(k) == unabhängige networkx-Neuberechnung nach JEDER Entfernungsstufe, alle vier Strategien, >380 Instanzen; Grad-adaptiv == Brute-Force auf kleinen Instanzen; Betweenness-adaptiv (recompute_every=1) == unabhängige Brandes-Neuberechnung bei jedem Schritt |
| **Betriebsnetz** (100 Knoten, 144 Straßen, 20 % gesperrt) | R(Zufall)=0.3198, R(Grad-statisch)=0.2972, R(Grad-adaptiv)=0.2055, **R(Betweenness-adaptiv)=0.1679 (am verheerendsten hier)** |
| **Skalenfreies Netz** (150 Knoten, 296 Kanten) | R(Zufall)=0.4065, R(Grad-statisch)=0.1195, **R(Grad-adaptiv)=0.1112 (am verheerendsten hier)**, R(Betweenness-adaptiv)=0.1148 |
| **Barbell** (16 Knoten, k=8) | R(Zufall)=0.3750, R(Grad-statisch)=0.3320, R(Grad-adaptiv)=0.2500, R(Betweenness-adaptiv)=0.3320 (verliert deutlich gegen Grad) |
| **R-Vergleich der drei Vehikel** (Zufall = Mittel über 30 Reihenfolgen, gegen Grad-adaptiv) | Betriebsnetz-Gap 0.090, Barbell-Gap 0.104, **Skalenfrei-Gap 0.300 (3× größer als beim Betriebsnetz)** |
| **Perkolationsschwelle ER gegen Cohen (n=400, kleine 5 %-Schwelle)** | ⟨k⟩=3: vorhergesagt 0.667, gemessen 0.700 (−0.033) — ⟨k⟩=4: 0.750 gegen 0.757 (−0.007) — ⟨k⟩=6: 0.833 gegen 0.822 (+0.012) — ⟨k⟩=8: 0.875 gegen 0.850 (+0.025) |
| **Perkolationsschwelle ER gegen Cohen (allgemeine 50 %-Schwelle)** | bei jedem ⟨k⟩ 0.30–0.38 UNTER der Cohen-Vorhersage – struktureller Definitionsunterschied, kein Rauschen (s. Design-Entscheidung) |
| **Barbell von Hand** (k=8) | gezielter Angriff trennt nach 1 Entfernung in Stücke der Größe 7 und 8; Zufallsreihenfolge trifft ein Brückenende im Mittel nach 4.7 Entfernungen ((n−2)/3=14/3) |

Presets (8), alle mit den Zahlen in ihren Hilfetexten (`tests/test_presets.py`):

| Preset | Was es zeigt |
|---|---|
| Barbell-Lehrbuch (ein Treffer trennt sofort) | k=8: gezielter Angriff trennt sofort in 7+8, Zufall trifft im Mittel erst nach 4.7 Entfernungen |
| Betriebsnetz Standardfall | R(Zufall)=0.3198 gegen R(Grad-adaptiv)=0.2055 – messbarer, aber kleinerer Unterschied als beim skalenfreien Netz |
| Skalenfrei robust gegen Zufall | R(Zufall)=0.4065 – die Riesenkomponente übersteht zufälligen Ausfall lange |
| Skalenfrei fragil gegen gezielten Angriff | R(Grad-adaptiv)=0.1112 – der größte Zufall/gezielt-Kontrast aller drei Netze |
| Perkolationsschwelle ER gegen Cohen-Formel | 400 Knoten, ⟨k⟩=3.8, f_c=0.737 gegen die kleine 5 %-Schwelle (Abweichung nur 0.01–0.03) |
| Statisch gegen adaptiv (Skalenfrei) | R(Grad-statisch)=0.1195 gegen R(Grad-adaptiv)=0.1112 – kaum Unterschied, weil die ursprünglichen Hubs meist Hubs bleiben |
| Grad- gegen Betweenness-Angriff (Betriebsnetz) | Betweenness (R=0.1679) schlägt hier Grad (R=0.2055) – anders als beim skalenfreien Netz |
| Drei-Netze-Vergleich | R-Tabelle nebeneinander: Betriebsnetz-Gap 0.09, Barbell-Gap 0.10, Skalenfrei-Gap 0.30 |

## Modell und Verfahren

- **Betriebsnetz** (`rob_scenario.py`, `generate`, wortgleich aus `strukturkennzahlen-demo`/`centrality-demo`): gestörtes Straßenraster mit gesperrtem Anteil, oder ein Zufallsgraph gleicher Kantenzahl (= eine ER(n,m)-artige Instanz für die Perkolationsschwellen-Messung).
- **Skalenfreies Netz** (`barabasi_albert_instance`, Barabási und Albert 1999, wortgleich aus `strukturkennzahlen-demo`): Kern aus m0 Knoten, jeder weitere Knoten hängt sich mit m Kanten proportional zum Grad an.
- **Barbell-Lehrbuch** (`barbell_instance`, wortgleich aus `centrality-demo`): zwei vollständige Graphen K_k, durch eine Brücke verbunden.
- **Vier Entfernungsstrategien** (`rob_algorithm.py`): `random_order` (Zufallspermutation), `degree_order_static` (einmalige Rangfolge), `degree_order_adaptive` (Max-Heap mit lazy deletion, kein O(n)-Rescan je Schritt), `betweenness_order_adaptive` (volle Brandes-Neuberechnung nur alle `recompute_every` Entfernungen, dazwischen die zuletzt berechnete Rangfolge unter den noch vorhandenen Knoten weiterverwendet – explizite Näherung).
- **S(k), Perkolationsschwelle, Robustheitsindex** (`remove_sequence`, `percolation_threshold`, `robustness_index`): Größe der größten Komponente nach jeder Entfernung, gemessene endliche-Größe-Schwelle, Fläche unter der S(k)/n-Kurve (Schneider u. a. 2011).
- **Cohen-Vorhersage** (`er_threshold_prediction`, Cohen, Erez, ben-Avraham & Havlin 2000): f_c = 1 − 1/⟨k⟩ für zufälligen Ausfall auf ER-artigen Netzen.

## Was die App zeigt

1. **Vier Schritte** (Schritt-Regler): **Angriff in Aktion** (Karte mit Schieberegler über den Entfernungsfortschritt, entfernte Knoten ausgegraut, größte Restkomponente hervorgehoben) → **Riesenkomponente über den entfernten Anteil** (S(f)-Kurve, gemessene Schwelle markiert, bei der Zufallsgraph-Option zusätzlich Cohens Vorhersage) → **Zufall gegen gezielt** (alle vier Strategien überlagert, R-Balken) → **Drei Netze im Vergleich** (Betriebsnetz/Skalenfrei/Barbell je Zufall vs. Grad-adaptiv, R-Tabelle).
2. Regler: Instanz (Betriebsnetz / Skalenfreies Netz / Barbell), instanzspezifische Parameter, Entfernungsstrategie, Neuberechnungs-Intervall (NUR bei Betweenness-adaptiv sichtbar), Zufalls-Seed (+🎲), Nachbarreihenfolge; Permalink in der Adresszeile.
3. Der Schritt-Regler für den Entfernungsfortschritt (Schritt 1) ist unabhängig vom App-Schritt-Regler.

## Was nicht funktioniert hat / Grenzen

- **Zwei verschiedene Perkolationsschwellen.** Die allgemeine 50 %-Schwelle der App ist NICHT direkt mit Cohens f_c vergleichbar (s. Design-Entscheidung oben) – ein Definitionsproblem, das erst beim Testen gegen die Cohen-Formel auffiel.
- **Betweenness-adaptiv mit recompute_every>1 ist eine explizite Näherung.** Nach dem Kappen einer Brücke (Barbell) bleibt keine Betweenness-Information mehr übrig – die Näherung wählt dann arbiträr weiter, was die Strategie dort schlechter als Grad-adaptiv macht.
- **Cohens Formel gilt nur für ER-artige (Poisson-Gradverteilung) Netze unter ZUFÄLLIGEM Ausfall.** Für das skalenfreie Netz oder unter gezieltem Angriff gibt es keine analoge geschlossene Formel dieser Art in dieser Demo.
- **Der Robustheitsindex R ist ein einziger Mittelwert.** Er unterscheidet nicht, OB ein Netz früh oder erst spät zusammenbricht.
- **Synthetische Instanzen.** Betriebsnetz, skalenfreies Netz und Barbell sind erzeugt, keine echten Infrastruktur- oder Sozialnetzdaten.
- **Site- statt Bond-Perkolation.** Hier werden Knoten entfernt; Stück 1 der Reihe hat die verwandte, aber andere Frage (zufällig gesperrte Kanten) schon behandelt.

## Tests

`tests/test_scenario.py` (Rauchtests der drei Instanzen + Erdős-Rényi), `tests/test_algorithm.py` (Korrektheits-Kette Punkte 1, 2, 3, 5, 8, 9: S(k) gegen networkx auf >380 Instanzen, S(k) monoton, Grad-adaptiv exakt gegen Brute-Force, Barbell von Hand, Buchführung/Determinismus, Sonderfälle), `tests/test_betweenness_adaptive.py` (Korrektheits-Kette Punkt 4: recompute_every=1 exakt gegen unabhängige Brandes-Neuberechnung bei jedem Schritt, recompute_every>1 korrektes Carry-Forward), `tests/test_evaluation.py` (Korrektheits-Kette Punkte 6-7: Perkolationsschwelle gebändert gegen Cohen, Robustheitsindex exakt und die Mittelwert-Aussage gegen Zufall), `tests/test_presets.py` (jede Zahl der Hilfetexte), `tests/test_claims.py` (jede README-Zahl über die echten Auswertungsfunktionen, inkl. der Design-Entscheidung und der widerlegten Hypothesen), `tests/test_app.py` (AppTest – Voreinstellung, jedes Preset, jeder Schritt für jede Instanzart, bedingte Regler, Permalink-Grenzen, Footer). 107 Tests insgesamt.

```
python -m pytest tests/ -v
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-App |
| `rob_algorithm.py` | Entfernungsstrategien, S(k), Perkolationsschwelle, Robustheitsindex, Cohen-Vorhersage |
| `rob_scenario.py` | Betriebsnetz, skalenfreies Netz, Barbell, Erdős-Rényi |
| `rob_evaluation.py` | Analyse, Strategievergleich, Schwellen-Check, Netzvergleich |
| `rob_visualization.py` | Plotly-Figuren (Angriffskarte, S(f)-Kurve, Strategie-Overlay, Netzvergleich) |
| `rob_presets.py`, `rob_constants.py` | Permalink, Presets, gemessene Werte |
| `tests/` | Tests |

## Bewusst nicht umgesetzt

Kaskaden und Ausbreitung, kritische Knoten härten – eigene Stücke der Reihe (Stück 9-10). Ein formaler Mitigation-/Härtungs-Mechanismus (Schneider u. a. 2011 selbst behandelt das, hier nur der R-Index zitiert).

## Lokal ausführen

```
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\streamlit run app.py
```

## Literatur

- Albert, R., Jeong, H., & Barabási, A.-L. (2000). *Error and attack tolerance of complex networks.* Nature 406, 378–382.
- Cohen, R., Erez, K., ben-Avraham, D., & Havlin, S. (2000). *Resilience of the Internet to random breakdowns.* Physical Review Letters 85(21), 4626–4628.
- Cohen, R., Erez, K., ben-Avraham, D., & Havlin, S. (2001). *Breakdown of the Internet under intentional attack.* Physical Review Letters 86(16), 3682–3685.
- Schneider, C. M., Moreira, A. A., Andrade, J. S., Herrmann, H. J., & Havlin, S. (2011). *Mitigation of malicious attacks on networks.* Proceedings of the National Academy of Sciences 108(10), 3838–3841 (nur die Definition des Robustheitsindex R zitiert – die "Mitigation"/Härtung selbst ist Thema von Stück 10, hier bewusst nicht gebaut).
- Brandes, U. (2001). *A faster algorithm for betweenness centrality.* Journal of Mathematical Sociology 25(2), 163–177.

Gebaut mit Streamlit, Plotly, NumPy und pandas.
