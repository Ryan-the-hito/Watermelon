# -*- coding: utf-8 -*-
"""Watermelon: photographing paper with the Mac's cameras, and PDFs that carry the writing (2026-11-21).

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (5.14)
Ryan 2026-11-21: "我还想用 MacBook 拍图，想连接到系统的摄像头里面，MacBook 本身有前置的摄像头，然后也可以有
camera continuity 去用手机的…MacBook 本身还可以拍键盘方向的图片，刚好用来拍文件很合适"; "自动裁切图片，然后可能
自动调整锐化，让字更清晰，然后自动 OCR 文字"; the writing "保存在这个文件附件一起…是不是可以变成 PDF 上的注释
或者什么，总之让用户可以在预览的时候直接去复制图片里的文字".

Everything here is the system's own (no library is added):
  straighten_photo   Vision finds the sheet of paper, Core Image straightens it and makes the writing clear
  recognize_lines    Vision reads the writing (Chinese, Japanese, English), every line with its place
  write_text_pdf     pictures → a PDF: each picture is a page, its writing lies over it as an INVISIBLE layer,
                     line by line in place — so Preview, Quick Look, Spotlight and Watermelon's own preview
                     window can select, copy and search it. (The system's "save the OCR text" option of
                     PDFKit was tried first: it writes no text.)
  CameraWindow       the cameras of this Mac (built-in, Desk View, an iPhone as Continuity Camera): a live
                     picture, a list to choose the camera, Capture
The three functions block; call them from a thread. Import this module AFTER the QApplication exists.
"""
import logging
import os

from PyQt6.QtCore import Qt, QObject, QRectF, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from glass_kit import _tr, MacNormalButton, DropdownButton, NATIVE_TITLEBAR_HEIGHT
import watermelon_ui

OCR_LANGUAGES = ['zh-Hans', 'zh-Hant', 'ja-JP', 'en-US']
SHEET_CONFIDENCE = 0.6           # below this the photo is kept as it is (no sheet of paper in it)
PDF_POINTS_PER_PIXEL = 0.5       # a page is its picture at 144 dpi
# The font of the invisible writing. Not PingFang / Heiti / Songti: when a page written with those is put into
# another PDF, 牛 力 比 一 二 人 大 … come back as the look-alike radical signs (⽜ ⼒ ⽐ — measured 2026-11-21,
# 23 of 60 characters); with Hiragino Sans GB every character comes back as written.
TEXT_LAYER_FONT = 'Hiragino Sans GB'


def available() -> bool:
    try:
        import Vision  # noqa: F401
        import Quartz  # noqa: F401
        return True
    except Exception:
        return False


def _pool():
    import objc
    return objc.autorelease_pool()


def _load_cgimage(path: str):
    import Quartz
    from Foundation import NSURL
    source = Quartz.CGImageSourceCreateWithURL(NSURL.fileURLWithPath_(path), None)
    if source is None:
        return None
    return Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)


def straighten_photo(source: str, target: str) -> bool:
    """The sheet of paper in the photo, straightened and cleared, written to `target` (JPEG).
    False = no sheet was found (or something failed): nothing is written, use the photo as it is."""
    try:
        import Quartz
        import Vision
        from Foundation import NSURL
        with _pool():
            image = Quartz.CIImage.imageWithContentsOfURL_(NSURL.fileURLWithPath_(source))
            if image is None:
                return False
            request = Vision.VNDetectDocumentSegmentationRequest.alloc().init()
            handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(image, None)
            handler.performRequests_error_([request], None)
            found = (request.results() or [None])[0]
            if found is None or float(found.confidence()) < SHEET_CONFIDENCE:
                return False
            extent = image.extent()
            width, height = extent.size.width, extent.size.height

            def corner(point):
                return Quartz.CIVector.vectorWithX_Y_(point.x * width, point.y * height)

            flat = image.imageByApplyingFilter_withInputParameters_('CIPerspectiveCorrection', {
                'inputTopLeft': corner(found.topLeft()), 'inputTopRight': corner(found.topRight()),
                'inputBottomLeft': corner(found.bottomLeft()), 'inputBottomRight': corner(found.bottomRight())})
            clear = flat.imageByApplyingFilter_withInputParameters_('CIDocumentEnhancer', {'inputAmount': 1.0})
            if clear is None or clear.extent().size.width < 40 or clear.extent().size.height < 40:
                return False
            context = Quartz.CIContext.context()
            made = context.createCGImage_fromRect_(clear, clear.extent())
            if made is None:
                return False
            os.makedirs(os.path.dirname(target), exist_ok=True)
            destination = Quartz.CGImageDestinationCreateWithURL(NSURL.fileURLWithPath_(target), 'public.jpeg', 1, None)
            Quartz.CGImageDestinationAddImage(destination, made, {Quartz.kCGImageDestinationLossyCompressionQuality: 0.88})
            return bool(Quartz.CGImageDestinationFinalize(destination))
    except Exception:
        logging.exception('Straightening the photo failed.')
        return False


def recognize_lines(path: str, cgimage=None) -> list:
    """[(text, x, y, width, height)] — the lines of writing in the picture; the place as fractions of the
    picture, measured from its bottom-left corner (the system's way)."""
    try:
        import Vision
        with _pool():
            image = cgimage if cgimage is not None else _load_cgimage(path)
            if image is None:
                return []
            request = Vision.VNRecognizeTextRequest.alloc().init()
            request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            request.setRecognitionLanguages_(OCR_LANGUAGES)
            request.setUsesLanguageCorrection_(True)
            Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(image, None).performRequests_error_([request], None)
            lines = []
            for found in request.results() or []:
                best = found.topCandidates_(1)
                if not best:
                    continue
                box = found.boundingBox()
                text = str(best[0].string() or '').strip()
                if text:
                    lines.append((text, float(box.origin.x), float(box.origin.y), float(box.size.width), float(box.size.height)))
            return lines
    except Exception:
        logging.exception('Reading the writing in a picture failed.')
        return []


def write_text_pdf(pictures, target: str, read=True) -> bool:
    """`pictures` (paths) → one PDF at `target`: a page per picture, and over each page its writing as an
    invisible layer (read=False: pictures only). Written whole, then moved into place."""
    try:
        import CoreText
        import Quartz
        from Foundation import NSAttributedString, NSURL
        temporary = target + '.part'
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with _pool():
            context = Quartz.CGPDFContextCreateWithURL(NSURL.fileURLWithPath_(temporary), None, None)
            if context is None:
                return False
            pages = 0
            for path in pictures:
                image = _load_cgimage(path)
                if image is None:
                    continue
                width = Quartz.CGImageGetWidth(image) * PDF_POINTS_PER_PIXEL
                height = Quartz.CGImageGetHeight(image) * PDF_POINTS_PER_PIXEL
                box = Quartz.CGRectMake(0, 0, width, height)
                Quartz.CGContextBeginPage(context, box)
                Quartz.CGContextDrawImage(context, box, image)
                if read:
                    Quartz.CGContextSetTextDrawingMode(context, Quartz.kCGTextInvisible)
                    for text, x, y, w, h in recognize_lines(path, image):
                        size = max(4.0, h * height * 0.82)
                        font = CoreText.CTFontCreateWithName(TEXT_LAYER_FONT, size, None)
                        line = CoreText.CTLineCreateWithAttributedString(
                            NSAttributedString.alloc().initWithString_attributes_(text, {CoreText.kCTFontAttributeName: font}))
                        natural = CoreText.CTLineGetTypographicBounds(line, None, None, None)
                        natural = natural[0] if isinstance(natural, tuple) else natural
                        Quartz.CGContextSaveGState(context)
                        Quartz.CGContextTranslateCTM(context, x * width, y * height + h * height * 0.2)
                        Quartz.CGContextScaleCTM(context, (w * width) / max(1.0, float(natural)), 1.0)   # as wide as in the picture
                        Quartz.CGContextSetTextPosition(context, 0, 0)
                        CoreText.CTLineDraw(line, context)
                        Quartz.CGContextRestoreGState(context)
                Quartz.CGContextEndPage(context)
                pages += 1
            Quartz.CGPDFContextClose(context)
            del context
        if not pages:
            os.path.exists(temporary) and os.remove(temporary)
            return False
        os.replace(temporary, target)
        return True
    except Exception:
        logging.exception('Writing the PDF with its text failed.')
        return False


def append_pdf(existing: str, extra: str, target: str) -> bool:
    """The pages of `extra` after the pages of `existing`, written to `target` (may be `existing` itself)."""
    try:
        import Quartz
        from Foundation import NSURL
        with _pool():
            base = Quartz.PDFDocument.alloc().initWithURL_(NSURL.fileURLWithPath_(existing))
            more = Quartz.PDFDocument.alloc().initWithURL_(NSURL.fileURLWithPath_(extra))
            if base is None or more is None:
                return False
            for index in range(more.pageCount()):
                base.insertPage_atIndex_(more.pageAtIndex_(index), base.pageCount())
            temporary = target + '.part'
            if not base.writeToFile_(temporary):
                return False
        os.replace(temporary, target)
        return True
    except Exception:
        logging.exception('Adding pages to the PDF failed.')
        return False


# ── the cameras ──────────────────────────────────────────────────────────────────────────────────────
class CameraSource(QObject):
    """The Mac's cameras through Qt Multimedia. frame = the live picture; captured = a still."""
    frame = pyqtSignal(QImage)
    captured = pyqtSignal(QImage)
    failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera = None
        self._session = None
        self._sink = None
        self._still = None
        self._devices = []
        self._last = QImage()

    def names(self) -> list:
        from PyQt6.QtMultimedia import QMediaDevices
        self._devices = list(QMediaDevices.videoInputs())
        return [device.description() for device in self._devices]

    def start(self, index: int):
        from PyQt6.QtMultimedia import QCamera, QImageCapture, QMediaCaptureSession, QVideoSink
        self.stop()
        if not self._devices:
            self.names()
        if not 0 <= index < len(self._devices):
            self.failed.emit('no camera')
            return
        device = self._devices[index]
        self._camera = QCamera(device, self)
        formats = sorted(device.videoFormats(), key=lambda f: f.resolution().width() * f.resolution().height())
        if formats:
            self._camera.setCameraFormat(formats[-1])           # the most detail the camera has
        self._camera.errorOccurred.connect(lambda _error, text: self.failed.emit(str(text)))
        self._session = QMediaCaptureSession(self)
        self._session.setCamera(self._camera)
        self._sink = QVideoSink(self)
        self._sink.videoFrameChanged.connect(self._on_frame)
        self._session.setVideoSink(self._sink)
        self._still = QImageCapture(self)
        self._still.imageCaptured.connect(lambda _id, image: self.captured.emit(QImage(image)))
        self._still.errorOccurred.connect(lambda _id, _error, text: self._capture_from_live(str(text)))
        self._session.setImageCapture(self._still)
        self._camera.start()

    def _on_frame(self, video_frame):
        image = video_frame.toImage()
        if not image.isNull():
            self._last = image
            self.frame.emit(image)

    def _capture_from_live(self, why=''):
        if self._last.isNull():
            self.failed.emit(why or 'no picture')
        else:
            self.captured.emit(QImage(self._last))      # no still from this camera: the live picture

    def capture(self):
        if self._still is not None and self._still.isReadyForCapture():
            self._still.capture()
        else:
            self._capture_from_live()

    def stop(self):
        if self._camera is not None:
            self._camera.stop()
        for thing in (self._still, self._sink, self._session, self._camera):
            if thing is not None:
                thing.deleteLater()
        self._camera = self._session = self._sink = self._still = None
        self._last = QImage()


def _preferred_camera(names, remembered='') -> int:
    """The camera used last time; the first time the one that looks down at the desk, if this Mac has it."""
    if remembered in names:
        return names.index(remembered)
    for index, name in enumerate(names):
        if 'desk view' in name.lower():
            return index
    return 0 if names else -1


class _LiveView(QWidget):
    """The live picture, whole, on a dark sheet (it is content: no glass)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage()
        self._text = ''
        self.setMinimumSize(320, 240)

    def set_image(self, image):
        self._image = image
        self._text = ''
        self.update()

    def set_text(self, text):
        self._image = QImage()
        self._text = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        shape = QPainterPath()
        shape.addRoundedRect(QRectF(self.rect()), 8, 8)
        painter.setClipPath(shape)
        painter.fillRect(self.rect(), QColor('#1C1C1E'))
        if not self._image.isNull():
            size = self._image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            painter.drawImage(QRectF((self.width() - size.width()) / 2.0, (self.height() - size.height()) / 2.0,
                                     size.width(), size.height()), self._image)
        elif self._text:
            painter.setPen(QColor('#8E8E93'))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self._text)
        painter.end()


class CameraWindow(QWidget):
    """Photographing paper: the camera list on top, the live picture, Capture below. It stays open for the
    next page; every photo goes out through `photo_taken`. Space / Return = Capture, Esc = close."""
    photo_taken = pyqtSignal(QImage)
    camera_chosen = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, source=None, remembered='', parent=None):
        super().__init__(parent)
        self.source = source or CameraSource(self)
        self._taken = 0
        watermelon_ui.make_native_glass_window(self, resizable=True)
        self.setWindowTitle(_tr('Camera'))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.resize(560, 520)
        self.setMinimumSize(360, 380)
        box = QVBoxLayout(self)
        box.setContentsMargins(12, NATIVE_TITLEBAR_HEIGHT, 12, 12)
        box.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(8)
        self.cameras = DropdownButton(self, compact_light=True)
        self.cameras.setFixedWidth(240)
        top.addWidget(self.cameras)
        top.addStretch(1)
        box.addLayout(top)
        self.view = _LiveView(self)
        box.addWidget(self.view, 1)
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self.status = QLabel('', self)
        self.status.setStyleSheet('font-size: 12px; color: #8E8E93; background: transparent;')
        self.btn_capture = MacNormalButton(_tr('Capture'), self)
        self.btn_capture.setFixedHeight(watermelon_ui.GREY_ROW_HEIGHT)
        self.btn_capture.setMinimumWidth(96)
        self.btn_capture.clicked.connect(self.capture)
        bar.addWidget(self.status)
        bar.addStretch(1)
        bar.addWidget(self.btn_capture)
        box.addLayout(bar)
        self.source.frame.connect(self.view.set_image)
        self.source.captured.connect(self._on_captured)
        self.source.failed.connect(self._on_failed)
        self._names = []
        try:
            self._names = list(self.source.names())
        except Exception:
            logging.exception('Listing the cameras failed.')
        self.cameras.addItems(self._names)
        self.btn_capture.setEnabled(bool(self._names))
        if not self._names:
            self.view.set_text(_tr('No camera found.'))
        else:
            self.cameras.setCurrentIndex(_preferred_camera(self._names, remembered))
            self.cameras.currentIndexChanged.connect(self._choose)
            QTimer.singleShot(0, lambda: self._start(self.cameras.currentIndex()))

    def _start(self, index):
        self.view.set_text(_tr('Starting the camera…'))
        self._with_permission(lambda: self.source.start(index))

    def _with_permission(self, then):
        """macOS asks once whether Watermelon may use the camera."""
        try:
            from PyQt6.QtCore import QCameraPermission
            from PyQt6.QtWidgets import QApplication
            app, permission = QApplication.instance(), QCameraPermission()
            state = app.checkPermission(permission)
            if state == Qt.PermissionStatus.Granted:
                then()
            elif state == Qt.PermissionStatus.Undetermined:
                app.requestPermission(permission, self, lambda answer: then() if getattr(answer, 'status', lambda: None)() == Qt.PermissionStatus.Granted
                                      else self._on_failed('denied'))
            else:
                self._on_failed('denied')
        except Exception:
            then()

    def _choose(self, index):
        if 0 <= index < len(self._names):
            self.camera_chosen.emit(self._names[index])
            self._start(index)

    def capture(self):
        if self.btn_capture.isEnabled():
            self.source.capture()

    def _on_captured(self, image):
        if image.isNull():
            return
        self._taken += 1
        self.status.setText(_tr('%d taken') % self._taken)
        self.photo_taken.emit(image)

    def _on_failed(self, why):
        if why == 'denied':
            self.view.set_text(_tr('Watermelon may not use the camera. Allow it in System Settings › Privacy & Security › Camera.'))
        else:
            self.view.set_text(_tr("The camera couldn't be started."))
        logging.warning('Camera: %s', why)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.capture()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        try:
            self.source.stop()                # the camera's light goes out with the window
        except Exception:
            logging.exception('Stopping the camera failed.')
        self.closed.emit()
        super().closeEvent(event)


watermelon_ui.install_native_glass_window_class(CameraWindow, fixed=False)
