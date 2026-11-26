# -*- coding: utf-8 -*-
"""Watermelon's Office area (2026-11-20): Word / Excel / PowerPoint files in the editing column.

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (5.11, 5.14)
Ryan 2026-11-20: "Office 组件当然是自己带一份了，肯定是要自己内置的"; "把它包起来…不要让它孤零零的就这么
露出来"; switching files: "用那个下拉栏去切换".

The editing component is the same bundled one Broccoli's editor uses (office_editor/, driven through
office_editor_bridge.py, both copied unchanged). It is content, never glass, and keeps its own toolbar,
menus and status bar (5.11). Watermelon wraps it in the same thin frame as its web area.

OfficePanel shows ONE document at a time:
    show_file(path)     save the document shown (if it was edited), then show this one
    leave()             save the document shown (if it was edited); the panel may be hidden afterwards
    flush_blocking()    before quitting: wait (a few seconds at most) for the last save
It saves by itself a moment after every edit, to the file the document was opened from.
Import this module AFTER the QApplication exists.
"""
import logging
import os
import sys
import tempfile

from PyQt6.QtCore import Qt, QTimer, QEventLoop, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout

import office_editor_bridge
from office_editor_bridge import OFFICE_EDITOR_EXTS
from glass_kit import _tr

AUTOSAVE_DELAY_MS = 1200        # after an edit
QUIT_SAVE_WAIT_MS = 15000       # the longest a quit waits for the last save
MAX_OFFICE_FILE_BYTES = 300 * 1024 * 1024


def is_office_path(path) -> bool:
    return str(path or '').lower().endswith(OFFICE_EDITOR_EXTS)


def component_folder(app_resources: str) -> str:
    """The bundled component: inside the app, or beside this file when run from source."""
    for folder in (os.path.join(app_resources, 'office_editor'),
                   os.path.join(os.path.dirname(os.path.abspath(__file__)), 'office_editor')):
        if os.path.isfile(os.path.join(folder, 'manifest.json')):
            return folder
    return ''


_COMPONENT = []   # [(component or None, reason)]


def load_component(app_resources: str):
    """(component, '') or (None, reason); looked up once."""
    if not _COMPONENT:
        folder = component_folder(app_resources)
        if not folder:
            _COMPONENT.append((None, 'the Office component is not installed'))
        else:
            _COMPONENT.append(office_editor_bridge.load_component(folder))
    return _COMPONENT[0]


def write_file_atomically(path: str, data: bytes) -> None:
    """The file is replaced in one step (a crash in the middle leaves the old file), keeping its mode."""
    folder = os.path.dirname(path) or '.'
    handle, temp_path = tempfile.mkstemp(prefix='.wm-office-', dir=folder)
    try:
        with os.fdopen(handle, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        try:
            os.chmod(temp_path, os.stat(path).st_mode & 0o7777)
        except OSError:
            pass
        os.replace(temp_path, path)
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


BLOCK_RADIUS = 4   # the corner of Watermelon's text boxes; the main window cuts this block to the same corner


class _RoundedEdge(QWidget):
    """The block's border: one smooth line on top of the component, along the rounded corner the window
    shape is cut to (web content has square corners and would cover a border drawn underneath it)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.color = QColor('grey')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self.color, 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), BLOCK_RADIUS, BLOCK_RADIUS)
        painter.end()


class OfficePanel(QWidget):
    fileSaved = pyqtSignal(str)              # path
    saveFailed = pyqtSignal(str, str)        # path, reason (the document stays shown)
    switchRefused = pyqtSignal(str)          # the path still shown: its changes could not be saved
    fileOpened = pyqtSignal(str)

    def __init__(self, component, language='en', dark_getter=None, parent=None):
        super().__init__(parent)
        self.setObjectName('OfficeModePanel')
        self._component = component
        self._language = language
        self._dark_getter = dark_getter or (lambda: False)
        self._view = None
        self._view_dark = None
        self._path = ''                # the document shown
        self._touched = False          # edited since it was opened / last saved
        self._saving_path = ''         # a save is on its way for this path
        self._after_save = []          # callbacks(ok) once the running save ends
        self._next_path = None         # show this after the running save
        self._frame = QFrame(self)
        self._frame.setObjectName('officeModeFrame')
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._frame)
        self._frame_layout = QVBoxLayout(self._frame)
        self._frame_layout.setContentsMargins(1, 1, 1, 1)
        self._frame_layout.setSpacing(0)
        # "opening … / could not open": one grey line in the middle (5.11), over the component
        self._status = QLabel('', self._frame)
        self._status.setObjectName('officeModeStatus')
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setWordWrap(True)
        self._edge = _RoundedEdge(self)
        self._autosave = QTimer(self)
        self._autosave.setSingleShot(True)
        self._autosave.setInterval(AUTOSAVE_DELAY_MS)
        self._autosave.timeout.connect(self._save_now)
        self._dark = None
        self.apply_theme()

    # ── look ──
    def apply_theme(self):
        dark = bool(self._dark_getter())
        if dark == self._dark:
            return
        self._dark = dark
        background = '#2D2D2D' if dark else '#FFFFFF'
        border = '#555555' if dark else 'grey'
        grey = '#8E8E93' if dark else '#A0A0A6'
        self.setStyleSheet(
            'QWidget#OfficeModePanel { background: transparent; border: none; }'
            'QFrame#officeModeFrame { border: none; background: transparent; }'
            'QLabel#officeModeStatus { border: none; border-radius: %dpx; background: %s; color: %s; font-size: 13px; }'
            % (BLOCK_RADIUS, background, grey))
        self._edge.color = QColor(border)
        self._edge.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_status()

    def _place_status(self):
        self._status.setGeometry(self._frame.rect().adjusted(1, 1, -1, -1))
        self._edge.setGeometry(self.rect())
        self._edge.raise_()

    def _show_status(self, text):
        self._status.setText(text)
        self._place_status()
        self._status.show()
        self._status.raise_()
        self._edge.raise_()

    # ── state ──
    def current_path(self) -> str:
        return self._path

    def is_busy_saving(self) -> bool:
        return bool(self._saving_path)

    def has_unsaved_changes(self) -> bool:
        return bool(self._path and (self._touched or self._saving_path))

    # ── the component view (built on first use; rebuilt when light / dark changed since: 5.11) ──
    def _ensure_view(self):
        dark = bool(self._dark_getter())
        if self._view is not None and self._view_dark == dark:
            return self._view
        self._drop_view()
        view = office_editor_bridge.OfficeEditorView(self._component, language=self._language, dark=dark,
                                                     parent=self._frame)
        view.opened.connect(self._on_opened)
        view.failed.connect(self._on_failed)
        view.dirtyChanged.connect(self._on_dirty)
        view.saved.connect(self._on_saved)
        view.saveFailed.connect(self._on_save_failed)
        self._frame_layout.addWidget(view)
        self._edge.raise_()
        self._view, self._view_dark = view, dark
        return view

    def _drop_view(self):
        if self._view is None:
            return
        view, self._view = self._view, None
        try:
            view.shutdown()
        except Exception:
            logging.exception('Closing the Office view failed.')
        self._frame_layout.removeWidget(view)
        view.hide()
        view.deleteLater()

    # ── actions ──
    def show_file(self, path: str) -> None:
        path = str(path or '')
        if path == self._path and not self._next_path:
            return
        if self.has_unsaved_changes():
            self._next_path = path
            self._save_then(lambda ok: self._after_switch_save(ok))
            return
        self._open(path)

    def _after_switch_save(self, ok: bool) -> None:
        path, self._next_path = self._next_path, None
        if path is None:
            return
        if ok:
            self._open(path)
        else:
            self.switchRefused.emit(self._path)

    def _open(self, path: str) -> None:
        self._autosave.stop()
        self._path = path
        self._touched = False
        name = os.path.basename(path)
        try:
            if os.path.getsize(path) > MAX_OFFICE_FILE_BYTES:
                raise OSError(_tr('the file is too large'))
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            self._show_status(_tr('Could not open "%1": %2').replace('%1', name).replace('%2', str(exc.strerror or exc)))
            return
        self._show_status(_tr('Opening "%1"…').replace('%1', name))
        self._ensure_view().open_bytes(name, data)

    def leave(self) -> None:
        """The panel is about to be hidden: save what was edited (the save finishes in the background)."""
        if self._touched and not self._saving_path:
            self._save_now()

    def copy_to(self, target_path: str, done) -> None:
        """Save the document shown, then copy its file to target_path; done(ok, reason)."""
        source = self._path

        def after(ok):
            if not ok:
                done(False, _tr('the changes could not be saved'))
                return
            try:
                with open(source, 'rb') as handle:
                    write_file_atomically(target_path, handle.read())
                done(True, '')
            except OSError as exc:
                done(False, str(exc.strerror or exc))

        if self.has_unsaved_changes():
            self._save_then(after)
        else:
            after(True)

    def flush_blocking(self, timeout_ms: int = QUIT_SAVE_WAIT_MS) -> bool:
        """Before quitting: the last edits reach the file. False when they did not in time."""
        if not self.has_unsaved_changes():
            return True
        loop = QEventLoop()
        result = []

        def after(ok):
            result.append(ok)
            loop.quit()

        self._save_then(after)
        if not result:
            QTimer.singleShot(int(timeout_ms), loop.quit)
            loop.exec()
        return bool(result and result[0])

    def shutdown(self) -> None:
        self._autosave.stop()
        self._drop_view()

    # ── saving ──
    def _save_then(self, callback) -> None:
        self._after_save.append(callback)
        if not self._saving_path:
            self._save_now()

    def _save_now(self) -> None:
        self._autosave.stop()
        if self._saving_path:
            return
        view = self._view
        if view is None or not self._path:
            self._finish_save(True)
            return
        if not self._touched:
            self._finish_save(True)
            return
        if not view.save():
            if view.is_busy():           # still opening: nothing can have been edited yet … try again shortly
                self._autosave.start(400)
                return
            self._finish_save(False, 'the component cannot save right now')
            return
        self._saving_path = self._path
        self._touched = False            # edits made from now on mark it again

    def _on_saved(self, data: bytes) -> None:
        path, self._saving_path = self._saving_path, ''
        if not path:
            return
        try:
            write_file_atomically(path, bytes(data))
        except Exception as exc:
            self._touched = True
            self._finish_save(False, str(getattr(exc, 'strerror', None) or exc), path)
            return
        self.fileSaved.emit(path)
        if self._touched:                # edited while the save ran
            self._autosave.start()
            if self._after_save:         # … and somebody is waiting for a complete save
                self._save_now()
                return
        self._finish_save(True)

    def _on_save_failed(self, reason: str) -> None:
        path, self._saving_path = self._saving_path, ''
        self._touched = True
        self._finish_save(False, reason, path)

    def _finish_save(self, ok: bool, reason: str = '', path: str = '') -> None:
        waiting, self._after_save = self._after_save, []
        if not ok:
            logging.warning('Saving the Office file %s failed: %s', path or self._path, reason)
            self.saveFailed.emit(path or self._path, reason)
        for callback in waiting:
            try:
                callback(ok)
            except Exception:
                logging.exception('An after-save step failed.')

    # ── events from the component ──
    def _on_opened(self) -> None:
        self._status.hide()
        self._touched = False
        self.fileOpened.emit(self._path)

    def _on_failed(self, reason: str) -> None:
        self._show_status(_tr('Could not open "%1": %2').replace('%1', os.path.basename(self._path)).replace(
            '%2', str(reason)))

    def _on_dirty(self, dirty: bool) -> None:
        if dirty:
            self._touched = True
            self._autosave.start()
