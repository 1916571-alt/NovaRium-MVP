import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.services.experiment_analysis import _p_value_from_z


def test_p_value_from_z_symmetry():
    assert abs(_p_value_from_z(2.0) - _p_value_from_z(-2.0)) < 1e-12


def test_p_value_from_z_monotonic():
    assert _p_value_from_z(0.5) > _p_value_from_z(2.0)
    assert _p_value_from_z(2.0) > _p_value_from_z(4.0)

