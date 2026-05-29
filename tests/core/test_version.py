import lexiflow_core


def test_core_exposes_version_string() -> None:
    assert isinstance(lexiflow_core.__version__, str)
    assert lexiflow_core.__version__
