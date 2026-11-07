"""Die vier Experimente der App per AppTest: Lokalsuche Zug für Zug, Start × Nachbarschaft, Gewinn, Mehrfachstart; dazu das PDF."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import sgn_constants as C
import sgn_evaluation as ev
from sgn_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SETTING_KEYS = {"n": "n_slider", "family": "family_select", "depot": "depot_select", "routes": "routes_slider", "fill": "fill_slider", "seed": "seed_input", "start": "start_select", "neigh": "neigh_select"}


def _app(preset=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    if preset:
        at.session_state["permalink_loaded"] = True
        for key, state_key in SETTING_KEYS.items():
            at.session_state[state_key] = C.PRESETS[preset][key]
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join([x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning] + [x.value for x in at.error])


def test_the_default_shows_the_hand_run():
    text = _texts(_app())
    assert "in 7 Zügen (Verschieben 7)" in text and "auf 44,36" in text


def test_every_start_and_every_neighborhood_runs():
    at = _app()
    for s in range(len(C.START_KEYS)):
        at.selectbox(key="start_select").set_value(s).run()
        assert not at.exception, s
    at.selectbox(key="start_select").set_value(0).run()
    for nk in range(len(C.NEIGH_KEYS)):
        at.selectbox(key="neigh_select").set_value(nk).run()
        assert not at.exception, nk
        assert "Aus Zufallsfolge + Split" in _texts(at)


def test_a_step_can_be_chosen_and_the_instance_controls_work():
    at = _app("Der schlechte Start braucht die Nachbarschaft (25 Kunden)")
    slider = next(s for s in at.slider if s.key and s.key.startswith("ls_step_"))
    slider.set_value(0).run()
    assert not at.exception
    for family in range(len(C.FAMILIES)):
        at.selectbox(key="family_select").set_value(family).run()
        assert not at.exception, family
    at.selectbox(key="family_select").set_value(1).run()
    at.slider(key="n_slider").set_value(14).run()
    assert not at.exception and "Aus " in _texts(at)


def test_the_random_start_slider_and_the_band_selection():
    at = _app("Zufallsstarts gegen Savings (50 Kunden)")
    for k in (1, 5, 20):
        at.slider(key="k_random").set_value(k).run()
        assert not at.exception, k
        assert f"Das beste von {k} Zufallsstarts mit Lokalsuche kostet" in _texts(at)
    for n in C.BAND_SIZES:
        at.radio(key="band_n").set_value(n).run()
        assert not at.exception, n
        assert f"Bei {n} Kunden (" in _texts(at)
        for which in C.BAND_SETS:
            at.radio(key="band_set").set_value(which).run()
            assert not at.exception, (n, which)


def test_large_instances_show_the_bands_instead_of_the_live_run():
    at = _app()
    at.selectbox(key="family_select").set_value(1).run()
    at.slider(key="n_slider").set_value(80).run()
    assert not at.exception
    assert any("Live gerechnet wird nur bis" in i.value for i in at.info) and "Bei 100 Kunden (" in _texts(at)


def test_pdf_download_button_exists_and_the_pdf_is_built_for_every_preset():
    assert len(_app().get("download_button")) == 1
    for preset in C.PRESETS.values():
        s = ev.Settings(preset["n"], preset["family"], preset["depot"], preset["routes"], preset["fill"], preset["seed"])
        ch = ev.Choice(preset["start"], preset["neigh"])
        live = ev.live_matrix(s) if s.n <= C.LIVE_N_MAX else None
        data = build_pdf(s, ch, live)
        assert data[:5] == b"%PDF-" and len(data) > 1500
    big = build_pdf(ev.Settings(80, 1, 0, 3, 90, 1), ev.Choice(), None)
    assert big[:5] == b"%PDF-"
