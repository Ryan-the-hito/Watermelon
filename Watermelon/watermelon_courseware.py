# -*- coding: utf-8 -*-
"""Watermelon: screenshots as course material (2026-11-21).

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (5.14)
Ryan 2026-11-21: when there is no course material, "把 Broccoli 的同位置截图搬过来" — the first time an area of
the screen is chosen, afterwards one press takes that same area again; every picture is a page of the
course material (it is listed on the left and starts a round of cards); "结束时合成一份 PDF，存进这张笔记当附件。
已有的 PDF 也可以用这个办法往后加页" (when: at the end — my suggestion, he agreed).

  RegionPicker     the whole screen dimmed, the area is dragged out (Esc = cancel)
  Courseware       the area, the pictures of this lecture, taking one more, making the PDF
Pictures are taken by the system's own `screencapture` (the area only), on a thread of its own.
Import this module AFTER the QApplication exists.
"""
import datetime
import hashlib
import json
import logging
import os
import shutil
import subprocess
import threading

from PyQt6.QtCore import Qt, QMarginsF, QObject, QPoint, QRect, QRectF, QSizeF, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QGuiApplication, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter, QPen
from PyQt6.QtWidgets import QWidget

from glass_kit import _tr

SCREENCAPTURE = '/usr/sbin/screencapture'
NO_NOTE = 'no-note'
PICTURE_EXTS = ('.png', '.jpg', '.jpeg', '.heic', '.tiff', '.tif', '.gif', '.bmp')
MIN_SIDE = 40


class RegionPicker(QWidget):
    """The screen the pointer is on, dimmed; the area is dragged out with the mouse and shown clear with a
    thin white edge and its size. Released = picked (screen coordinates, points); Esc / right click = cancel."""
    picked = pyqtSignal(QRect)
    cancelled = pyqtSignal()

    def __init__(self, screen=None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        screen = screen or QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self.setGeometry(screen.geometry())
        self._start = None
        self._now = None
        self._done = False

    def selection(self) -> QRect:
        if self._start is None or self._now is None:
            return QRect()
        left, top = min(self._start.x(), self._now.x()), min(self._start.y(), self._now.y())
        area = QRect(left, top, abs(self._start.x() - self._now.x()), abs(self._start.y() - self._now.y()))
        return area.intersected(self.rect())

    started = pyqtSignal()                      # a drag began here (the other screens' pickers go away)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._cancel()
            return
        self.activateWindow()                   # Esc reaches the screen the area is dragged on
        self._start = self._now = event.position().toPoint()
        self.started.emit()
        self.update()

    def mouseMoveEvent(self, event):
        if self._start is not None:
            self._now = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self._start is None:
            return
        self._now = event.position().toPoint()
        area = self.selection()
        if area.width() < MIN_SIDE or area.height() < MIN_SIDE:
            self._start = self._now = None      # too small to be meant: try again
            self.update()
            return
        self._done = True
        self.hide()                             # off the screen before the picture is taken
        self.picked.emit(area.translated(self.geometry().topLeft()))
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()

    def _cancel(self):
        if not self._done:
            self._done = True
            self.cancelled.emit()
        self.close()

    def closeEvent(self, event):
        if not self._done:
            self._done = True
            self.cancelled.emit()
        super().closeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = self.selection()
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))
        if area.isEmpty():
            font = painter.font()
            font.setPixelSize(15)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255, 235))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, _tr('Drag over the area to capture. Esc to cancel.'))
        else:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(area, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(255, 255, 255, 235), 1))
            painter.drawRect(QRectF(area).adjusted(0.5, 0.5, -0.5, -0.5))
            font = painter.font()
            font.setPixelSize(11)
            painter.setFont(font)
            label = '%d × %d' % (area.width(), area.height())
            where = QPoint(area.left() + 4, area.top() - 6 if area.top() > 20 else area.top() + 14)
            painter.drawText(where, label)
        painter.end()


class RegionPickerGroup(QObject):
    """One RegionPicker on EVERY screen (Ryan 2026-11-24: "我有多个外接屏，似乎都没法在别的外接屏上截屏" — the
    picker used to cover only the screen the pointer was on, i.e. the one Watermelon is on). The area is
    dragged out on whichever screen; the first press there takes the other screens' dimming away. Esc /
    right click on any of them = cancel all. The same signals as one picker."""
    picked = pyqtSignal(QRect)
    cancelled = pyqtSignal()

    def __init__(self, screens=None, parent=None):
        super().__init__(parent)
        self._done = False
        self.pickers = []
        for screen in (screens if screens is not None else QGuiApplication.screens()) or [QGuiApplication.primaryScreen()]:
            picker = RegionPicker(screen)
            picker.picked.connect(lambda area, me=picker: self._on_picked(me, area))
            picker.cancelled.connect(self._on_cancelled)
            picker.started.connect(lambda me=picker: self._close_others(me))
            self.pickers.append(picker)

    def show(self):
        under = QGuiApplication.screenAt(QCursor.pos())
        first = None
        for picker in self.pickers:
            picker.show()
            picker.raise_()
            if under is not None and picker.geometry() == under.geometry():
                first = picker
        (first or self.pickers[0]).activateWindow()

    def raise_(self):
        for picker in self.pickers:
            picker.raise_()

    def activateWindow(self):
        pass                                    # done in show(): the screen under the pointer

    def close(self):
        self._on_cancelled()

    def _close_others(self, keep):
        for picker in list(self.pickers):
            if picker is not keep:
                self.pickers.remove(picker)
                picker._done = True             # leaving quietly: not a cancel
                picker.close()

    def _on_picked(self, picker, area):
        if self._done:
            return
        self._done = True
        self._close_others(picker)
        self.picked.emit(QRect(area))

    def _on_cancelled(self):
        if self._done:
            return
        self._done = True
        for picker in self.pickers:
            picker._done = True
            picker.close()
        self.pickers = []
        self.cancelled.emit()


def pdfkit_available() -> bool:
    try:
        import Quartz  # noqa: F401
        return hasattr(Quartz, 'PDFDocument')
    except Exception:
        return False


def write_pdf(pictures, target: str, existing: str = '') -> bool:
    """The pictures as pages of a PDF, each page the size of its picture, with the writing in each picture
    as an invisible layer over it (it can be selected, copied and searched — watermelon_scan). With
    `existing` the pages are put after that PDF's own pages. Written whole next to the target, then moved
    into place. Blocks."""
    pictures = [path for path in pictures if os.path.isfile(path)]
    if not pictures:
        return False
    os.makedirs(os.path.dirname(target), exist_ok=True)
    temporary = target + '.new'
    try:
        if pdfkit_available():
            import watermelon_scan
            if not watermelon_scan.write_text_pdf(pictures, temporary):
                return False
            if existing:
                ok = watermelon_scan.append_pdf(existing, temporary, target)
                os.remove(temporary)
                return ok
        elif existing:
            return False
        else:
            writer = QPdfWriter(temporary)
            writer.setResolution(144)
            painter = None
            for path in pictures:
                image = QImage(path)
                if image.isNull():
                    continue
                size = QPageSize(QSizeF(image.width() / 2.0, image.height() / 2.0), QPageSize.Unit.Point)
                writer.setPageLayout(QPageLayout(size, QPageLayout.Orientation.Portrait, QMarginsF(0, 0, 0, 0)))
                if painter is None:
                    painter = QPainter(writer)
                else:
                    writer.newPage()
                painter.drawImage(QRectF(0, 0, writer.width(), writer.height()), image)
            if painter is None:
                return False
            painter.end()
        os.replace(temporary, target)
        return True
    except Exception:
        logging.exception('Making the PDF of the screenshots failed.')
        try:
            os.path.exists(temporary) and os.remove(temporary)
        except OSError:
            pass
        return False


class Courseware(QObject):
    """The screenshots / photos not yet put into a note, kept PER NOTE and kept across restarts (Ryan
    2026-11-24: "重启后没加进笔记的截图在列表里就看不到了…那我再怎么…删"): `root`/<note>/shot-<time>-<n>.png in
    Watermelon's own data folder (not the system's cache, which may be cleared). They stay until the person
    puts them into the note, makes a PDF of them or deletes them — never thrown away by themselves.
    `set_note(key, name)` = the note now open (its screenshots come back). The area chosen last is kept too."""
    changed = pyqtSignal(str)               # the path of a picture just added ('' = something else changed)
    failed = pyqtSignal()
    pdf_done = pyqtSignal(bool, str, str)   # ok, the PDF, the PDF it was added to ('' = a new one)

    def __init__(self, root: str, parent=None):
        super().__init__(parent)
        self.root = root
        self.note_key = None
        self.folder = os.path.join(root, NO_NOTE)
        self.region = self._load_region()   # QRect, screen coordinates
        self.shots = []
        self._count = 0
        self._busy = False
        self._picker = None
        self._from_thread.connect(self._on_thread)
        self._pictures_from_thread.connect(self._on_pictures)

    _from_thread = pyqtSignal(str, bool, str, str)

    # the pictures
    def items(self) -> list:
        """As entries of the list on the left."""
        return [{'path': path, 'name': _tr('Shot %d') % (index + 1), 'kind': 'image', 'offset': -1, 'courseware': True}
                for index, path in enumerate(self.shots)]

    def label_of(self, path: str) -> str:
        return _tr('Shot %d') % (self.shots.index(path) + 1) if path in self.shots else ''

    def _next_path(self, extension='.png') -> str:
        self._count += 1
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        return os.path.join(self.folder, 'shot-%s-%03d%s' % (stamp, self._count, extension))

    # which note
    @staticmethod
    def folder_name(key: str) -> str:
        return hashlib.sha1(str(key).encode('utf-8')).hexdigest()[:16] if key else NO_NOTE

    def set_note(self, key: str, name: str = ''):
        """The note now open: its own screenshots are the list's (read back from its folder)."""
        key = str(key or '')
        if key == self.note_key:
            return
        self.note_key = key
        self.folder = os.path.join(self.root, self.folder_name(key))
        self._note_name = str(name or '')
        try:
            names = sorted(entry for entry in os.listdir(self.folder)
                           if entry.startswith('shot-') and entry.lower().endswith(PICTURE_EXTS) and '.raw.' not in entry)
        except OSError:
            names = []
        self.shots = [os.path.join(self.folder, entry) for entry in names]
        self.changed.emit('')

    def _remember_note(self):
        """A small note.json beside the pictures: which note they belong to (for a person looking in Finder)."""
        try:
            os.makedirs(self.folder, exist_ok=True)
            with open(os.path.join(self.folder, 'note.json'), 'w', encoding='utf-8') as handle:
                json.dump({'note': self.note_key or '', 'name': getattr(self, '_note_name', '')}, handle, ensure_ascii=False)
        except OSError:
            pass

    # the area, kept across restarts
    def _region_path(self) -> str:
        return os.path.join(self.root, 'region.json')

    def _load_region(self):
        try:
            with open(self._region_path(), 'r', encoding='utf-8') as handle:
                data = json.load(handle)
            area = QRect(int(data['x']), int(data['y']), int(data['width']), int(data['height']))
            screens = [screen.geometry() for screen in (QGuiApplication.screens() or [])]
            return area if area.width() >= MIN_SIDE and area.height() >= MIN_SIDE and any(g.intersects(area) for g in screens) else None
        except Exception:
            return None

    def _save_region(self):
        try:
            os.makedirs(self.root, exist_ok=True)
            area = self.region
            with open(self._region_path(), 'w', encoding='utf-8') as handle:
                json.dump({'x': area.x(), 'y': area.y(), 'width': area.width(), 'height': area.height()}, handle)
        except Exception:
            logging.warning('Keeping the screenshot area failed.', exc_info=True)

    def pick_region(self, then_shoot=True):
        """Choose the area (again). The picture of it is taken right after."""
        if self._picker is not None:
            return self._picker
        picker = RegionPickerGroup()            # every screen: the area can be on any of them
        self._picker = picker

        def picked(area):
            self._picker = None
            self.region = QRect(area)
            self._save_region()
            if then_shoot:
                self.shoot()

        picker.picked.connect(picked)
        picker.cancelled.connect(lambda: setattr(self, '_picker', None))
        picker.show()
        picker.raise_()
        picker.activateWindow()
        return picker

    def shoot(self):
        """One more picture of the chosen area (no area yet = choose it first)."""
        if self.region is None:
            self.pick_region()
            return
        if self._busy:
            return
        self._busy = True
        area, path = QRect(self.region), self._next_path()

        def work():
            ok = False
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                ok = self._capture(area, path)
            except Exception:
                logging.exception('Taking the screenshot failed.')
            self._from_thread.emit('shot', bool(ok), path, '')

        threading.Thread(target=work, daemon=True, name='watermelon-courseware-shot').start()

    @staticmethod
    def _capture(area: QRect, path: str) -> bool:
        subprocess.run([SCREENCAPTURE, '-x', '-R', '%d,%d,%d,%d' % (area.x(), area.y(), area.width(), area.height()), path],
                       capture_output=True, timeout=20)
        return os.path.isfile(path) and os.path.getsize(path) > 0

    def add_pictures(self, paths):
        """Pictures from elsewhere (a photo of the blackboard…) as further pages; copied, on a thread."""
        paths = [path for path in paths if os.path.isfile(path)]
        targets = [self._next_path(os.path.splitext(path)[1].lower() or '.png') for path in paths]

        def work():
            for source, target in zip(paths, targets):
                try:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    shutil.copyfile(source, target)
                    self._from_thread.emit('shot', True, target, '')
                except Exception:
                    logging.exception('Adding a picture to the course material failed.')
                    self._from_thread.emit('shot', False, target, '')

        if paths:
            threading.Thread(target=work, daemon=True, name='watermelon-courseware-add').start()

    def add_photo(self, image: QImage):
        """A photo from a camera: the sheet of paper in it is found, straightened and cleared (no sheet in
        it = the photo as it is), then it is a page like the others. On a thread."""
        if image is None or image.isNull():
            return
        raw, page = self._next_path('.raw.jpg'), ''
        page = raw[:-len('.raw.jpg')] + '.jpg'
        image = QImage(image)

        def work():
            try:
                os.makedirs(os.path.dirname(raw), exist_ok=True)
                if not image.save(raw, 'JPG', 92):
                    self._from_thread.emit('shot', False, page, '')
                    return
                import watermelon_scan
                if watermelon_scan.available() and watermelon_scan.straighten_photo(raw, page):
                    os.remove(raw)
                else:
                    os.replace(raw, page)
                self._from_thread.emit('shot', True, page, '')
            except Exception:
                logging.exception('Adding a photo to the course material failed.')
                self._from_thread.emit('shot', False, page, '')

        threading.Thread(target=work, daemon=True, name='watermelon-courseware-photo').start()

    def export_pictures(self, folder: str, stem: str, paths=None):
        """The pictures (all, or `paths`) copied into `folder` as files of the note (Ryan 2026-11-24: "那你也加
        一个右键去作为图片加入的不就行了" — next to Save as PDF, the pictures as they are). On a thread; then
        `pictures_done(ok, copies)` and the copied ones are out of the course material."""
        chosen = [path for path in (paths if paths is not None else self.shots) if path in self.shots]
        if not chosen:
            return
        stamp = datetime.datetime.now().strftime('%Y-%m-%d %H%M%S')

        def work():
            copies = []
            try:
                os.makedirs(folder, exist_ok=True)
                for index, source in enumerate(chosen, 1):
                    extension = os.path.splitext(source)[1].lower() or '.png'
                    target = os.path.join(folder, '%s shot %s-%d%s' % (stem, stamp, index, extension))
                    shutil.copyfile(source, target)
                    copies.append((source, target))
            except Exception:
                logging.exception('Copying the screenshots into the note failed.')
            self._pictures_from_thread.emit(copies, len(copies) == len(chosen))

        threading.Thread(target=work, daemon=True, name='watermelon-courseware-pictures').start()

    pictures_done = pyqtSignal(bool, list)        # ok, the copies (paths) in the order taken
    _pictures_from_thread = pyqtSignal(list, bool)

    def _on_pictures(self, copies, ok):
        for source, _target in copies:
            if source in self.shots:
                self.shots.remove(source)
                try:
                    os.path.isfile(source) and os.remove(source)
                except OSError:
                    pass
        if copies:
            self.changed.emit('')
        self.pictures_done.emit(bool(ok), [target for _source, target in copies])

    def remove(self, path: str) -> bool:
        """One picture out of the course material (Ryan 2026-11-24: the list's right-click menu had no way to
        delete one). It is Watermelon's own copy in the lecture's folder: the file goes with it."""
        if path not in self.shots:
            return False
        self.shots.remove(path)

        def work():
            try:
                os.path.isfile(path) and os.remove(path)
            except OSError:
                logging.warning('Removing a screenshot of the course material failed.', exc_info=True)

        threading.Thread(target=work, daemon=True, name='watermelon-courseware-remove').start()
        self.changed.emit('')
        return True

    def discard(self):
        """All of this note's pictures deleted (only when the person says so)."""
        gone, self.shots = list(self.shots), []

        def work():
            for path in gone:
                try:
                    os.path.isfile(path) and os.remove(path)
                except OSError:
                    pass

        threading.Thread(target=work, daemon=True, name='watermelon-courseware-discard').start()
        self.changed.emit('')

    # the PDF
    def make_pdf(self, target: str, existing: str = '', paths=None):
        """All the pictures, or only `paths` (the ones chosen in the list), as one PDF. When it is made, those
        pictures are out of the course material (the others stay)."""
        pictures = [path for path in (paths if paths is not None else self.shots) if path in self.shots]
        self._pdf_pictures = list(pictures)

        def work():
            ok = write_pdf(pictures, target, existing)
            self._from_thread.emit('pdf', bool(ok), target, existing)

        threading.Thread(target=work, daemon=True, name='watermelon-courseware-pdf').start()

    def _on_thread(self, what, ok, path, existing):
        if what == 'shot':
            self._busy = False
            if ok and os.path.dirname(path) != self.folder:
                return                      # taken for a note that is no longer open: it waits in that note's folder
            if ok:
                self.shots.append(path)
                self._remember_note()
                self.changed.emit(path)
            else:
                self.failed.emit()
        else:
            if ok:
                for used in getattr(self, '_pdf_pictures', []):
                    if used in self.shots:
                        self.shots.remove(used)
                        try:
                            os.path.isfile(used) and os.remove(used)
                        except OSError:
                            pass
                self._pdf_pictures = []
                self.changed.emit('')
            self.pdf_done.emit(ok, path, existing)
