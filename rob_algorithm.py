"""Vier Entfernungsstrategien (welchen Knoten als nächstes entfernen?) und ihre Bausteine. **Zufall**: gleichverteilte Permutation. **Grad statisch**: Rangfolge einmal aus dem ursprünglichen Netz.
**Grad adaptiv** (Cohen, Erez, ben-Avraham & Havlin 2001): nach jeder Entfernung neu der aktuell höchstgradige Restknoten - genau diese adaptive Angriffsform bringt selbst robuste (skalenfreie) Netze
zum Einsturz, weil ständig ein NEUER Hub ins Visier gerät, sobald der alte weg ist. **Betweenness adaptiv**: dasselbe mit der aktuell höchsten Betweenness (Brandes 2001), mit einstellbarem
Neuberechnungs-Intervall (volle Brandes-Neuberechnung ist teuer, O(n*m) je Aufruf).

`adjacency()`, `bfs_distances()`, `degree_centrality()`, `betweenness_brandes()` (+ `_shortest_path_dag`, `brandes_source`) sind wortgleiche Kopien aus `cen_algorithm.py`."""

import heapq
import random
from collections import deque
from dataclasses import dataclass, field


def adjacency(n, edges, order="fixed", seed=0):
    """Adjazenzliste aus Kanten (u, v, ...); "fixed" = aufsteigende Nachbarn, "shuffled" = je Knoten gemischt (Seed fest, Python-`random`). Wortgleiche Kopie aus `cen_algorithm.py`."""
    adj = [[] for _ in range(n)]
    for e in edges:
        u, v = int(e[0]), int(e[1])
        adj[u].append(v)
        adj[v].append(u)
    for lst in adj:
        lst.sort()
    if order == "shuffled":
        rng = random.Random(int(seed) * 1_000_003 + 5150)
        for lst in adj:
            rng.shuffle(lst)
    elif order != "fixed":
        raise ValueError(f"unbekannte Reihenfolge {order}")
    return adj


def bfs_distances(adj, s):
    """Abstand von s zu jedem erreichbaren Knoten (-1 = unerreichbar). Gibt (dist, Schritte) zurück. Wortgleiche Kopie aus `cen_algorithm.py`."""
    n = len(adj)
    dist = [-1] * n
    dist[s] = 0
    queue = deque([s])
    steps = 1
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            steps += 1
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                queue.append(v)
                steps += 1
    return dist, steps


def degree_centrality(adj):
    """Grad je Knoten (Zahl der Nachbarn). Wortgleiche Kopie aus `cen_algorithm.py`."""
    return [len(nbrs) for nbrs in adj]


def _key(u, v):
    return (u, v) if u < v else (v, u)


def _shortest_path_dag(adj, s):
    """BFS-Vorgänger-DAG von s: (dist, sigma, order (Entdeckungsreihenfolge), preds, Schritte). Wortgleiche Kopie aus `cen_algorithm.py`."""
    n = len(adj)
    dist = [-1] * n
    sigma = [0] * n
    dist[s] = 0
    sigma[s] = 1
    preds = [[] for _ in range(n)]
    order = [s]
    queue = deque([s])
    steps = 1
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            steps += 1
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                queue.append(v)
                order.append(v)
                steps += 1
            if dist[v] == dist[u] + 1:
                sigma[v] += sigma[u]
                preds[v].append(u)
    return dist, sigma, order, preds, steps


@dataclass
class BrandesRun:
    source: int
    dist: list
    sigma: list
    order: list             # BFS-Entdeckungsreihenfolge (Vorwärtsphase)
    preds: list
    delta: list = field(default_factory=list)          # Abhängigkeit je Knoten NACH der Rückwärtsphase
    edge_delta: dict = field(default_factory=dict)      # Kanten-Abhängigkeit dieser einen Quelle
    steps: int = 0


def brandes_source(adj, s):
    """Ein Brandes-Durchlauf von einer einzigen Quelle s. Wortgleiche Kopie aus `cen_algorithm.py`."""
    dist, sigma, order, preds, steps = _shortest_path_dag(adj, s)
    n = len(adj)
    delta = [0.0] * n
    edge_delta = {}
    for w in reversed(order):
        coeff = (1.0 + delta[w]) / sigma[w]
        steps += 1
        for v in preds[w]:
            steps += 1
            c = sigma[v] * coeff
            delta[v] += c
            e = _key(v, w)
            edge_delta[e] = edge_delta.get(e, 0.0) + c
    return BrandesRun(s, dist, sigma, order, preds, delta, edge_delta, steps)


def betweenness_brandes(adj):
    """Brandes (2001): eine BFS je Startknoten (O(n*m) insgesamt), liefert Knoten- UND Kanten-Betweenness (unnormiert). Gibt (Knoten-Liste, Kanten-Dict, Elementarschritte) zurück. Wortgleiche Kopie
    aus `cen_algorithm.py`."""
    n = len(adj)
    node_raw = [0.0] * n
    edge_raw = {}
    steps = 0
    for s in range(n):
        run = brandes_source(adj, s)
        steps += run.steps
        for v in range(n):
            if v != s:
                node_raw[v] += run.delta[v]
        for e, c in run.edge_delta.items():
            edge_raw[e] = edge_raw.get(e, 0.0) + c
    node_between = [v * 0.5 for v in node_raw]
    edge_between = {e: c * 0.5 for e, c in edge_raw.items()}
    return node_between, edge_between, steps


# --- Komponenten (BFS, wiederverwendet aus bfs_distances) ---------------------------------------------------------------------------------------------


def components(adj):
    """Liste der Komponentengrößen (Reihenfolge = Fundreihenfolge des kleinsten Knotens jeder Komponente), über wiederholte BFS."""
    n = len(adj)
    seen = [False] * n
    sizes = []
    for s in range(n):
        if seen[s]:
            continue
        dist, _ = bfs_distances(adj, s)
        comp = [v for v, d in enumerate(dist) if d >= 0]
        for v in comp:
            seen[v] = True
        sizes.append(len(comp))
    return sizes


# --- Strategie 1: Zufall -------------------------------------------------------------------------------------------------------------------------------


def random_order(n, seed):
    """Gleichverteilte Zufallspermutation der n Knoten (Python-`random`-Hauskonvention, plattformunabhängig)."""
    rng = random.Random(int(seed) * 1_000_003 + 3391)
    order = list(range(n))
    rng.shuffle(order)
    return order


# --- Strategie 2: Grad statisch -------------------------------------------------------------------------------------------------------------------------


def degree_order_static(adj):
    """Rangfolge einmal aus dem URSPRÜNGLICHEN Grad, absteigend; Gleichstand nach kleinstem Index (deterministisch)."""
    n = len(adj)
    degree = [len(a) for a in adj]
    return sorted(range(n), key=lambda v: (-degree[v], v))


# --- Strategie 3: Grad adaptiv --------------------------------------------------------------------------------------------------------------------------


def degree_order_adaptive(adj):
    """Wiederholt der Knoten mit dem AKTUELL höchsten Grad im Restgraphen (Cohen u. a. 2001). Effizient über einen Max-Heap mit mitgeführten Gradzählern und Nachbarmengen: bei jeder Entfernung werden
    nur die Grade der (ehemaligen) Nachbarn dekrementiert und eine neue Heap-Eintragung für sie gepusht (lazy deletion - eine veraltete Eintragung wird beim Pop verworfen, wenn ihr gespeicherter Grad
    nicht mehr mit dem aktuellen Grad des Knotens übereinstimmt); KEIN volles O(n)-Neuscannen des gesamten Restgraphen je Schritt. Gleichstand nach kleinstem Index (Heap-Tupel-Vergleich)."""
    n = len(adj)
    neighbours = [set(a) for a in adj]
    degree = [len(a) for a in adj]
    alive = [True] * n
    heap = [(-degree[v], v) for v in range(n)]
    heapq.heapify(heap)
    order = []
    while heap:
        neg_d, v = heapq.heappop(heap)
        if not alive[v] or -neg_d != degree[v]:
            continue                                        # veraltete Eintragung (Grad hat sich seither geändert oder Knoten schon entfernt)
        order.append(v)
        alive[v] = False
        for u in neighbours[v]:
            if alive[u]:
                neighbours[u].discard(v)
                degree[u] -= 1
                heapq.heappush(heap, (-degree[u], u))
        neighbours[v] = set()
    return order


# --- Strategie 4: Betweenness adaptiv -------------------------------------------------------------------------------------------------------------------


def betweenness_order_adaptive(adj, recompute_every=1):
    """Wiederholt der Knoten mit der aktuell höchsten Betweenness im Restgraphen. Volle Brandes-Neuberechnung (teuer, O(n*m) je Aufruf) nur alle `recompute_every` Entfernungen; dazwischen wird die
    ZULETZT berechnete Rangfolge unter den noch vorhandenen Knoten weiterverwendet (explizite Näherung, nicht der exakte aktuelle Wert - kalibriert gegen die Kosten, s. README). `recompute_every=1`
    berechnet bei JEDEM Schritt neu und ist damit exakt."""
    n = len(adj)
    recompute_every = max(1, int(recompute_every))
    neighbours = [set(a) for a in adj]
    alive = [True] * n
    order = []
    ranking = []                                            # zuletzt berechnete Rangfolge (Knoten, absteigende Betweenness, Gleichstand kleinster Index), nur unter den noch lebenden Knoten gültig
    since_recompute = recompute_every                       # erzwingt eine Neuberechnung beim allerersten Schritt

    def current_adj():
        return [sorted(neighbours[v]) if alive[v] else [] for v in range(n)]

    def recompute_ranking():
        cur = current_adj()
        node_between, _, _ = betweenness_brandes(cur)
        alive_nodes = [v for v in range(n) if alive[v]]
        # Gleichstand nach kleinstem Index: Betweenness-Werte, die mathematisch gleich sind, unterscheiden sich in Gleitkommazahlen oft um 1e-13 (Summationsreihenfolge) - ohne Rundung
        # entschiede dieses Rauschen statt des Index (z. B. Würfel, Dodekaeder, zirkulante Graphen); Rundung auf 9 Stellen beseitigt das, echte Unterschiede sind viel größer.
        return sorted(alive_nodes, key=lambda v: (-round(node_between[v], 9), v))

    while any(alive):
        if since_recompute >= recompute_every:
            ranking = recompute_ranking()
            since_recompute = 0
        else:
            ranking = [v for v in ranking if alive[v]]      # zuletzt berechnete Rangfolge, auf die noch vorhandenen Knoten eingeschränkt
        pick = ranking[0]
        order.append(pick)
        alive[pick] = False
        for u in neighbours[pick]:
            neighbours[u].discard(pick)
        neighbours[pick] = set()
        since_recompute += 1
    return order


# --- Entfernungsfolge: S(k), Komponentenzahl, mittlerer Restgrad ------------------------------------------------------------------------------------------


def remove_sequence(adj, order):
    """Entfernt die Knoten in `order` einen nach dem anderen (k=0..n Knoten entfernt) und misst nach JEDEM Schritt: Größe der größten Komponente S(k) (Riesenkomponente), Zahl der Komponenten unter
    den verbleibenden Knoten, mittlerer Restgrad. Gibt drei Listen der Länge n+1 zurück (Index k = Zustand nach k Entfernungen; k=0 ist das ursprüngliche Netz)."""
    n = len(adj)
    neighbours = [set(a) for a in adj]
    alive = [True] * n

    def _state():
        remaining = [v for v in range(n) if alive[v]]
        if not remaining:
            return 0, 0, 0.0
        sub_adj = [sorted(neighbours[v]) if alive[v] else [] for v in range(n)]
        alive_sizes = [len(comp) for comp in _alive_components(sub_adj, alive)]
        largest = max(alive_sizes) if alive_sizes else 0
        mean_degree = sum(len(neighbours[v]) for v in remaining) / len(remaining)
        return largest, len(alive_sizes), mean_degree

    largest_seq, count_seq, degree_seq = [], [], []
    l0, c0, d0 = _state()
    largest_seq.append(l0)
    count_seq.append(c0)
    degree_seq.append(d0)
    for v in order:
        alive[v] = False
        for u in neighbours[v]:
            neighbours[u].discard(v)
        neighbours[v] = set()
        largest, count, mean_degree = _state()
        largest_seq.append(largest)
        count_seq.append(count)
        degree_seq.append(mean_degree)
    return largest_seq, count_seq, degree_seq


def _alive_components(sub_adj, alive):
    """Liste der Komponenten (je eine Liste lebender Knoten) unter den noch lebenden Knoten, per BFS - tote (isolierte) Knoten werden nicht mitgezählt."""
    n = len(sub_adj)
    seen = [False] * n
    comps = []
    for s in range(n):
        if not alive[s] or seen[s]:
            continue
        dist, _ = bfs_distances(sub_adj, s)
        comp = [v for v, d in enumerate(dist) if d >= 0 and alive[v]]
        for v in comp:
            seen[v] = True
        comps.append(comp)
    return comps


def percolation_threshold(sizes, n, frac=0.5):
    """Kleinstes k/n, bei dem S(k) < frac*n (gemessene, ENDLICHE-Größe-Schwelle - keine asymptotische Definition). `sizes` ist S(k) für k=0..n (wie von `remove_sequence` geliefert). Gibt 1.0 zurück,
    wenn die Schwelle nie unterschritten wird (z. B. n zu klein)."""
    if n <= 0:
        return 0.0
    threshold_size = frac * n
    for k, s in enumerate(sizes):
        if s < threshold_size:
            return k / n
    return 1.0


def robustness_index(sizes, n):
    """R = (1/n) * Sum_{k=1}^{n} S(k)/n (Schneider, Moreira, Andrade, Herrmann & Havlin 2011) - die Fläche unter der (normierten) Riesenkomponenten-Kurve, ein zusammenfassender Robustheitswert je
    Strategie/Instanz. `sizes` ist S(k) für k=0..n; die Summe läuft bewusst NUR über k=1..n (S(0), das intakte Netz vor jeder Entfernung, zählt nicht mit - wie im Original)."""
    if n <= 0:
        return 0.0
    total = sum(sizes[k] for k in range(1, n + 1)) / n
    return total / n


def er_threshold_prediction(adj):
    """f_c = 1 - 1/<k> (Cohen, Erez, ben-Avraham & Havlin 2000) - geschlossene Vorhersage der Perkolationsschwelle unter ZUFÄLLIGEM Knotenausfall auf ER-artigen (Poisson-Gradverteilung) Netzen,
    aus dem mittleren Grad <k> des ungestörten Netzes. Gibt 0.0 zurück, wenn <k> <= 1 (kein Anteil reicht dann aus, keine sinnvolle Vorhersage - der Nenner der Formel würde <=0)."""
    n = len(adj)
    if n == 0:
        return 0.0
    mean_degree = sum(len(a) for a in adj) / n
    if mean_degree <= 1.0:
        return 0.0
    return 1.0 - 1.0 / mean_degree


# --- Zustand nach k Entfernungen (fuer die "Angriff in Aktion"-Karte, Schritt 1 der App) --------------------------------------------------------------


def partial_removal_state(adj, order, k):
    """Zustand nach den ersten k Entfernungen aus `order`: (entfernte Knoten als Menge, Liste der Komponenten unter den noch lebenden Knoten - je eine sortierte Liste, groesste zuerst)."""
    n = len(adj)
    alive = [True] * n
    for v in order[:k]:
        alive[v] = False
    sub_adj = [[u for u in adj[v] if alive[u]] if alive[v] else [] for v in range(n)]
    comps = [sorted(c) for c in _alive_components(sub_adj, alive)]
    comps.sort(key=len, reverse=True)
    removed = set(order[:k])
    return removed, comps
