# -*- coding: utf-8 -*-
"""Watermelon: the outline of the note, on the right edge of the rendered page (2026-11-21).

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (5.14)
Ryan 2026-11-21: "大纲我说了学 broccoli，broccoli 放在渲染后的页面的右侧，就这个导航条的样式，你学一下"
(with a picture of Broccoli's Agent page: a column of short grey ticks at the right edge, the current one
longer and darker). This is Broccoli's AgentQuestionRail with headings instead of questions: at rest a
column of thin short ticks, one per heading, the current one longer and darker; after the pointer rests on
it (250 ms) it opens to the left into a list of the headings (indented by level, scrollable, click = go
there) and closes 300 ms after the pointer left. Sizes, colours and timings are Broccoli's.

  headings_in(markdown)   [(line number, level, text)] — ATX headings outside code blocks
  OutlineRail             the ticks / the list
"""
import re

from PyQt6.QtCore import Qt, QEasingCurve, QEvent, QPropertyAnimation, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from glass_kit import is_dark_theme
import glass_kit

_HEADING = re.compile(r'^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$')
_FENCE = re.compile(r'^ {0,3}(```|~~~)')


def headings_in(markdown: str) -> list:
    out, fence = [], None
    for number, line in enumerate(str(markdown or '').split('\n')):
        mark = _FENCE.match(line)
        if mark:
            fence = None if fence == mark.group(1) else (fence or mark.group(1))
            continue
        if fence:
            continue
        found = _HEADING.match(line)
        if found:
            text = re.sub(r'[*_`]+', '', found.group(2)).strip()
            if text:
                out.append((number, len(found.group(1)), text))
    return out


class OutlineRail(QWidget):
    jump_requested = pyqtSignal(int)      # the line number of the heading

    COLLAPSED_W = 26
    EXPANDED_W = 264
    TICK_W = 14
    TICK_W_ACTIVE = 24
    TICK_H = 3
    TICK_SPACING = 10
    ITEM_H = 30
    PAD = 10
    LEVEL_INDENT = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._headings = []           # [(line, level, text)]
        self._current_pos = -1
        self._hover_pos = -1
        self._expanded = False
        self._tick_scroll = 0
        self._list_scroll = 0
        self._anchor = None           # (right_x, center_y, max_h)
        self._geom_anim = None
        self._allowed = True
        self._expand_timer = QTimer(self)
        self._expand_timer.setSingleShot(True)
        self._expand_timer.setInterval(250)
        self._expand_timer.timeout.connect(self._expand)
        self._collapse_timer = QTimer(self)
        self._collapse_timer.setSingleShot(True)
        self._collapse_timer.setInterval(300)
        self._collapse_timer.timeout.connect(self._collapse)
        self.hide()

    # content
    def headings(self) -> list:
        return list(self._headings)

    def set_markdown(self, markdown: str):
        headings = headings_in(markdown)
        if headings == self._headings:
            return
        self._headings = headings
        self._hover_pos = -1
        self._current_pos = min(self._current_pos, len(headings) - 1)
        self._apply_geometry(animated=False)
        self._ensure_current_visible()
        self._clamp_scrolls()
        self.sync_visibility()
        self.update()

    def set_current_line(self, line: int):
        """The heading the cursor is under (the last one at or above that line)."""
        pos = -1
        for index, (number, _level, _text) in enumerate(self._headings):
            if number <= int(line):
                pos = index
            else:
                break
        if pos != self._current_pos:
            self._current_pos = pos
            self._ensure_current_visible()
            self.update()

    def current_position(self) -> int:
        return self._current_pos

    def is_expanded(self) -> bool:
        return self._expanded

    # shown or not, where
    def set_allowed(self, allowed: bool):
        self._allowed = bool(allowed)
        self.sync_visibility()

    def sync_visibility(self):
        wanted = self._allowed and bool(self._headings)
        if wanted == self.isVisible():
            if wanted:
                self.raise_()
            return
        if wanted:
            self.show()
            self.raise_()
        else:
            self._expanded = False
            self.hide()

    def set_anchor(self, right_x: int, center_y: int, max_h: int):
        self._anchor = (int(right_x), int(center_y), max(120, int(max_h)))
        self._apply_geometry(animated=False)
        self._ensure_current_visible()

    def _target_geometry(self) -> QRect:
        if self._anchor is None:
            return self.geometry()
        right_x, center_y, max_h = self._anchor
        count = max(1, len(self._headings))
        if self._expanded:
            width = self.EXPANDED_W
            height = min(max_h, count * self.ITEM_H + 2 * self.PAD)
            height = max(height, min(max_h, 3 * self.ITEM_H))
        else:
            width = self.COLLAPSED_W
            height = min(max_h, count * self.TICK_SPACING + 2 * self.PAD)
        x = max(0, right_x - width)
        y = max(4, center_y - height // 2)
        parent = self.parentWidget()
        if parent is not None:
            y = min(y, max(4, parent.height() - height - 4))
        return QRect(x, y, width, height)

    def _apply_geometry(self, animated: bool):
        target = self._target_geometry()
        if self._geom_anim is not None:
            self._geom_anim.stop()
            self._geom_anim = None
        if not animated or not self.isVisible():
            self.setGeometry(target)
            return
        anim = QPropertyAnimation(self, b'geometry', self)
        anim.setDuration(180)
        anim.setStartValue(self.geometry())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._geom_anim = anim

    # open / closed
    def _expand(self):
        if self._expanded or not self._headings:
            return
        self._expanded = True
        self._ensure_current_visible()
        self._apply_geometry(animated=True)
        self.raise_()
        self.update()

    def _collapse(self):
        if not self._expanded:
            return
        self._expanded = False
        self._hover_pos = -1
        self._apply_geometry(animated=True)
        self.update()

    def enterEvent(self, event):
        self._collapse_timer.stop()
        if not self._expanded:
            self._expand_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._expand_timer.stop()
        if self._expanded:
            self._collapse_timer.start()
        super().leaveEvent(event)

    # scrolling
    def _tick_capacity(self) -> int:
        return max(1, (self.height() - 2 * self.PAD) // self.TICK_SPACING)

    def _list_capacity_px(self) -> int:
        return max(self.ITEM_H, self.height() - 2 * self.PAD)

    def _clamp_scrolls(self):
        max_tick = max(0, len(self._headings) - self._tick_capacity())
        self._tick_scroll = max(0, min(self._tick_scroll, max_tick))
        max_px = max(0, len(self._headings) * self.ITEM_H - self._list_capacity_px())
        self._list_scroll = max(0, min(self._list_scroll, max_px))

    def _ensure_current_visible(self):
        if self._current_pos < 0:
            return
        capacity = self._tick_capacity()
        if self._current_pos < self._tick_scroll:
            self._tick_scroll = self._current_pos
        elif self._current_pos >= self._tick_scroll + capacity:
            self._tick_scroll = self._current_pos - capacity + 1
        top_px = self._current_pos * self.ITEM_H
        if top_px < self._list_scroll:
            self._list_scroll = top_px
        elif top_px + self.ITEM_H > self._list_scroll + self._list_capacity_px():
            self._list_scroll = top_px + self.ITEM_H - self._list_capacity_px()
        self._clamp_scrolls()

    def resizeEvent(self, event):
        # opening / folding changes how much fits: what was scrolled for the small shape is put right
        super().resizeEvent(event)
        self._clamp_scrolls()
        self._ensure_current_visible()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if self._expanded:
            self._list_scroll -= int(delta * 0.6)
        else:
            self._tick_scroll += -1 if delta > 0 else 1
        self._clamp_scrolls()
        self.update()
        event.accept()

    # the pointer
    def _pos_at(self, y: int) -> int:
        if not self._expanded:
            return -1
        pos = (y - self.PAD + self._list_scroll) // self.ITEM_H
        return int(pos) if 0 <= pos < len(self._headings) else -1

    def mouseMoveEvent(self, event):
        if self._expanded:
            pos = self._pos_at(int(event.position().y()))
            if pos != self._hover_pos:
                self._hover_pos = pos
                self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._expanded:
                pos = self._pos_at(int(event.position().y()))
                if pos >= 0:
                    self._current_pos = pos
                    self._ensure_current_visible()
                    self.jump_requested.emit(self._headings[pos][0])
                    self._collapse_timer.start()
                    self.update()
            else:
                self._expand_timer.stop()
                self._expand()
            event.accept()
            return
        super().mousePressEvent(event)

    # look (Broccoli's colours)
    def _palette_colors(self) -> dict:
        if is_dark_theme(glass_kit.app):
            return {'panel_bg': QColor(44, 45, 49, 242), 'panel_border': QColor(255, 255, 255, 26),
                    'tick': QColor(255, 255, 255, 64), 'tick_active': QColor(255, 255, 255, 205),
                    'text': QColor('#E8EAED'), 'text_dim': QColor('#9AA0A6'),
                    'hover_bg': QColor(255, 255, 255, 18), 'active_bar': QColor('#8AB4F8')}
        return {'panel_bg': QColor(255, 255, 255, 246), 'panel_border': QColor(0, 0, 0, 22),
                'tick': QColor(0, 0, 0, 56), 'tick_active': QColor(0, 0, 0, 185),
                'text': QColor('#202124'), 'text_dim': QColor('#80868B'),
                'hover_bg': QColor(0, 0, 0, 14), 'active_bar': QColor('#1A73E8')}

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        colors = self._palette_colors()
        if self._expanded:
            self._paint_list(painter, colors)
        else:
            self._paint_ticks(painter, colors)
        painter.end()

    def _paint_ticks(self, painter, colors):
        capacity = self._tick_capacity()
        start = self._tick_scroll
        visible = self._headings[start:start + capacity]
        y = self.PAD + max(0, (self.height() - 2 * self.PAD - len(visible) * self.TICK_SPACING) // 2)
        painter.setPen(Qt.PenStyle.NoPen)
        for offset, _item in enumerate(visible):
            active = start + offset == self._current_pos
            width = self.TICK_W_ACTIVE if active else self.TICK_W
            painter.setBrush(QBrush(colors['tick_active'] if active else colors['tick']))
            painter.drawRoundedRect(self.width() - width - 4, y + offset * self.TICK_SPACING, width, self.TICK_H,
                                    self.TICK_H / 2.0, self.TICK_H / 2.0)
        painter.setBrush(QBrush(colors['tick']))       # more above / below: a faint dot
        if start > 0:
            painter.drawEllipse(self.width() - 8, 3, 3, 3)
        if start + capacity < len(self._headings):
            painter.drawEllipse(self.width() - 8, self.height() - 6, 3, 3)

    def _paint_list(self, painter, colors):
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QPen(colors['panel_border'], 1))
        painter.setBrush(QBrush(colors['panel_bg']))
        painter.drawRoundedRect(rect, 14, 14)
        painter.setClipRect(rect.adjusted(2, self.PAD - 2, -2, -(self.PAD - 2)))
        font = painter.font()
        font.setPointSize(11)
        first = max(0, (self._list_scroll - self.PAD) // self.ITEM_H)
        last = min(len(self._headings), first + self._list_capacity_px() // self.ITEM_H + 2)
        for pos in range(first, last):
            _line, level, text = self._headings[pos]
            top = self.PAD + pos * self.ITEM_H - self._list_scroll
            item_rect = QRect(10, top, self.width() - 20, self.ITEM_H - 4)
            if pos == self._hover_pos:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(colors['hover_bg']))
                painter.drawRoundedRect(item_rect, 9, 9)
            if pos == self._current_pos:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(colors['active_bar']))
                painter.drawRoundedRect(QRect(item_rect.left() + 2, item_rect.top() + 6, 3, item_rect.height() - 12), 1.5, 1.5)
            font.setBold(level == 1)
            painter.setFont(font)
            painter.setPen(QPen(colors['text'] if level <= 2 else colors['text_dim']))
            indent = 12 + (min(level, 4) - 1) * self.LEVEL_INDENT
            text_rect = QRect(item_rect.left() + indent, item_rect.top(), item_rect.width() - indent - 8, item_rect.height())
            elided = painter.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)

    def changeEvent(self, event):
        if event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange):
            self.update()
        super().changeEvent(event)
