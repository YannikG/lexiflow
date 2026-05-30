"""Tests for add-text submission wiring."""

from __future__ import annotations

import sys
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.text_pipeline.models import InputTab
from lexiflow_ui.add_text_flow import submit_add_text
from lexiflow_ui.dialogs.add_text_dialog import AddTextFormData
from lexiflow_ui.worker_supervisor import WorkerSupervisor

from tests.ui.fakes import FakeProcess


def test_submit_add_text_spawns_worker(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, _index = LibraryCoordinator.open(data_root)
    del coordinator
    FakeProcess.instances.clear()
    supervisor = WorkerSupervisor(
        data_root=data_root,
        executable=sys.executable,
        process_factory=FakeProcess,
    )
    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    form = AddTextFormData(
        group="News",
        pasted_content="Article text for worker spawn test.",
        input_tab=InputTab.NATIVE,
        source_url=None,
    )
    text_id = submit_add_text(
        data_root=data_root,
        settings=settings,
        supervisor=supervisor,
        form=form,
        parent=None,
    )
    assert text_id is not None
    assert len(FakeProcess.instances) == 1
