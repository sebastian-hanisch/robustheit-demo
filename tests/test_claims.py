"""Jede Zahl aus README und rob_constants-Kommentar, nachgerechnet über die echten Auswertungsfunktionen (Hauskonvention: keine erfundenen Zahlen)."""

import pytest

import rob_algorithm as A
import rob_constants as C
import rob_evaluation as ev
import rob_scenario as S


def test_readme_er_threshold_check_numbers():
    rows = ev.threshold_check(n=C.ER_N_THRESHOLD, mean_degrees=C.ER_MEAN_DEGREES, seeds=C.ER_THRESHOLD_SEEDS)
    by_k = {r["mean_degree"]: r for r in rows}
    assert round(by_k[3.0]["predicted"], 4) == 0.6667 and round(by_k[3.0]["measured_mean"], 4) == pytest.approx(0.6996, abs=0.01)
    assert round(by_k[4.0]["predicted"], 4) == 0.75 and round(by_k[4.0]["measured_mean"], 4) == pytest.approx(0.7565, abs=0.01)
    assert round(by_k[6.0]["predicted"], 4) == 0.8333 and round(by_k[6.0]["measured_mean"], 4) == pytest.approx(0.8219, abs=0.01)
    assert round(by_k[8.0]["predicted"], 4) == 0.875 and round(by_k[8.0]["measured_mean"], 4) == pytest.approx(0.8496, abs=0.01)
    # der Abstand waechst mit <k> (endliche-Groesse-Effekt bei der kleinen Vanish-Schwelle)
    gaps = [abs(by_k[k]["predicted"] - by_k[k]["measured_mean"]) for k in C.ER_MEAN_DEGREES]
    assert all(g < 0.05 for g in gaps)


def test_readme_frac_one_half_structural_gap_numbers():
    rows = ev.threshold_check(n=C.ER_N_THRESHOLD, mean_degrees=C.ER_MEAN_DEGREES, seeds=C.ER_THRESHOLD_SEEDS, frac=C.PERCOLATION_FRAC)
    for row in rows:
        gap = row["predicted"] - row["measured_mean"]
        assert gap > 0.28                                                # README: "0.30-0.38", strukturell, kein Rauschen


def test_readme_network_comparison_core_claim():
    city = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", seed=35)
    ba = ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, seed=35)
    barbell = ev.Settings(kind="barbell", k_barbell=8, seed=35)
    rows = ev.network_comparison(city, ba, barbell, seed=35, n_random_orders=C.N_RANDOM_ORDERS_FOR_MEAN)
    by_label = {r["label"]: r for r in rows}
    assert by_label["Skalenfrei"]["gap"] > 2.5 * by_label["Betriebsnetz"]["gap"]     # README: "3x groesser"
    assert by_label["Skalenfrei"]["gap"] > 2.5 * by_label["Barbell"]["gap"]


def test_readme_betriebsnetz_is_not_hardly_different_hypothesis_is_refuted():
    """README-Befund: schon auf dem (leicht gestoerten) Betriebsnetz ist Zufall/gezielt MESSBAR verschieden -- die Ausgangs-Hypothese ('kaum Unterschied, weil keine echten Hubs') ist NICHT bestaetigt,
    auch wenn der Unterschied kleiner ist als beim skalenfreien Netz."""
    a_random = ev.analyse(ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="random", seed=35))[1]
    a_adaptive = ev.analyse(ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="degree_adaptive", seed=35))[1]
    gap = a_random.robustness - a_adaptive.robustness
    assert gap > 0.05                                                    # messbar, nicht "kaum Unterschied" (waere z.B. < 0.02)


def test_readme_degree_vs_betweenness_no_uniform_winner():
    """README-Befund: kein einheitlicher Sieger zwischen Grad-adaptiv und Betweenness-adaptiv - je nach Netz gewinnt der eine oder der andere."""
    settings_pairs = [
        ("Betriebsnetz", ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", seed=35)),
        ("Skalenfrei", ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, seed=35)),
        ("Barbell", ev.Settings(kind="barbell", k_barbell=8, seed=35)),
    ]
    winners = {}
    for label, base in settings_pairs:
        base.strategy = "degree_adaptive"
        r_deg = ev.analyse(base)[1].robustness
        base2 = ev.Settings(**{**base.__dict__, "strategy": "betweenness_adaptive"})
        r_bet = ev.analyse(base2)[1].robustness
        winners[label] = "betweenness" if r_bet < r_deg else "degree"
    assert winners["Betriebsnetz"] == "betweenness"
    assert winners["Skalenfrei"] == "degree"
    assert winners["Barbell"] == "degree"
    assert len(set(winners.values())) > 1                                # kein einheitlicher Sieger ueber alle drei Netze


def test_barbell_bridge_split_theorem_holds_for_several_k():
    for k in (4, 6, 8, 10, 12):
        inst = S.barbell_instance(k)
        adj = A.adjacency(inst.n, inst.edges)
        order = A.degree_order_static(adj)
        sizes, count, _ = A.remove_sequence(adj, order)
        assert count[1] == 2
        remaining = sorted(A.components(_induced_local(adj, order[0])))
        assert remaining == [k - 1, k]


def _induced_local(adj, removed):
    n = len(adj)
    remaining = [v for v in range(n) if v != removed]
    remap = {old: new for new, old in enumerate(remaining)}
    sub = [[] for _ in remaining]
    for old in remaining:
        for nb in adj[old]:
            if nb != removed:
                sub[remap[old]].append(remap[nb])
    return sub
