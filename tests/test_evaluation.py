"""Zentrale Korrektheits-Kette Punkte 6-7 (Perkolationsschwelle gegen Cohen-Formel, Robustheitsindex R) plus Rauchtests von rob_evaluation.py.

6) Gemessene ER-Schwelle liegt innerhalb einer Toleranzbande um f_c=1-1/<k> über mehrere mittlere Grade und Seeds (endliche Größe - gebändert, nie exakt).
7) R exakt gegen Neuberechnung aus der S(k)-Folge; R(Grad-adaptiv) <= Mittelwert von R(Zufall) über viele Zufallsreihenfolgen auf jeder gemessenen Instanz (Mittelwert-Aussage, NICHT als
   Einzelfall-Satz fuer jede einzelne Zufallsfolge)."""

import pytest

import rob_algorithm as A
import rob_constants as C
import rob_evaluation as ev
import rob_scenario as S


def test_analyse_smoke_all_kinds_and_strategies():
    for kind in C.KINDS:
        for strategy in C.STRATEGIES:
            settings = ev.Settings(kind=kind, strategy=strategy, seed=7)
            inst, a = ev.analyse(settings)
            assert len(a.sizes) == inst.n + 1
            assert a.sizes[0] == max(A.components(A.adjacency(inst.n, inst.edges)), default=0)
            assert a.sizes[-1] == 0
            assert 0.0 <= a.threshold <= 1.0
            assert 0.0 <= a.robustness <= 1.0


def test_compare_strategies_returns_all_four():
    inst = S.barabasi_albert_instance(60, 2, 4, 5)
    out = ev.compare_strategies(inst, seed=5)
    assert set(out) == set(C.STRATEGIES)
    for strategy, a in out.items():
        assert a.strategy == strategy
        assert len(a.sizes) == inst.n + 1


# --- 6. Perkolationsschwelle: gemessene ER-Schwelle gegen Cohen-Formel (gebändert) ----------------------------------------------------------------------


def test_er_percolation_threshold_within_tolerance_band_of_cohen_formula():
    """WICHTIG (Design-Entscheidung, s. rob_constants.PERCOLATION_FRAC_VANISH): verglichen wird NICHT die "auf die Haelfte gefallen"-Schwelle (frac=0.5, die allgemeine Anzeige-Schwelle der App),
    sondern die kleinere PERCOLATION_FRAC_VANISH -- nur dort ist die Abweichung ein echter endliche-Groesse-Effekt (schrumpft mit kleinerem frac), waehrend frac=0.5 selbst im n->unendlich-Limes
    einen strukturellen Abstand von ueber 0.3 zu f_c haette (nachgerechnet per Mean-Field-Selbstkonsistenzgleichung, s. Kommentar in rob_constants.py) -- kein Test-, sondern ein Definitionsproblem."""
    rows = ev.threshold_check(n=C.ER_N_THRESHOLD, mean_degrees=C.ER_MEAN_DEGREES, seeds=C.ER_THRESHOLD_SEEDS)
    assert len(rows) == len(C.ER_MEAN_DEGREES)
    for row in rows:
        assert row["predicted"] == pytest.approx(1.0 - 1.0 / row["mean_degree"], abs=1e-9)
        # endliche Groesse (n=400) -- gebaendert, NIE exakt gleichgesetzt. 0.05 deckt den finite-size-Effekt komfortabel ab (empirisch bei diesen n bestimmt, gemessene Luecke 0.004-0.023).
        assert row["measured_mean"] == pytest.approx(row["predicted"], abs=0.05)


def test_percolation_threshold_at_frac_one_half_is_structurally_far_from_cohen_formula():
    """Ehrlicher Gegenbefund (Verifikation verlangt das ausdruecklich): die ALLGEMEINE 0.5-Schwelle der App (percolation_threshold-Vorgabewert) liegt WEIT von Cohens f_c entfernt -- kein Rauschen,
    sondern ein struktureller Definitionsunterschied (die Riesenkomponente schrumpft kontinuierlich, "auf die Haelfte gefallen" tritt daher deutlich VOR dem asymptotischen "verschwindet" ein)."""
    rows = ev.threshold_check(n=C.ER_N_THRESHOLD, mean_degrees=C.ER_MEAN_DEGREES, seeds=C.ER_THRESHOLD_SEEDS, frac=C.PERCOLATION_FRAC)
    for row in rows:
        gap = row["predicted"] - row["measured_mean"]
        assert gap > 0.2                                                 # deutlich groesser als jede plausible endliche-Groesse-Bande


def test_er_threshold_prediction_matches_cohen_formula_by_hand():
    # <k>=4 auf einem regulaeren Netz mit n Knoten: f_c = 1 - 1/4 = 0.75
    n, mean_k = 100, 4
    pairs = S.erdos_renyi_gnm(n, int(n * mean_k / 2), seed=1)
    adj = A.adjacency(n, [(u, v, 1.0) for u, v in pairs])
    got = A.er_threshold_prediction(adj)
    assert got == pytest.approx(0.75, abs=0.02)                 # <k> selbst ist nur ungefaehr 4 (zufaellig gezogen), daher eine kleine Bande


def test_er_threshold_prediction_zero_for_very_sparse_networks():
    adj = A.adjacency(10, [(0, 1, 1.0)])                          # <k> = 0.2 <= 1
    assert A.er_threshold_prediction(adj) == 0.0


# --- 7. Robustheitsindex R: exakt aus S(k), R(Grad-adaptiv) <= Mittelwert R(Zufall) -----------------------------------------------------------------------


def test_robustness_index_matches_hand_recomputation_from_sizes():
    inst = S.generate(6, 0.2, "grid", 3)
    adj = A.adjacency(inst.n, inst.edges)
    order = A.random_order(inst.n, 3)
    sizes, _, _ = A.remove_sequence(adj, order)
    n = inst.n
    hand = sum(sizes[k] / n for k in range(1, n + 1)) / n
    got = A.robustness_index(sizes, n)
    assert got == pytest.approx(hand, abs=1e-12)


def test_robustness_index_by_hand_on_tiny_example():
    # n=3, S(0)=3, S(1)=2, S(2)=1, S(3)=0 (Pfad, Endknoten zuerst entfernt) -> R = (1/3)*((2/3)+(1/3)+(0/3)) = (1/3)*1 = 1/3
    sizes = [3, 2, 1, 0]
    assert A.robustness_index(sizes, 3) == pytest.approx(1.0 / 3.0, abs=1e-12)


@pytest.mark.parametrize("kind,settings_kwargs", [
    ("city", dict(side=8, blocked=0.2, nettype="grid")),
    ("ba", dict(n_ba=100, m_ba=2, m0_ba=4)),
    ("barbell", dict(k_barbell=10)),
])
def test_degree_adaptive_robustness_at_or_below_mean_random_robustness(kind, settings_kwargs):
    """Mittelwert-Aussage (NICHT fuer jede einzelne Zufallsfolge): R(Grad-adaptiv) <= Mittelwert von R(Zufall) ueber viele unabhaengige Zufallsreihenfolgen, auf jeder gemessenen Instanz."""
    settings = ev.Settings(kind=kind, seed=11, **settings_kwargs)
    inst = ev.instance(settings)
    adj = A.adjacency(inst.n, inst.edges)
    n_orders = 40
    random_rs = []
    for i in range(n_orders):
        order = A.random_order(inst.n, 11 * 1_000_003 + i)
        sizes, _, _ = A.remove_sequence(adj, order)
        random_rs.append(A.robustness_index(sizes, inst.n))
    mean_random_r = sum(random_rs) / len(random_rs)
    adaptive_order = A.degree_order_adaptive(adj)
    sizes_adaptive, _, _ = A.remove_sequence(adj, adaptive_order)
    r_adaptive = A.robustness_index(sizes_adaptive, inst.n)
    assert r_adaptive <= mean_random_r + 1e-9


def test_network_comparison_smoke_and_direction():
    city = ev.Settings(kind="city", side=8, blocked=0.2, nettype="grid")
    ba = ev.Settings(kind="ba", n_ba=100, m_ba=2, m0_ba=4)
    barbell = ev.Settings(kind="barbell", k_barbell=10)
    rows = ev.network_comparison(city, ba, barbell, seed=9, n_random_orders=20)
    assert {r["label"] for r in rows} == {"Betriebsnetz", "Skalenfrei", "Barbell"}
    for row in rows:
        assert row["r_degree_adaptive"] <= row["r_random_mean"] + 1e-9
        assert row["gap"] >= -1e-9
