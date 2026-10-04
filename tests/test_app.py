"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt für jede Instanzart, bedingte Regler, Permalink-Grenzen, m<=m0-Kopplung, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import rob_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=300)
    state.setdefault("rob_step", step)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _click(at, key):
    next(b for b in at.button if b.key == key).click().run()


def test_default_run_shows_the_summary():
    at = _run()
    _ok(at)
    assert {"Knoten", "Kanten", "Perkolationsschwelle (50%)", "Robustheitsindex R"} <= {m.label for m in at.metric}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run(kind_select="city", side_slider=8)
    _click(at, f"preset_{name}")
    _ok(at)
    p, ss = C.PRESETS[name], at.session_state
    assert ss["kind_select"] == p["kind"] and ss["rob_step"] == p["step"]


@pytest.mark.parametrize("step", [1, 2, 3, 4])
@pytest.mark.parametrize("kind", ["city", "ba", "barbell"])
def test_every_step_runs_for_every_kind(step, kind):
    at = _run(step=step, kind_select=kind, side_slider=8, nba_slider=40, kbarbell_slider=6)
    _ok(at)
    assert at.session_state["rob_step"] == step


def test_step2_shows_cohen_prediction_only_for_random_nettype():
    at = _run(step=2, kind_select="city", nettype_select="grid")
    _ok(at)
    assert not any("f_c=1-1/⟨k⟩=" in c.value for c in at.caption)
    assert any("die Option 'Zufallsgraph' wählen" in c.value for c in at.caption)
    at2 = _run(step=2, kind_select="city", nettype_select="random")
    _ok(at2)
    assert any("f_c=1-1/⟨k⟩=" in c.value for c in at2.caption)


def test_step3_shows_all_four_strategies_and_a_winner():
    at = _run(step=3, kind_select="ba", nba_slider=40)
    _ok(at)
    assert any("Verheerendste Strategie" in c.value for c in at.caption)


def test_step4_shows_network_comparison_table():
    at = _run(step=4, side_slider=8, nba_slider=40, kbarbell_slider=6)
    _ok(at)
    assert len(at.dataframe) >= 1


@pytest.mark.parametrize("nettype", ["grid", "random"])
def test_step1_every_nettype(nettype):
    at = _run(step=1, kind_select="city", side_slider=8, nettype_select=nettype)
    _ok(at)


def test_blocked_slider_only_shown_for_grid_nettype():
    at = _run(kind_select="city", nettype_select="grid")
    assert any(w.key == "blocked_widget" for w in at.select_slider)
    at2 = _run(kind_select="city", nettype_select="random")
    assert not any(w.key == "blocked_widget" for w in at2.select_slider)


def test_recompute_slider_only_shown_for_betweenness_adaptive():
    at1 = _run(strategy_select="betweenness_adaptive")
    assert any(w.key == "recompute_widget" for w in at1.slider)
    for strategy in ("random", "degree_static", "degree_adaptive"):
        at2 = _run(strategy_select=strategy)
        assert not any(w.key == "recompute_widget" for w in at2.slider)


def test_sidebar_shows_the_controls_that_belong_to_the_instance():
    city = _run(kind_select="city")
    assert any(w.key == "side_widget" for w in city.slider) and not any(w.key == "nba_widget" for w in city.slider)
    ba = _run(kind_select="ba")
    assert any(w.key == "nba_widget" for w in ba.slider) and not any(w.key == "side_widget" for w in ba.slider)
    barbell = _run(kind_select="barbell")
    assert any(w.key == "kbarbell_widget" for w in barbell.slider) and not any(w.key == "nba_widget" for w in barbell.slider)


def test_ba_m_slider_never_exceeds_m0():
    at = _run(kind_select="ba", m0ba_slider=3, mba_slider=10)          # m gespeichert > neues m0 -> muss geklemmt werden
    _ok(at)
    assert at.session_state["mba_slider"] <= 3


def test_dice_button_changes_the_seed_and_the_visible_widget():
    at = _run(kind_select="city")
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old and at.session_state["seed_widget"] == at.session_state["seed_input"]


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="nope", side="9999", blocked="0.33", nettype="sideways", nba="99999", kbarbell="9999", strategy="up", recompute="9999", seed="-4", order="up", step="9").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert ss["kind_select"] == "city"
    assert ss["side_slider"] == C.SIDE_MAX
    assert ss["blocked_select"] == C.DEFAULT_BLOCKED
    assert ss["nettype_select"] == "grid"
    assert ss["nba_slider"] == C.N_BA_MAX
    assert ss["kbarbell_slider"] == C.BARBELL_K_MAX
    assert ss["strategy_select"] == "random"
    assert ss["recompute_slider"] == C.RECOMPUTE_EVERY_MAX
    assert ss["seed_input"] == 0
    assert ss["order_select"] == "fixed"
    assert ss["rob_step"] == 1


def test_permalink_accepts_valid_values_and_writes_them_back():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="ba", nba="60", m0ba="5", mba="2", strategy="degree_adaptive", seed="7", step="3").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["kind_select"], ss["nba_slider"], ss["m0ba_slider"], ss["strategy_select"], ss["seed_input"], ss["rob_step"]) == ("ba", 60, 5, "degree_adaptive", 7, 3)
    assert at.query_params["seed"] in (["7"], "7") and at.query_params["step"] in (["3"], "3")
    assert ss["nba_widget"] == 60 and ss["seed_widget"] == 7


def test_switching_kind_back_and_forth_keeps_the_stored_values():
    at = _run(kind_select="city", side_slider=14, blocked_select=0.4, seed_input=11)
    at.session_state["kind_select"] = "ba"
    at.run()
    _ok(at)
    at.session_state["kind_select"] = "city"
    at.run()
    _ok(at)
    assert at.session_state["side_widget"] == 14 and at.session_state["blocked_widget"] == 0.4 and at.session_state["seed_widget"] == 11


@pytest.mark.parametrize("kw", [dict(kind_select="city", side_slider=C.SIDE_MIN), dict(kind_select="city", side_slider=C.SIDE_MAX), dict(kind_select="ba", nba_slider=C.N_BA_MIN),
                                 dict(kind_select="ba", nba_slider=C.N_BA_MAX), dict(kind_select="ba", m0ba_slider=C.M0_BA_MIN), dict(kind_select="ba", m0ba_slider=C.M0_BA_MAX),
                                 dict(kind_select="barbell", kbarbell_slider=C.BARBELL_K_MIN), dict(kind_select="barbell", kbarbell_slider=C.BARBELL_K_MAX)])
def test_extreme_settings_run_on_every_step(kw):
    for step in (1, 2, 3, 4):
        _ok(_run(step=step, **kw))


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Cohen" in m.value and "Schneider" in m.value for e in at.expander for m in e.markdown)
