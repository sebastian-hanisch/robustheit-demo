"""Unabhängiges Orakel für die Entfernungsstrategien: Grad-adaptiv gegen naives Neuscannen, Betweenness-adaptiv gegen exakte rationale Betweenness (Fractions) auch auf Graphen mit vielen
mathematischen Gleichständen (Würfel, Dodekaeder, zirkulant, Raster), S(k)/Komponenten/mittlerer Restgrad gegen networkx, R und Schwelle von Hand. Früher entschied bei mathematisch gleicher
Betweenness Gleitkommarauschen statt des Index (Gleichstandsregel "kleinster Index" verletzt)."""

import random
from collections import deque
from fractions import Fraction

import networkx as nx
import pytest

import rob_algorithm as A
import rob_scenario as S


def _exact_betweenness(nb):
    n = len(nb)
    bc = [Fraction(0)] * n
    for s in range(n):
        dist, sigma, pred, order, q = {s: 0}, {s: 1}, {s: []}, [], deque([s])
        while q:
            u = q.popleft()
            order.append(u)
            for v in nb[u]:
                if v not in dist:
                    dist[v], sigma[v], pred[v] = dist[u] + 1, 0, []
                    q.append(v)
                if dist[v] == dist[u] + 1:
                    sigma[v] += sigma[u]
                    pred[v].append(u)
        delta = {v: Fraction(0) for v in order}
        for w in reversed(order):
            for v in pred[w]:
                delta[v] += Fraction(sigma[v], sigma[w]) * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]
    return [x / 2 for x in bc]


def _exact_order(adj, every):
    n = len(adj)
    nbrs = [set(a) for a in adj]
    alive = [True] * n
    order, ranking, since = [], [], every
    while any(alive):
        if since >= every:
            bc = _exact_betweenness([sorted(nbrs[v]) if alive[v] else [] for v in range(n)])
            ranking = sorted([v for v in range(n) if alive[v]], key=lambda v: (-bc[v], v))
            since = 0
        else:
            ranking = [v for v in ranking if alive[v]]
        p = ranking[0]
        order.append(p)
        alive[p] = False
        for u in nbrs[p]:
            nbrs[u].discard(p)
        nbrs[p] = set()
        since += 1
    return order


def _adj(g):
    n = g.number_of_nodes()
    return A.adjacency(n, [(min(u, v), max(u, v), 1.0) for u, v in g.edges])


def _symmetric_graphs():
    gs = [nx.cycle_graph(k) for k in (5, 6, 8, 10)]
    gs += [nx.convert_node_labels_to_integers(nx.hypercube_graph(3)), nx.dodecahedral_graph(), nx.circulant_graph(10, [1, 2]), nx.petersen_graph(),
           nx.complete_bipartite_graph(3, 3), nx.convert_node_labels_to_integers(nx.grid_2d_graph(3, 4)), nx.barbell_graph(4, 1)]
    return gs


def test_betweenness_adaptive_matches_exact_rational_ranking_with_ties():
    for g in _symmetric_graphs():
        adj = _adj(g)
        for every in (1, 3):
            assert A.betweenness_order_adaptive(adj, every) == _exact_order(adj, every)


def test_betweenness_adaptive_on_small_demo_instances_matches_exact():
    for inst in [S.generate(5, 0.2, "grid", sd) for sd in (1, 2)] + [S.barabasi_albert_instance(25, 2, 3, 4), S.barbell_instance(4)]:
        adj = A.adjacency(inst.n, inst.edges)
        for every in (1, 5):
            assert A.betweenness_order_adaptive(adj, every) == _exact_order(adj, every)


def test_degree_orders_sequence_and_indices_against_networkx_and_by_hand():
    rng = random.Random(7)
    for _ in range(120):
        n = rng.randint(1, 13)
        p = rng.choice([0, 0.1, 0.25, 0.5, 1.0])
        pairs = [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < p]
        g = nx.Graph()
        g.add_nodes_from(range(n))
        g.add_edges_from(pairs)
        adj = A.adjacency(n, [(u, v, 1.0) for u, v in pairs])
        cur, want = g.copy(), []
        while cur.number_of_nodes():
            v = min(cur.nodes, key=lambda x: (-cur.degree[x], x))
            want.append(v)
            cur.remove_node(v)
        assert A.degree_order_adaptive(adj) == want
        order = list(range(n))
        rng.shuffle(order)
        largest, counts, mdeg = A.remove_sequence(adj, order)
        cur = g.copy()
        for k in range(n + 1):
            if k:
                cur.remove_node(order[k - 1])
            comps = list(nx.connected_components(cur))
            assert largest[k] == (max(map(len, comps)) if comps else 0) and counts[k] == len(comps)
            assert mdeg[k] == pytest.approx(sum(d for _, d in cur.degree) / cur.number_of_nodes() if cur.number_of_nodes() else 0.0)
        if n:
            assert A.robustness_index(largest, n) == pytest.approx(sum(largest[k] / n for k in range(1, n + 1)) / n)
            for frac in (0.05, 0.5):
                k0 = next((k for k in range(n + 1) if largest[k] < frac * n), None)
                assert A.percolation_threshold(largest, n, frac) == pytest.approx(k0 / n if k0 is not None else 1.0)
