"""Inline library search field with a dropdown result list."""

from __future__ import annotations

import re
from collections.abc import Callable

from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.search import search_texts
from lexiflow_core.library.search_models import SearchHit
from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QFontMetrics, QKeyEvent, QPainter, QPalette, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

_MAX_VISIBLE_RESULTS = 8
_MIN_POPUP_WIDTH = 280
_ITEM_HORIZONTAL_PADDING = 12
_ITEM_VERTICAL_PADDING = 12
_ITEM_LINE_SPACING = 8
_TITLE_FONT_SIZE_DELTA = 2
_SNIPPET_FONT_SIZE_DELTA = -1
_MARK_TAG_PATTERN = re.compile(r"</?mark>")


def _elide_text(text: str, font: QFont, width: int) -> str:
    metrics = QFontMetrics(font)
    return metrics.elidedText(text, Qt.TextElideMode.ElideRight, max(width, 1))


def _title_font(base: QFont) -> QFont:
    font = QFont(base)
    font.setPointSize(font.pointSize() + _TITLE_FONT_SIZE_DELTA)
    font.setWeight(QFont.Weight.DemiBold)
    return font


def _snippet_font(base: QFont) -> QFont:
    font = QFont(base)
    font.setPointSize(max(font.pointSize() + _SNIPPET_FONT_SIZE_DELTA, 9))
    return font


def _line_height(font: QFont) -> int:
    metrics = QFontMetrics(font)
    return max(metrics.lineSpacing(), metrics.boundingRect("ÁÖÜß#").height())


def _plain_snippet(snippet: str) -> str:
    """Render FTS snippets as readable text in the result list."""
    return _MARK_TAG_PATTERN.sub("", snippet)


def _result_label(hit: SearchHit) -> str:
    return f"{hit.title} · {hit.variant}\n{_plain_snippet(hit.snippet)}"


def _result_title(hit: SearchHit) -> str:
    return f"{hit.title} · {hit.variant}"


class SearchQueryLineEdit(QLineEdit):
    """Search input that keeps arrow keys for result navigation."""

    move_selection = Signal(int)
    confirm_selection = Signal()
    cancel_search = Signal()

    def event(self, event: QEvent) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.ShortcutOverride and isinstance(
            event, QKeyEvent
        ):
            if event.key() in {
                Qt.Key.Key_Down,
                Qt.Key.Key_Up,
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Escape,
            }:
                event.accept()
                return True
        return super().event(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if self.handle_navigation_key(event):
            return
        super().keyPressEvent(event)

    def handle_navigation_key(self, event: QKeyEvent) -> bool:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.cancel_search.emit()
            event.accept()
            return True
        if key in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
            self.confirm_selection.emit()
            event.accept()
            return True
        if key == Qt.Key.Key_Down:
            self.move_selection.emit(1)
            event.accept()
            return True
        if key == Qt.Key.Key_Up:
            self.move_selection.emit(-1)
            event.accept()
            return True
        return False


class SearchResultItemDelegate(QStyledItemDelegate):
    """Paint search hits with a bold title line and snippet below it."""

    def __init__(self, *, list_width: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        base = QApplication.font()
        self._title_font = _title_font(base)
        self._snippet_font = _snippet_font(base)
        self._list_width = list_width

    def set_list_width(self, width: int) -> None:
        self._list_width = width

    def size_hint_for(self, hit: SearchHit, width: int) -> QSize:
        height = (
            _ITEM_VERTICAL_PADDING * 2
            + _ITEM_LINE_SPACING
            + _line_height(self._title_font)
            + _line_height(self._snippet_font)
        )
        return QSize(width, height)

    def sizeHint(  # noqa: N802
        self,
        option: QStyleOptionViewItem,
        index,
    ) -> QSize:
        hit = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(hit, SearchHit):
            return super().sizeHint(option, index)
        width = option.rect.width() if option.rect.width() > 0 else self._list_width
        return self.size_hint_for(hit, width)

    def paint(  # noqa: N802
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index,
    ) -> None:
        hit = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(hit, SearchHit):
            super().paint(painter, option, index)
            return

        painter.save()
        rect = option.rect
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if selected:
            painter.fillRect(rect, option.palette.highlight())
            title_color = option.palette.highlightedText().color()
            snippet_color = title_color
        else:
            title_color = option.palette.text().color()
            snippet_color = option.palette.color(QPalette.ColorRole.PlaceholderText)

        content_width = max(rect.width() - 2 * _ITEM_HORIZONTAL_PADDING, 1)
        x = rect.x() + _ITEM_HORIZONTAL_PADDING
        y = rect.y() + _ITEM_VERTICAL_PADDING
        title_text = _elide_text(_result_title(hit), self._title_font, content_width)
        snippet_text = _elide_text(
            _plain_snippet(hit.snippet), self._snippet_font, content_width
        )
        title_height = _line_height(self._title_font)
        snippet_height = _line_height(self._snippet_font)
        align = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        painter.setFont(self._title_font)
        painter.setPen(title_color)
        painter.drawText(
            QRect(x, y, content_width, title_height),
            align,
            title_text,
        )

        painter.setFont(self._snippet_font)
        painter.setPen(snippet_color)
        snippet_rect = QRect(
            x,
            y + title_height + _ITEM_LINE_SPACING,
            content_width,
            snippet_height,
        )
        painter.drawText(
            snippet_rect,
            align,
            snippet_text,
        )
        painter.restore()


class LibrarySearchField(QWidget):
    hit_selected = Signal(object)

    def __init__(
        self,
        *,
        index: LibraryIndex,
        language_code: Callable[[], str | None],
        object_name: str = "library_search",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self._index = index
        self._language_code = language_code
        self._hits: list[SearchHit] = []
        self._selected_row = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._query = SearchQueryLineEdit(self)
        self._query.setObjectName(f"{object_name}_query")
        self._query.setPlaceholderText("Search library")
        self._query.setClearButtonEnabled(True)
        self._query.textChanged.connect(self._refresh_results)
        self._query.move_selection.connect(self._move_selection)
        self._query.confirm_selection.connect(self._confirm_selection)
        self._query.cancel_search.connect(self._hide_popup)
        self._query.installEventFilter(self)
        layout.addWidget(self._query)

        self._popup = QFrame(
            None,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint,
        )
        self._popup.setObjectName(f"{object_name}_popup")
        self._popup.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        self._results = QListWidget(self._popup)
        self._results.setObjectName(f"{object_name}_results")
        self._results.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._results.setSpacing(0)
        self._results.setFrameShape(QFrame.Shape.NoFrame)
        self._results.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._results.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._results.setStyleSheet(
            "QListWidget { background: palette(base); border: none; outline: none; }"
            "QListWidget::item { padding: 0px; margin: 0px; border: none; }"
            "QListWidget::item:selected { background: transparent; }"
        )
        self._delegate = SearchResultItemDelegate(
            list_width=_MIN_POPUP_WIDTH,
            parent=self._results,
        )
        self._results.setItemDelegate(self._delegate)
        self._results.itemActivated.connect(self._emit_selected_item)
        self._results.itemClicked.connect(self._emit_selected_item)
        popup_layout.addWidget(self._results)

        app = QApplication.instance()
        if app is not None:
            app.applicationStateChanged.connect(self._on_application_state_changed)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        window = self.window()
        if window is not None:
            window.installEventFilter(self)

    def _on_application_state_changed(self, state: Qt.ApplicationState) -> None:
        if state != Qt.ApplicationState.ApplicationActive:
            self._hide_popup()
            return
        QTimer.singleShot(0, self._restore_popup_if_needed)

    def _restore_popup_if_needed(self) -> None:
        if not isValid(self) or not isValid(self._query) or not isValid(self._popup):
            return
        if self._query.text().strip() and self._results.count() > 0:
            row = self._selected_row if self._selected_row >= 0 else 0
            self._show_popup()
            self._apply_selection(row)

    def line_edit(self) -> QLineEdit:
        return self._query

    def _confirm_selection(self) -> None:
        if not self._popup.isVisible() or self._selected_row < 0:
            return
        item = self._results.item(self._selected_row)
        if item is not None:
            self._emit_selected_item(item)

    def focus_search(self) -> None:
        """Move keyboard focus to the search field with a fresh query."""
        self._query.clear()
        self._hits = []
        self._results.clear()
        self._selected_row = -1
        self._hide_popup()
        self._query.setFocus()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.WindowDeactivate:
            window = self.window()
            if watched is window:
                self._hide_popup()
                return False
        if event.type() == QEvent.Type.WindowActivate:
            window = self.window()
            if watched is window:
                QTimer.singleShot(0, self._restore_popup_if_needed)
                return False
        if watched is self._query and isinstance(event, QKeyEvent):
            if (
                event.type() == QEvent.Type.KeyPress
                and self._query.handle_navigation_key(event)
            ):
                return True
        return super().eventFilter(watched, event)

    def _move_selection(self, delta: int) -> None:
        count = self._results.count()
        if count == 0:
            return
        if not self._popup.isVisible():
            self._show_popup()
        current = self._selected_row
        if current < 0:
            target = 0 if delta >= 0 else count - 1
        else:
            target = max(0, min(current + delta, count - 1))
        self._apply_selection(target)

    def _apply_selection(self, row: int) -> None:
        if self._results.count() == 0:
            self._selected_row = -1
            return
        row = max(0, min(row, self._results.count() - 1))
        self._selected_row = row
        self._results.setCurrentRow(row)
        item = self._results.item(row)
        if item is not None:
            self._results.scrollToItem(item)
        self._results.viewport().update()

    def _refresh_results(self) -> None:
        language = self._language_code()
        query = self._query.text().strip()
        self._results.clear()
        self._selected_row = -1
        if language is None or not query:
            self._hits = []
            self._hide_popup()
            return
        self._hits = search_texts(self._index, lang=language, query=query)
        if not self._hits:
            self._hide_popup()
            return
        popup_width = max(self.width(), _MIN_POPUP_WIDTH)
        self._delegate.set_list_width(popup_width)
        for hit in self._hits:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, hit)
            item.setSizeHint(self._delegate.size_hint_for(hit, popup_width))
            self._results.addItem(item)
        self._apply_selection(0)
        self._show_popup()

    def _popup_position(self) -> tuple[QPoint, int]:
        top_left = self.mapToGlobal(QPoint(0, 0))
        bottom = self._query.mapToGlobal(self._query.rect().bottomLeft())
        width = max(self.width(), _MIN_POPUP_WIDTH)
        return QPoint(top_left.x(), bottom.y()), width

    def _results_content_height(self) -> int:
        count = self._results.count()
        if count == 0:
            return 0
        visible_rows = min(count, _MAX_VISIBLE_RESULTS)
        height = 0
        for row in range(visible_rows):
            item = self._results.item(row)
            if item is not None:
                height += item.sizeHint().height()
        return height

    def _show_popup(self) -> None:
        if self._results.count() == 0:
            self._hide_popup()
            return
        content_height = self._results_content_height()
        if self._results.count() > _MAX_VISIBLE_RESULTS:
            self._results.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
        else:
            self._results.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
        anchor, width = self._popup_position()
        self._popup.setFixedWidth(width)
        self._popup.setFixedHeight(content_height)
        self._results.setFixedHeight(content_height)
        self._popup.setParent(None)
        self._popup.move(anchor)
        self._popup.show()
        if self._selected_row >= 0:
            self._apply_selection(self._selected_row)
        elif self._results.count() > 0:
            self._apply_selection(0)
        QTimer.singleShot(0, self._query.setFocus)

    def _hide_popup(self) -> None:
        self._popup.hide()

    def _emit_selected_item(self, item: QListWidgetItem) -> None:
        hit = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(hit, SearchHit):
            return
        self._query.clear()
        self._hide_popup()
        self.hit_selected.emit(hit)
