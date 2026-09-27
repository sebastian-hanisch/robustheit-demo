"""Plotly-Figuren: Angriffskarte (entfernte Knoten ausgegraut, größte Restkomponente hervorgehoben), S(f)-Kurve mit Perkolationsschwelle (+ Cohen-Vorhersage bei ER-artigen Instanzen), alle vier
Strategien überlagert samt R-Balken, Drei-Netze-Vergleichstabelle/-Balken. Alle Achsen fest (fixedrange), Karten nutzen `scaleanchor` mit autorange und zwei unsichtbaren Eckpunkten (Hauskonvention)."""

import plotly.graph_objects as go

TEAL, ORANGE, BLUE, RED, PURPLE, GREY, LIGHT = "#2F6B65", "#f58518", "#4c78a8", "#e45756", "#7b3fbf", "#b7bec7", "#e8ebee"
STRATEGY_COLORS = {"random": BLUE, "degree_static": ORANGE, "degree_adaptive": RED, "betweenness_adaptive": PURPLE}


def _lines(xy, pairs):
    xs, ys = [], []
    for u, v in pairs:
        xs += [xy[u][0], xy[v][0], None]
        ys += [xy[u][1], xy[v][1], None]
    return xs, ys


def _corners_trace(xy):
    pad = 0.4
    return go.Scatter(x=[xy[:, 0].min() - pad, xy[:, 0].max() + pad], y=[xy[:, 1].min() - pad, xy[:, 1].max() + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip")


# --- 1 · Angriff in Aktion ------------------------------------------------------------------------------------------------------------------------------


def build_attack_map(xy, edges, removed, giant_nodes):
    """Karte: entfernte Knoten/Kanten hellgrau, überlebende Kanten dünn grau, die größte Restkomponente TEAL hervorgehoben, übrige lebende Knoten (kleinere Komponenten) ORANGE."""
    n = len(xy)
    giant_set = set(giant_nodes)
    alive_edges = [(u, v) for u, v in edges if u not in removed and v not in removed]
    removed_edges = [(u, v) for u, v in edges if u in removed or v in removed]

    fig = go.Figure()
    rx, ry = _lines(xy, removed_edges)
    fig.add_trace(go.Scatter(x=rx, y=ry, mode="lines", line=dict(color=LIGHT, width=1.0), hoverinfo="skip", showlegend=False))
    ax, ay = _lines(xy, alive_edges)
    fig.add_trace(go.Scatter(x=ax, y=ay, mode="lines", line=dict(color=GREY, width=1.0), opacity=0.6, hoverinfo="skip", showlegend=False))

    removed_xy = [xy[v] for v in range(n) if v in removed]
    other_xy = [xy[v] for v in range(n) if v not in removed and v not in giant_set]
    giant_xy = [xy[v] for v in range(n) if v in giant_set]

    if removed_xy:
        fig.add_trace(go.Scatter(x=[p[0] for p in removed_xy], y=[p[1] for p in removed_xy], mode="markers", marker=dict(size=6, color=LIGHT, line=dict(width=1, color=GREY)),
                                  name=f"Entfernt ({len(removed_xy)})", hoverinfo="skip"))
    if other_xy:
        fig.add_trace(go.Scatter(x=[p[0] for p in other_xy], y=[p[1] for p in other_xy], mode="markers", marker=dict(size=6, color=ORANGE), name=f"Andere Komponente ({len(other_xy)})",
                                  hoverinfo="skip"))
    if giant_xy:
        fig.add_trace(go.Scatter(x=[p[0] for p in giant_xy], y=[p[1] for p in giant_xy], mode="markers", marker=dict(size=7, color=TEAL), name=f"Größte Komponente ({len(giant_xy)})",
                                  hoverinfo="skip"))
    fig.add_trace(_corners_trace(xy))
    fig.update_layout(height=460, margin=dict(l=10, r=10, t=20, b=10), showlegend=True, legend=dict(orientation="h", y=1.08), plot_bgcolor="white")
    fig.update_xaxes(visible=False, fixedrange=True, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, fixedrange=True)
    return fig


# --- 2 · Riesenkomponente über den entfernten Anteil ----------------------------------------------------------------------------------------------------


def build_giant_component_curve(sizes, n, threshold_frac, cohen_fc=None, vanish_threshold=None):
    """S(f) = S(k)/n über f = k/n, mit einer gestrichelten Linie an der gemessenen Schwelle (S(f) < threshold_frac); bei ER-artigen Instanzen (nettype "random") zusätzlich Cohens f_c=1-1/<k> als
    gepunktete Linie - beide Schwellen sind absichtlich unterschiedlich definiert (s. rob_constants.PERCOLATION_FRAC_VANISH), darum niemals gleichgesetzt."""
    fs = [k / n for k in range(len(sizes))] if n else [0.0]
    ys = [s / n for s in sizes] if n else [0.0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fs, y=ys, mode="lines", line=dict(color=TEAL, width=2.6), name="S(f)/n (Riesenkomponente)"))
    fig.add_hline(y=threshold_frac, line=dict(color=GREY, width=1.2, dash="dot"), annotation_text=f"S(f) < {threshold_frac:.0%} von n", annotation_position="bottom right")
    threshold = None
    for k, s in enumerate(sizes):
        if s < threshold_frac * n:
            threshold = k / n
            break
    if threshold is not None:
        fig.add_vline(x=threshold, line=dict(color=ORANGE, width=1.8, dash="dash"), annotation_text=f"gemessen f={threshold:.3f}", annotation_position="top right")
    if cohen_fc is not None:
        fig.add_vline(x=cohen_fc, line=dict(color=RED, width=1.8, dash="dot"), annotation_text=f"Cohen f_c={cohen_fc:.3f}", annotation_position="top left")
    if vanish_threshold is not None:
        fig.add_vline(x=vanish_threshold, line=dict(color=PURPLE, width=1.4, dash="dashdot"), annotation_text=f"gemessen (klein, f={vanish_threshold:.3f})", annotation_position="bottom left")
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.14), plot_bgcolor="white")
    fig.update_xaxes(title="Entfernter Anteil f = k/n", range=[0, 1.02], autorange=False, fixedrange=True)
    fig.update_yaxes(title="S(f)/n (Anteil in der größten Komponente)", range=[0, 1.05], autorange=False, fixedrange=True, gridcolor=LIGHT)
    return fig


# --- 3 · Zufall gegen gezielt ----------------------------------------------------------------------------------------------------------------------------


def build_strategy_overlay(curves, n, strategy_labels):
    """`curves`: {strategy: sizes}. Alle vier S(f)-Kurven derselben Instanz überlagert."""
    fig = go.Figure()
    for strategy, sizes in curves.items():
        fs = [k / n for k in range(len(sizes))] if n else [0.0]
        ys = [s / n for s in sizes] if n else [0.0]
        fig.add_trace(go.Scatter(x=fs, y=ys, mode="lines", line=dict(color=STRATEGY_COLORS.get(strategy, GREY), width=2.4), name=strategy_labels.get(strategy, strategy)))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", y=1.16), plot_bgcolor="white")
    fig.update_xaxes(title="Entfernter Anteil f = k/n", range=[0, 1.02], autorange=False, fixedrange=True)
    fig.update_yaxes(title="S(f)/n", range=[0, 1.05], autorange=False, fixedrange=True, gridcolor=LIGHT)
    return fig


def build_r_bars(r_by_strategy, strategy_labels):
    """Balken: Robustheitsindex R je Strategie (Schneider u. a. 2011) - eine zusammenfassende Zahl je Kurve oben."""
    strategies = list(r_by_strategy)
    values = [r_by_strategy[s] for s in strategies]
    colors = [STRATEGY_COLORS.get(s, GREY) for s in strategies]
    labels = [strategy_labels.get(s, s) for s in strategies]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=values, marker_color=colors, text=[f"{v:.4f}" for v in values], textposition="outside"))
    top = max(values) * 1.25 if values else 1.0
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), showlegend=False, plot_bgcolor="white", title=dict(text="Robustheitsindex R (höher = robuster)", x=0.02, font=dict(size=13)))
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(range=[0, top], autorange=False, fixedrange=True, gridcolor=LIGHT)
    return fig


# --- 4 · Drei Netze im Vergleich -------------------------------------------------------------------------------------------------------------------------


def build_network_comparison_bars(rows):
    """`rows`: Liste von {"label", "r_random_mean", "r_degree_adaptive", ...} - je Netz zwei Balken (Zufall-Mittel gegen Grad-adaptiv) nebeneinander, macht den Albert-Jeong-Barabási-Kontrast
    sichtbar (Nature 2000: skalenfreie Netze robust gegen Zufall, fragil gegen gezielten Angriff - deutlich groesserer Abstand als bei den anderen beiden Netzen)."""
    labels = [r["label"] for r in rows]
    random_vals = [r["r_random_mean"] for r in rows]
    adaptive_vals = [r["r_degree_adaptive"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=random_vals, name="Zufall (Mittel)", marker_color=BLUE, text=[f"{v:.3f}" for v in random_vals], textposition="outside"))
    fig.add_trace(go.Bar(x=labels, y=adaptive_vals, name="Grad-adaptiv (gezielt)", marker_color=RED, text=[f"{v:.3f}" for v in adaptive_vals], textposition="outside"))
    top = max(random_vals + adaptive_vals) * 1.3 if rows else 1.0
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), barmode="group", legend=dict(orientation="h", y=1.14), plot_bgcolor="white")
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title="Robustheitsindex R", range=[0, top], autorange=False, fixedrange=True, gridcolor=LIGHT)
    return fig
