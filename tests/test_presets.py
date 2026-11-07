"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Zahlen in den Hilfetexten stehen in test_claims.py."""

import sgn_constants as C
import sgn_evaluation as ev
import sgn_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)
        assert (preset["fill"] - C.FILL_MIN) % C.FILL_STEP == 0, name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(first["n"], first["family"], first["depot"], first["routes"], first["fill"], first["seed"]) == ev.Settings()
    assert ev.Choice(first["start"], first["neigh"]) == ev.Choice()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_preset_has_a_distinct_configuration():
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)


def test_constants_are_consistent():
    assert C.N_MAX >= max(C.BAND_SIZES) >= C.LIVE_N_MAX >= C.EXACT_MAX and C.EXACT_MAX in C.BAND_SIZES and set(C.FRESH_SIZES) <= set(C.BAND_SIZES)
    assert set(C.START_KEYS) == set(C.STARTS) and set(C.NEIGH_KEYS) == set(C.NEIGH) and C.NEIGH["alle"][1] == ("2opt", "move", "swap")
    assert all(set(moves) <= {"2opt", "move", "swap"} for _, moves in C.NEIGH.values()) and C.ES_MAX_N >= C.LIVE_N_MAX
    assert 0 <= C.DEFAULT_START < len(C.START_KEYS) and 0 <= C.DEFAULT_NEIGH < len(C.NEIGH_KEYS) and C.LIVE_RANDOM_MAX <= C.RANDOM_STARTS
