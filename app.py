"""Robustheit – Zufall gegen gezielten Angriff, Perkolationsschwelle – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Achtes Stück der Graphen-und-Netzwerke-Reihe, Kind der Strukturkennzahlen (Stück 7): dort wurde die Struktur eines Netzes vermessen, jetzt geht es darum, was diese Struktur für den AUSFALL
bedeutet. Vier Entfernungsstrategien (Zufall, Grad statisch, Grad adaptiv, Betweenness adaptiv) auf drei Instanzen (Betriebsnetz, skalenfreies Netz, Barbell-Lehrbuch) - der klassische
Albert-Jeong-Barabási-Kontrast (Nature 2000): skalenfreie Netze robust gegen zufälligen Ausfall, aber verwundbar gegen gezielten Angriff auf ihre Hubs.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import rob_algorithm as A
import rob_constants as C
import rob_evaluation as ev
import rob_visualization as viz
from rob_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, store_from_widget, sync_query_params, push_to_widget

st.set_page_config(page_title="Robustheit – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _compare_strategies(settings):
    inst = ev.instance(settings)
    return inst, ev.compare_strategies(inst, settings.seed, settings.recompute_every, settings.order)


@st.cache_data(show_spinner=False)
def _network_comparison(city_settings, ba_settings, barbell_settings, seed, n_random_orders):
    return ev.network_comparison(city_settings, ba_settings, barbell_settings, seed, n_random_orders)


def _german(x):
    return f"{x:,}".replace(",", ".") if isinstance(x, int) else x


st.title("🛡️ Robustheit – Zufall gegen gezielten Angriff")
st.markdown(
    """
**Achtes Stück der Graphen-und-Netzwerke-Reihe**, Kind der Strukturkennzahlen (Stück 7: dort die Struktur vermessen, jetzt ihre Folgen für den Ausfall). Vier Entfernungsstrategien: **Zufall**,
**Grad statisch** (Rangfolge einmal aus dem Ausgangsnetz), **Grad adaptiv** (Cohen, Erez, ben-Avraham & Havlin 2001: nach jeder Entfernung neu der aktuell höchstgradige Restknoten - trifft immer
den NEUEN Hub, sobald der alte weg ist), **Betweenness adaptiv** (dieselbe Idee mit der aktuellen Betweenness, Brandes 2001). Der klassische Befund (Albert, Jeong & Barabási 2000, Nature 406,
378–382): **skalenfreie Netze sind erstaunlich robust gegen zufälligen Ausfall, aber sehr verwundbar gegen gezielten Angriff auf ihre Hubs** - bei einem Netz mit enger Gradverteilung macht es dagegen
kaum Unterschied, welchen Knoten man entfernt (hier gemessen, nicht angenommen - mit einer echten Überraschung, s. unten). Als **Perkolationsschwelle** wird gemessen, ab welchem entfernten Anteil die
größte Komponente stark schrumpft; für Erdős-Rényi-artige Netze unter zufälligem Ausfall gibt es eine geschlossene Vorhersage (Cohen, Erez, ben-Avraham & Havlin 2000: f_c = 1 - 1/⟨k⟩). Als
zusammenfassende Kennzahl je Strategie/Netz dient der **Robustheitsindex** R = (1/n)·Σ S(k)/n (Schneider, Moreira, Andrade, Herrmann & Havlin 2011) - die Fläche unter der Riesenkomponenten-Kurve.
"""
)
st.caption(
    "Kind der Strukturkennzahlen-Demo (achtes Stück der Graphen-und-Netzwerke-Reihe); geplante Nachfolger (nicht gebaut): Kaskaden und Ausbreitung, kritische Knoten härten. Abgrenzung: Stück 1 "
    "(BFS und DFS) hat schon einmal eine Perkolationsschwelle gemessen, aber dort wurden zufällig KANTEN gesperrt (Bond-Perkolation) - hier werden KNOTEN entfernt (Site-Perkolation), eine "
    "verwandte, aber eigene Frage."
)

with st.expander("So funktioniert die Messung", expanded=True):
    st.markdown(
        """
1. **Vier Entfernungsstrategien:** Zufall (gleichverteilte Permutation), Grad statisch (einmalige Rangfolge nach Ausgangsgrad), Grad adaptiv (immer der AKTUELL höchstgradige Restknoten - Cohen
   u. a. 2001), Betweenness adaptiv (dieselbe Idee mit der aktuellen Betweenness, volle Neuberechnung nur alle paar Schritte - teuer, s. Regler).
2. **S(k):** Größe der größten Komponente (Riesenkomponente) nach jeder Entfernung. Ein Satz, kein Zufall: S(k) ist monoton nicht wachsend in k.
3. **Perkolationsschwelle:** kleinster entfernter Anteil, ab dem S(k) unter eine Schwelle fällt - eine GEMESSENE, endliche Schwelle, keine asymptotische Definition. Für Erdős-Rényi-artige Netze
   (Zufallsgraph-Option beim Betriebsnetz) gibt es Cohens geschlossene Vorhersage f_c = 1-1/⟨k⟩ zum Vergleich.
4. **Robustheitsindex R (Schneider u. a. 2011):** die Fläche unter der S(k)/n-Kurve, normiert auf [0,1] - höher heißt robuster gegen genau diese Entfernungsstrategie.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:4], preset_names[4:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()
ss = st.session_state

with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                     help="Betriebsnetz: gestörtes Straßenraster oder Zufallsgraph. Skalenfreies Netz: Barabási-Albert, bevorzugte Anbindung. Barbell: Lehrbuchbeispiel, von Hand nachrechenbar.")

    side, blocked, nettype = C.DEFAULT_SIDE, C.DEFAULT_BLOCKED, "grid"
    n_ba, m_ba, m0_ba = C.DEFAULT_N_BA, C.DEFAULT_M_BA, C.DEFAULT_M0_BA
    k_barbell = C.DEFAULT_BARBELL_K

    if kind == "city":
        side = st.slider("Seitenlänge des Rasters", *bounds("side_slider"), value=int(ss["side_slider"]), key="side_widget", on_change=store_from_widget, args=("side_slider",),
                          help="Die Instanz hat Seitenlänge² Kreuzungen.")
        nettype = st.radio("Netztyp", options=list(C.NETTYPES), format_func=lambda v: C.NETTYPE_LABELS[v], key="nettype_widget", on_change=store_from_widget, args=("nettype_select",),
                            index=list(C.NETTYPES).index(ss["nettype_select"]),
                            help="Zufallsgraph = Erdős-Rényi-artige Instanz (für den Vergleich mit Cohens Perkolationsschwellen-Formel in Schritt 2).")
        if nettype == "grid":
            blocked = st.select_slider("Gesperrter Anteil der Straßen", options=list(C.BLOCKED_OPTIONS), value=float(ss["blocked_select"]), format_func=lambda v: f"{v * 100:.0f} %",
                                        key="blocked_widget", on_change=store_from_widget, args=("blocked_select",))
        else:
            blocked = 0.0
    elif kind == "ba":
        n_ba = st.slider("Zahl der Knoten n", *bounds("nba_slider"), value=int(ss["nba_slider"]), key="nba_widget", on_change=store_from_widget, args=("nba_slider",))
        m0_ba = st.slider("Kerngröße m0 (Kreis aus m0 Knoten)", *bounds("m0ba_slider"), value=int(ss["m0ba_slider"]), key="m0ba_widget", on_change=store_from_widget, args=("m0ba_slider",))
        if ss["mba_slider"] > m0_ba:
            ss["mba_slider"] = m0_ba
            push_to_widget("mba_slider")
        if C.M_BA_MIN < m0_ba:
            m_ba = st.slider("Neue Kanten je Knoten m (bevorzugte Anbindung)", C.M_BA_MIN, m0_ba, value=int(ss["mba_slider"]), key="mba_widget", on_change=store_from_widget, args=("mba_slider",),
                              help="Jeder neue Knoten hängt sich mit m Kanten an m bereits vorhandene Knoten an, proportional zu deren Grad gezogen.")
        else:
            m_ba = C.M_BA_MIN                                        # m0 == M_BA_MIN: keine Wahl möglich (min==max würde den Regler zum Absturz bringen)
    else:
        k_barbell = st.slider("Cliquengröße k (Barbell hat 2k Knoten)", *bounds("kbarbell_slider"), value=int(ss["kbarbell_slider"]), key="kbarbell_widget", on_change=store_from_widget,
                               args=("kbarbell_slider",), help="Zwei vollständige Graphen K_k, durch eine einzelne Brücke verbunden.")

    strategy = st.radio("Entfernungsstrategie", options=list(C.STRATEGIES), format_func=lambda v: C.STRATEGY_LABELS[v], key="strategy_select",
                         help="Gilt für Schritt 1 und 2 (Einzelanalyse). Schritt 3 zeigt ohnehin alle vier, Schritt 4 vergleicht Zufall gegen Grad-adaptiv.")
    if strategy == "betweenness_adaptive":
        recompute_every = st.slider("Neuberechnungs-Intervall (Betweenness)", *bounds("recompute_slider"), value=int(ss["recompute_slider"]), key="recompute_widget", on_change=store_from_widget,
                                     args=("recompute_slider",), help="1 = bei jedem Schritt neu (exakt, aber teuer - O(n·m) je Aufruf). Größere Werte: die zuletzt berechnete Rangfolge wird "
                                     "mehrere Schritte weiterverwendet (Näherung, kalibriert gegen die Kosten, s. README).")
    else:
        recompute_every = int(ss["recompute_slider"])

    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    order = st.radio("Nachbarreihenfolge", options=list(C.ORDERS), format_func=lambda v: C.ORDER_LABELS[v], key="order_select",
                      help="Ändert nie S(k) oder R - nur die interne Buchführungsreihenfolge (Determinismus-Test).")

step = st.select_slider("Schritt", options=list(C.STEPS), key="rob_step", format_func=lambda s: C.STEPS[s])

sync_query_params({"kind_select": kind, "side_slider": int(side) if kind == "city" else int(ss["side_slider"]),
                    "blocked_select": float(blocked) if kind == "city" and nettype == "grid" else float(ss["blocked_select"]), "nettype_select": nettype if kind == "city" else ss["nettype_select"],
                    "nba_slider": int(n_ba) if kind == "ba" else int(ss["nba_slider"]), "m0ba_slider": int(m0_ba) if kind == "ba" else int(ss["m0ba_slider"]),
                    "mba_slider": int(m_ba) if kind == "ba" else int(ss["mba_slider"]), "kbarbell_slider": int(k_barbell) if kind == "barbell" else int(ss["kbarbell_slider"]),
                    "strategy_select": strategy, "recompute_slider": int(recompute_every), "seed_input": int(seed), "order_select": order, "rob_step": int(step)})

settings = ev.Settings(kind=kind, side=int(side), blocked=float(blocked), nettype=nettype, n_ba=int(n_ba), m_ba=int(m_ba), m0_ba=int(m0_ba), k_barbell=int(k_barbell), strategy=strategy,
                        recompute_every=int(recompute_every), seed=int(seed), order=order)

with st.spinner("Rechne..."):
    inst, a = _analysis(settings)
adj = A.adjacency(inst.n, inst.edges)

st.markdown("## 🎯 Die Instanz und ihre Robustheit")
st.markdown(f"**{_german(inst.n)} Knoten, {_german(inst.m)} Kanten**, Strategie **{C.STRATEGY_LABELS[strategy]}**. Perkolationsschwelle (S(k) < 50% von n) bei f={a.threshold:.3f}, "
            f"Robustheitsindex R={a.robustness:.4f}.")

if step == 1:
    k_max = inst.n
    k = st.slider("Entfernte Knoten (k)", 0, k_max, value=min(k_max, max(1, k_max // 4)), key=f"k_slider_{kind}_{seed}_{strategy}",
                   help="Entfernungsfortschritt entlang der gewählten Strategie-Reihenfolge.") if k_max > 0 else 0
    removed, comps = A.partial_removal_state(adj, a.node_order, k)
    giant = comps[0] if comps else []
    st.plotly_chart(viz.build_attack_map(inst.xy, [(u, v) for u, v, _ in inst.edges], removed, giant), width="stretch", key=f"s1_map_{kind}_{seed}_{strategy}_{k}")
    st.caption(f"Nach {k} von {inst.n} Entfernungen: größte Komponente {len(giant)} Knoten, {len(comps)} Komponenten unter den noch lebenden Knoten insgesamt.")
elif step == 2:
    cohen_fc = None
    vanish = None
    if kind == "city" and nettype == "random":
        cohen_fc = A.er_threshold_prediction(adj)
        vanish = A.percolation_threshold(a.sizes, a.n, C.PERCOLATION_FRAC_VANISH)
    st.plotly_chart(viz.build_giant_component_curve(a.sizes, a.n, C.PERCOLATION_FRAC, cohen_fc, vanish), width="stretch", key=f"s2_curve_{kind}_{seed}_{strategy}_{recompute_every}")
    if cohen_fc is not None:
        st.caption(f"Cohen-Vorhersage (Zufallsausfall auf ER-artigen Netzen) f_c=1-1/⟨k⟩={cohen_fc:.4f}. Die kleine, nahe am asymptotischen 'Verschwinden' liegende Schwelle (5% von n) ist gemessen "
                   f"bei f={vanish:.4f} - näher an Cohen als die allgemeine 50%-Schwelle der App (f={a.threshold:.4f}), weil beide etwas anderes messen (s. README 'Design-Entscheidung').")
    else:
        st.caption("Die Cohen-Vorhersage gilt nur für Erdős-Rényi-artige Netze unter ZUFÄLLIGEM Ausfall - beim Betriebsnetz die Option 'Zufallsgraph' wählen, um sie einzublenden.")
elif step == 3:
    with st.spinner("Rechne alle vier Strategien..."):
        _, strat_out = _compare_strategies(settings)
    curves = {s: strat_out[s].sizes for s in C.STRATEGIES}
    r_by_strategy = {s: strat_out[s].robustness for s in C.STRATEGIES}
    st.plotly_chart(viz.build_strategy_overlay(curves, inst.n, C.STRATEGY_LABELS), width="stretch", key=f"s3_overlay_{kind}_{seed}_{recompute_every}")
    st.plotly_chart(viz.build_r_bars(r_by_strategy, C.STRATEGY_LABELS), width="stretch", key=f"s3_bars_{kind}_{seed}_{recompute_every}")
    winner = min(r_by_strategy, key=r_by_strategy.get)
    st.caption(f"Verheerendste Strategie auf dieser Instanz: **{C.STRATEGY_LABELS[winner]}** (R={r_by_strategy[winner]:.4f}, niedrigster Wert = am robustheitsschädlichsten).")
else:
    city_settings = ev.Settings(kind="city", side=int(side) if kind == "city" else C.DEFAULT_SIDE, blocked=float(blocked) if kind == "city" else C.DEFAULT_BLOCKED,
                                 nettype=nettype if kind == "city" else "grid", seed=int(seed))
    ba_settings = ev.Settings(kind="ba", n_ba=int(n_ba) if kind == "ba" else C.DEFAULT_N_BA, m_ba=int(m_ba) if kind == "ba" else C.DEFAULT_M_BA,
                               m0_ba=int(m0_ba) if kind == "ba" else C.DEFAULT_M0_BA, seed=int(seed))
    barbell_settings = ev.Settings(kind="barbell", k_barbell=int(k_barbell) if kind == "barbell" else C.DEFAULT_BARBELL_K, seed=int(seed))
    with st.spinner("Rechne Netzvergleich..."):
        rows = _network_comparison(city_settings, ba_settings, barbell_settings, int(seed), C.N_RANDOM_ORDERS_FOR_MEAN)
    st.plotly_chart(viz.build_network_comparison_bars(rows), width="stretch", key=f"s4_bars_{seed}_{side}_{blocked}_{nettype}_{n_ba}_{m_ba}_{m0_ba}_{k_barbell}")
    st.dataframe([{"Netz": r["label"], "n": r["n"], "m": r["m"], "R(Zufall, Mittel)": round(r["r_random_mean"], 4), "R(Grad-adaptiv)": round(r["r_degree_adaptive"], 4),
                   "Abstand": round(r["gap"], 4)} for r in rows], width="stretch", hide_index=True)
    st.caption(f"Zufall = Mittel über {C.N_RANDOM_ORDERS_FOR_MEAN} unabhängige Zufallsreihenfolgen je Netz. Größter Abstand (Albert-Jeong-Barabási-Kontrast): "
               f"{max(rows, key=lambda r: r['gap'])['label']}.")

st.markdown("---")

st.markdown("## 🎯 Was die Robustheit verrät")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Knoten", _german(inst.n))
r2.metric("Kanten", _german(inst.m))
r3.metric("Perkolationsschwelle (50%)", f"{a.threshold:.3f}")
r4.metric("Robustheitsindex R", f"{a.robustness:.4f}")

st.markdown("---")

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die 50%-Schwelle der App ist keine asymptotische Perkolationsschwelle** | Sie liegt strukturell 0.3-0.4 UNTER Cohens f_c=1-1/⟨k⟩ (nicht nur Messrauschen) - für den Vergleich mit Cohen wird eine viel kleinere Schwelle (5%) verwendet. | - |
| **Cohens Formel gilt nur für ER-artige (Poisson-Gradverteilung) Netze unter ZUFÄLLIGEM Ausfall** | Beim skalenfreien Netz oder unter gezieltem Angriff ist sie nicht anwendbar - dort gibt es keine geschlossene Formel dieser Art. | - |
| **Betweenness-adaptiv mit recompute_every>1 ist eine explizite Näherung** | Zwischen zwei Neuberechnungen kann die verwendete Rangfolge veraltet sein - bei sehr großem Intervall nähert sie sich Grad-statisch an. | - |
| **Der Robustheitsindex R ist ein einziger Mittelwert über die ganze Kurve** | Er unterscheidet nicht, OB ein Netz früh oder erst spät zusammenbricht - zwei sehr unterschiedliche S(k)-Kurven können denselben R-Wert haben. | - |
| **Synthetische Instanzen** | Betriebsnetz, skalenfreies Netz und Barbell sind erzeugt, keine echten Infrastruktur- oder Sozialnetzdaten. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Riesenkomponente S(k).** Größe der größten Zusammenhangskomponente, nachdem k Knoten (in der gewählten Strategie-Reihenfolge) entfernt wurden. Satz: $S(k) \ge S(k+1)$ für alle $k$ (monoton
nicht wachsend).

**Grad-adaptiv (Cohen, Erez, ben-Avraham & Havlin 2001).** Wiederholt: entferne $\arg\max_v \deg(v)$ unter den noch vorhandenen Knoten $v$ - im Unterschied zu Grad-statisch, das die Rangfolge
EINMALIG aus dem Ausgangsgrad bildet.

**Betweenness adaptiv.** Wiederholt: entferne den Knoten mit der aktuell höchsten (unnormierten) Betweenness (Brandes 2001); volle Neuberechnung nur alle `recompute_every` Entfernungen, dazwischen
wird die zuletzt berechnete Rangfolge unter den noch vorhandenen Knoten weiterverwendet.

**Perkolationsschwelle (gemessen).** $f^* = \min\{k/n : S(k) < \text{frac} \cdot n\}$ - eine ENDLICHE-GRÖSSE-Schwelle, keine asymptotische Definition.

**Cohen-Vorhersage (Cohen, Erez, ben-Avraham & Havlin 2000).** $f_c = 1 - \dfrac{1}{\langle k \rangle}$ für zufälligen Knotenausfall auf Erdős-Rényi-artigen (Poisson-Gradverteilung) Netzen - der
Punkt, an dem der mittlere Restgrad $\langle k \rangle (1-f)$ auf 1 fällt.

**Robustheitsindex (Schneider, Moreira, Andrade, Herrmann & Havlin 2011).** $R = \dfrac{1}{n} \sum_{k=1}^{n} \dfrac{S(k)}{n}$ - die Fläche unter der normierten S(k)-Kurve, $R \in (0, 0.5]$ für ein
zusammenhängendes Ausgangsnetz.

**Barbell-Graph.** Zwei vollständige Graphen $K_k$, durch eine Brücke verbunden. Die Brückenenden haben Grad $k$ (höchster Grad im Graphen); ihre Entfernung trennt den Graphen SOFORT in Stücke der
Größe $k-1$ und $k$.

**Literatur.** Albert, R., Jeong, H., & Barabási, A.-L. (2000). *Error and attack tolerance of complex networks.* Nature 406, 378–382. Cohen, R., Erez, K., ben-Avraham, D., & Havlin, S. (2000).
*Resilience of the Internet to random breakdowns.* Physical Review Letters 85(21), 4626–4628. Cohen, R., Erez, K., ben-Avraham, D., & Havlin, S. (2001). *Breakdown of the Internet under
intentional attack.* Physical Review Letters 86(16), 3682–3685. Schneider, C. M., Moreira, A. A., Andrade, J. S., Herrmann, H. J., & Havlin, S. (2011). *Mitigation of malicious attacks on
networks.* Proceedings of the National Academy of Sciences 108(10), 3838–3841. Brandes, U. (2001). *A faster algorithm for betweenness centrality.* Journal of Mathematical Sociology 25(2),
163–177.

Implementiert in `rob_algorithm.py` (Entfernungsstrategien, S(k), Perkolationsschwelle, Robustheitsindex), `rob_scenario.py` (Instanzen), `rob_evaluation.py` (Analyse, Vergleiche).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
