"""Reusable dirty-state guard for edit surfaces (reader, vocabulary, etc.)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from PySide6.QtWidgets import QMessageBox, QWidget

DEFAULT_DISCARD_TITLE = "Discard unsaved changes?"
DEFAULT_DISCARD_MESSAGE = "You have unsaved edits. Discard them and continue?"


def prompt_discard_unsaved_changes(
    parent: QWidget,
    *,
    title: str = DEFAULT_DISCARD_TITLE,
    message: str = DEFAULT_DISCARD_MESSAGE,
) -> QMessageBox.StandardButton:
    """Ask whether to discard unsaved edits. Patch in tests to avoid modal dialogs."""
    return QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Cancel,
    )


@runtime_checkable
class DirtyEditor(Protocol):
    """Edit surface that may block navigation while unsaved changes exist."""

    def is_editing(self) -> bool: ...

    def has_unsaved_edits(self) -> bool: ...

    def leave_edit_mode_without_save(self) -> None: ...


def fields_differ_from_snapshot(**current_vs_baseline: tuple[str, str]) -> bool:
    """Return True when any named field differs from its baseline value."""
    return any(
        current != baseline for current, baseline in current_vs_baseline.values()
    )


def _dialog_parent(parent: QWidget | None, editor: DirtyEditor) -> QWidget:
    if parent is not None:
        return parent
    if isinstance(editor, QWidget):
        return editor
    msg = "parent is required when editor is not a QWidget"
    raise TypeError(msg)


def can_proceed_past_dirty_editor(
    parent: QWidget | None,
    editor: DirtyEditor,
) -> bool:
    """Query whether navigation may continue. Does not mutate editor state."""
    if not editor.is_editing():
        return True
    if not editor.has_unsaved_edits():
        return True
    answer = prompt_discard_unsaved_changes(_dialog_parent(parent, editor))
    return answer == QMessageBox.StandardButton.Discard


def abandon_edit_mode(editor: DirtyEditor) -> None:
    """Command: exit edit mode without saving."""
    if editor.is_editing():
        editor.leave_edit_mode_without_save()


def confirm_leave_dirty_editor(
    parent: QWidget | None,
    editor: DirtyEditor,
) -> bool:
    """Return True after the user may leave; runs abandon when allowed."""
    if not can_proceed_past_dirty_editor(parent, editor):
        return False
    abandon_edit_mode(editor)
    return True


def confirm_leave_dirty_editors(
    parent: QWidget | None,
    editors: tuple[DirtyEditor, ...] | list[DirtyEditor],
) -> bool:
    """Return True when navigation may proceed away from all registered editors."""
    for editor in editors:
        if not confirm_leave_dirty_editor(parent, editor):
            return False
    return True
