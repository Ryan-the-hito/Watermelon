# -*- coding: utf-8 -*-
"""Watermelon: the attachments of the open note / file — a list on the left of the editing column, and
small preview windows (2026-11-21).

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (5.14)
Ryan 2026-11-21: the empty strip left of the editing column "是不是可以利用起来，比如变成 notes 中的所有附件
的 list"; "左边是列表的视图，有缩略图…点开之后我希望可以在一个新的小的独立弹窗内预览，特别是 pdf 文件，可以上下、
左右翻页。然后你可以打开多个文件看"; Word / Excel / PowerPoint: "不希望在一个小窗口里打开一个三件套，太麻烦了"
→ a read-only Quick Look preview in the small window, and a button that opens the file in the editing column.

  attachments_in(markdown, base_dir)   the local files a Markdown text refers to, in text order
  AttachmentRail                       the list (a Liquid Glass panel in the strip left of the column, always light)
  AttachmentPreviewWindow              one file: PDF (scroll, or one page at a time with ‹ ›), picture,
                                       anything else by the system's Quick Look
Import this module AFTER the QApplication exists.
"""
import logging
import os
import re
import subprocess
import unicodedata
import urllib.parse

from PyQt6.QtCore import Qt, QMimeData, QPoint, QSize, QTimer, QUrl, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (QColor, QDrag, QFont, QFontMetrics, QGuiApplication, QImage, QKeySequence, QPainter, QPainterPath,
                         QPalette, QPen, QPixmap)
from PyQt6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QMenu, QScrollArea, QVBoxLayout, QWidget)

import glass_kit
from glass_kit import (_tr, MacNormalButton, attach_inwindow_liquid_glass, style_broccoli_context_menu,
                       NATIVE_TITLEBAR_HEIGHT)
import watermelon_ui
import watermelon_notes

IMAGE_EXTS = watermelon_notes.IMAGE_EXTS
OFFICE_EXTS = ('.docx', '.xlsx', '.pptx')
VIDEO_EXTS = ('.mp4', '.mov', '.m4v', '.avi', '.mkv', '.webm')
AUDIO_EXTS = ('.mp3', '.m4a', '.wav', '.aac', '.flac', '.aiff', '.caf')
RAIL_WIDTH = 127          # fills the empty strip left of the editing column (8 from the window's edge, 8 from the column)
RAIL_RADIUS = 16          # a floating panel (style book 2.1, third tier)
THUMB_WIDTH, THUMB_HEIGHT = 100, 72
ITEM_RADIUS = 7

_IMAGE_REF = re.compile(r'!\[([^\]]*)\]\(\s*<?([^)>]+?)>?\s*\)')
_FILE_LINE = re.compile(r'^[ \t]*\[([^\]]+)\]\(\s*<?((?:file://|/|~)[^)>]+?)>?\s*\)[ \t]*$', re.M)


def kind_of(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXTS:
        return 'image'
    if ext == '.pdf':
        return 'pdf'
    if ext in OFFICE_EXTS:
        return 'office'
    if ext in VIDEO_EXTS:
        return 'video'
    if ext in AUDIO_EXTS:
        return 'audio'
    return 'file'


def _resolve(reference: str, base_dir: str) -> str:
    path = watermelon_notes.local_path_of(reference)
    if path:
        return path
    reference = urllib.parse.unquote(str(reference or '').strip())
    if base_dir and reference and '://' not in reference and not reference.startswith(('#', 'data:')):
        candidate = os.path.normpath(os.path.join(base_dir, reference))
        if os.path.isfile(candidate):
            return candidate
    return ''


def attachments_in(markdown: str, base_dir: str = '') -> list:
    """[{'path', 'name', 'kind', 'offset'}] — the local files the text refers to (a picture `![name](file)`
    of any type, or a link to a local file alone on its line), in the order they stand in the text. Code is
    skipped."""
    text = str(markdown or '')
    skip = []
    for match in re.finditer(r'(^[ \t]*```.*?^[ \t]*```[ \t]*$|`[^`\n]*`)', text, re.S | re.M):
        skip.append((match.start(), match.end()))
    found = []
    for pattern in (_IMAGE_REF, _FILE_LINE):
        for match in pattern.finditer(text):
            if any(start <= match.start() < end for start, end in skip):
                continue
            path = _resolve(match.group(2), base_dir)
            if path:
                found.append({'path': path, 'name': match.group(1).strip() or os.path.basename(path),
                              'kind': kind_of(path), 'offset': match.start()})
    found.sort(key=lambda item: item['offset'])
    out, seen = [], set()
    for item in found:
        if item['offset'] in seen:
            continue
        seen.add(item['offset'])
        out.append(item)
    return out


def reference_span(markdown: str, item: dict, base_dir: str = ''):
    """(start, end) of what to take out of the text to remove this attachment: its reference, and its line
    when nothing else is on it (with one of the blank lines around it, so no gap is left). None when the
    text no longer has that reference at that place (it was changed meanwhile)."""
    text = str(markdown or '')
    offset = int(item.get('offset', -1))
    if offset < 0 or offset > len(text):
        return None
    for pattern in (_IMAGE_REF, _FILE_LINE):
        match = pattern.match(text, offset)
        if match and _resolve(match.group(2), base_dir) == item.get('path'):
            break
    else:
        return None
    start, end = match.start(), match.end()
    line_start = text.rfind('\n', 0, start) + 1
    line_end = text.find('\n', end)
    line_end = len(text) if line_end < 0 else line_end
    if text[line_start:start].strip() or text[end:line_end].strip():
        return start, end                       # other words on the line: only the reference goes
    start, end = line_start, min(len(text), line_end + 1)
    blank_before = start >= 2 and text[start - 2:start] == '\n\n' or start == 1 and text[0] == '\n'
    blank_after = text[end:end + 1] == '\n'
    if blank_after and (blank_before or start == 0):
        end += 1                                 # the paragraph's blank line goes too
    elif blank_before and end >= len(text):
        start -= 1
    return start, end


def markdown_reference(path: str) -> str:
    """How a dropped file is written into the text (the same forms the Notes link reads and writes)."""
    return watermelon_notes.attachment_reference(path, os.path.basename(path))


# ── thumbnails ────────────────────────────────────────────────────────────────────────────────────────
_THUMBS = {}


def _file_icon(path: str, size: int) -> QPixmap:
    try:
        from AppKit import NSWorkspace, NSBitmapImageRep, NSPNGFileType
        image = NSWorkspace.sharedWorkspace().iconForFile_(path)
        image.setSize_((size * 2, size * 2))
        rep = NSBitmapImageRep.imageRepWithData_(image.TIFFRepresentation())
        data = rep.representationUsingType_properties_(NSPNGFileType, None)
        pixmap = QPixmap()
        pixmap.loadFromData(bytes(data))
        return pixmap
    except Exception:
        return QPixmap()


def thumbnail(path: str, kind: str) -> QPixmap:
    try:
        stamp = (path, os.path.getmtime(path))
    except OSError:
        return QPixmap()
    cached = _THUMBS.get(stamp)
    if cached is not None:
        return cached
    pixmap = QPixmap()
    if kind == 'image':
        image = QImage(path)
        if not image.isNull():
            pixmap = QPixmap.fromImage(image.scaled(THUMB_WIDTH * 2, THUMB_HEIGHT * 2, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
    elif kind == 'pdf':
        try:
            from PyQt6.QtPdf import QPdfDocument
            document = QPdfDocument(None)
            document.load(path)
            if document.pageCount() > 0:
                size = document.pagePointSize(0)
                scale = min(THUMB_WIDTH * 2 / max(1.0, size.width()), THUMB_HEIGHT * 2 / max(1.0, size.height()))
                page = document.render(0, QSize(max(1, int(size.width() * scale)), max(1, int(size.height() * scale))))
                if not page.isNull():
                    white = QImage(page.size(), QImage.Format.Format_ARGB32)
                    white.fill(QColor('#FFFFFF'))
                    painter = QPainter(white)
                    painter.drawImage(0, 0, page)
                    painter.end()
                    pixmap = QPixmap.fromImage(white)
            document.close()
        except Exception:
            logging.exception('PDF thumbnail failed.')
    if pixmap.isNull():
        pixmap = _file_icon(path, 44)
    if len(_THUMBS) > 200:
        _THUMBS.clear()
    _THUMBS[stamp] = pixmap
    return pixmap


# ── the list ──────────────────────────────────────────────────────────────────────────────────────────
SHOTS_MIME = 'application/x-watermelon-shots'     # screenshots of the course material dragged into the note


def _accent() -> QColor:
    return QApplication.palette().color(QPalette.ColorRole.Accent)


def _mix(a: QColor, b: QColor, share: float) -> QColor:
    """`share` of a over b."""
    return QColor(round(a.red() * share + b.red() * (1 - share)), round(a.green() * share + b.green() * (1 - share)),
                  round(a.blue() * share + b.blue() * (1 - share)))


def draw_check_box(painter, box: QRectF):
    """Style book 5.3.1: 13 × 13, corner 3.5, ticked = accent with a white tick; on a selected item a 1-point
    white edge round it."""
    path = QPainterPath()
    path.addRoundedRect(box, 3.5, 3.5)
    painter.fillPath(path, _accent())
    painter.setPen(QPen(QColor('#FFFFFF'), 1))
    painter.drawPath(path)
    tick = QPen(QColor('#FFFFFF'), 1.8)
    tick.setCapStyle(Qt.PenCapStyle.RoundCap)
    tick.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(tick)
    painter.drawPolyline([QPointF(box.left() + 3.2, box.center().y() + 0.2), QPointF(box.left() + 5.6, box.bottom() - 3.4),
                          QPointF(box.right() - 3.0, box.top() + 3.4)])


class _Item(QWidget):
    clicked = pyqtSignal(dict, object)          # the item, the keys held (⌘ = add / take away, ⇧ = a run)
    menu_requested = pyqtSignal(dict, object)
    drag_requested = pyqtSignal(dict)

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = item
        self._hover = False
        self.selected = False
        self._press = None
        self.setFixedSize(RAIL_WIDTH - 16, THUMB_HEIGHT + 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(item['name'])
        self._pixmap = thumbnail(item['path'], item['kind'])

    def set_selected(self, on: bool):
        if bool(on) != self.selected:
            self.selected = bool(on)
            self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press = event.position().toPoint()

    def mouseMoveEvent(self, event):
        # a screenshot is dragged into the note (Ryan 2026-11-24: "拖动也能插入")
        if (self._press is not None and self.item.get('courseware') and event.buttons() & Qt.MouseButton.LeftButton
                and (event.position().toPoint() - self._press).manhattanLength() >= QApplication.startDragDistance()):
            self._press = None
            self.drag_requested.emit(self.item)

    def mouseReleaseEvent(self, event):
        pressed, self._press = self._press, None
        if (event.button() == Qt.MouseButton.LeftButton and pressed is not None
                and self.rect().contains(event.position().toPoint())):
            self.clicked.emit(self.item, event.modifiers())

    def contextMenuEvent(self, event):
        self.menu_requested.emit(self.item, event.globalPos())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        whole = QPainterPath()
        whole.addRoundedRect(QRectF(self.rect()), ITEM_RADIUS, ITEM_RADIUS)
        if self.selected:              # style book (the tray's many-at-once): accent 10 %, a 2-point accent edge inside
            painter.fillPath(whole, QColor(_accent().red(), _accent().green(), _accent().blue(), 26))
        elif self._hover:
            painter.fillPath(whole, QColor(0, 0, 0, 16))
        area = QRectF((self.width() - THUMB_WIDTH) / 2.0, 4, THUMB_WIDTH, THUMB_HEIGHT)
        if not self._pixmap.isNull():
            size = QSize(self._pixmap.size()).scaled(int(area.width()), int(area.height()), Qt.AspectRatioMode.KeepAspectRatio)
            target = QRectF(area.center().x() - size.width() / 2.0, area.center().y() - size.height() / 2.0, size.width(), size.height())
            clip = QPainterPath()
            clip.addRoundedRect(target, 4, 4)
            painter.save()
            painter.setClipPath(clip)
            painter.drawPixmap(target, self._pixmap, QRectF(self._pixmap.rect()))
            painter.restore()
        font = QFont(self.font())
        font.setPixelSize(11)
        painter.setFont(font)
        painter.setPen(_mix(_accent(), QColor('#000000'), 0.55) if self.selected else QColor('#1D1D1F'))
        name = QFontMetrics(font).elidedText(self.item['name'], Qt.TextElideMode.ElideMiddle, self.width() - 8)
        painter.drawText(QRectF(4, THUMB_HEIGHT + 8, self.width() - 8, 18), Qt.AlignmentFlag.AlignCenter, name)
        if self.selected:              # on top of everything: the edge, then the tick (top right, 4 from both sides)
            edge = QPainterPath()
            edge.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), ITEM_RADIUS - 1, ITEM_RADIUS - 1)
            painter.setPen(QPen(_accent(), 2))
            painter.drawPath(edge)
            draw_check_box(painter, QRectF(self.width() - 4 - 13, 4, 13, 13))
        painter.end()


def drag_picture(pixmaps, count: int) -> QPixmap:
    """What is seen while dragging: up to three thumbnails stacked (each further one 4 up and right), with a
    red number in the corner when more than one is dragged (as the tray of Broccoli)."""
    pixmaps = [p for p in pixmaps if p is not None and not p.isNull()][:3] or [QPixmap(THUMB_WIDTH, THUMB_HEIGHT)]
    width, height = 64, 46
    shift = 4 * (len(pixmaps) - 1)
    canvas = QPixmap(width + shift + 12, height + shift + 12)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    for index in reversed(range(len(pixmaps))):
        box = QRectF(4 * index, 10 + shift - 4 * index, width, height)
        clip = QPainterPath()
        clip.addRoundedRect(box, 4, 4)
        painter.fillPath(clip, QColor('#FFFFFF'))
        painter.save()
        painter.setClipPath(clip)
        painter.drawPixmap(box, pixmaps[index], QRectF(pixmaps[index].rect()))
        painter.restore()
        painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
        painter.drawPath(clip)
    if count > 1:
        font = QFont()
        font.setPixelSize(12)
        font.setBold(True)
        label = str(count)
        badge_width = max(20, QFontMetrics(font).horizontalAdvance(label) + 12)
        badge = QRectF(canvas.width() - badge_width, 0, badge_width, 20)
        path = QPainterPath()
        path.addRoundedRect(badge, 10, 10)
        painter.fillPath(path, QColor('#FF3B30'))
        painter.setFont(font)
        painter.setPen(QColor('#FFFFFF'))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, label)
    painter.end()
    return canvas


class AttachmentRail(QWidget):
    """The attachments of the open note / file, top to bottom in text order. A Liquid Glass panel, always
    the light glass (Ryan 2026-11-21: "不要用深色液态玻璃，浅色的"); as wide as the empty strip, never on the
    editing column. On top the camera: a screenshot of the same area / a photo as course material — it ADDS
    attachments, so it is on this side (Ryan 2026-11-21: "添加照相的按钮应该放在左边，因为是添加附件")."""
    opened = pyqtSignal(dict)
    show_in_text = pyqtSignal(dict)
    files_dropped = pyqtSignal(list)
    shot_requested = pyqtSignal()
    shot_menu_requested = pyqtSignal(object)
    remove_requested = pyqtSignal(dict)            # an attachment of the note: its line out of the text
    # the screenshots of the course material, one or the selected ones (Ryan 2026-11-24: "每一个图片上右键选择插入，
    # 拖动也能插入，然后多选右键可以生成 pdf，单图也能删除")
    shots_insert_requested = pyqtSignal(list)
    shots_pdf_requested = pyqtSignal(list, str)    # the screenshots, a PDF of the note to add them to ('' = a new one)
    shots_delete_requested = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self.can_remove = lambda item: True        # the window says when the text can't be changed
        self.note_pdfs = lambda: []                # the PDFs of the note (screenshots can be added to one)
        self.can_insert = lambda: True             # the text can take screenshots now
        self._selected = []                        # paths of the selected screenshots, in the order chosen
        self._anchor = ''                          # the one clicked last (⇧ selects from there)
        self.setAcceptDrops(True)
        self.setFixedWidth(RAIL_WIDTH)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 8, 4, 8)
        outer.setSpacing(4)
        from watermelon_lecture import _Glyph          # the line icons of the right panel's top row
        row = QHBoxLayout()
        row.setContentsMargins(4, 0, 4, 0)
        self.btn_shot = _Glyph('shot', _tr('Screenshot as course material (right-click for more)'), self)
        self.btn_shot.clicked.connect(self.shot_requested.emit)
        self.btn_shot.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_shot.customContextMenuRequested.connect(lambda point: self.shot_menu_requested.emit(self.btn_shot.mapToGlobal(point)))
        row.addWidget(self.btn_shot)
        row.addStretch(1)
        outer.addLayout(row)
        self._scroll = QScrollArea(self)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # style book 5.9: the rule names only the area and its content — "QScrollArea > QWidget > QWidget" also
        # picks the scroll bar, which then turns into the old kind with arrows (Ryan 2026-11-21: "这个滚动条也没有
        # 按照 broccoli 最后更新的样式书"); the panel is light glass: the system's knob for a light ground
        self._scroll.setStyleSheet('QScrollArea { background: transparent; } '
                                   'QScrollArea > QWidget#qt_scrollarea_viewport > QWidget { background: transparent; }')
        glass_kit.keep_scroll_bar_knob(self._scroll, False)
        self._scroll.viewport().setAutoFillBackground(False)
        self._holder = QWidget()
        self._holder.setAutoFillBackground(False)
        self._list = QVBoxLayout(self._holder)
        self._list.setContentsMargins(4, 0, 4, 0)
        self._list.setSpacing(4)
        self._list.addStretch(1)
        self._scroll.setWidget(self._holder)
        outer.addWidget(self._scroll)
        self.empty_label = QLabel(_tr('No attachments yet. Drop files here, or use the camera above.'), self._holder)
        self.empty_label.setWordWrap(True)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.empty_label.setStyleSheet('color: #6E6E73; font-size: 11px; background: transparent; padding: 12px 2px;')
        self._list.insertWidget(0, self.empty_label)

    # content
    def items(self):
        return list(self._items)

    def set_items(self, items):
        key = [(item['path'], item['offset'], item['name']) for item in items]
        if key == [(item['path'], item['offset'], item['name']) for item in self._items]:
            return
        self._items = list(items)
        shots = [item['path'] for item in self._items if item.get('courseware')]
        self._selected = [path for path in self._selected if path in shots]
        if self._anchor not in shots:
            self._anchor = ''
        while self._list.count() > 2:
            widget = self._list.takeAt(1).widget()
            if widget is not None:
                widget.hide()               # gone now (the glass image is drawn before deleteLater has run)
                widget.setParent(None)
                widget.deleteLater()
        for position, item in enumerate(self._items):
            row = _Item(item, self._holder)
            row.set_selected(item['path'] in self._selected and bool(item.get('courseware')))
            row.clicked.connect(self._clicked)
            row.menu_requested.connect(self._menu)
            row.drag_requested.connect(self._drag)
            self._list.insertWidget(position + 1, row, 0, Qt.AlignmentFlag.AlignHCenter)
        self.empty_label.setVisible(not self._items)
        helper = getattr(self, '_broccoli_inwindow_glass', None)
        if helper is not None and helper.active:
            helper.gate_new_children()     # the new rows never paint into the window under the glass (it blurs them)

    # choosing screenshots: as in Finder / the tray of Broccoli (style book: ⌘ = add / take away, ⇧ = a run
    # from the one clicked last; a plain click = only look at this one and the choice is gone)
    def _rows(self):
        return [self._list.itemAt(index).widget() for index in range(self._list.count())
                if isinstance(self._list.itemAt(index).widget(), _Item)]

    def _shots(self):
        return [item['path'] for item in self._items if item.get('courseware')]

    def selected(self) -> list:
        order = self._shots()
        return [path for path in order if path in self._selected]

    def set_selected(self, paths):
        shots = self._shots()
        self._selected = [path for path in paths if path in shots]
        for row in self._rows():
            row.set_selected(row.item['path'] in self._selected)

    def _clicked(self, item, modifiers):
        modifiers = Qt.KeyboardModifier(int(modifiers.value) if hasattr(modifiers, 'value') else int(modifiers))
        if item.get('courseware') and modifiers & Qt.KeyboardModifier.ControlModifier:     # ⌘ on a Mac
            path = item['path']
            self.set_selected([p for p in self._selected if p != path] if path in self._selected else self._selected + [path])
            self._anchor = path
            return
        if item.get('courseware') and modifiers & Qt.KeyboardModifier.ShiftModifier:
            shots = self._shots()
            start = shots.index(self._anchor) if self._anchor in shots else shots.index(item['path'])
            stop = shots.index(item['path'])
            run = shots[min(start, stop):max(start, stop) + 1]
            self.set_selected(self._selected + [p for p in run if p not in self._selected])
            return
        self.set_selected([])
        self._anchor = item['path'] if item.get('courseware') else ''
        self.opened.emit(item)

    def _drag(self, item):
        """Pressed and moved on a screenshot: it — or, when it is one of the chosen ones, all of them — goes
        where it is dropped in the note. Pressed on one not chosen: only that one, the choice is gone."""
        if item['path'] in self._selected:
            paths = self.selected()
        else:
            self.set_selected([])
            paths = [item['path']]
        rows = {row.item['path']: row for row in self._rows()}
        data = QMimeData()
        data.setData(SHOTS_MIME, '\n'.join(paths).encode('utf-8'))
        drag = QDrag(self)
        drag.setMimeData(data)
        picture = drag_picture([rows[path]._pixmap for path in paths if path in rows], len(paths))
        drag.setPixmap(picture)
        drag.setHotSpot(QPoint(picture.width() // 2, picture.height() // 2))
        drag.exec(Qt.DropAction.CopyAction)

    def _menu(self, item, where):
        if item.get('courseware'):
            self._shots_menu(item, where)
            return
        menu = QMenu(self)
        style_broccoli_context_menu(menu)
        preview = menu.addAction(_tr('Preview'))
        show = menu.addAction(_tr('Show in Text'))
        menu.addSeparator()
        default_app = menu.addAction(_tr('Open with Default App'))
        finder = menu.addAction(_tr('Show in Finder'))
        # Ryan 2026-11-24: "没有删除的地方". An attachment of the note → Remove from Note (only its line in the
        # text, ⌘Z brings it back; the file itself stays where it is)
        remove = None
        if self.can_remove(item):
            menu.addSeparator()
            remove = menu.addAction(_tr('Remove from Note'))
        chosen = menu.exec(where)
        if chosen is not None and chosen is remove:
            self.remove_requested.emit(item)
        elif chosen is preview:
            self.opened.emit(item)
        elif chosen is show:
            self.show_in_text.emit(item)
        elif chosen is default_app:
            subprocess.Popen(['/usr/bin/open', item['path']])
        elif chosen is finder:
            subprocess.Popen(['/usr/bin/open', '-R', item['path']])

    def _shots_menu(self, item, where):
        """A screenshot of the course material (or the chosen ones, when it is one of them): insert into the
        note as pictures, one PDF of them, delete. Right-click on one not chosen = only that one."""
        if item['path'] not in self._selected:
            self.set_selected([])
            self._anchor = item['path']
        paths = self.selected() or [item['path']]
        many = len(paths) > 1
        editable = bool(self.can_insert())
        menu = QMenu(self)
        style_broccoli_context_menu(menu)
        insert = menu.addAction(_tr('Insert %d Screenshots into Note') % len(paths) if many else _tr('Insert into Note'))
        insert.setEnabled(editable)
        pdf = menu.addAction(_tr('Make PDF of %d Screenshots') % len(paths) if many else _tr('Make PDF'))
        pdf.setEnabled(editable)
        into = {}
        for note_pdf in list(self.note_pdfs() or [])[:5]:
            action = menu.addAction(_tr('Add to “%s”') % note_pdf['name'])
            action.setEnabled(editable)
            into[action] = note_pdf['path']
        menu.addSeparator()
        preview = finder = None
        if not many:
            preview = menu.addAction(_tr('Preview'))
            finder = menu.addAction(_tr('Show in Finder'))
            menu.addSeparator()
        shots = self._shots()
        select_all = menu.addAction(_tr('Select All Screenshots')) if len(shots) > 1 and len(self._selected) < len(shots) else None
        deselect = menu.addAction(_tr('Deselect All')) if self._selected else None
        if select_all is not None or deselect is not None:
            menu.addSeparator()
        delete = menu.addAction(_tr('Delete %d Screenshots') % len(paths) if many else _tr('Delete'))
        chosen = menu.exec(where)
        if chosen is None:
            return
        if chosen is insert:
            self.shots_insert_requested.emit(paths)
        elif chosen is pdf:
            self.shots_pdf_requested.emit(paths, '')
        elif chosen in into:
            self.shots_pdf_requested.emit(paths, into[chosen])
        elif chosen is delete:
            self.shots_delete_requested.emit(paths)
        elif chosen is preview:
            self.opened.emit(item)
        elif chosen is finder:
            subprocess.Popen(['/usr/bin/open', '-R', item['path']])
        elif chosen is select_all:
            self.set_selected(shots)
        elif chosen is deselect:
            self.set_selected([])

    # files dragged onto the list are added to the text
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile() and os.path.isfile(url.toLocalFile())]
        if paths:
            event.acceptProposedAction()
            self.files_dropped.emit(paths)

    # look
    def showEvent(self, event):
        super().showEvent(event)
        try:
            if getattr(self, '_broccoli_inwindow_glass', None) is None:
                attach_inwindow_liquid_glass(self, lambda w=self: float(RAIL_RADIUS), lambda w=self: False)
        except RuntimeError:
            pass

    def paintEvent(self, event):
        if getattr(self, '_liquid_glass_active', False) or getattr(self, '_glass_foreground_pass', False):
            return
        painter = QPainter(self)          # no system glass: the same shape, light and nearly solid
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), RAIL_RADIUS, RAIL_RADIUS)
        painter.fillPath(path, QColor(246, 246, 246, 238))
        painter.setPen(QColor(0, 0, 0, 30))
        painter.drawPath(path)
        painter.end()


# ── a preview window ─────────────────────────────────────────────────────────────────────────────────
class _PictureView(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self._image = QImage(path)

    def paintEvent(self, event):
        if self._image.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        size = self._image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF((self.width() - size.width()) / 2.0, (self.height() - size.height()) / 2.0, size.width(), size.height())
        painter.drawImage(target, self._image, QRectF(self._image.rect()))
        painter.end()


class _QuickLookArea(QWidget):
    """The system's Quick Look preview of any file (read only), placed over this widget's area.
    The system view is added straight to the window's own native view and follows this widget's rectangle
    (wrapping it with QWidget.createWindowContainer aborts the program when the window is shown —
    tried 2026-11-21)."""

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self._path = path
        self._view = None
        self.available = QGuiApplication.platformName() == 'cocoa'

    def _ensure(self):
        if not self.available or not self.isVisible():
            return
        try:
            import objc
            from Foundation import NSURL, NSMakeRect
            if self._view is None:
                from Quartz import QLPreviewView
                host = objc.objc_object(c_void_p=int(self.window().winId()))
                view = QLPreviewView.alloc().initWithFrame_style_(NSMakeRect(0, 0, 100, 100), 0)
                view.setAutostarts_(False)
                view.setPreviewItem_(NSURL.fileURLWithPath_(self._path))
                host.addSubview_(view)
                self._view = view
            corner = self.mapTo(self.window(), self.rect().topLeft())
            self._view.setFrame_(NSMakeRect(corner.x(), corner.y(), self.width(), self.height()))   # Qt's view counts from the top
        except Exception:
            logging.exception('Quick Look preview failed.')
            self.available = False

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._ensure)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ensure()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._ensure()

    def release(self):
        view, self._view = self._view, None
        if view is not None:
            try:
                view.close()
                view.removeFromSuperview()
            except Exception:
                pass


_SELECTABLE_PDF_VIEW = []
_RADICAL_SIGNS = {code: unicodedata.normalize('NFKC', chr(code)) for code in list(range(0x2F00, 0x2FD6)) + list(range(0x2E80, 0x2EF4))
                  if unicodedata.normalize('NFKC', chr(code)) != chr(code)}


def plain_ideographs(text: str) -> str:
    """Some PDFs give 牛 力 比 … back as the look-alike radical signs (⽜ ⼒ ⽐): the ordinary characters."""
    return str(text or '').translate(_RADICAL_SIGNS)



def selectable_pdf_view_class():
    """QPdfView that lets the text of a page be picked with the mouse (Qt's own view cannot): drag over the
    writing = it is marked; ⌘C or the right-click menu copies it. Ryan 2026-11-21: "让用户可以在预览的时候
    直接去复制图片里的文字" (a scanned page carries its writing as an invisible layer — watermelon_scan)."""
    if _SELECTABLE_PDF_VIEW:
        return _SELECTABLE_PDF_VIEW[0]
    from PyQt6.QtPdf import QPdfSelection
    from PyQt6.QtPdfWidgets import QPdfView

    class SelectablePdfView(QPdfView):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._press = None          # (page, point on it in page points)
            self._selection = None      # (page, QPdfSelection)
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

        # where the pages are — the same sums Qt's view does when it lays the pages out
        def page_rects(self) -> dict:
            """{page: (QRectF in the viewport, points → pixels)} for the pages laid out now."""
            document = self.document()
            if document is None or document.pageCount() == 0:
                return {}
            margins, viewport = self.documentMargins(), self.viewport()
            resolution = self.logicalDpiX() / 72.0
            single = self.pageMode() == QPdfView.PageMode.SinglePage
            first = self.pageNavigator().currentPage() if single else 0
            pages = range(first, first + 1) if single else range(document.pageCount())
            sizes, widest = {}, 0
            for page in pages:
                points = document.pagePointSize(page)
                if self.zoomMode() == QPdfView.ZoomMode.Custom:
                    size = QSize(int(points.width() * resolution * self.zoomFactor()), int(points.height() * resolution * self.zoomFactor()))
                else:
                    size = QSize(int(points.width() * resolution), int(points.height() * resolution))
                    room_w = viewport.width() - margins.left() - margins.right()
                    if self.zoomMode() == QPdfView.ZoomMode.FitToWidth:
                        factor = room_w / max(1.0, float(size.width()))
                    else:
                        room_h = viewport.height() - margins.top() - margins.bottom()
                        factor = min(room_w / max(1.0, float(size.width())), room_h / max(1.0, float(size.height())))
                    size = QSize(int(size.width() * factor), int(size.height() * factor))
                sizes[page] = size
                widest = max(widest, size.width())
            total = widest + margins.left() + margins.right()
            scroll_x, scroll_y = self.horizontalScrollBar().value(), self.verticalScrollBar().value()
            out, y = {}, margins.top()
            for page in pages:
                size = sizes[page]
                x = (max(total, viewport.width()) - size.width()) // 2
                points = document.pagePointSize(page)
                out[page] = (QRectF(x - scroll_x, y - scroll_y, size.width(), size.height()),
                             size.width() / max(1.0, points.width()))
                y += size.height() + self.pageSpacing()
            return out

        def _page_point(self, position, only_page=None):
            for page, (rect, scale) in self.page_rects().items():
                if only_page is not None and page != only_page:
                    continue
                if only_page is not None or rect.contains(QPointF(position)):
                    x = min(max(position.x() - rect.left(), 0.0), rect.width())
                    y = min(max(position.y() - rect.top(), 0.0), rect.height())
                    return page, QPointF(x / scale, y / scale)
            return None

        # the selection
        def selected_text(self) -> str:
            return plain_ideographs(self._selection[1].text()) if self._selection is not None else ''

        def clear_selection(self):
            if self._selection is not None:
                self._selection = None
                self.viewport().update()

        def copy_selection(self) -> bool:
            text = self.selected_text()
            if text:
                QApplication.clipboard().setText(text)
            return bool(text)

        def page_text(self, page=None) -> str:
            document = self.document()
            if document is None:
                return ''
            page = self.pageNavigator().currentPage() if page is None else page
            return plain_ideographs(document.getAllText(page).text())

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._press = self._page_point(event.position())
                self.clear_selection()
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event):
            if self._press is not None and event.buttons() & Qt.MouseButton.LeftButton:
                page, start = self._press
                now = self._page_point(event.position(), only_page=page)
                if now is not None:
                    selection = self.document().getSelection(page, start, now[1])
                    self._selection = (page, selection) if selection.isValid() and selection.text() else None
                    self.viewport().update()
                return
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):
            self._press = None
            super().mouseReleaseEvent(event)

        def contextMenuEvent(self, event):
            menu = QMenu(self)
            style_broccoli_context_menu(menu)
            copy = menu.addAction(_tr('Copy'))
            copy.setEnabled(bool(self.selected_text()))
            page = menu.addAction(_tr('Copy Text of This Page'))
            page.setEnabled(bool(self.page_text().strip()))
            chosen = menu.exec(event.globalPos())
            if chosen is copy:
                self.copy_selection()
            elif chosen is page:
                QApplication.clipboard().setText(self.page_text())

        def paintEvent(self, event):
            super().paintEvent(event)
            if self._selection is None:
                return
            page, selection = self._selection
            placed = self.page_rects().get(page)
            if placed is None:
                return
            rect, scale = placed
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            colour = QColor(watermelon_ui.accent_color())
            colour.setAlpha(90)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colour)
            for polygon in selection.bounds():
                box = polygon.boundingRect()
                painter.drawRect(QRectF(rect.left() + box.left() * scale, rect.top() + box.top() * scale,
                                        box.width() * scale, box.height() * scale))
            painter.end()

    _SELECTABLE_PDF_VIEW.append(SelectablePdfView)
    return SelectablePdfView


class AttachmentPreviewWindow(QWidget):
    """One attachment in its own small window (several can be open). PDF: scrolls, or one page at a time
    with ‹ › / the arrow keys; a picture fits the window; any other file is shown by Quick Look, read only —
    a Word / Excel / PowerPoint file gets an "Open in Editor" button instead of an editor in here."""
    open_in_editor = pyqtSignal(str)
    page_changed = pyqtSignal(str, int)
    closed = pyqtSignal(object)

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = dict(item)
        self.path = item['path']
        self.kind = item['kind']
        self._document = None
        self._pdf = None
        self._quick_look = None
        watermelon_ui.make_native_glass_window(self, resizable=True)
        self.setWindowTitle(os.path.basename(self.path))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.resize(560, 720)
        self.setMinimumSize(320, 360)
        box = QVBoxLayout(self)
        box.setContentsMargins(12, NATIVE_TITLEBAR_HEIGHT, 12, 12)
        box.setSpacing(8)
        self._paper = QFrame(self)        # the file itself is content: an opaque sheet on the glass
        self._paper.setObjectName('attachmentPaper')
        self._paper.setStyleSheet('QFrame#attachmentPaper { background: #FFFFFF; border: 1px solid rgba(0,0,0,0.12); border-radius: 8px; }')
        sheet = QVBoxLayout(self._paper)
        sheet.setContentsMargins(1, 1, 1, 1)
        box.addWidget(self._paper, 1)
        self._bar = QHBoxLayout()
        self._bar.setSpacing(8)
        box.addLayout(self._bar)
        self._page_label = None
        if self.kind == 'pdf':
            self._build_pdf(sheet)
        elif self.kind == 'image':
            sheet.addWidget(_PictureView(self.path, self._paper))
            self._bar.addStretch(1)
        else:
            self._quick_look = _QuickLookArea(self.path, self._paper)
            if self._quick_look.available:
                sheet.setContentsMargins(4, 4, 4, 4)
                sheet.addWidget(self._quick_look)
            else:
                note = QLabel(_tr('No preview for this file.'), self._paper)
                note.setAlignment(Qt.AlignmentFlag.AlignCenter)
                note.setStyleSheet('color: #8E8E93; font-size: 13px; background: transparent; border: none;')
                sheet.addWidget(note)
            self._bar.addStretch(1)
        if self.kind == 'office':
            edit = MacNormalButton(_tr('Open in Editor'), self)
            edit.setFixedHeight(watermelon_ui.GREY_ROW_HEIGHT)
            edit.clicked.connect(lambda: self.open_in_editor.emit(self.path))
            self._bar.addWidget(edit)

    # PDF
    def _build_pdf(self, sheet):
        from PyQt6.QtPdf import QPdfDocument
        from PyQt6.QtPdfWidgets import QPdfView
        self._document = QPdfDocument(self)
        self._document.load(self.path)
        self._pdf = selectable_pdf_view_class()(self._paper)      # text can be picked with the mouse and copied
        self._pdf.setDocument(self._document)
        self._pdf.setPageMode(QPdfView.PageMode.MultiPage)
        self._pdf.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self._pdf.setFrameShape(QFrame.Shape.NoFrame)
        sheet.addWidget(self._pdf)
        self._previous = MacNormalButton('‹', self)
        self._next = MacNormalButton('›', self)
        for button in (self._previous, self._next):
            button.setFixedSize(34, watermelon_ui.GREY_ROW_HEIGHT)
        self._previous.clicked.connect(lambda: self.go_to_page(self.current_page() - 1))
        self._next.clicked.connect(lambda: self.go_to_page(self.current_page() + 1))
        self._page_label = QLabel('', self)
        self._page_label.setStyleSheet('font-size: 12px; background: transparent;')
        self._mode = MacNormalButton(_tr('One Page'), self)
        self._mode.setFixedHeight(watermelon_ui.GREY_ROW_HEIGHT)
        self._mode.clicked.connect(self.toggle_page_mode)
        self._bar.addWidget(self._previous)
        self._bar.addWidget(self._page_label)
        self._bar.addWidget(self._next)
        self._bar.addStretch(1)
        self._bar.addWidget(self._mode)
        self._pdf.pageNavigator().currentPageChanged.connect(self._on_page)
        self._on_page(0)

    def page_count(self) -> int:
        return self._document.pageCount() if self._document is not None else 0

    def current_page(self) -> int:
        return self._pdf.pageNavigator().currentPage() if self._pdf is not None else 0

    def go_to_page(self, page):
        if self._pdf is None:
            return
        page = max(0, min(self.page_count() - 1, int(page)))
        self._pdf.pageNavigator().jump(page, QPointF(0, 0))

    def single_page(self) -> bool:
        from PyQt6.QtPdfWidgets import QPdfView
        return self._pdf is not None and self._pdf.pageMode() == QPdfView.PageMode.SinglePage

    def toggle_page_mode(self):
        """Scrolling through all pages ⇄ one page at a time (turned with ‹ › or the arrow keys)."""
        from PyQt6.QtPdfWidgets import QPdfView
        page = self.current_page()
        single = not self.single_page()
        self._pdf.setPageMode(QPdfView.PageMode.SinglePage if single else QPdfView.PageMode.MultiPage)
        self._pdf.setZoomMode(QPdfView.ZoomMode.FitInView if single else QPdfView.ZoomMode.FitToWidth)
        self._mode.setText(_tr('Scroll') if single else _tr('One Page'))
        self.go_to_page(page)

    def _on_page(self, _page=0):
        if self._page_label is not None:
            self._page_label.setText('%d / %d' % (self.current_page() + 1, max(1, self.page_count())))
        self.page_changed.emit(self.path, self.current_page())

    def current_page_image(self, width=1400) -> QImage:
        """The page being looked at as a picture (a PDF), or the picture itself."""
        if self.kind == 'image':
            return QImage(self.path)
        if self._document is None or self.page_count() == 0:
            return QImage()
        size = self._document.pagePointSize(self.current_page())
        scale = width / max(1.0, size.width())
        page = self._document.render(self.current_page(), QSize(int(size.width() * scale), int(size.height() * scale)))
        white = QImage(page.size(), QImage.Format.Format_RGB32)
        white.fill(QColor('#FFFFFF'))
        painter = QPainter(white)
        painter.drawImage(0, 0, page)
        painter.end()
        return white

    def keyPressEvent(self, event):
        if self._pdf is not None and event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            self.go_to_page(self.current_page() + (1 if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_PageDown) else -1))
            return
        if self._pdf is not None and event.matches(QKeySequence.StandardKey.Copy):
            self._pdf.copy_selection()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self._quick_look is not None:
            self._quick_look.release()
        self.closed.emit(self)
        super().closeEvent(event)


watermelon_ui.install_native_glass_window_class(AttachmentPreviewWindow, fixed=False)
