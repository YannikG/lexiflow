"""Add text dialog for creating texts via paste."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lexiflow_core.library.group_repository import GroupRepository
from lexiflow_core.library.index import LibraryIndex, ensure_library_index
from lexiflow_core.text_pipeline.models import InputTab
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class AddTextFormData:
    group: str
    pasted_content: str
    input_tab: InputTab
    source_url: str | None


class AddTextDialog(QDialog):
    def __init__(
        self,
        *,
        data_root: Path,
        target_language: str,
        groups: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add text")
        self.setObjectName("add_text_dialog")
        self._data_root = data_root
        self._target_language = target_language

        root = QVBoxLayout(self)
        form = QFormLayout()

        self._group = QComboBox(self)
        self._group.setObjectName("add_text_group")
        self._group.setEditable(True)
        for name in groups:
            self._group.addItem(name)
        form.addRow("Group", self._group)

        self._source_url = QLineEdit(self)
        self._source_url.setObjectName("add_text_source_url")
        self._source_url.setPlaceholderText("Optional")
        form.addRow("Source URL", self._source_url)

        tab_row = QWidget(self)
        tab_layout = QHBoxLayout(tab_row)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        self._native_tab_btn = QPushButton("Native", tab_row)
        self._native_tab_btn.setObjectName("add_text_tab_native")
        self._native_tab_btn.setCheckable(True)
        self._native_tab_btn.setChecked(True)
        self._target_tab_btn = QPushButton("Target", tab_row)
        self._target_tab_btn.setObjectName("add_text_tab_target")
        self._target_tab_btn.setCheckable(True)
        self._native_tab_btn.clicked.connect(self._select_native_tab)
        self._target_tab_btn.clicked.connect(self._select_target_tab)
        tab_layout.addWidget(self._native_tab_btn)
        tab_layout.addWidget(self._target_tab_btn)
        form.addRow("Input", tab_row)

        self._paste = QPlainTextEdit(self)
        self._paste.setObjectName("add_text_paste")
        self._paste.clear()
        form.addRow("Content", self._paste)

        root.addLayout(form)

        save_cancel = (
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons = QDialogButtonBox(
            save_cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def paste_edit(self) -> QPlainTextEdit:
        return self._paste

    def form_data(self) -> AddTextFormData | None:
        group = self._group.currentText().strip()
        if not group:
            return None
        pasted = self._paste.toPlainText()
        if not pasted.strip():
            return None
        url = self._source_url.text().strip() or None
        tab = InputTab.NATIVE if self._native_tab_btn.isChecked() else InputTab.TARGET
        return AddTextFormData(
            group=group,
            pasted_content=pasted,
            input_tab=tab,
            source_url=url,
        )

    def _select_native_tab(self) -> None:
        self._native_tab_btn.setChecked(True)
        self._target_tab_btn.setChecked(False)

    def _select_target_tab(self) -> None:
        self._native_tab_btn.setChecked(False)
        self._target_tab_btn.setChecked(True)

    def _on_accept(self) -> None:
        if self.form_data() is None:
            return
        self.accept()


def open_add_text_dialog(
    *,
    data_root: Path,
    target_language: str,
    parent: QWidget | None = None,
) -> AddTextFormData | None:
    """Show the add-text dialog and return form data when saved."""
    ensure_library_index(data_root)
    index = LibraryIndex(data_root)
    groups = GroupRepository(data_root, index).list_groups(target_language)
    dialog = AddTextDialog(
        data_root=data_root,
        target_language=target_language,
        groups=groups,
        parent=parent,
    )
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.form_data()
