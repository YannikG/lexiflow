"""Application entry: QApplication and main window."""

from __future__ import annotations

import sys
from collections.abc import Callable

from lexiflow_core.config.bootstrap import bootstrap_runtime
from lexiflow_core.config.settings_store import SettingsStore
from PySide6.QtWidgets import QApplication

from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.onboarding.system_info import SystemInfo
from lexiflow_ui.onboarding.wizard import OnboardingWizard, run_onboarding_if_needed
from lexiflow_ui.single_instance import SingleInstanceGuard
from lexiflow_ui.worker_supervisor import WorkerSupervisor


def run(
    argv: list[str] | None = None,
    *,
    settings_store: SettingsStore | None = None,
    instance_guard: SingleInstanceGuard | None = None,
    system_info: SystemInfo | None = None,
    wizard_factory: Callable[..., OnboardingWizard] | None = None,
) -> int:
    app = QApplication.instance()
    if app is None:
        if argv is None:
            argv = sys.argv
        app = QApplication(argv)

    guard = instance_guard if instance_guard is not None else SingleInstanceGuard()
    if not guard.try_acquire():
        return guard.handle_secondary_launch()

    store = settings_store if settings_store is not None else SettingsStore()
    data_root = bootstrap_runtime(store)
    settings = store.load()
    settings = run_onboarding_if_needed(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=system_info,
        wizard_factory=wizard_factory,
    )
    if settings is None:
        return 0

    supervisor = WorkerSupervisor(data_root=data_root)
    window = MainWindow(supervisor=supervisor, settings=settings, data_root=data_root)
    guard.listen_for_activation(window.request_activation)
    window.show()
    try:
        return app.exec()
    finally:
        supervisor.shutdown(wait=True)
        guard.release()
