# -*- coding: utf-8 -*-
"""Watermelon: Anki cards from what is selected, made by Broccoli (2026-11-21).

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (5.14)
Ryan 2026-11-21: "根据当前选定的 note，不管是本地普通 note 还是 applenotes，其实如果网页的文字或者三件套里的文本
可以被获取就更好了，然后可以根据选定的文字，以及附件（可选加入不加入，以及特定页数），然后连接 broccoli 去生成
anki 的卡牌，挖空选择题那种基础的，或者正反面最基础的。然后保存在特定位置，之后还可以在它的基础上增加卡牌等等。
然后用户可以打开卡牌的位置，然后手动添加到 anki 中".

A deck is a folder: cards.json (the cards, each with a fixed id) and two text files Anki imports as they
are — "<deck> - Basic.txt" (front / back) and "<deck> - Cloze.txt" (fill in the blank). They carry Anki's
file headers (note type, deck, the id column), so importing a deck again after cards were added updates it
and adds the new ones instead of doubling everything. Nothing here talks to Anki: the person opens the
folder and imports the files.

  parse_pages / anki_prompt / parse_cards / export_text
  AnkiStore        the decks on the disk
  AnkiSession      one request to Broccoli (its public door: attachments, thread, id, reply_to) and its answer
  AnkiDialog       deck, kind of cards, how many, which attachments and pages
Import this module AFTER the QApplication exists.
"""
import datetime
import html
import json
import logging
import os
import re
import threading
import time
import uuid

from PyQt6.QtCore import Qt, QFileSystemWatcher, QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

import glass_kit
from glass_kit import _tr, MacNormalButton, DropdownButton, is_dark_theme
import watermelon_broccoli
import watermelon_ui

KINDS = [('basic', 'Front / Back'), ('cloze', 'Fill in the blank'), ('both', 'Both kinds')]
COUNTS = [(0, 'As many as fit'), (5, '5'), (10, '10'), (20, '20'), (30, '30')]
MAX_PAGES = 12
TEXT_CHARS_SENT = 12000
REPLY_TIMEOUT_SECONDS = 900
BASIC_FILE = '%s - Basic.txt'
CLOZE_FILE = '%s - Cloze.txt'


def deck_folder_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\n\r\t]+', ' ', str(name or '')).strip().strip('.')[:80]


def parse_pages(text: str, count: int) -> list:
    """"1-3, 5" → [0, 1, 2, 4] (page numbers as people write them → as programs count them); only pages
    the file has, each once, at most MAX_PAGES. Empty = no page."""
    pages = []
    for part in re.split(r'[,，、;；\s]+', str(text or '').strip()):
        found = re.fullmatch(r'(\d+)(?:\s*[-–~～]\s*(\d+))?', part)
        if not found:
            continue
        first, last = int(found.group(1)), int(found.group(2) or found.group(1))
        for page in range(min(first, last), max(first, last) + 1):
            if 1 <= page <= count and page - 1 not in pages:
                pages.append(page - 1)
    return pages[:MAX_PAGES]


# ── what is asked, reading the answer ────────────────────────────────────────────────────────────────
def anki_prompt(text: str, kind: str = 'both', count: int = 0, language: str = '', known=(), pictures: int = 0) -> str:
    parts = ['Make Anki flashcards from the material below for someone studying it.']
    if pictures:
        parts.append('%d attached picture(s) are pages of the same material: use them too.' % pictures)
    if kind == 'basic':
        parts.append('Make only front/back cards: {"type": "basic", "front": "a question or a term", "back": "the answer, short"}.')
    elif kind == 'cloze':
        parts.append('Make only fill-in-the-blank cards: {"type": "cloze", "text": "a full sentence with the key part hidden as '
                     '{{c1::hidden part}}", "extra": "optional note"}. One or two blanks per card (c1, c2).')
    else:
        parts.append('Use two kinds, whichever fits each fact: {"type": "basic", "front": "…", "back": "…"} and '
                     '{"type": "cloze", "text": "a full sentence with the key part hidden as {{c1::hidden part}}", "extra": "optional note"}.')
    parts.append('Make %s. One fact per card; a card must be understandable by itself.' % (
        ('exactly %d cards' % count) if count else 'as many cards as the material has facts worth remembering (at most 40)'))
    parts.append(('Write the cards in %s.' % language) if language else 'Write the cards in the language of the material.')
    known = [str(item) for item in known if item][:80]
    if known:
        parts.append('The deck already has cards about these, do not repeat them: %s.' % '; '.join(known))
    parts.append('Formulas as $…$. Reply with ONLY a JSON array of cards, no other text and no code fence.')
    text = str(text or '').strip()
    if len(text) > TEXT_CHARS_SENT:
        text = text[:TEXT_CHARS_SENT] + '…'
    return '\n'.join(parts) + '\n\n--- MATERIAL ---\n' + (text or '(see the attached pages)')


def _clean(item):
    if not isinstance(item, dict):
        return None
    kind = str(item.get('type', '') or '').strip().lower()
    text = str(item.get('text', '') or '').strip()
    front, back = str(item.get('front', '') or '').strip(), str(item.get('back', '') or '').strip()
    if (kind == 'cloze' or (not kind and text)) and re.search(r'\{\{c\d+::.+?\}\}', text, re.S):
        return {'type': 'cloze', 'text': text, 'extra': str(item.get('extra', '') or '').strip()}
    if front and back:
        return {'type': 'basic', 'front': front, 'back': back}
    return None


def parse_cards(answer: str) -> list:
    """The cards in Broccoli's answer (text around the JSON is skipped; cards that are not whole are left out)."""
    text = str(answer or '').strip()
    decoder = json.JSONDecoder()
    for match in re.finditer(r'[\[{]', text):
        try:
            value, _end = decoder.raw_decode(text[match.start():])
        except ValueError:
            continue
        if isinstance(value, dict):
            value = value.get('cards') if isinstance(value.get('cards'), list) else [value]
        if isinstance(value, list):
            cards = [card for card in (_clean(item) for item in value[:80]) if card]
            if cards:
                return cards
    return []


def card_key(card: dict) -> str:
    """What makes two cards the same card: its question (basic) or its sentence without the blanks (cloze)."""
    text = card.get('front', '') if card.get('type') == 'basic' else re.sub(r'\{\{c\d+::(.+?)(?:::.*?)?\}\}', r'\1', card.get('text', ''), flags=re.S)
    return card.get('type', '') + ':' + re.sub(r'\s+', '', text).lower()


def _field(text: str) -> str:
    """A field of Anki's text file: HTML, one line, no tab; $…$ formulas as Anki's \\(…\\)."""
    text = str(text or '')
    text = re.sub(r'\$\$(.+?)\$\$', lambda m: '\\[' + m.group(1).strip() + '\\]', text, flags=re.S)
    text = re.sub(r'(?<![\\$\w])\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\d)', lambda m: '\\(' + m.group(1) + '\\)', text)
    return html.escape(text, quote=False).replace('\t', ' ').replace('\r', '').replace('\n', '<br>')


def export_text(deck: str, cards: list, kind: str) -> str:
    """Anki's text import file for the deck's cards of one kind ('' = the deck has none of that kind)."""
    cards = [card for card in cards if card.get('type') == kind]
    if not cards:
        return ''
    head = ['#separator:tab', '#html:true', '#notetype:%s' % ('Cloze' if kind == 'cloze' else 'Basic'), '#deck:%s' % deck,
            '#guid column:1', '#columns:%s' % ('ID\tText\tBack Extra' if kind == 'cloze' else 'ID\tFront\tBack')]
    rows = []
    for card in cards:
        if kind == 'cloze':
            rows.append('\t'.join((card['id'], _field(card.get('text')), _field(card.get('extra')))))
        else:
            rows.append('\t'.join((card['id'], _field(card.get('front')), _field(card.get('back')))))
    return '\n'.join(head + rows) + '\n'


# ── the decks ─────────────────────────────────────────────────────────────────────────────────────────
class AnkiStore:
    def __init__(self, root: str):
        self.root = root

    def folder(self, deck: str) -> str:
        return os.path.join(self.root, deck_folder_name(deck))

    def decks(self) -> list:
        try:
            names = [name for name in os.listdir(self.root) if os.path.isfile(os.path.join(self.root, name, 'cards.json'))]
        except OSError:
            return []
        return sorted(names, key=lambda name: -os.path.getmtime(os.path.join(self.root, name, 'cards.json')))

    def cards(self, deck: str) -> list:
        try:
            with open(os.path.join(self.folder(deck), 'cards.json'), encoding='utf-8') as handle:
                data = json.load(handle)
            return [card for card in data.get('cards', []) if isinstance(card, dict) and card.get('id')]
        except Exception:
            return []

    def add(self, deck: str, new_cards: list, source: str = '') -> int:
        """New cards into the deck (one it has already is left out); the text files are written again.
        → how many were added. Blocks (small files)."""
        deck = deck_folder_name(deck)
        cards = self.cards(deck)
        have = {card_key(card) for card in cards}
        now, added = datetime.datetime.now().isoformat(timespec='seconds'), 0
        for card in new_cards:
            key = card_key(card)
            if key in have:
                continue
            have.add(key)
            cards.append(dict(card, id=uuid.uuid4().hex[:16], source=str(source or ''), created=now))
            added += 1
        folder = self.folder(deck)
        os.makedirs(folder, exist_ok=True)
        self._write(os.path.join(folder, 'cards.json'), json.dumps({'deck': deck, 'cards': cards}, ensure_ascii=False, indent=1))
        for kind, pattern in (('basic', BASIC_FILE), ('cloze', CLOZE_FILE)):
            text, path = export_text(deck, cards, kind), os.path.join(folder, pattern % deck)
            if text:
                self._write(path, text)
            elif os.path.exists(path):
                os.remove(path)
        return added

    @staticmethod
    def _write(path, text):
        with open(path + '.tmp', 'w', encoding='utf-8') as handle:
            handle.write(text)
        os.replace(path + '.tmp', path)


# ── one request ───────────────────────────────────────────────────────────────────────────────────────
class AnkiSession(QObject):
    done = pyqtSignal(str, int, int)          # deck, cards added, cards in the deck now
    failed = pyqtSignal(str)                  # 'not_installed' | 'no_answer' | 'failed' | 'no_cards'
    _sent = pyqtSignal(str, bool, str)

    def __init__(self, store: AnkiStore, reply_dir: str, pages_dir: str, send=None, parent=None):
        super().__init__(parent)
        self.store, self.reply_dir, self.pages_dir = store, reply_dir, pages_dir
        self._send = send or watermelon_broccoli.send
        self._pending = {}
        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_reply_folder)
        self._timeout = QTimer(self)
        self._timeout.setInterval(60000)
        self._timeout.timeout.connect(self._drop_old)
        self._sent.connect(self._on_sent)

    def busy(self) -> bool:
        return bool(self._pending)

    def request(self, deck: str, text: str, kind: str, count: int, pictures=(), language: str = '', document: str = ''):
        """`pictures`: paths of pictures (pages already rendered) sent with the text."""
        deck = deck_folder_name(deck) or 'Watermelon'
        request_id = uuid.uuid4().hex
        try:
            os.makedirs(self.reply_dir, exist_ok=True)
            if self.reply_dir not in self._watcher.directories():
                self._watcher.addPath(self.reply_dir)
        except OSError:
            logging.exception('The folder for Broccoli\'s answers could not be made.')
        pictures = [path for path in pictures if path]
        known = [card.get('front') or re.sub(r'\{\{c\d+::(.+?)(?:::.*?)?\}\}', r'\1', card.get('text', '')) for card in self.store.cards(deck)]
        prompt = anki_prompt(text, kind, count, language, known[-80:], len(pictures))
        self._pending[request_id] = {'deck': deck, 'at': time.time(), 'document': document}
        self._timeout.start()
        extra = {'thread': 'anki/%s' % deck, 'id': request_id, 'reply_to': self.reply_dir}
        if pictures:
            extra['attachments'] = list(pictures)
        send = self._send

        def work():
            try:
                ok, detail = send(prompt, title='Anki · %s' % deck, metadata={'watermelon_anki': deck}, extra=extra)
            except Exception as error:
                logging.exception('Sending the Anki request to Broccoli failed.')
                ok, detail = False, str(error)
            self._sent.emit(request_id, bool(ok), str(detail))

        threading.Thread(target=work, daemon=True, name='watermelon-anki-send').start()
        return request_id

    def _on_sent(self, request_id, ok, detail):
        if request_id not in self._pending:
            return
        if ok:
            self._on_reply_folder()
            return
        self._finish(request_id)
        self.failed.emit('not_installed' if detail == 'not_installed' else 'no_answer')

    def _on_reply_folder(self, _path=''):
        try:
            names = os.listdir(self.reply_dir)
        except OSError:
            return
        for name in names:
            request_id = name[:-5]
            if not name.endswith('.json') or request_id not in self._pending:
                continue
            path = os.path.join(self.reply_dir, name)
            try:
                with open(path, encoding='utf-8') as handle:
                    data = json.load(handle)
            except Exception:
                data = {}
            try:
                os.remove(path)
            except OSError:
                pass
            request = self._pending.get(request_id) or {}
            self._finish(request_id)
            cards = parse_cards(data.get('answer', '')) if str(data.get('status', '')) != 'failed' else []
            if not cards:
                self.failed.emit('failed' if str(data.get('status', '')) == 'failed' else 'no_cards')
                continue
            try:
                added = self.store.add(request['deck'], cards, request.get('document', ''))
            except Exception:
                logging.exception('Saving the Anki cards failed.')
                self.failed.emit('failed')
                continue
            self.done.emit(request['deck'], added, len(self.store.cards(request['deck'])))

    def _finish(self, request_id):
        self._pending.pop(request_id, None)
        if not self._pending:
            self._timeout.stop()

    def _drop_old(self):
        now = time.time()
        old = [rid for rid, request in self._pending.items() if now - request['at'] > REPLY_TIMEOUT_SECONDS]
        for request_id in old:
            self._finish(request_id)
        if old:
            self.failed.emit('no_answer')


# ── the dialog ────────────────────────────────────────────────────────────────────────────────────────
class AnkiDialog(QWidget):
    """An edit dialog (style book 5.7 / 5.14): the window is the card — window glass, corner 16; compact
    grey drop-downs, normal inputs, the system's tick boxes, grey normal buttons at the bottom right.
    Return = Generate, Esc = Cancel. `attachments`: [{'path', 'name', 'kind', 'pages' (a PDF's count),
    'page' (the page being looked at, 1-based, or 0)}]."""
    generate = pyqtSignal(dict)       # {'deck', 'kind', 'count', 'attachments': [(item, [pages])]}
    show_folder = pyqtSignal(str)

    def __init__(self, decks, source_text: str, source_label: str, attachments=(), suggested_deck: str = '', parent=None):
        super().__init__(parent)
        watermelon_ui.make_glass_dialog(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle(_tr('Make Anki Cards'))
        self._decks = list(decks)
        self._rows = []
        dark = is_dark_theme(glass_kit.app)
        text_colour = '#F2F2F7' if dark else '#20242B'
        box = QVBoxLayout(self)
        box.setContentsMargins(20, 18, 20, 16)
        box.setSpacing(10)
        title = QLabel(_tr('Make Anki Cards'), self)
        title.setStyleSheet('font-size: 13px; font-weight: 600; color: %s; background: transparent;' % text_colour)
        box.addWidget(title)
        self.source_label = QLabel(source_label, self)
        self.source_label.setWordWrap(True)
        self.source_label.setStyleSheet('font-size: 12px; color: #8E8E93; background: transparent;')
        box.addWidget(self.source_label)

        def label(text):
            widget = QLabel(text, self)
            widget.setStyleSheet('font-size: 13px; color: %s; background: transparent;' % text_colour)
            widget.setFixedWidth(84)
            return widget

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(label(_tr('Deck:')))
        self.deck_list = DropdownButton(self, compact_light=True)
        self.deck_list.setFixedWidth(200)
        self.deck_list.addItems(self._decks + [_tr('New Deck…')])
        row.addWidget(self.deck_list)
        self.deck_name = QLineEdit(self)
        self.deck_name.setFixedHeight(watermelon_ui.GREY_ROW_HEIGHT)
        self.deck_name.setPlaceholderText(_tr('Name of the new deck'))
        self.deck_name.setStyleSheet(glass_kit._settings_lineedit_stylesheet(dark))
        self.deck_name.setText(deck_folder_name(suggested_deck))
        row.addWidget(self.deck_name, 1)
        box.addLayout(row)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(label(_tr('Cards:')))
        self.kind_list = DropdownButton(self, compact_light=True)
        self.kind_list.setFixedWidth(200)
        self.kind_list.addItems([_tr('Front / Back'), _tr('Fill in the blank'), _tr('Both kinds')])
        self.kind_list.setCurrentIndex(2)
        row.addWidget(self.kind_list)
        self.count_list = DropdownButton(self, compact_light=True)
        self.count_list.setFixedWidth(130)
        self.count_list.addItems([_tr('As many as fit')] + [str(value) for value, _name in COUNTS[1:]])
        row.addWidget(self.count_list)
        row.addStretch(1)
        box.addLayout(row)
        if attachments:
            head = QLabel(_tr('Attachments to send with the text:'), self)
            head.setStyleSheet('font-size: 12px; color: #8E8E93; background: transparent; padding-top: 4px;')
            box.addWidget(head)
        for item in list(attachments)[:8]:
            row = QHBoxLayout()
            row.setSpacing(8)
            tick = QCheckBox(item['name'], self)
            tick.setStyleSheet('font-size: 13px; color: %s; background: transparent;' % text_colour)
            row.addWidget(tick, 1)
            pages = None
            if item.get('kind') == 'pdf':
                pages = QLineEdit(self)
                pages.setFixedSize(150, watermelon_ui.GREY_ROW_HEIGHT)
                pages.setPlaceholderText(_tr('Pages, e.g. 1-3, 5'))
                pages.setStyleSheet(glass_kit._settings_lineedit_stylesheet(dark))
                pages.setText(str(item.get('page') or 1))
                pages.setEnabled(False)
                tick.toggled.connect(pages.setEnabled)
                of = QLabel(_tr('of %d') % int(item.get('pages') or 0), self)
                of.setStyleSheet('font-size: 12px; color: #8E8E93; background: transparent;')
                row.addWidget(pages)
                row.addWidget(of)
            box.addLayout(row)
            self._rows.append((item, tick, pages))
        self.note = QLabel('', self)
        self.note.setStyleSheet('font-size: 12px; color: #FF6B6B; background: transparent;')
        box.addWidget(self.note)
        box.addStretch(1)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.btn_folder = MacNormalButton(_tr('Show Deck Folder'), self)
        self.btn_folder.clicked.connect(lambda: self.show_folder.emit(self.deck()))
        self.btn_cancel = MacNormalButton(_tr('Cancel'), self)
        self.btn_cancel.setMinimumWidth(96)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_generate = MacNormalButton(_tr('Generate'), self)
        self.btn_generate.setMinimumWidth(96)
        self.btn_generate.clicked.connect(self._generate)
        row.addWidget(self.btn_folder)
        row.addStretch(1)
        row.addWidget(self.btn_cancel)
        row.addWidget(self.btn_generate)
        box.addLayout(row)
        self._has_text = bool(str(source_text or '').strip())
        self.deck_list.currentIndexChanged.connect(lambda _index: self._sync())
        self.deck_list.setCurrentIndex(0 if self._decks else len(self._decks))
        self._sync()
        self.resize(560, self.sizeHint().height())

    def _new_deck(self) -> bool:
        return self.deck_list.currentIndex() >= len(self._decks)

    def _sync(self):
        self.deck_name.setVisible(self._new_deck())
        self.btn_folder.setEnabled(not self._new_deck())

    def deck(self) -> str:
        return deck_folder_name(self.deck_name.text()) if self._new_deck() else self._decks[self.deck_list.currentIndex()]

    def choices(self):
        """None (and a red line saying why) when something is missing."""
        deck = self.deck()
        if not deck:
            self.note.setText(_tr('Give the new deck a name.'))
            return None
        chosen = []
        for item, tick, pages in self._rows:
            if not tick.isChecked():
                continue
            numbers = []
            if pages is not None:
                numbers = parse_pages(pages.text(), int(item.get('pages') or 0))
                if not numbers:
                    self.note.setText(_tr('Write which pages of “%s” to send.') % item['name'])
                    return None
            chosen.append((item, numbers))
        if not self._has_text and not chosen:
            self.note.setText(_tr('There is no text: tick an attachment to send.'))
            return None
        self.note.setText('')
        return {'deck': deck, 'kind': KINDS[self.kind_list.currentIndex()][0], 'count': COUNTS[self.count_list.currentIndex()][0],
                'attachments': chosen}

    def _generate(self):
        choices = self.choices()
        if choices is not None:
            self.generate.emit(choices)
            self.close()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._generate()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)


watermelon_ui.install_glass_dialog_class(AnkiDialog)
