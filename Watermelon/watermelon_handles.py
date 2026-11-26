# -*- coding: utf-8 -*-
"""Watermelon: the two handles that bring the side panels out (2026-11-21).

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (5.14, 5.10, 5.12)
Ryan 2026-11-21 (after seeing a round Lecture button added below the typewriter): "不要你多加一个按钮…好丑";
"学习一下 tomato 和 strawberry 那个点一下拉出来的按钮，鼠标 hover 上去才有圆形按钮，就那个样式就行了，
左边一个按钮右边一个，各一个".
The same handle as Strawberry's card drawer / Tomato's editing panel: a glass round button 22 with a system
chevron, not shown normally; it fades in (0.15 s) after the pointer rested 0.15 s in a band along the edge of
the editing column, and fades out 0.25 s after the pointer left; never while a mouse button is down. It
stands in the empty strip beside the column (6 from the column, vertically centred), never on the column.

  HandleButton     the round button
  SideHandles      the two of them: where the pointer is, showing / hiding, the click
Import this module AFTER the QApplication exists.
"""
from PyQt6.QtCore import Qt, QEvent, QObject, QPoint, QRect, QSize, QTimer, QVariantAnimation, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QIcon, QPainter, QPalette
from PyQt6.QtWidgets import QApplication, QPushButton

from glass_kit import edge_hint_symbol_pixmap, glass_button

HANDLE_SIZE = 22
HANDLE_GAP = 6            # from the editing column's edge
BAND_INSIDE = 28          # the band where the pointer brings the handle up: this far into the column …
HOVER_DELAY_MS = 150
FADE_MS = 150
HIDE_DELAY_MS = 250
HOVER_POLL_MS = 60        # while the pointer is over the window: where it is


class HandleButton(QPushButton):
    """A glass round button 22 with a system line icon 16 (style book 5.1). Always the light glass, like the
    two panels (Ryan 2026-11-21: "不要用深色液态玻璃，浅色的"). Without glass: the same disc, solid."""

    def __init__(self, symbol, parent=None):
        super().__init__('', parent)
        self._symbol = ''
        self.setAutoDefault(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(HANDLE_SIZE, HANDLE_SIZE)
        self.setIconSize(QSize(16, 16))
        self.setStyleSheet('QPushButton { background-color: rgba(255,255,255,0.92); border: 1px solid rgba(0,0,0,0.12);'
                           ' border-radius: %dpx; padding: 0; } QPushButton:pressed { background-color: rgba(228,228,228,0.96); }'
                           % (HANDLE_SIZE // 2))
        self.set_symbol(symbol)
        glass_button(self, radius_for=lambda b: b.height() / 2.0, dark_for=lambda b: False)

    def symbol(self) -> str:
        return self._symbol

    def set_badge(self, on: bool):
        """A small dot in the system accent colour on the button's corner: something new is behind it."""
        if bool(on) != getattr(self, '_badge', False):
            self._badge = bool(on)
            self.update()

    def has_badge(self) -> bool:
        return bool(getattr(self, '_badge', False))

    def paintEvent(self, event):
        super().paintEvent(event)
        if getattr(self, '_badge', False):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QApplication.palette().color(QPalette.ColorRole.Accent))
            painter.drawEllipse(self.width() - 8, 1, 7, 7)
            painter.end()

    def set_symbol(self, symbol):
        if symbol == self._symbol:
            return
        self._symbol = str(symbol)
        pixmap = edge_hint_symbol_pixmap(self._symbol, QColor('#3A3A3C'), 16)
        self.setIcon(QIcon(pixmap) if pixmap is not None else QIcon())
        if pixmap is None:
            self.setText('‹' if self._symbol.endswith('left') else '›')


class _Side:
    def __init__(self, name, button):
        self.name = name
        self.button = button
        self.inside = False
        self.attention = False      # stays in view (with its dot) until the panel was looked at
        self.show_timer = QTimer()
        self.show_timer.setSingleShot(True)
        self.show_timer.setInterval(HOVER_DELAY_MS)
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(HIDE_DELAY_MS)
        self.fade = QVariantAnimation()
        self.fade.setDuration(FADE_MS)


class SideHandles(QObject):
    """`column()` → the editing column's rectangle in the window (empty = no handles now);
    `panel(side)` → the side panel's rectangle while it is out (else None); `available(side)`;
    `is_open(side)`; `tip(side)`. `changed` tells the window that a handle came or went (its click shape)."""
    clicked = pyqtSignal(str)        # 'left' | 'right'
    changed = pyqtSignal()

    def __init__(self, window, column, panel, available, is_open, tip):
        super().__init__(window)
        self._window = window
        self._column, self._panel, self._available, self._is_open, self._tip = column, panel, available, is_open, tip
        self._sides = {}
        for name in ('left', 'right'):
            button = HandleButton('chevron.left', window)
            button.hide()
            side = _Side(name, button)
            button.clicked.connect(lambda _checked=False, n=name: self._on_click(n))
            side.show_timer.timeout.connect(lambda n=name: self._show(n))
            side.hide_timer.timeout.connect(lambda n=name: self._maybe_hide(n))
            side.fade.valueChanged.connect(lambda value, n=name: self._set_alpha(n, value))
            side.fade.finished.connect(lambda n=name: self._fade_finished(n))
            self._sides[name] = side
        self._poll = QTimer(self)
        self._poll.setInterval(HOVER_POLL_MS)
        self._poll.timeout.connect(self.check_pointer)
        window.installEventFilter(self)

    def button(self, side) -> HandleButton:
        return self._sides[side].button

    def visible_rects(self) -> list:
        return [side.button.geometry() for side in self._sides.values() if side.button.isVisible()]

    # where
    def handle_rect(self, side) -> QRect:
        column = self._column()
        if column.isEmpty():
            return QRect()
        y = column.center().y() - HANDLE_SIZE // 2
        if side == 'left':
            return QRect(column.left() - HANDLE_GAP - HANDLE_SIZE, y, HANDLE_SIZE, HANDLE_SIZE)
        return QRect(column.right() + 1 + HANDLE_GAP, y, HANDLE_SIZE, HANDLE_SIZE)

    def band(self, side) -> QRect:
        """Along the column's edge, this far into it; with the panel out, the panel too."""
        column = self._column()
        if column.isEmpty() or not self._available(side):
            return QRect()
        if side == 'left':
            band = QRect(column.left(), column.top(), BAND_INSIDE, column.height())
        else:
            band = QRect(column.right() + 1 - BAND_INSIDE, column.top(), BAND_INSIDE, column.height())
        panel = self._panel(side)
        return band.united(panel) if panel is not None and not panel.isEmpty() else band

    def _pointer_in(self, side, pos=None) -> bool:
        band = self.band(side)
        if band.isEmpty():
            return False
        pos = self._window.mapFromGlobal(QCursor.pos()) if pos is None else pos
        button = self._sides[side].button
        return band.contains(pos) or (button.isVisible() and button.geometry().adjusted(-4, -4, 4, 4).contains(pos))

    # the pointer
    def eventFilter(self, obj, event):
        if obj is self._window:
            if event.type() == QEvent.Type.Enter:
                self._poll.start()
                self.check_pointer()
            elif event.type() in (QEvent.Type.Leave, QEvent.Type.Hide):
                self._poll.stop()
                self.check_pointer(QPoint(-10000, -10000) if event.type() == QEvent.Type.Hide else None)
        return False

    def check_pointer(self, pos=None):
        for name, side in self._sides.items():
            inside = self._pointer_in(name, pos)
            if inside == side.inside and (inside or not side.button.isVisible() or side.hide_timer.isActive()
                                          or side.fade.state() == side.fade.State.Running):
                continue
            side.inside = inside
            if inside:
                side.hide_timer.stop()
                if not side.button.isVisible() or side.fade.endValue() == 0.0:
                    side.show_timer.start()
            else:
                side.show_timer.stop()
                if side.button.isVisible():
                    side.hide_timer.start()

    # showing and hiding
    def _show(self, name):
        side = self._sides[name]
        if QApplication.mouseButtons() != Qt.MouseButton.NoButton or not self._pointer_in(name):
            return
        self.refresh(name)
        start = 0.0 if not side.button.isVisible() else self._alpha(name)
        side.button.show()
        side.button.raise_()
        side.fade.stop()
        side.fade.setStartValue(start)
        side.fade.setEndValue(1.0)
        side.fade.start()
        self.changed.emit()

    def refresh(self, name):
        """The chevron points the way the panel will go: out into the strip, or back."""
        side = self._sides[name]
        out = self._is_open(name)
        outward = 'chevron.left' if name == 'left' else 'chevron.right'
        inward = 'chevron.right' if name == 'left' else 'chevron.left'
        side.button.set_symbol(inward if out else outward)
        side.button.setToolTip(self._tip(name))
        rect = self.handle_rect(name)
        if not rect.isEmpty():
            side.button.setGeometry(rect)

    def set_attention(self, name, on: bool):
        """Something new is in the panel while it is pushed back: the handle stays in view with a dot until
        the panel is pulled out."""
        side = self._sides[name]
        side.attention = bool(on)
        side.button.set_badge(side.attention)
        self.sync_attention()

    def sync_attention(self):
        for name, side in self._sides.items():
            if side.attention and not side.button.isVisible() and not self.handle_rect(name).isEmpty():
                self.refresh(name)
                side.fade.stop()
                self._set_alpha(name, 1.0)
                side.button.show()
                side.button.raise_()
                self.changed.emit()
            elif not side.attention and side.button.isVisible() and not self._pointer_in(name) and not side.hide_timer.isActive():
                side.hide_timer.start()

    def _maybe_hide(self, name):
        side = self._sides[name]
        if self._pointer_in(name) or not side.button.isVisible() or side.attention:
            return
        side.fade.stop()
        side.fade.setStartValue(self._alpha(name))
        side.fade.setEndValue(0.0)
        side.fade.start()

    def hide_now(self, name=None):
        for key, side in self._sides.items():
            if name in (None, key):
                side.show_timer.stop()
                side.hide_timer.stop()
                side.fade.stop()
                side.inside = False
                if side.button.isVisible():
                    side.button.hide()
                    self._set_alpha(key, 1.0)
                    self.changed.emit()

    def _glass(self, name):
        helper = getattr(self._sides[name].button, '_broccoli_inwindow_glass', None)
        return getattr(helper, 'glass', None)

    def _alpha(self, name) -> float:
        glass = self._glass(name)
        try:
            return float(glass.alphaValue()) if glass is not None else 1.0
        except Exception:
            return 1.0

    def _set_alpha(self, name, value):
        glass = self._glass(name)
        if glass is not None:
            try:
                glass.setAlphaValue_(max(0.0, min(1.0, float(value))))
            except Exception:
                pass

    def _fade_finished(self, name):
        side = self._sides[name]
        if side.fade.endValue() == 0.0:
            side.button.hide()
            self._set_alpha(name, 1.0)
            self.changed.emit()

    def _on_click(self, name):
        self.clicked.emit(name)
        self.refresh(name)           # the panel came out / went back: the chevron turns round
        self.check_pointer()
