"""Unit tests for the shared unsaved-changes guard."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from lexiflow_ui.unsaved_changes import (
    can_proceed_past_dirty_editor,
    confirm_leave_dirty_editor,
    confirm_leave_dirty_editors,
    fields_differ_from_snapshot,
)
from PySide6.QtWidgets import QMessageBox, QWidget


@dataclass
class FakeEditor:
    editing: bool = False
    dirty: bool = False
    left_without_save: int = field(default=0, init=False)

    def is_editing(self) -> bool:
        return self.editing

    def has_unsaved_edits(self) -> bool:
        return self.dirty

    def leave_edit_mode_without_save(self) -> None:
        self.left_without_save += 1
        self.editing = False
        self.dirty = False


def test_fields_differ_from_snapshot_detects_any_change() -> None:
    assert not fields_differ_from_snapshot(title=("A", "A"), body=("x", "x"))
    assert fields_differ_from_snapshot(title=("B", "A"), body=("x", "x"))


def test_confirm_leave_dirty_editor_when_not_editing(qtbot) -> None:
    editor = FakeEditor()
    parent = QWidget()
    qtbot.addWidget(parent)

    assert confirm_leave_dirty_editor(parent, editor) is True
    assert editor.left_without_save == 0


def test_can_proceed_past_dirty_editor_clean_edit_does_not_mutate(
    qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def _prompt(*_args, **_kwargs) -> QMessageBox.StandardButton:
        nonlocal calls
        calls += 1
        return QMessageBox.StandardButton.Discard

    monkeypatch.setattr(
        "lexiflow_ui.unsaved_changes.prompt_discard_unsaved_changes",
        _prompt,
    )
    editor = FakeEditor(editing=True, dirty=False)
    parent = QWidget()
    qtbot.addWidget(parent)

    assert can_proceed_past_dirty_editor(parent, editor) is True
    assert calls == 0
    assert editor.left_without_save == 0


def test_confirm_leave_dirty_editor_exits_clean_edit_without_prompt(
    qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def _prompt(*_args, **_kwargs) -> QMessageBox.StandardButton:
        nonlocal calls
        calls += 1
        return QMessageBox.StandardButton.Discard

    monkeypatch.setattr(
        "lexiflow_ui.unsaved_changes.prompt_discard_unsaved_changes",
        _prompt,
    )
    editor = FakeEditor(editing=True, dirty=False)
    parent = QWidget()
    qtbot.addWidget(parent)

    assert confirm_leave_dirty_editor(parent, editor) is True
    assert calls == 0
    assert editor.left_without_save == 1


def test_confirm_leave_dirty_editor_cancel_blocks(
    qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.unsaved_changes.prompt_discard_unsaved_changes",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Cancel,
    )
    editor = FakeEditor(editing=True, dirty=True)
    parent = QWidget()
    qtbot.addWidget(parent)

    assert confirm_leave_dirty_editor(parent, editor) is False
    assert editor.left_without_save == 0
    assert editor.editing is True


def test_confirm_leave_dirty_editor_discard_proceeds(
    qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.unsaved_changes.prompt_discard_unsaved_changes",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Discard,
    )
    editor = FakeEditor(editing=True, dirty=True)
    parent = QWidget()
    qtbot.addWidget(parent)

    assert confirm_leave_dirty_editor(parent, editor) is True
    assert editor.left_without_save == 1


def test_confirm_leave_dirty_editors_stops_at_first_cancel(
    qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompts = 0

    def _prompt(*_args, **_kwargs) -> QMessageBox.StandardButton:
        nonlocal prompts
        prompts += 1
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(
        "lexiflow_ui.unsaved_changes.prompt_discard_unsaved_changes",
        _prompt,
    )
    first = FakeEditor(editing=True, dirty=True)
    second = FakeEditor(editing=True, dirty=True)
    parent = QWidget()
    qtbot.addWidget(parent)

    assert confirm_leave_dirty_editors(parent, (first, second)) is False
    assert prompts == 1
    assert first.left_without_save == 0
    assert second.left_without_save == 0
