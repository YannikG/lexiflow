"""Tests for add-text submission wiring."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.text_pipeline.models import InputTab
from lexiflow_ui.add_text_flow import submit_add_text
from lexiflow_ui.dialogs.add_text_dialog import AddTextFormData
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtWidgets import QMessageBox

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
        title="Worker spawn test",
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


def test_submit_add_text_allows_same_content_without_source_url(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    body = "Shared article body."
    repo.create_text(
        CreateTextRequest(
            title="Existing",
            group="News",
            target_language="es",
            native_language="en",
            body=body,
        )
    )
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
        title="Second text",
        group="News",
        pasted_content=body,
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


def test_submit_add_text_prompts_on_duplicate_source_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    repo.create_text(
        CreateTextRequest(
            title="Existing",
            group="News",
            target_language="es",
            native_language="en",
            body="original",
            source_url="https://example.com/article",
        )
    )
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
        title="Duplicate URL attempt",
        group="News",
        pasted_content="different paste",
        input_tab=InputTab.NATIVE,
        source_url="https://example.com/article",
    )
    question = MagicMock(return_value=QMessageBox.StandardButton.No)
    monkeypatch.setattr(
        "lexiflow_ui.add_text_flow.QMessageBox.question",
        question,
    )

    text_id = submit_add_text(
        data_root=data_root,
        settings=settings,
        supervisor=supervisor,
        form=form,
        parent=None,
    )

    assert text_id is None
    question.assert_called_once()
    assert "source URL" in question.call_args.args[2]
    assert len(FakeProcess.instances) == 0
