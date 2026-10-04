"""Regler-Grenzen, feste Annahmen, gemessene Werte und Presets."""

SPACING = 1.0                    # Abstand der Kreuzungen im Betriebsnetz-Raster
JITTER = 0.18
SEED_MAX = 999999
DEFAULT_SEED = 35

KINDS = ("city", "ba", "barbell")
KIND_LABELS = {"city": "Betriebsnetz (Raster/Zufallsgraph)", "ba": "Skalenfreies Netz (Barabási-Albert)", "barbell": "Barbell-Lehrbuch"}

# --- Betriebsnetz (wortgleich aus strukturkennzahlen-demo) -----------------------------------------------------------------------------------------
SIDE_MIN, SIDE_MAX, DEFAULT_SIDE = 4, 20, 10                  # 20 (400 Knoten) wird vom "Perkolationsschwelle ER gegen Cohen-Formel"-Preset gebraucht (mean_degree~3.8)
NETTYPES = ("grid", "random")
NETTYPE_LABELS = {"grid": "Raster (Straßennetz)", "random": "Zufallsgraph (gleiche Kantenzahl)"}
BLOCKED_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
DEFAULT_BLOCKED = 0.2

# --- Skalenfreies Netz (Barabási und Albert 1999) ---------------------------------------------------------------------------------------------------
N_BA_MIN, N_BA_MAX, DEFAULT_N_BA = 30, 300, 150
M0_BA_MIN, M0_BA_MAX, DEFAULT_M0_BA = 3, 12, 4
M_BA_MIN, DEFAULT_M_BA = 1, 2                                 # oberes Ende von m ist immer das gewählte m0 (m <= m0)

# --- Barbell-Lehrbuch (wortgleich aus centrality-demo) ----------------------------------------------------------------------------------------------
BARBELL_K_MIN, BARBELL_K_MAX, DEFAULT_BARBELL_K = 3, 40, 8

# --- Entfernungsstrategien ---------------------------------------------------------------------------------------------------------------------------
STRATEGIES = ("random", "degree_static", "degree_adaptive", "betweenness_adaptive")
STRATEGY_LABELS = {"random": "Zufall", "degree_static": "Grad statisch", "degree_adaptive": "Grad adaptiv", "betweenness_adaptive": "Betweenness adaptiv"}
RECOMPUTE_EVERY_MIN, RECOMPUTE_EVERY_MAX, DEFAULT_RECOMPUTE_EVERY = 1, 20, 5    # kalibriert in der Vormessung, s. README

ORDERS = ("fixed", "shuffled")
ORDER_LABELS = {"fixed": "feste Reihenfolge (nach Knotennummer)", "shuffled": "gemischt (nach Seed)"}

STEPS = {1: "1 · Angriff in Aktion", 2: "2 · Riesenkomponente über den entfernten Anteil", 3: "3 · Zufall gegen gezielt", 4: "4 · Drei Netze im Vergleich"}

# --- Perkolationsschwelle (Cohen, Erez, ben-Avraham & Havlin 2000) ----------------------------------------------------------------------------------
# PERCOLATION_FRAC (0.5, "Riesenkomponente auf die Haelfte des Netzes gefallen") ist die griffige, allgemeine Anzeige-Schwelle in der App (Schritt 2 markiert
# sie in der S(f)-Kurve). WICHTIG (Design-Entscheidung, s. README "Design-Entscheidung"): diese 0.5-Schwelle ist NICHT direkt mit Cohens f_c=1-1/<k> vergleichbar
# -- f_c beschreibt, wann die Riesenkomponente asymptotisch VERSCHWINDET (ihr Anteil geht gegen 0), waehrend "auf 50% gefallen" schon deutlich FRUEHER eintritt,
# weil die Riesenkomponente kontinuierlich schrumpft (kein Sprung). Der Abstand zwischen beiden ist bei <k>=3..8 ca. 0.31-0.38 -- ein STRUKTURELLER Unterschied
# der Definitionen, kein endliche-Groesse-Rauschen (nachgerechnet mit der Mean-Field-Selbstkonsistenzgleichung, s. tests/test_evaluation.py). Fuer den Vergleich
# GEGEN die Cohen-Formel wird darum die deutlich kleinere PERCOLATION_FRAC_VANISH verwendet ("Riesenkomponente auf einen kleinen Rest gefallen" - naeher am
# asymptotischen "verschwindet"), bei der die verbleibende Abweichung tatsaechlich ein endliche-Groesse-Effekt ist (schrumpft mit kleinerem frac gegen 0).
PERCOLATION_FRAC = 0.5
PERCOLATION_FRAC_VANISH = 0.05
ER_MEAN_DEGREES = (3.0, 4.0, 6.0, 8.0)
ER_N_THRESHOLD = 400
ER_THRESHOLD_SEEDS = tuple(range(200000, 200012))

# --- Robustheitsindex-Vergleich (Grad-adaptiv gegen Mittel vieler Zufallsreihenfolgen) --------------------------------------------------------------
N_RANDOM_ORDERS_FOR_MEAN = 30

# --- Gemessene Werte (Seed 35, sofern nicht anders angegeben; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem
# --- Seed und ändern sich nie mit einer Bibliotheksversion; 2026-09-27, alle Werte über ev.*/A.* nachgerechnet, s. tests/test_claims.py) ------------------
# R JE STRATEGIE, STANDARDFALL: Betriebsnetz (n=100,m=144) R(Zufall)=0.3198, R(Grad-statisch)=0.2972, R(Grad-adaptiv)=0.2055, R(Betweenness-adaptiv)=0.1679
#   -- ÜBERRASCHUNG: schon auf dem Betriebsnetz ist der Unterschied Zufall/gezielt MESSBAR (nicht "kaum Unterschied", wie die Ausgangs-Hypothese vermutete),
#   weil das Sperren von 20% der Straßen die Gradverteilung uneinheitlich macht; Betweenness-adaptiv ist hier sogar VERHEERENDER als Grad-adaptiv (findet
#   Bruecken/Engstellen, die reiner Grad nicht sieht). Skalenfreies Netz (n=150,m=296) R(Zufall)=0.4065, R(Grad-adaptiv)=0.1112 -- der mit Abstand GRÖSSTE
#   Zufall/gezielt-Kontrast aller drei Netze, genau der Albert-Jeong-Barabási-Befund (Nature 2000). Barbell (n=16,k=8) R(Zufall)=0.3750, R(Grad-adaptiv)=0.2500.
# R-VERGLEICH DER DREI VEHIKEL (Kernaussage, Zufall = Mittel über 30 unabhängige Reihenfolgen gegen Grad-adaptiv): Betriebsnetz gap=0.0902, Barbell
#   gap=0.1038, Skalenfreies Netz gap=0.2999 -- der Skalenfrei-Abstand ist 3x größer als beim Betriebsnetz: robust gegen Zufall, fragil gegen gezielten
#   Angriff, GEMESSEN, nicht nur behauptet.
# GRAD- GEGEN BETWEENNESS-ANGRIFF (offene Frage der Messreihe, hier beantwortet): KEIN einheitlicher Sieger. Auf dem Betriebsnetz schlägt Betweenness-adaptiv
#   Grad-adaptiv klar (R 0.1679 gegen 0.2055). Auf dem skalenfreien Netz und dem Barbell gewinnt dagegen Grad-adaptiv knapp (Skalenfrei: 0.1112 gegen 0.1148;
#   Barbell: 0.2500 gegen 0.3320 -- dort verliert Betweenness deutlich, weil nach dem Kappen der Brücke keine Betweenness-Information mehr übrig bleibt und
#   die Näherung dann arbiträr weiterwählt). Grad ist also nicht grundsätzlich schwächer als Betweenness, wie man vielleicht erwarten würde.
# PERKOLATIONSSCHWELLE ER GEGEN COHEN-FORMEL (n=400, 12 Seeds, PERCOLATION_FRAC_VANISH=0.05 -- s. Design-Entscheidung unten): <k>=3 vorhergesagt 0.6667,
#   gemessen 0.6996 (Differenz -0.033); <k>=4: 0.7500 gegen 0.7565 (-0.0065); <k>=6: 0.8333 gegen 0.8219 (+0.0115); <k>=8: 0.8750 gegen 0.8496 (+0.0254) --
#   eine kleine, mit <k> wachsende endliche-Größe-Abweichung, wie erwartet. MIT DER ALLGEMEINEN 0.5-SCHWELLE (PERCOLATION_FRAC) dagegen liegt die gemessene
#   Schwelle 0.30-0.38 UNTER der Cohen-Vorhersage bei jedem <k> -- das ist KEIN Rauschen, sondern ein struktureller Definitionsunterschied (s. unten).
PRESET_HELP_MEASURED_AT = "2026-09-27"

PRESETS = {
    "Barbell-Lehrbuch (ein Treffer trennt sofort)": {"kind": "barbell", "kbarbell": 8, "strategy": "degree_static", "seed": 35, "step": 1},
    "Betriebsnetz Standardfall": {"kind": "city", "side": 10, "blocked": 0.2, "nettype": "grid", "strategy": "random", "seed": 35, "step": 1},
    "Skalenfrei robust gegen Zufall": {"kind": "ba", "nba": 150, "mba": 2, "m0ba": 4, "strategy": "random", "seed": 35, "step": 2},
    "Skalenfrei fragil gegen gezielten Angriff": {"kind": "ba", "nba": 150, "mba": 2, "m0ba": 4, "strategy": "degree_adaptive", "seed": 35, "step": 2},
    "Perkolationsschwelle ER gegen Cohen-Formel": {"kind": "city", "side": 20, "blocked": 0.0, "nettype": "random", "strategy": "random", "seed": 35, "step": 2},
    "Statisch gegen adaptiv (Skalenfrei)": {"kind": "ba", "nba": 150, "mba": 2, "m0ba": 4, "strategy": "degree_static", "seed": 35, "step": 3},
    "Grad- gegen Betweenness-Angriff (Betriebsnetz)": {"kind": "city", "side": 10, "blocked": 0.2, "nettype": "grid", "strategy": "betweenness_adaptive", "seed": 35, "step": 3},
    "Drei-Netze-Vergleich": {"kind": "city", "side": 10, "blocked": 0.2, "nettype": "grid", "nba": 150, "mba": 2, "m0ba": 4, "kbarbell": 8, "strategy": "random", "seed": 35, "step": 4},
}
PRESET_HELP = {
    "Barbell-Lehrbuch (ein Treffer trennt sofort)": "16 Knoten (k=8): der gezielte Grad-Angriff entfernt zuerst ein Brückenende (Grad 8, höchster Grad im Graphen) - der Graph zerfällt SOFORT (nach "
                                                     "nur 1 Entfernung) in Stücke der Größe 7 und 8. Eine zufällige Reihenfolge trifft eines der beiden Brückenenden dagegen erst im Mittel bei der "
                                                     "(n+1)/3=5.7. Entfernung (davor im Mittel (n-2)/3=4.7 unschädliche).",
    "Betriebsnetz Standardfall": "100 Kreuzungen, 144 Straßen (20% gesperrt): R(Zufall)=0.3198 gegen R(Grad-adaptiv)=0.2055 - ÜBERRASCHUNG: schon hier ein MESSBARER Unterschied (nicht \"kaum "
                                  "Unterschied\", wie oft vermutet), weil das Sperren die Gradverteilung uneinheitlich macht. Betweenness-adaptiv ist hier sogar am verheerendsten (R=0.1679).",
    "Skalenfrei robust gegen Zufall": "150 Knoten, 296 Kanten: unter rein zufälligem Ausfall bleibt die Riesenkomponente lange groß (R=0.4065, höher als beim Betriebsnetz mit R=0.3198; mittlerer Grad 3.9 "
                                       "gegen 2.9) - die Hubs werden selten getroffen, wenn zufällig gewählt wird.",
    "Skalenfrei fragil gegen gezielten Angriff": "Dieselbe Instanz, jetzt Grad-adaptiv: R fällt auf 0.1112 - der mit Abstand größte Zufall/gezielt-Kontrast aller drei Vehikel (Gap 0.30, gegen nur "
                                                  "0.09 beim Betriebsnetz; jeweils Mittel über 30 Zufallsreihenfolgen minus Grad-adaptiv) - der Albert-Jeong-Barabási-Befund (Nature 2000) gemessen, nicht nur behauptet.",
    "Perkolationsschwelle ER gegen Cohen-Formel": "400 Knoten, 760 Kanten, <k>=3.8: Cohens Vorhersage f_c=1-1/<k>=0.737. Bei der kleinen 5%-Schwelle (nahe am asymptotischen \"Verschwinden\") liegt "
                                                   "die Messung nur 0.01-0.03 daneben (endliche Größe) - bei der allgemeinen 50%-Schwelle der App dagegen 0.30+ daneben, weil das etwas anderes misst "
                                                   "(s. Design-Entscheidung im README).",
    "Statisch gegen adaptiv (Skalenfrei)": "Auf dem skalenfreien Netz unterscheiden sich Grad-statisch (R=0.1195) und Grad-adaptiv (R=0.1112) kaum - die ursprünglichen Hubs bleiben meist auch nach "
                                            "ein paar Entfernungen noch die höchstgradigen Knoten.",
    "Grad- gegen Betweenness-Angriff (Betriebsnetz)": "Hier schlägt Betweenness-adaptiv (R=0.1679) den Grad-Angriff (R=0.2055) klar - auf dem skalenfreien Netz und dem Barbell ist es dagegen "
                                                       "umgekehrt (s. README): kein einheitlicher Sieger.",
    "Drei-Netze-Vergleich": "Die R-Tabelle nebeneinander: Betriebsnetz-Gap 0.09, Barbell-Gap 0.10, Skalenfrei-Gap 0.30 (Zufall-Mittel minus Grad-adaptiv) - der Albert-Jeong-Barabási-Kontrast auf "
                            "einen Blick.",
}
