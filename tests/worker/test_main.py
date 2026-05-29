from lexiflow_worker.main import main


def test_main_exits_zero() -> None:
    assert main() == 0
