"""Auswertung: Analyse einer Instanz/Strategie (S(k)-Kurve, Perkolationsschwelle, Robustheitsindex R), Vergleich aller vier Strategien auf derselben Instanz, gemessene ER-Schwelle gegen die
Cohen-Formel über mehrere mittlere Grade, R-Vergleich der drei Vehikel unter Zufall gegen gezielt (die Kernaussage der Demo)."""

from dataclasses import dataclass

import rob_algorithm as A
import rob_constants as C
import rob_scenario as S


@dataclass
class Settings:
    kind: str = "city"                   # "city" | "ba" | "barbell"
    # Betriebsnetz
    side: int = C.DEFAULT_SIDE
    blocked: float = C.DEFAULT_BLOCKED
    nettype: str = "grid"                # "grid" | "random"
    # Skalenfreies Netz
    n_ba: int = C.DEFAULT_N_BA
    m_ba: int = C.DEFAULT_M_BA
    m0_ba: int = C.DEFAULT_M0_BA
    # Barbell-Lehrbuch
    k_barbell: int = C.DEFAULT_BARBELL_K
    # gemeinsam
    strategy: str = "random"             # "random" | "degree_static" | "degree_adaptive" | "betweenness_adaptive"
    recompute_every: int = C.DEFAULT_RECOMPUTE_EVERY
    seed: int = C.DEFAULT_SEED
    order: str = "fixed"                 # ändert nie S(k)/R - nur die interne Buchführungsreihenfolge


@dataclass
class Analysis:
    n: int
    m: int
    strategy: str
    node_order: list                     # Entfernungsreihenfolge
    sizes: list                          # S(k), k=0..n
    counts: list                         # Komponentenzahl, k=0..n
    mean_degrees: list                   # mittlerer Restgrad, k=0..n
    threshold: float                     # gemessene Perkolationsschwelle (Anteil), frac=0.5
    robustness: float                    # R


def instance(settings):
    if settings.kind == "city":
        return S.generate(settings.side, settings.blocked, settings.nettype, settings.seed)
    if settings.kind == "ba":
        return S.barabasi_albert_instance(settings.n_ba, settings.m_ba, settings.m0_ba, settings.seed)
    if settings.kind == "barbell":
        return S.barbell_instance(settings.k_barbell)
    raise ValueError(f"unbekannte Instanzart {settings.kind}")


def order_for(strategy, adj, n, seed, recompute_every):
    if strategy == "random":
        return A.random_order(n, seed)
    if strategy == "degree_static":
        return A.degree_order_static(adj)
    if strategy == "degree_adaptive":
        return A.degree_order_adaptive(adj)
    if strategy == "betweenness_adaptive":
        return A.betweenness_order_adaptive(adj, recompute_every)
    raise ValueError(f"unbekannte Strategie {strategy}")


def analyse(settings):
    inst = instance(settings)
    adj = A.adjacency(inst.n, inst.edges, settings.order, settings.seed)
    order = order_for(settings.strategy, adj, inst.n, settings.seed, settings.recompute_every)
    sizes, counts, mean_degrees = A.remove_sequence(adj, order)
    threshold = A.percolation_threshold(sizes, inst.n, C.PERCOLATION_FRAC)
    robustness = A.robustness_index(sizes, inst.n)
    a = Analysis(inst.n, inst.m, settings.strategy, order, sizes, counts, mean_degrees, threshold, robustness)
    return inst, a


# --- Alle vier Strategien auf derselben Instanz (Schritt 3: Zufall gegen gezielt) -----------------------------------------------------------------------


def compare_strategies(inst, seed, recompute_every=C.DEFAULT_RECOMPUTE_EVERY, order_mode="fixed"):
    adj = A.adjacency(inst.n, inst.edges, order_mode, seed)
    out = {}
    for strategy in C.STRATEGIES:
        node_order = order_for(strategy, adj, inst.n, seed, recompute_every)
        sizes, counts, mean_degrees = A.remove_sequence(adj, node_order)
        threshold = A.percolation_threshold(sizes, inst.n, C.PERCOLATION_FRAC)
        robustness = A.robustness_index(sizes, inst.n)
        out[strategy] = Analysis(inst.n, inst.m, strategy, node_order, sizes, counts, mean_degrees, threshold, robustness)
    return out


# --- Perkolationsschwelle: gemessene ER-Schwelle gegen die Cohen-Formel (Schritt 2) -----------------------------------------------------------------------


def threshold_check(n, mean_degrees=C.ER_MEAN_DEGREES, seeds=C.ER_THRESHOLD_SEEDS, frac=C.PERCOLATION_FRAC_VANISH):
    """Für mehrere mittlere Grade <k>: erzeugt ein ER(n,m)-Netz mit m = round(n*<k>/2), entfernt Knoten in ZUFÄLLIGER Reihenfolge (die Voraussetzung der Cohen-Formel, s. Moduldoc), misst die
    Perkolationsschwelle über mehrere Seeds und vergleicht mit f_c = 1 - 1/<k>. WICHTIG: hier absichtlich mit dem KLEINEN `frac` (Riesenkomponente auf einen kleinen Rest gefallen, nicht auf die
    Hälfte) - nur so ist der Vergleich mit Cohens asymptotischer "verschwindet"-Definition sinnvoll, s. rob_constants.PERCOLATION_FRAC_VANISH."""
    rows = []
    for k_mean in mean_degrees:
        m = int(round(n * k_mean / 2))
        measured = []
        prediction = None
        for seed in seeds:
            pairs = S.erdos_renyi_gnm(n, m, seed)
            adj = A.adjacency(n, [(u, v, 1.0) for u, v in pairs])
            if prediction is None:
                prediction = A.er_threshold_prediction(adj)
            order = A.random_order(n, seed)
            sizes, _, _ = A.remove_sequence(adj, order)
            measured.append(A.percolation_threshold(sizes, n, frac))
        mean_measured = sum(measured) / len(measured)
        rows.append({"mean_degree": k_mean, "predicted": prediction, "measured_mean": mean_measured, "measured": measured})
    return rows


# --- R-Vergleich der drei Vehikel unter Zufall gegen gezielt (Schritt 4, die Kernaussage) -------------------------------------------------------------------


def network_comparison(city_settings, ba_settings, barbell_settings, seed, n_random_orders=C.N_RANDOM_ORDERS_FOR_MEAN):
    """Betriebsnetz/Skalenfreies Netz/Barbell je unter Zufall (Mittel über `n_random_orders` unabhängige Zufallsreihenfolgen) und Grad-adaptiv - die R-Tabelle, die den Albert-Jeong-Barabási-Kontrast
    sichtbar macht (Nature 2000)."""
    rows = []
    for label, settings in (("Betriebsnetz", city_settings), ("Skalenfrei", ba_settings), ("Barbell", barbell_settings)):
        inst = instance(settings)
        adj = A.adjacency(inst.n, inst.edges)
        random_r = []
        for i in range(n_random_orders):
            order = A.random_order(inst.n, seed * 1_000_003 + i)
            sizes, _, _ = A.remove_sequence(adj, order)
            random_r.append(A.robustness_index(sizes, inst.n))
        mean_random_r = sum(random_r) / len(random_r)
        adaptive_order = A.degree_order_adaptive(adj)
        sizes_adaptive, _, _ = A.remove_sequence(adj, adaptive_order)
        r_adaptive = A.robustness_index(sizes_adaptive, inst.n)
        rows.append({"label": label, "n": inst.n, "m": inst.m, "r_random_mean": mean_random_r, "r_degree_adaptive": r_adaptive, "gap": mean_random_r - r_adaptive})
    return rows
