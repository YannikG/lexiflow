"""Global library search field tests."""

from __future__ import annotations

from uuid import UUID

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.search import SearchHit
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.widgets.library_search_field import (
    LibrarySearchField,
    SearchResultItemDelegate,
    _plain_snippet,
    _result_label,
)
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence


@pytest.fixture(autouse=True)
def _disable_search_debounce(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(LibrarySearchField, "_SEARCH_DEBOUNCE_MS", 0)


def test_plain_snippet_strips_mark_tags() -> None:
    assert _plain_snippet("...Gege<mark>nmaßnah</mark>men...") == "...Gegenmaßnahmen..."
    assert "<mark>" not in _result_label(
        SearchHit(
            text_id=UUID("00000000-0000-0000-0000-000000000001"),
            title="Article",
            variant="native",
            snippet="<mark>Maßnah</mark>men gegen die Paketflut",
        )
    )


def test_search_shortcut_focuses_toolbar_field(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    focused: list[bool] = []

    def fake_focus() -> None:
        focused.append(True)
        window._toolbar_search.focus_search()

    monkeypatch.setattr(window, "_focus_library_search", fake_focus)
    window._search_action.trigger()

    assert focused == [True]
    assert window._search_action.shortcut() == QKeySequence(
        QKeySequence.StandardKey.Find
    )


def test_typing_in_search_shows_dropdown_results(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window._text_repository.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="en",
            body="palabraunica",
        )
    )
    window.show()
    qtbot.waitExposed(window)

    qtbot.keyClicks(window._toolbar_search.line_edit(), "palabra")

    assert window._toolbar_search._popup.isVisible()
    assert window._toolbar_search._results.count() >= 1


def test_can_continue_typing_while_results_popup_is_open(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window._text_repository.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="en",
            body="palabraunica",
        )
    )
    window.show()
    qtbot.waitExposed(window)

    line_edit = window._toolbar_search.line_edit()
    line_edit.setFocus()
    qtbot.keyClicks(line_edit, "pa")
    assert window._toolbar_search._popup.isVisible()

    qtbot.keyClicks(line_edit, "labra")

    assert line_edit.text() == "palabra"
    assert window._toolbar_search._popup.isVisible()


def test_popup_is_positioned_below_search_field(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window._text_repository.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="en",
            body="palabraunica",
        )
    )
    window.show()
    qtbot.waitExposed(window)

    search = window._toolbar_search
    line_edit = search.line_edit()
    line_edit.setFocus()
    qtbot.keyClicks(line_edit, "palabra")

    popup_top = search._popup.frameGeometry().top()
    field_bottom = search.mapToGlobal(search.rect().bottomLeft()).y()
    assert popup_top >= field_bottom - 2


def test_popup_height_matches_result_count(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="de", native_language="en"),
    )
    qtbot.addWidget(window)
    window._text_repository.create_text(
        CreateTextRequest(
            title="Maßnahmen gegen die Paketflut",
            group="News",
            target_language="de",
            native_language="en",
            body="Maßnahmen gegen die Paketflut",
        )
    )
    window.show()
    qtbot.waitExposed(window)

    search = window._toolbar_search
    qtbot.keyClicks(search.line_edit(), "Paket")

    assert search._popup.isVisible()
    assert search._results.count() == 1
    expected_height = search._results_content_height()
    assert search._popup.height() == expected_height
    assert search._results.height() == expected_height


def test_popup_hides_when_application_becomes_inactive(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window._text_repository.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="en",
            body="palabraunica",
        )
    )
    window.show()
    qtbot.waitExposed(window)

    search = window._toolbar_search
    line_edit = search.line_edit()
    line_edit.setFocus()
    qtbot.keyClicks(line_edit, "palabra")
    assert search._popup.isVisible()

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    QApplication.instance().applicationStateChanged.emit(
        Qt.ApplicationState.ApplicationInactive
    )

    assert not search._popup.isVisible()


def test_popup_returns_when_application_becomes_active_again(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window._text_repository.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="en",
            body="palabraunica",
        )
    )
    window.show()
    qtbot.waitExposed(window)

    search = window._toolbar_search
    line_edit = search.line_edit()
    line_edit.setFocus()
    qtbot.keyClicks(line_edit, "palabra")
    assert search._popup.isVisible()

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    app.applicationStateChanged.emit(Qt.ApplicationState.ApplicationInactive)
    assert not search._popup.isVisible()

    search._restore_popup_if_needed()

    assert search._popup.isVisible()
    assert search._results.count() >= 1


def test_arrow_keys_move_selection_in_search_results(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window._text_repository.create_text(
        CreateTextRequest(
            title="Alpha",
            group="News",
            target_language="es",
            native_language="en",
            body="alpha keyword",
        )
    )
    window._text_repository.create_text(
        CreateTextRequest(
            title="Beta",
            group="News",
            target_language="es",
            native_language="en",
            body="beta keyword",
        )
    )
    window.show()
    qtbot.waitExposed(window)

    search = window._toolbar_search
    line_edit = search.line_edit()
    line_edit.setFocus()
    qtbot.keyClicks(line_edit, "keyword")
    assert search._results.currentRow() == 0

    qtbot.keyPress(line_edit, Qt.Key.Key_Down)
    assert search._selected_row == 1

    qtbot.keyPress(line_edit, Qt.Key.Key_Up)
    assert search._selected_row == 0
    assert search._results.item(0).isSelected()
    assert not search._results.item(1).isSelected()


def test_result_row_height_matches_delegate_size_hint(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window._text_repository.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="en",
            body="keyword match",
        )
    )
    window.show()
    qtbot.waitExposed(window)

    search = window._toolbar_search
    qtbot.keyClicks(search.line_edit(), "keyword")

    item = search._results.item(0)
    hit = item.data(Qt.ItemDataRole.UserRole)
    assert item is not None
    assert hit is not None
    assert isinstance(search._delegate, SearchResultItemDelegate)
    assert (
        item.sizeHint().height()
        == search._delegate.size_hint_for(hit, item.sizeHint().width()).height()
    )


def test_delegate_row_height_fits_title_and_snippet(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="de", native_language="en"),
    )
    qtbot.addWidget(window)
    ebola_title = (
        "Drei Ebola-Impfstoffe in Entwicklung angesichts wachsender Ausbruchsängste"
    )
    for variant_body in (
        "Maßnahmen gegen die Paketflut im Detail.",
        "Es gibt wachsende Besorgnis über den Ausbruch in Uganda.",
    ):
        window._text_repository.create_text(
            CreateTextRequest(
                title="Maßnahmen gegen die Paketflut",
                group="News",
                target_language="de",
                native_language="en",
                body=variant_body,
            )
        )
        window._text_repository.create_text(
            CreateTextRequest(
                title=ebola_title,
                group="News",
                target_language="de",
                native_language="en",
                body=variant_body,
            )
        )
    window.show()
    qtbot.waitExposed(window)

    search = window._toolbar_search
    qtbot.keyClicks(search.line_edit(), "Maß")

    delegate = search._delegate
    for row in range(search._results.count()):
        item = search._results.item(row)
        hit = item.data(Qt.ItemDataRole.UserRole)
        assert item is not None
        row_height = item.sizeHint().height()
        expected = delegate.size_hint_for(hit, item.sizeHint().width()).height()
        assert row_height >= expected


def test_selecting_search_hit_opens_reader_on_variant(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    record = window._text_repository.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    hit = SearchHit(
        text_id=record.id,
        title=record.title,
        variant="native",
        snippet="<mark>hola</mark>",
    )
    opened: list[tuple[UUID, str]] = []
    query_seen: list[str] = []

    def tracking_open(**kwargs: object) -> bool:
        opened.append((kwargs["record"].id, kwargs["initial_tab"]))  # type: ignore[index]
        return True

    def tracking_scroll(query: str) -> None:
        query_seen.append(query)

    monkeypatch.setattr(window._reader, "open_text", tracking_open)
    monkeypatch.setattr(window._reader, "scroll_to_match", tracking_scroll)

    window._open_reader_for_search_hit(hit, query="hola")

    assert opened == [(record.id, "native")]
    assert query_seen == ["hola"]


def test_library_search_field_can_be_found_by_object_name(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)

    assert window.findChild(LibrarySearchField, "toolbar_search") is not None
