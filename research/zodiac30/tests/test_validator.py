from pathlib import Path
import importlib.util


def load():
    path=Path(__file__).parents[1]/'scripts/validate_atlas_gate.py'
    spec=importlib.util.spec_from_file_location('validator',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_expected_total():
    module=load()
    assert sum(module.EXPECTED.values())==299
