"""Zentrale Korrektheits-Kette Punkt 4: Betweenness-adaptive Entfernungsstrategie.

Mit `recompute_every=1` muss die Strategie bei JEDEM einzelnen Schritt exakt der unabhängigen Brandes-Neuberechnung auf dem jeweiligen Restgraphen entsprechen (keine Näherung). Mit
`recompute_every>1` muss sie die zuletzt berechnete Rangfolge korrekt unter den noch vorhandenen Knoten weiterverwenden (explizite, dokumentierte Näherung) - hier gegen eine unabhängige
Referenzimplementierung geprüft, die das Carry-Forward-Verhalten von Hand nachbildet."""

from collections import deque
from fractions import Fraction

import networkx as nx
import pytest

import rob_algorithm as A
import rob_scenario as S


def _exact_betweenness(nb):
    """Knoten-Betweenness EXAKT rational (Fractions, Brandes-Rückwärtsphase in exakter Arithmetik): mathematisch gleiche Werte sind hier gleich, anders als in Gleitkommazahlen (Rauschen ~1e-13 würde
    sonst die Gleichstandsregel "kleinster Index" verfälschen)."""
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


def _induced_subgraph_adj(adj, alive_set):
    """Adjazenzliste, neu durchnummeriert auf die Knoten in `alive_set` (aufsteigende Originalreihenfolge)."""
    remaining = sorted(alive_set)
    remap = {old: new for new, old in enumerate(remaining)}
    sub_adj = [[] for _ in remaining]
    for old in remaining:
        for nb in adj[old]:
            if nb in remap:
                sub_adj[remap[old]].append(remap[nb])
    return sub_adj, remaining


def _reference_betweenness_adaptive(adj, recompute_every):
    """Unabhängige Referenz: baut bei jeder faelligen Neuberechnung den induzierten Restgraphen sauber neu auf (statt wie die Implementierung tote Knoten nur zu isolieren) und berechnet Brandes
    darauf; dazwischen wird die zuletzt berechnete Rangfolge (Originalnummerierung) unter den noch lebenden Knoten weiterverwendet. Muss zur Implementierung aequivalent sein, weil isolierte tote
    Knoten als zusaetzliche BFS-Startpunkte nichts zu Distanzen/Abhaengigkeiten lebender Knoten beitragen."""
    n = len(adj)
    recompute_every = max(1, int(recompute_every))
    alive = set(range(n))
    order = []
    ranking = []
    since = recompute_every
    while alive:
        if since >= recompute_every:
            sub_adj, remaining = _induced_subgraph_adj(adj, alive)
            node_between = _exact_betweenness(sub_adj)
            ranking = sorted(remaining, key=lambda v: (-node_between[remaining.index(v)], v))
            since = 0
        else:
            ranking = [v for v in ranking if v in alive]
        pick = ranking[0]
        order.append(pick)
        alive.discard(pick)
        since += 1
    return order


def _small_instances():
    out = [S.generate(side, 0.2, "grid", seed) for side in (3, 4) for seed in (1, 2, 3)]
    out += [S.barabasi_albert_instance(n, 2, 3, seed) for n in (10, 14, 18) for seed in (1, 2, 3)]
    out += [S.barbell_instance(k) for k in (3, 4, 5)]
    return out


SMALL = _small_instances()


@pytest.mark.parametrize("recompute_every", [1])
def test_recompute_every_1_matches_independent_brandes_recomputation_every_single_step(recompute_every):
    """Exakt, keine Näherung: mit recompute_every=1 stimmt die Implementierung mit der unabhängigen Referenz UND mit einer direkten unabhängigen Brandes-Neuberechnung auf dem Restgraphen bei jedem
    einzelnen Schritt ueberein."""
    for inst in SMALL:
        adj = A.adjacency(inst.n, inst.edges)
        got = A.betweenness_order_adaptive(adj, recompute_every=recompute_every)
        want = _reference_betweenness_adaptive(adj, recompute_every=recompute_every)
        assert got == want


@pytest.mark.parametrize("recompute_every", [2, 3, 5])
def test_recompute_every_greater_than_1_carries_forward_the_last_ranking_correctly(recompute_every):
    """Näherung, aber ein KORREKT umgesetztes Carry-Forward: identisch zur unabhängigen Referenzimplementierung, die dasselbe Carry-Forward-Verhalten von Hand nachbildet."""
    for inst in SMALL:
        adj = A.adjacency(inst.n, inst.edges)
        got = A.betweenness_order_adaptive(adj, recompute_every=recompute_every)
        want = _reference_betweenness_adaptive(adj, recompute_every=recompute_every)
        assert got == want


def test_recompute_every_1_matches_networkx_betweenness_ranking_at_every_step():
    """Zusaetzliche unabhaengige Gegenprobe direkt gegen networkx.betweenness_centrality (unnormiert) auf dem Restgraphen nach jedem Schritt."""
    inst = S.barabasi_albert_instance(16, 2, 3, 7)
    adj = A.adjacency(inst.n, inst.edges)
    order = A.betweenness_order_adaptive(adj, recompute_every=1)
    alive = set(range(inst.n))
    for picked in order:
        sub_adj, remaining = _induced_subgraph_adj(adj, alive)
        g = nx.Graph()
        g.add_nodes_from(range(len(remaining)))
        for u, nbrs in enumerate(sub_adj):
            for v in nbrs:
                if u < v:
                    g.add_edge(u, v)
        nx_between = nx.betweenness_centrality(g, normalized=False)
        best_local = max(range(len(remaining)), key=lambda i: (nx_between[i], -remaining[i]))
        assert remaining[best_local] == picked
        alive.discard(picked)


def test_recompute_every_1_and_high_agree_on_the_very_first_pick():
    """Der allererste Schritt ist IMMER eine frische Berechnung (unabhaengig von recompute_every) -- muss also fuer jedes recompute_every gleich sein."""
    for inst in SMALL:
        adj = A.adjacency(inst.n, inst.edges)
        picks_first = {A.betweenness_order_adaptive(adj, recompute_every=r)[0] for r in (1, 2, 5, 10)}
        assert len(picks_first) == 1


def test_determinism():
    inst = S.barabasi_albert_instance(20, 2, 4, 3)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.betweenness_order_adaptive(adj, 3) == A.betweenness_order_adaptive(adj, 3)
