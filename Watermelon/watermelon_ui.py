# -*- coding: utf-8 -*-
"""Watermelon's Liquid Glass UI (2026-11-20) — the parts built on glass_kit.py.

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (section 5.14)
Ryan 2026-11-20: "帮我更新液态玻璃的语言，根据最新的样式书".

Watermelon's main window is a see-through canvas: the editing area (content, never glass) stands on a
picture of a typewriter, and the controls sit on that picture. So only what already was "glass" / a
white capsule becomes system glass (the round buttons on the typewriter, the web tab bar, the white
capsules); the dark grey buttons on the typewriter stay grey; the standalone windows get the system's
traffic lights and window glass; questions are system alerts; every menu is a system menu.

The window / dialog helpers are Tomato's (tomato_ui.py, 2026-11-15), unchanged in behaviour.
Import this module AFTER the QApplication exists.
"""
import logging
import os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QDialog
from PyQt6.QtCore import Qt, QRectF, QTimer, QCoreApplication, QTranslator
from PyQt6.QtGui import QColor, QPainter, QFont, QPalette

app = QApplication.instance()
if app is None:
    raise RuntimeError('watermelon_ui: create the QApplication before importing this module')

import glass_kit
from glass_kit import (_tr, is_dark_theme, MacNormalButton, WhiteButton, glass_corner_radius,
                       install_window_liquid_glass, install_native_traffic_lights, approval_window_width,
                       show_broccoli_message, ask_broccoli_message, smooth_round_rect_path,
                       MAIN_WINDOW_SMOOTH_RADIUS, NATIVE_TITLEBAR_HEIGHT)

GREY_ROW_HEIGHT = 22            # grey normal button / compact drop-down / normal input (5.1, 5.2, 5.4)
ROUND_BUTTON_SIZE = 34          # a round button in a bar (5.1); Watermelon's sit in a 38 box with 2 around


def ui_palette(dark=None) -> dict:
    if dark is None:
        dark = is_dark_theme(app)
    if dark:
        return {'dark': True, 'body': QColor('#2D2D2D'), 'text': '#F2F2F7', 'secondary': '#8E8E93',
                'line': '#4A4B4F'}
    return {'dark': False, 'body': QColor('#FFFFFF'), 'text': '#20242B', 'secondary': '#8E8E93',
            'line': '#ECECEC'}


def accent_color() -> QColor:
    """The system accent colour (style book 5.8: never a fixed blue)."""
    return QColor(app.palette().color(QPalette.ColorRole.Accent))


# ── standalone windows and dialogs ─────────────────────────────────────────────────────────────────────
def make_native_glass_window(widget, kind=Qt.WindowType.Window, resizable=False, stays_on_top=True):
    """A standalone window per the style book: the system's own traffic lights (new design, 5.7.2) in the
    compact transparent title bar (content starts 40 down), and the window's Liquid Glass behind
    everything (4.1 ①: frosted, untinted, corner 16, system shadow). Without glass the window paints the
    same rounded card itself (see glass_window_paint)."""
    widget.setWindowFlags(glass_kit.native_titlebar_window_flags(kind, zoom=resizable, stays_on_top=stays_on_top))
    widget.setAttribute(Qt.WidgetAttribute.WA_ContentsMarginsRespectsSafeArea, False)
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
    widget.radius = MAIN_WINDOW_SMOOTH_RADIUS
    layout = QWidget.layout(widget)   # some windows keep a `layout` attribute that hides the method
    if layout is not None:
        left, top, right, bottom = layout.getContentsMargins()
        layout.setContentsMargins(max(left, 20), NATIVE_TITLEBAR_HEIGHT, max(right, 20), max(bottom, 16))


def glass_window_paint(widget, event):
    """Paint for a glass window: nothing while its glass is up, the rounded body colour (light / dark)
    when there is no glass."""
    if getattr(widget, '_liquid_glass_active', False):
        return
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = smooth_round_rect_path(QRectF(widget.rect()), getattr(widget, 'radius', MAIN_WINDOW_SMOOTH_RADIUS))
    painter.fillPath(path, ui_palette()['body'])
    painter.end()


_MAIN_WINDOW = []   # [getter] → the main window, for placing dialogs over it


def set_dialog_host(getter):
    _MAIN_WINDOW[:] = [getter]


def _dialog_host():
    try:
        main = _MAIN_WINDOW[0]() if _MAIN_WINDOW else None
        if main is not None and main.isVisible() and main.width() > 200:
            return main
    except Exception:
        pass
    return None


def place_glass_dialog(dialog):
    """Style book 3: an edit / confirm dialog is the approval width (main window − 32, 420…640) and
    opens over the main window while that is open, else in the middle of the screen."""
    host = _dialog_host()
    width = approval_window_width(host) if host is not None else 640
    if getattr(dialog, '_keep_width', False):
        width = dialog.width()
    dialog.resize(max(width, dialog.minimumSizeHint().width()), dialog.height())
    area = host.frameGeometry() if host is not None else dialog.screen().availableGeometry()
    frame = dialog.frameGeometry()
    frame.moveCenter(area.center())
    bounds = (host.screen() if host is not None else dialog.screen()).availableGeometry()
    left = max(bounds.left() + 16, min(frame.left(), bounds.right() - frame.width() - 16))
    top = max(bounds.top() + 16, min(frame.top(), bounds.bottom() - frame.height() - 16))
    dialog.move(left, top)


def install_glass_dialog_class(cls, radius=None):
    """A frameless dialog whose whole window is the card: window glass at corner 16 with the system shadow
    (4.1 ①, 2.3), the fallback paint, placed by place_glass_dialog on first show."""
    cls.paintEvent = lambda self, event: glass_window_paint(self, event)
    install_window_liquid_glass(
        cls, (lambda w: glass_corner_radius(MAIN_WINDOW_SMOOTH_RADIUS, smooth=True)) if radius is None else radius, 0,
        keep_shadow=True, menu_look=True)
    original = cls.showEvent

    def showEvent(self, event, _original=original):
        if not getattr(self, '_glass_dialog_placed', False) and not getattr(self, '_no_auto_place', False):
            self._glass_dialog_placed = True
            place_glass_dialog(self)
        _original(self, event)

    cls.showEvent = showEvent


def install_native_glass_window_class(cls, fixed=True):
    """Every window of `cls`: traffic lights set just before each show, window glass on first show
    (radius = glass 16), the fallback paint."""
    cls.paintEvent = lambda self, event: glass_window_paint(self, event)
    install_native_traffic_lights(cls, fixed_buttons=fixed)
    install_window_liquid_glass(cls, lambda w: glass_corner_radius(getattr(w, 'radius', MAIN_WINDOW_SMOOTH_RADIUS),
                                                                   smooth=True), 0,
                                keep_shadow=True, menu_look=True)


def make_glass_dialog(dialog, stays_on_top=True):
    """Window flags / attributes of a frameless glass dialog (see install_glass_dialog_class)."""
    flags = Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
    if stays_on_top:
        flags |= Qt.WindowType.WindowStaysOnTopHint
    dialog.setWindowFlags(flags)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    dialog.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
    dialog.radius = MAIN_WINDOW_SMOOTH_RADIUS


# ── notices and questions: the system alert (style book 5.7, corner 26) ───────────────────────────────
def watermelon_alert(parent, title: str, text: str):
    """A notice / warning: the system alert over the window that asked."""
    show_broccoli_message(parent, title, text)


def watermelon_choice(parent, title: str, text: str, buttons, default=None, escape=None) -> str:
    """A question with the given buttons as the system alert; returns the chosen label. `default` is the
    Return button; `escape` is what Esc / closing means when the alert has to fall back to a dialog."""
    buttons = list(buttons)
    return ask_broccoli_message(parent, title, text, buttons, default or buttons[0],
                                escape_button_text=escape)


# ── a small "please wait" card (style book 5.12 "同步中小卡片": window glass, corner 16) ─────────────────
class BusyCard(QDialog):
    """A small glass card with one line of text; it does not block the app and has no buttons."""

    def __init__(self, text='', parent=None, size=(260, 90)):
        super().__init__(parent)
        make_glass_dialog(self)
        self._no_auto_place = True
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedSize(*size)
        box = QVBoxLayout(self)
        box.setContentsMargins(20, 16, 20, 16)
        self.label = QLabel(text, self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont(self.label.font())
        font.setPixelSize(13)
        self.label.setFont(font)
        box.addWidget(self.label)

    def set_text(self, text):
        self.label.setText(text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()   # Esc must not dismiss a wait card
            return
        super().keyPressEvent(event)


install_glass_dialog_class(BusyCard)


# ── translation (style book 1.6; the same scheme as Tomato's / Strawberry's / Broccoli's) ───────────────
UI_LANGUAGES = (('en', 'English'), ('zh_CN', '简体中文'), ('ja_JP', '日本語'))
_TRANSLATORS = []


def _language_file(data_dir: str) -> str:
    return os.path.join(data_dir, 'ui_language.txt')


def read_ui_language_setting(data_dir: str) -> str:
    """English until another language is chosen in the menu-bar menu."""
    try:
        with open(_language_file(data_dir), 'r', encoding='utf-8') as handle:
            code = handle.read().strip()
        return code if code in dict(UI_LANGUAGES) else 'en'
    except OSError:
        return 'en'


def write_ui_language_setting(data_dir: str, code: str) -> None:
    try:
        os.makedirs(data_dir, exist_ok=True)
        with open(_language_file(data_dir), 'w', encoding='utf-8') as handle:
            handle.write(code or '')
    except OSError:
        logging.exception('Saving the language failed.')


def load_translation(lang: str, dirs) -> bool:
    """Install watermelon_<lang>.qm from the first of `dirs` that has it. English needs no file."""
    for translator in _TRANSLATORS:
        QCoreApplication.removeTranslator(translator)
    _TRANSLATORS.clear()
    if lang in ('', 'en'):
        return True
    for folder in dirs:
        path = os.path.join(folder, 'watermelon_%s.qm' % lang)
        if os.path.isfile(path):
            translator = QTranslator(app)
            if translator.load(path):
                QCoreApplication.installTranslator(translator)
                _TRANSLATORS.append(translator)
                return True
    return False


# ── light / dark (style book 5.8: both sets, following the system live) ───────────────────────────────
_THEME_HOOKS = []   # callback(dark) after the application stylesheet changed


def refresh_kit_theme(dark=None):
    """The kit's own controls and the glass follow a light / dark switch (the application stylesheet and
    palette are set by the main file's apply_theme, which calls this at its end)."""
    if dark is None:
        dark = is_dark_theme(app)
    for widget in app.allWidgets():
        try:
            if isinstance(widget, MacNormalButton):
                widget.update_theme()
            elif isinstance(widget, WhiteButton):
                if not getattr(widget, '_pinned_stylesheet', False):
                    widget.apply_default_style()
            elif isinstance(widget, glass_kit.DropdownButton):
                widget._update_style()
        except RuntimeError:
            pass
    for callback in list(_THEME_HOOKS):
        try:
            callback(dark)
        except Exception:
            logging.exception('theme hook failed')
    for top in app.topLevelWidgets():
        try:
            glass_kit.resync_inwindow_glass(top)
            top.update()
        except Exception:
            pass
