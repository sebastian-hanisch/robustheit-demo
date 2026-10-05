"""Jede Zahl aus den PRESET_HELP-Hilfetexten, nachgerechnet über die echten Auswertungsfunktionen."""

import pytest

import rob_algorithm as A
import rob_constants as C
import rob_evaluation as ev
import rob_scenario as S


def test_barbell_preset_numbers():
    inst = S.barbell_instance(8)
    adj = A.adjacency(inst.n, inst.edges)
    order = A.degree_order_static(adj)
    sizes, count, _ = A.remove_sequence(adj, order)
    assert count[1] == 2
    assert sorted(A.components(_induced(adj, order[0]))) == [7, 8]
    n = inst.n
    trials = 500
    positions = []
    for seed in range(trials):
        o = A.random_order(n, seed)
        first = next(i for i, v in enumerate(o) if v in (7, 8))
        positions.append(first)
    mean_pos = sum(positions) / len(positions)
    assert round(mean_pos, 1) == pytest.approx(4.7, abs=0.3)


def _induced(adj, removed):
    n = len(adj)
    remaining = [v for v in range(n) if v != removed]
    remap = {old: new for new, old in enumerate(remaining)}
    sub = [[] for _ in remaining]
    for old in remaining:
        for nb in adj[old]:
            if nb != removed:
                sub[remap[old]].append(remap[nb])
    return sub


def test_betriebsnetz_standardfall_preset_numbers():
    settings = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="random", seed=35)
    inst, a_random = ev.analyse(settings)
    assert inst.n == 100 and inst.m == 144
    assert round(a_random.robustness, 4) == 0.3198
    a_adaptive = ev.analyse(ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="degree_adaptive", seed=35))[1]
    assert round(a_adaptive.robustness, 4) == 0.2055
    a_bet = ev.analyse(ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="betweenness_adaptive", seed=35))[1]
    assert round(a_bet.robustness, 4) == 0.1666
    assert a_bet.robustness < a_adaptive.robustness                     # Betweenness-adaptiv ist hier verheerender als Grad-adaptiv


def test_skalenfrei_presets_numbers():
    a_random = ev.analyse(ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, strategy="random", seed=35))[1]
    assert round(a_random.robustness, 4) == 0.4065
    a_adaptive = ev.analyse(ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, strategy="degree_adaptive", seed=35))[1]
    assert round(a_adaptive.robustness, 4) == 0.1112
    a_static = ev.analyse(ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, strategy="degree_static", seed=35))[1]
    assert round(a_static.robustness, 4) == 0.1195


def test_perkolationsschwelle_preset_numbers():
    inst = S.generate(20, 0.0, "random", 35)
    assert inst.n == 400 and inst.m == 760
    adj = A.adjacency(inst.n, inst.edges)
    fc = A.er_threshold_prediction(adj)
    assert round(fc, 3) == 0.737


def test_grad_gegen_betweenness_betriebsnetz_preset():
    a_deg = ev.analyse(ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="degree_adaptive", seed=35))[1]
    a_bet = ev.analyse(ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="betweenness_adaptive", seed=35))[1]
    assert round(a_deg.robustness, 4) == 0.2055 and round(a_bet.robustness, 4) == 0.1666


def test_drei_netze_vergleich_preset_gaps():
    city = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", seed=35)
    ba = ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, seed=35)
    barbell = ev.Settings(kind="barbell", k_barbell=8, seed=35)
    rows = ev.network_comparison(city, ba, barbell, seed=35, n_random_orders=C.N_RANDOM_ORDERS_FOR_MEAN)
    by_label = {r["label"]: r for r in rows}
    assert round(by_label["Betriebsnetz"]["gap"], 2) == 0.09
    assert round(by_label["Barbell"]["gap"], 2) == 0.10
    assert round(by_label["Skalenfrei"]["gap"], 2) == 0.30
    assert by_label["Skalenfrei"]["gap"] > by_label["Betriebsnetz"]["gap"]
    assert by_label["Skalenfrei"]["gap"] > by_label["Barbell"]["gap"]
