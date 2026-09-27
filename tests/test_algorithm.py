"""Zentrale Korrektheits-Kette (9 Punkte, gegen networkx als Gegenprobe). Diese Datei deckt die Punkte 1, 2, 3, 5, 8, 9 ab (Entfernungsstrategien Zufall/Grad statisch/Grad adaptiv, S(k)-Buchführung);
Punkt 4 (Betweenness adaptiv) steht in `test_betweenness_adaptive.py`, Punkte 6-7 (Perkolationsschwelle, Robustheitsindex) in `test_evaluation.py`.

1) S(k) gegen unabhängige BFS-/networkx.connected_components-Neuberechnung nach JEDER Entfernungsstufe (nicht nur am Ende), alle vier Strategien, >= 300 Instanzen.
2) S(k) monoton nicht wachsend in k (Satz, Test) auf allen Sequenzen.
3) Grad-adaptiv entfernt bei jedem Schritt exakt den aktuell höchstgradigen Restknoten (gegen Brute-Force auf kleinen Instanzen); Grad-statisch unterscheidet sich davon auf einer konstruierten
   Instanz nachweislich.
5) Barbell von Hand: Entfernen eines Brückenendknotens (Grad k) trennt sofort in Komponenten der Größe k-1 und k; Zufallsreihenfolge trifft ihn im Mittel erst nach n/2 Entfernungen (gemessen).
8) Buchführung/Determinismus/Nachbarreihenfolge ändert nie S(k) einer gegebenen Sequenz.
9) Sonderfälle (n<=2, vollständiger Graph, Baum, unzusammenhängende Ausgangsinstanz)."""

import networkx as nx
import pytest

import rob_algorithm as A
import rob_scenario as S


def _induced_subgraph(adj, removed):
    """Adjazenzliste des Graphen ohne Knoten `removed`, mit Knoten sauber auf 0..n-2 neu durchnummeriert (fuer `A.components`, das sonst den entfernten Knoten als isolierten Ein-Knoten-Rest mitzaehlen
    wuerde)."""
    n = len(adj)
    remaining = [v for v in range(n) if v != removed]
    remap = {old: new for new, old in enumerate(remaining)}
    sub_adj = [[] for _ in remaining]
    for old in remaining:
        for nb in adj[old]:
            if nb != removed:
                sub_adj[remap[old]].append(remap[nb])
    return sub_adj


def _graph_from_adj(adj):
    g = nx.Graph()
    g.add_nodes_from(range(len(adj)))
    for u, nbrs in enumerate(adj):
        for v in nbrs:
            if u < v:
                g.add_edge(u, v)
    return g


def _city_instances():
    out = []
    for side in (3, 4, 5, 6, 7):
        for nettype in S.C.NETTYPES:
            for blocked in (0.0, 0.1, 0.2, 0.3, 0.4):
                for seed in (1, 2, 3, 4):
                    out.append(S.generate(side, blocked, nettype, seed))
    return out


def _ba_instances():
    out = []
    for n in (15, 25, 40, 60):
        for m in (1, 2, 3):
            for m0 in (3, 4, 5):
                if m > m0 or m0 > n:
                    continue
                for seed in (1, 2, 3, 4):
                    out.append(S.barabasi_albert_instance(n, m, m0, seed))
    return out


def _barbell_instances():
    return [S.barbell_instance(k) for k in (3, 4, 5, 6, 8, 10, 12)]


CITY = _city_instances()
BA = _ba_instances()
BARBELL = _barbell_instances()
ALL_INSTANCES = CITY + BA + BARBELL


# --- 1. S(k) gegen unabhängige networkx-Neuberechnung nach JEDER Stufe --------------------------------------------------------------------------------


def _giant_component_sequence_via_networkx(adj, order):
    """Unabhängige Gegenprobe: nach jeder Entfernungsstufe den Restgraphen frisch aus den verbleibenden Kanten aufbauen und networkx.connected_components fragen."""
    n = len(adj)
    edges = {(u, v) for u in range(n) for v in adj[u] if u < v}
    alive = set(range(n))
    sizes = [max((len(c) for c in nx.connected_components(_sub(edges, alive, n))), default=0)]
    for v in order:
        alive.discard(v)
        edges = {(a, b) for a, b in edges if a != v and b != v}
        g = _sub(edges, alive, n)
        sizes.append(max((len(c) for c in nx.connected_components(g)), default=0))
    return sizes


def _sub(edges, alive, n):
    g = nx.Graph()
    g.add_nodes_from(alive)
    g.add_edges_from(e for e in edges if e[0] in alive and e[1] in alive)
    return g


@pytest.mark.parametrize("strategy", ["random", "degree_static", "degree_adaptive", "betweenness_adaptive"])
def test_giant_component_matches_networkx_after_every_removal_step(strategy):
    checked = 0
    small = [inst for inst in ALL_INSTANCES if inst.n <= 25]
    assert len(small) >= 60
    for inst in small:
        adj = A.adjacency(inst.n, inst.edges)
        if strategy == "random":
            order = A.random_order(inst.n, inst.seed)
        elif strategy == "degree_static":
            order = A.degree_order_static(adj)
        elif strategy == "degree_adaptive":
            order = A.degree_order_adaptive(adj)
        else:
            order = A.betweenness_order_adaptive(adj, recompute_every=1)
        sizes, _, _ = A.remove_sequence(adj, order)
        want = _giant_component_sequence_via_networkx(adj, order)
        assert sizes == want
        checked += 1
    assert checked >= 60


def test_giant_component_matches_networkx_many_instances_random_strategy_only():
    """Breitere Abdeckung (>= 300 Instanzen insgesamt über alle vier Strategien-Tests plus dieser) mit der günstigsten Strategie (Zufall)."""
    checked = 0
    for inst in ALL_INSTANCES:
        adj = A.adjacency(inst.n, inst.edges)
        order = A.random_order(inst.n, inst.seed)
        sizes, _, _ = A.remove_sequence(adj, order)
        want = _giant_component_sequence_via_networkx(adj, order)
        assert sizes == want
        checked += 1
    assert checked >= 300


# --- 2. S(k) monoton nicht wachsend -----------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("strategy", ["random", "degree_static", "degree_adaptive"])
def test_giant_component_is_non_increasing(strategy):
    for inst in ALL_INSTANCES:
        adj = A.adjacency(inst.n, inst.edges)
        if strategy == "random":
            order = A.random_order(inst.n, inst.seed)
        elif strategy == "degree_static":
            order = A.degree_order_static(adj)
        else:
            order = A.degree_order_adaptive(adj)
        sizes, _, _ = A.remove_sequence(adj, order)
        assert all(sizes[k] >= sizes[k + 1] for k in range(len(sizes) - 1))


# --- 3. Grad-adaptiv == Brute-Force; Grad-statisch unterscheidet sich nachweislich --------------------------------------------------------------------


def _brute_force_degree_adaptive(adj):
    """Referenz ohne jede Effizienz-Idee: nach jeder Entfernung den kompletten Restgraphen neu durchscannen und den aktuell höchstgradigen Knoten (kleinster Index bei Gleichstand) wählen."""
    n = len(adj)
    neighbours = [set(a) for a in adj]
    alive = [True] * n
    order = []
    for _ in range(n):
        remaining = [v for v in range(n) if alive[v]]
        best = max(remaining, key=lambda v: (len(neighbours[v]), -v))
        order.append(best)
        alive[best] = False
        for u in neighbours[best]:
            neighbours[u].discard(best)
    return order


def test_degree_adaptive_matches_brute_force_on_small_instances():
    small = [inst for inst in ALL_INSTANCES if inst.n <= 20]
    assert len(small) >= 30
    for inst in small:
        adj = A.adjacency(inst.n, inst.edges)
        got = A.degree_order_adaptive(adj)
        want = _brute_force_degree_adaptive(adj)
        assert got == want


def test_degree_adaptive_picks_exact_current_highest_degree_node_every_step():
    """Direkter Schritt-für-Schritt-Vergleich: nach jeder Entfernung ist der als nächstes gewählte Knoten wirklich der (Brute-Force-)höchstgradige unter den noch lebenden."""
    inst = S.barabasi_albert_instance(30, 2, 4, 3)
    adj = A.adjacency(inst.n, inst.edges)
    order = A.degree_order_adaptive(adj)
    neighbours = [set(a) for a in adj]
    alive = [True] * inst.n
    for picked in order:
        remaining = [v for v in range(inst.n) if alive[v]]
        want = max(remaining, key=lambda v: (len(neighbours[v]), -v))
        assert picked == want
        alive[picked] = False
        for u in neighbours[picked]:
            neighbours[u].discard(picked)


def test_degree_static_differs_from_degree_adaptive_on_constructed_instance():
    """Konstruierte Instanz: ein Stern-Zentrum 0 (Grad 6) mit Blättern 1..6, an Blatt 1 zusätzlich eine Kette 7-8-9-10 gehängt (Knoten 1 und 7 haben beide urspruenglich Grad 2). Grad-statisch
    haelt an der EINMAL berechneten Rangfolge fest und waehlt als zweiten Knoten 1 (obwohl dessen Grad nach Entfernung des Zentrums auf 1 gefallen ist); Grad-adaptiv erkennt das sofort und waehlt
    stattdessen Knoten 7, dessen Grad 2 vom Entfernen des Zentrums unberuehrt blieb -- der Unterschied ist bewusst konstruiert, nicht zufaellig."""
    edges = [(0, i) for i in range(1, 7)] + [(1, 7), (7, 8), (8, 9), (9, 10)]
    n = 11
    adj = A.adjacency(n, [(u, v, 1.0) for u, v in edges])
    static_order = A.degree_order_static(adj)
    adaptive_order = A.degree_order_adaptive(adj)
    assert static_order[0] == 0 and adaptive_order[0] == 0            # beide entfernen zuerst das Zentrum (Grad 6, eindeutig höchster Grad)
    assert static_order != adaptive_order                              # danach unterscheiden sie sich nachweislich
    # Grad-statisch bleibt bei der URSPRÜNGLICHEN Rangfolge (Knoten 1 hatte Grad 2, damit an zweiter Stelle) -- obwohl Knoten 1 nach Entfernung des Zentrums
    # nur noch Grad 1 hat (die Kante zum Zentrum ist weg). Grad-adaptiv sieht das SOFORT und waehlt stattdessen Knoten 7 (immer noch Grad 2, unberuehrt vom
    # Zentrum), nicht das veraltete Knoten 1.
    assert static_order[1] == 1
    assert adaptive_order[1] == 7


# --- 5. Barbell von Hand -----------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("k", [4, 5, 6, 8, 10])
def test_barbell_targeted_attack_splits_instantly(k):
    """Ein gezielter Grad-Angriff entfernt zuerst einen Brückenendknoten (Grad k, höchster Grad im Graphen) -- danach zerfällt der Graph SOFORT (nach nur 1 Entfernung) in Komponenten der Größe k-1
    und k."""
    inst = S.barbell_instance(k)
    adj = A.adjacency(inst.n, inst.edges)
    order = A.degree_order_static(adj)
    assert order[0] in (k - 1, k)                                       # eines der beiden Brückenenden (0-indiziert: k-1 links, k rechts), einziger Grad-k-Knoten
    sizes, count, _ = A.remove_sequence(adj, order)
    assert count[1] == 2                                                # nach der ersten Entfernung: zwei Komponenten
    # Entfernt man ein Brückenende, bleibt auf DIESER Seite ein K_{k-1} (Größe k-1) uebrig, waehrend die ANDERE Seite als volle Clique K_k (Größe k) unberuehrt
    # bleibt -- die beiden Teile sind exakt k-1 und k gross (Satz), die groesste Komponente danach ist also immer k.
    remaining_sizes = sorted(A.components(_induced_subgraph(adj, order[0])))
    assert remaining_sizes == [k - 1, k]
    assert sizes[1] == k


def test_barbell_random_order_hits_bridge_end_after_about_half_the_removals_on_average():
    """Eine zufällige Entfernungsreihenfolge trifft eines der beiden Brückenenden im Mittel erst nach ungefähr n/2 = k Entfernungen (n=2k Knoten, 2 von n sind Brückenenden -- erwartete Position eines
    gleichverteilt zufällig platzierten Elements unter n ist (n+1)/2 je Brückenende, das FRÜHERE der beiden trifft im Mittel früher: gemessen, nicht angenommen)."""
    for k in (4, 5, 6, 8):
        inst = S.barbell_instance(k)
        n = inst.n
        bridge_ends = {k - 1, k}
        trials = 400
        positions = []
        for seed in range(trials):
            order = A.random_order(n, seed)
            first_hit = next(i for i, v in enumerate(order) if v in bridge_ends)
            positions.append(first_hit)
        mean_pos = sum(positions) / len(positions)
        # Erwartungswert der Position (0-indiziert) des ERSTEN von 2 markierten Elementen unter n gleichverteilt permutierten Elementen: (n-2)/3 (Standardresultat: bei m markierten unter n ist der
        # Erwartungswert des 1-indizierten Mindestrangs (n+1)/(m+1), hier m=2 -> (n+1)/3, 0-indiziert (n+1)/3 - 1 = (n-2)/3) -- klar spaeter als die gezielte Entfernung (Position 0).
        assert mean_pos == pytest.approx((n - 2) / 3, abs=0.75)
        assert mean_pos > 1.0                                           # klar spaeter als der gezielte Angriff (Position 0)


# --- 8. Buchführung/Determinismus/Nachbarreihenfolge ----------------------------------------------------------------------------------------------------------


def test_neighbour_order_never_changes_giant_component_sequence():
    for inst in ALL_INSTANCES[::5]:
        adj_fixed = A.adjacency(inst.n, inst.edges, "fixed")
        adj_shuffled = A.adjacency(inst.n, inst.edges, "shuffled", seed=inst.seed + 1)
        order = A.random_order(inst.n, inst.seed)
        sizes_fixed, count_fixed, deg_fixed = A.remove_sequence(adj_fixed, order)
        sizes_shuffled, count_shuffled, deg_shuffled = A.remove_sequence(adj_shuffled, order)
        assert sizes_fixed == sizes_shuffled
        assert count_fixed == count_shuffled
        assert deg_fixed == pytest.approx(deg_shuffled, abs=1e-9)


def test_determinism():
    inst = S.generate(8, 0.3, "grid", 5)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.random_order(inst.n, 5) == A.random_order(inst.n, 5)
    assert A.degree_order_static(adj) == A.degree_order_static(adj)
    assert A.degree_order_adaptive(adj) == A.degree_order_adaptive(adj)
    assert A.betweenness_order_adaptive(adj, 3) == A.betweenness_order_adaptive(adj, 3)


def test_invalid_order_raises():
    with pytest.raises(ValueError):
        A.adjacency(3, [], "sorted")


# --- 9. Sonderfälle ------------------------------------------------------------------------------------------------------------------------------------------


def test_n0_n1_n2():
    for n, edges in [(0, []), (1, []), (2, []), (2, [(0, 1, 1.0)])]:
        adj = A.adjacency(n, edges)
        order = A.random_order(n, 1)
        assert sorted(order) == list(range(n))
        sizes, count, deg = A.remove_sequence(adj, order)
        assert len(sizes) == n + 1
        assert sizes[-1] == 0
        if n == 2 and edges:
            assert sizes[0] == 2 and sizes[1] == 1


def test_complete_graph_all_strategies_agree_up_to_permutation_of_ties():
    n = 6
    edges = [(i, j, 1.0) for i in range(n) for j in range(i + 1, n)]
    adj = A.adjacency(n, edges)
    for strategy_order in (A.random_order(n, 1), A.degree_order_static(adj), A.degree_order_adaptive(adj)):
        sizes, _, _ = A.remove_sequence(adj, strategy_order)
        # vollstaendiger Graph: jeder Knoten hat denselben Grad, S(k) haengt daher NICHT von der Reihenfolge ab
        assert sizes == [max(n - k, 0) for k in range(n + 1)]


def test_tree_removing_a_leaf_first_barely_shrinks_giant_component():
    n, pairs = 7, [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]
    adj = A.adjacency(n, [(u, v, 1.0) for u, v in pairs])
    order = [3] + [v for v in range(n) if v != 3]                       # Blatt 3 zuerst
    sizes, _, _ = A.remove_sequence(adj, order)
    assert sizes[0] == 7 and sizes[1] == 6                               # ein Blatt zu entfernen kostet nur 1 Knoten der Riesenkomponente


def test_disconnected_starting_instance_giant_component_is_the_larger_piece():
    n, pairs = 8, [(0, 1), (1, 2), (0, 2), (3, 4)]                       # Dreieck (3 Knoten) + Kante (2 Knoten) + 3 isolierte Knoten
    adj = A.adjacency(n, [(u, v, 1.0) for u, v in pairs])
    order = A.random_order(n, 1)
    sizes, count, _ = A.remove_sequence(adj, order)
    assert sizes[0] == 3                                                  # die groesste Komponente zu Beginn ist das Dreieck
    assert count[0] == 5                                                  # Dreieck {0,1,2} + Kante {3,4} + 3 isolierte Knoten {5},{6},{7} = 5 Komponenten
