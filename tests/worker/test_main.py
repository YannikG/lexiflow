from lexiflow_worker.__main__ import main


def test_main_exits_zero() -> None:
    assert main() == 0
