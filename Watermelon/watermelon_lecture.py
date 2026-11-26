# -*- coding: utf-8 -*-
"""Watermelon: Lecture Mode — the AI panel on the right of the editing column (2026-11-21).

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (5.14)
Ryan 2026-11-21: "右边可以作为一个 AI 区域，与 broccoli 联通"; a mode that sends "此刻的笔记 + 当前打开的附件"
to Broccoli "去总结知识点", the live voice transcript of Broccoli as a second line, results as "有动画的从上至下
的小卡片", a card "拖进编辑区 = 加一个信息块", cards can be archived, "有一页可以清空所有归档", the language of
the notes chosen in the settings. The looks: "都按你推荐".

Two lines feed the cards:
  the page line   the note so far + a picture of the page being looked at (a preview window's page, or a
                  screenshot taken as course material) → Broccoli → 0–3 cards. A new page = a new round;
                  quick page turns send only the page stopped on.
  the voice line  Broccoli's live transcript (finished sentences of its voice input). Cut by a pause or by
                  length first; the model then decides whether a passage continues the last card (merge) or
                  starts a new one.
Everything goes through Broccoli's public door (watermelon_broccoli.send) with its optional parts of
2026-11-21: attachments, thread (one Broccoli conversation per lecture), id + reply_to (the answer comes
back as a file in a folder that is watched — nothing is polled).

  CardStore / LectureSettings     the cards and the three switches, as small JSON files
  page_prompt / voice_prompt / parse_reply
  TranscriptFollower              subscribes to the live transcript and follows the file
  LectureSession                  the two lines, the requests and their answers
  LecturePanel                    the glass panel with the cards (always light, like the list on the left)
Import this module AFTER the QApplication exists.
"""
import datetime
import json
import logging
import os
import re
import threading
import time
import uuid

from PyQt6.QtCore import (Qt, QEvent, QEasingCurve, QFileSystemWatcher, QMimeData, QObject, QPoint, QPointF, QRectF, QSize,
                          QTimer, QVariantAnimation, pyqtSignal)
from PyQt6.QtGui import (QColor, QDrag, QFont, QFontMetrics, QImage, QPainter, QPainterPath, QPen, QPixmap,
                         QTextLayout, QTextOption)
from PyQt6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QScrollArea, QVBoxLayout, QWidget)

import glass_kit
from glass_kit import _tr, MacNormalButton, attach_inwindow_liquid_glass, style_broccoli_context_menu
import watermelon_broccoli

PANEL_WIDTH = 126                # fills the empty strip right of the editing column, never on the column
                                 # (Ryan 2026-11-21: "严格控制宽度，不要覆盖到主界面，刚好填满")
PANEL_RADIUS = 16                # a floating panel (style book 2.1, third tier)
CARD_RADIUS = 9                  # a small surface on it (fourth tier)
PAGE_SETTLE_MS = 2000            # a page must be looked at this long before it is sent (quick page turns)
VOICE_PAUSE_MS = 6000            # this long without a new sentence ends a passage
VOICE_PASSAGE_CHARS = 300        # …and so does this much text
REPLY_TIMEOUT_SECONDS = 600
NOTE_CHARS_SENT = 1500           # of the paragraph being written / the notes new since the last request
NOTE_PAUSE_MS = 6000             # the note line: this long without typing ends a piece of new notes …
NOTE_MIN_CHARS = 40              # … if it holds at least this much new text (a Chinese / Japanese character counts 2)
NOTE_LONG_CHARS = 500            # this much new text is sent without waiting for a pause
VOICE_MERGE_SECONDS = 120        # a passage may only be merged into a voice card this young (older = the talk has moved on)
VOICE_IN_FLIGHT = 2              # at most this many passages wait for Broccoli at once; more speech is gathered meanwhile
KNOWN_TITLES = 8                 # only the latest cards' titles go along (not to repeat them) — more pulls the model back


def text_weight(text: str) -> int:
    """How much was written: a Chinese / Japanese / Korean character says about as much as two letters."""
    return sum(2 if ord(ch) >= 0x2E80 else 1 for ch in str(text or '') if not ch.isspace())

# the language the cards are written in ('' = the language of the note); names are their own, not translated
LANGUAGES = [('', 'Same as the note'), ('Simplified Chinese', '简体中文'), ('Traditional Chinese', '繁體中文'),
             ('Japanese', '日本語'), ('English', 'English'), ('Korean', '한국어'), ('French', 'Français'),
             ('German', 'Deutsch'), ('Spanish', 'Español')]


def language_label(code: str) -> str:
    for value, name in LANGUAGES:
        if value == code:
            return _tr('Same as the note') if not value else name
    return _tr('Same as the note')


# ── the small files ──────────────────────────────────────────────────────────────────────────────────
def _write_json(path: str, data) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + '.tmp', 'w', encoding='utf-8') as handle:
            json.dump(data, handle, ensure_ascii=False)
        os.replace(path + '.tmp', path)
    except Exception:
        logging.exception('Saving %s failed.', os.path.basename(path))


def _read_json(path: str, default):
    try:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
        return data if isinstance(data, type(default)) else default
    except Exception:
        return default


class LectureSettings:
    """language ('' = the note's), voice (the voice line is on)."""
    DEFAULTS = {'language': '', 'voice': True, 'camera': ''}

    def __init__(self, path: str):
        self.path = path
        self._data = dict(self.DEFAULTS)
        self._data.update({k: v for k, v in _read_json(path, {}).items() if k in self.DEFAULTS})

    def get(self, key):
        return self._data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        if self._data.get(key) == value:
            return
        self._data[key] = value
        _write_json(self.path, self._data)


class CardStore:
    """Every card ever made that was not cleared: {id, title, body, page, source ('page' | 'voice'),
    document, created, archived}. Newest first. Saved whole on a thread of its own."""

    def __init__(self, path: str):
        self.path = path
        self._cards = [card for card in _read_json(path, {}).get('cards', []) if isinstance(card, dict) and card.get('id')]
        self._lock = threading.Lock()

    def _save(self):
        snapshot = {'cards': [dict(card) for card in self._cards]}

        def work():
            with self._lock:
                _write_json(self.path, snapshot)

        threading.Thread(target=work, daemon=True, name='watermelon-lecture-cards').start()

    def add(self, title, body, page='', source='page', document='', **more) -> dict:
        card = {'id': uuid.uuid4().hex[:12], 'title': str(title or '').strip(), 'body': str(body or '').strip(),
                'page': str(page or ''), 'source': source, 'document': str(document or ''),
                'created': datetime.datetime.now().isoformat(timespec='seconds'), 'archived': False}
        card.update(more)             # a mark of an attachment: 'file', 'file_page'
        self._cards.insert(0, card)
        self._save()
        return card

    def find(self, card_id):
        return next((card for card in self._cards if card['id'] == card_id), None)

    def update(self, card_id, **changes):
        card = self.find(card_id)
        if card is not None:
            card.update(changes)
            self._save()
        return card

    def remove(self, card_id):
        self._cards = [card for card in self._cards if card['id'] != card_id]
        self._save()

    def active(self, document=None) -> list:
        return [card for card in self._cards if not card.get('archived')
                and (document is None or card.get('document', '') == document)]

    def archived(self) -> list:
        return [card for card in self._cards if card.get('archived')]

    def clear_archived(self) -> int:
        count = len(self.archived())
        if count:
            self._cards = [card for card in self._cards if not card.get('archived')]
            self._save()
        return count


def card_markdown(card: dict) -> str:
    """A card as a block of the note: a quote with the title in bold."""
    lines = ['> **%s**' % card.get('title', '').strip()] if card.get('title', '').strip() else []
    for line in str(card.get('body', '') or '').strip().splitlines():
        lines.append('> ' + line.strip() if line.strip() else '>')
    return '\n'.join(lines)


# ── what is asked, and reading the answer ───────────────────────────────────────────────────────────
_REPLY_FORMAT = ('Reply with ONLY JSON, no other text and no code fence. Each card is '
                 '{"title": "one knowledge point, at most 12 words", "body": "2 to 4 short sentences; plain text, '
                 'formulas as $…$"}.')


def _language_line(language: str) -> str:
    return ('Write the cards in %s.' % language) if language else 'Write the cards in the language the notes are written in.'


# Ryan 2026-11-21: "右边应该生成的是现在这一张、现在这一段录音、目前正在记录的笔记相关的内容，而不是给前面的历史笔记做
# 解释" — every question is about what is in front of him NOW; the rest of the notes is never sent, only where
# he is in them (the headings above the cursor), and the earlier turns of the conversation are said to be done.
_ONLY_NOW = ('Only about what is given below as being NOW. Do not explain, summarize or repeat anything else — '
             'earlier pages, earlier notes and the earlier turns of this conversation are done already.')


def _context(current='', outline='', new_notes='', passage='') -> str:
    parts = []
    if outline:
        parts.append('--- WHERE I AM IN MY NOTES (for orientation only, not to be explained) ---\n' + outline)
    if new_notes.strip():
        parts.append('--- WHAT I HAVE JUST WRITTEN ---\n' + new_notes.strip()[-NOTE_CHARS_SENT:])
    if current.strip() and current.strip() not in new_notes:
        parts.append('--- THE PARAGRAPH I AM WRITING NOW ---\n' + current.strip()[-NOTE_CHARS_SENT:])
    if passage.strip():
        parts.append('--- WHAT WAS JUST SAID (speech recognition, may contain wrong words) ---\n' + passage.strip()[-NOTE_CHARS_SENT:])
    return '\n\n'.join(parts)


def page_prompt(page_label: str, language: str = '', known_titles=(), has_picture=True, current='', outline='', new_notes='') -> str:
    known = '; '.join(title for title in list(known_titles)[:30] if title)
    parts = ['I am taking notes during a lecture and want short study cards.']
    if has_picture:
        parts.append('NOW: the attached picture is the page of the course material shown right now (%s). '
                     'Make 1 to 3 cards for the key points of THIS page.' % (page_label or 'current page'))
    else:
        parts.append('NOW: there is no course material; make 0 to 2 cards for the key points of what I have just written.')
    parts.append(_ONLY_NOW)
    if known:
        parts.append('These points already have cards, do not repeat them: %s.' % known)
    parts.append(_language_line(language))
    parts.append(_REPLY_FORMAT + ' Reply a JSON array of cards; reply [] when there is nothing new.')
    return '\n'.join(parts) + '\n\n' + _context(current, outline, new_notes)


def note_prompt(new_notes: str, language: str = '', known_titles=(), current='', outline='', page_label='') -> str:
    known = '; '.join(title for title in list(known_titles)[:30] if title)
    parts = ['I am taking notes during a lecture and want short study cards.',
             'NOW: what I have just written (below). Make 0 to 2 cards that make ITS key points clear — a precise '
             'statement, a missing step, a definition it relies on.' + (' The course material open now is %s.' % page_label if page_label else ''),
             _ONLY_NOW]
    if known:
        parts.append('These points already have cards, do not repeat them: %s.' % known)
    parts.append(_language_line(language))
    parts.append(_REPLY_FORMAT + ' Reply a JSON array of cards; reply [] when nothing worth a card was written.')
    return '\n'.join(parts) + '\n\n' + _context(current, outline, new_notes)


def voice_prompt(passage: str, language: str = '', last_card=None) -> str:
    parts = ['I am taking notes during a lecture and want short study cards.',
             'NOW: what was just said (below; speech recognition: it may contain wrong words; ignore small talk).',
             _ONLY_NOW]
    if last_card:
        parts.append('The last card made from speech is: %s' % json.dumps(
            {'title': last_card.get('title', ''), 'body': last_card.get('body', '')}, ensure_ascii=False))
        parts.append('Only if the passage is clearly still about exactly that point, reply ONE object '
                     '{"merge": true, "title": …, "body": …}: that card rewritten to include the passage. '
                     'If the talk has moved on to anything else, do NOT merge: reply a JSON array of 0 to 2 new cards '
                     'about the new point only.')
    else:
        parts.append('Reply a JSON array of 0 to 2 cards.')
    parts.append(_language_line(language))
    parts.append(_REPLY_FORMAT + ' Reply [] when nothing worth a card was said.')
    return '\n'.join(parts) + '\n\n--- JUST SAID ---\n' + str(passage or '').strip()


def ask_prompt(question: str, language: str = '', about='', has_picture=False, page_label='', current='', outline='', passage='') -> str:
    """Ryan 2026-11-21: "我反倒是需要一个询问 broccoli 的按钮…可以让我问更具体的问题，而不是简单总结"."""
    parts = ['I am in a lecture, taking notes, and ask you a question about what is in front of me now.',
             'Answer it directly and briefly (at most 8 sentences), as plain text; formulas as $…$. No preamble.']
    if has_picture:
        parts.append('The attached picture is the page of the course material open now (%s).' % (page_label or 'current page'))
    parts.append(('Answer in %s.' % language) if language else 'Answer in the language of the question.')
    text = '\n'.join(parts) + '\n\n--- MY QUESTION ---\n' + str(question or '').strip()
    if about.strip():
        text += '\n\n--- WHAT THE QUESTION IS ABOUT ---\n' + about.strip()[-NOTE_CHARS_SENT * 2:]
    context = _context(current, outline, '', passage)
    return text + ('\n\n' + context if context else '')


def answer_text(answer: str) -> str:
    """A plain answer (a question's): without a code fence around it."""
    text = str(answer or '').strip()
    fenced = re.fullmatch(r'```[a-zA-Z]*\s*\n(.*?)\n?```', text, re.S)
    return (fenced.group(1) if fenced else text).strip()


def _clean_card(item):
    if not isinstance(item, dict):
        return None
    title = str(item.get('title', '') or '').strip()
    body = str(item.get('body', '') or item.get('text', '') or '').strip()
    return {'title': title[:200], 'body': body} if (title or body) else None


def parse_reply(answer: str):
    """→ (merge, cards). The answer should be JSON; text around it is skipped. An answer that is not JSON
    at all becomes one card (its first line the title) so nothing the model said is lost."""
    text = str(answer or '').strip()
    if not text:
        return False, []
    decoder = json.JSONDecoder()
    for match in re.finditer(r'[\[{]', text):
        try:
            value, _end = decoder.raw_decode(text[match.start():])
        except ValueError:
            continue
        if isinstance(value, dict) and isinstance(value.get('cards'), list):
            value = value['cards']
        if isinstance(value, dict):
            card = _clean_card(value)
            return (bool(value.get('merge')), [card]) if card else (False, [])
        if isinstance(value, list):
            return False, [card for card in (_clean_card(item) for item in value[:6]) if card]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0].lstrip('#').strip().strip('*')[:120]
    return False, [{'title': title, 'body': '\n'.join(lines[1:])}]


# ── Broccoli's live transcript ───────────────────────────────────────────────────────────────────────
class TranscriptFollower(QObject):
    """Subscribes (a small file that is renewed while Lecture Mode is on, removed when it ends) and reads the
    sentences Broccoli appends. The file is watched, not polled."""
    sentence = pyqtSignal(str, str)      # text, 'microphone' | 'system'
    SUBSCRIBER = 'watermelon'
    RENEW_MS = 30000
    KEEP_SECONDS = 90

    def __init__(self, paths=None, parent=None):
        super().__init__(parent)
        self._paths = paths or watermelon_broccoli.live_transcript_paths
        self.file = ''
        self.subscribers = ''
        self._offset = 0
        self._recent = []
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_change)
        self._watcher.directoryChanged.connect(self._on_change)
        self._renew = QTimer(self)
        self._renew.setInterval(self.RENEW_MS)
        self._renew.timeout.connect(self._subscribe)
        self.active = False

    def start(self) -> bool:
        """False = this Broccoli has no live transcript (an older one), or Broccoli has never run here."""
        self.stop()
        found = self._paths() if callable(self._paths) else self._paths
        if not found or not found[0] or not found[1]:
            return False
        self.file, self.subscribers = found
        try:
            os.makedirs(self.subscribers, exist_ok=True)
        except OSError:
            return False
        self._offset = os.path.getsize(self.file) if os.path.exists(self.file) else 0   # only what is said from now on
        self._recent = []
        self.active = True
        self._subscribe()
        self._renew.start()
        self._watcher.addPath(os.path.dirname(self.file))
        self._watch_file()
        return True

    def stop(self):
        self._renew.stop()
        for path in self._watcher.files() + self._watcher.directories():
            self._watcher.removePath(path)
        if self.active and self.subscribers:
            target = os.path.join(self.subscribers, self.SUBSCRIBER + '.json')
            threading.Thread(target=lambda: os.path.exists(target) and os.remove(target), daemon=True).start()
        self.active = False

    def _subscribe(self):
        target = os.path.join(self.subscribers, self.SUBSCRIBER + '.json')
        threading.Thread(target=_write_json, args=(target, {'until': time.time() + self.KEEP_SECONDS}), daemon=True).start()

    def _watch_file(self):
        if self.file and os.path.exists(self.file) and self.file not in self._watcher.files():
            self._watcher.addPath(self.file)

    def _on_change(self, _path=''):
        if not self.active:
            return
        self._watch_file()             # a file cut back is a new file: watch that one
        try:
            size = os.path.getsize(self.file)
        except OSError:
            return
        if size < self._offset:
            self._offset = 0           # cut back: read it again, lines already seen are skipped below
        if size == self._offset:
            return
        try:
            with open(self.file, 'rb') as handle:
                handle.seek(self._offset)
                data = handle.read(size - self._offset)
        except OSError:
            return
        end = data.rfind(b'\n')
        if end < 0:
            return
        self._offset += end + 1
        for line in data[:end].split(b'\n'):
            try:
                item = json.loads(line.decode('utf-8'))
            except Exception:
                continue
            text = str(item.get('text', '') or '').strip() if isinstance(item, dict) else ''
            key = (item.get('t'), text) if text else None
            if not text or key in self._recent:
                continue
            self._recent = (self._recent + [key])[-400:]
            self.sentence.emit(text, str(item.get('source', '') or 'microphone'))


# ── the session: the two lines, the requests, the answers ───────────────────────────────────────────
class LectureSession(QObject):
    cards_changed = pyqtSignal(str)          # the id of a card just made ('' = something else changed)
    status_changed = pyqtSignal(str)
    voice_heard = pyqtSignal()               # a sentence came in from Broccoli's voice input
    _sent = pyqtSignal(str, bool, str)       # from the sending thread

    def __init__(self, store: CardStore, settings: LectureSettings, reply_dir: str, pages_dir: str,
                 send=None, transcript: TranscriptFollower = None, parent=None):
        super().__init__(parent)
        self.store, self.settings = store, settings
        self.reply_dir, self.pages_dir = reply_dir, pages_dir
        self._send = send or watermelon_broccoli.send
        self.transcript = transcript or TranscriptFollower(parent=self)
        self.transcript.sentence.connect(self._on_sentence)
        self.active = False
        self.document = ''
        self._note = lambda: ''
        self._page = lambda: None
        self._focus = lambda: {}             # {'current': the paragraph being written, 'outline': where in the notes}
        self._note_seen = set()              # lines of the notes already there / already sent
        self._last_passage = ''
        self._pending = {}                   # id → {kind, page, at, files}
        self._last_page_key = None
        self._page_again = False
        self._thread = ''
        self._passage = []
        self.status = ''
        self.voice_available = False
        self.last_voice_at = 0.0
        self.broccoli_missing = False         # Broccoli is not on this Mac: nothing is sent (nor tried) until it is
        self._settle = QTimer(self)
        self._settle.setSingleShot(True)
        self._settle.setInterval(PAGE_SETTLE_MS)
        self._settle.timeout.connect(self._send_page)
        self._pause = QTimer(self)
        self._pause.setSingleShot(True)
        self._pause.setInterval(VOICE_PAUSE_MS)
        self._pause.timeout.connect(self._flush_passage)
        self._note_timer = QTimer(self)
        self._note_timer.setSingleShot(True)
        self._note_timer.setInterval(NOTE_PAUSE_MS)
        self._note_timer.timeout.connect(self._send_notes)
        self._timeout = QTimer(self)
        self._timeout.setInterval(60000)
        self._timeout.timeout.connect(self._drop_old_requests)
        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_reply_folder)
        self._sent.connect(self._on_sent)

    # on / off
    def set_sources(self, note=None, page=None, focus=None):
        """Where the material comes from: note() = the whole text, page() = the page looked at (or None),
        focus() = {'current': the paragraph being written, 'outline': the headings above it}."""
        if note is not None:
            self._note = note
        if page is not None:
            self._page = page
        if focus is not None:
            self._focus = focus

    def _ensure_replies(self):
        try:
            os.makedirs(self.reply_dir, exist_ok=True)
            os.makedirs(self.pages_dir, exist_ok=True)
            if self.reply_dir not in self._watcher.directories():
                self._watcher.addPath(self.reply_dir)
        except OSError:
            logging.exception('The folder for Broccoli\'s answers could not be made.')

    def start(self, document: str, note=None, page=None, focus=None, broccoli_missing=False):
        self.set_sources(note, page, focus)
        self.broccoli_missing = bool(broccoli_missing)
        self.active = True
        self.set_document(document)
        self._ensure_replies()
        self._note_seen = self._lines(self._note())    # what is written already is never sent: only what comes now
        self.set_voice(bool(self.settings.get('voice')))
        self._set_status(_tr('Broccoli is not on this Mac: pages, speech and notes are not made into cards') if self.broccoli_missing else '')

    def stop(self):
        self.active = False
        self._settle.stop()
        self._pause.stop()
        self._note_timer.stop()
        self._passage = []
        self.transcript.stop()
        for request_id in [rid for rid, request in self._pending.items() if request['kind'] != 'ask']:
            self._finish(request_id)               # a question asked is still answered
        self._set_status('')
        self.cards_changed.emit('')

    # the note line: what is written now
    @staticmethod
    def _lines(text) -> set:
        return {line.strip() for line in str(text or '').split('\n') if line.strip()}

    _ATTACHMENT_LINE = re.compile(r'^!?\[[^\]]*\]\([^)]*\)$')

    def _new_notes(self) -> list:
        """Lines written since they were last sent — not a line that only puts an attachment in the text."""
        seen = self._note_seen
        return [line.strip() for line in str(self._note() or '').split('\n')
                if line.strip() and line.strip() not in seen and not self._ATTACHMENT_LINE.match(line.strip())]

    def note_seen(self, text):
        """Text put into the notes that is not the person's writing (a card): never sent back as new notes."""
        self._note_seen |= self._lines(text)

    def note_changed(self):
        """The notes were typed in: once the typing stops (or much was written), the new part is sent."""
        if not self.active or self.broccoli_missing:
            return
        if text_weight(''.join(self._new_notes())) >= NOTE_LONG_CHARS:
            self._send_notes()
        else:
            self._note_timer.start()

    def _send_notes(self):
        self._note_timer.stop()
        if not self.active or any(request['kind'] in ('note', 'page') for request in self._pending.values()):
            return                                 # one at a time: what is new then goes with the next one
        lines = self._new_notes()
        new = '\n'.join(lines)
        if text_weight(new) < NOTE_MIN_CHARS:
            return
        self._note_seen |= set(lines)
        focus = self._focus() or {}
        page = self._page() or {}
        titles = [card.get('title', '') for card in self.store.active(self.document)[:KNOWN_TITLES]]
        prompt = note_prompt(new, self.settings.get('language'), titles, focus.get('current', ''), focus.get('outline', ''),
                             page.get('label', ''))
        self._dispatch('note', prompt, None, _tr('Notes'))

    # a question
    def ask(self, question: str, about: str = '') -> bool:
        """A question of the person's, with what is in front of them now; the answer is a card. Works with
        Lecture Mode off too."""
        question = str(question or '').strip()
        if not question:
            return False
        self._ensure_replies()
        focus = self._focus() or {}
        page = self._page() or {}
        image = page.get('image')
        has_picture = isinstance(image, QImage) and not image.isNull()
        passage = ' '.join([self._last_passage] + list(self._passage)).strip()
        prompt = ask_prompt(question, self.settings.get('language'), about, has_picture, page.get('label', ''),
                            focus.get('current', ''), focus.get('outline', ''), passage)
        self._dispatch('ask', prompt, image.copy() if has_picture else None, _tr('Question'), question=question)
        return True

    def set_document(self, document: str):
        document = str(document or '')
        if document == self.document and self._thread:
            return
        self.document = document
        self._thread = 'lecture/%s/%s' % (document, datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
        self._last_page_key = None
        self._passage = []
        self._pause.stop()
        self.cards_changed.emit('')

    def set_voice(self, on: bool):
        self.settings.set('voice', bool(on))
        if on and self.active and not self.broccoli_missing:
            self.voice_available = self.transcript.start()
        else:
            self.transcript.stop()
            self._pause.stop()
            self._passage = []
        self.cards_changed.emit('')

    def _set_status(self, text):
        if text != self.status:
            self.status = text
            self.status_changed.emit(text)

    # the page line
    def page_turned(self):
        """The page being looked at changed (or a new one was added): send it once it stays."""
        if self.active and not self.broccoli_missing:
            self._settle.start()

    def _send_page(self, force=False):
        if not self.active:
            return
        if any(request['kind'] == 'page' for request in self._pending.values()):
            self._page_again = True          # one page at a time: the newest goes when this one is answered
            return
        self._page_again = False
        page = self._page() or {}
        image = page.get('image')
        if not isinstance(image, QImage) or image.isNull():
            return                                 # no page to look at: the note line does the rest
        key = page.get('key')
        if not force and key is not None and key == self._last_page_key:
            return
        self._last_page_key = key
        lines = self._new_notes()                  # what was written since: goes along, and counts as sent
        self._note_seen |= set(lines)
        self._note_timer.stop()
        focus = self._focus() or {}
        titles = [card.get('title', '') for card in self.store.active(self.document)[:KNOWN_TITLES]]
        prompt = page_prompt(page.get('label', ''), self.settings.get('language'), titles, True, focus.get('current', ''),
                             focus.get('outline', ''), '\n'.join(lines))
        self._dispatch('page', prompt, image.copy(), page.get('label', ''))

    # the voice line
    def _on_sentence(self, text, _source):
        if not self.active or self.broccoli_missing:
            return
        self.last_voice_at = time.time()
        self.voice_heard.emit()
        self._passage.append(text)
        if sum(len(part) for part in self._passage) >= VOICE_PASSAGE_CHARS:
            self._flush_passage()
        else:
            self._pause.start()

    def _flush_passage(self):
        self._pause.stop()
        passage = ' '.join(self._passage).strip()
        if passage and self.active and sum(1 for r in self._pending.values() if r['kind'] == 'voice') >= VOICE_IN_FLIGHT:
            # Broccoli is behind: what is said meanwhile is kept and goes with the next passage (its newest part), so
            # requests never pile up and the cards stay with the talk (Ryan 2026-11-21: "非常慢…几乎没有实时的卡片")
            self._passage = [passage[-NOTE_CHARS_SENT:]]
            return
        self._passage = []
        if not passage or not self.active:
            return
        self._last_passage = passage
        last = next((card for card in self.store.active(self.document) if card.get('source') == 'voice'), None)
        if last is not None and self._age(last) > VOICE_MERGE_SECONDS:
            last = None                            # an older card is not offered for merging: the talk has moved on
        self._dispatch('voice', voice_prompt(passage, self.settings.get('language'), last), None, '',
                       merge_into=last['id'] if last else '')

    @staticmethod
    def _age(card) -> float:
        stamp = card.get('updated') or card.get('created') or ''
        try:
            return time.time() - datetime.datetime.fromisoformat(stamp).timestamp()
        except ValueError:
            return float('inf')

    # sending and the answers
    def _dispatch(self, kind, prompt, image, page_label, merge_into='', question=''):
        request_id = uuid.uuid4().hex
        picture = os.path.join(self.pages_dir, request_id + '.png') if image is not None else ''
        self._pending[request_id] = {'kind': kind, 'page': page_label, 'at': time.time(), 'merge_into': merge_into,
                                     'files': [picture] if picture else [], 'document': self.document, 'question': question}
        self._timeout.start()
        self._set_status(_tr('Asking Broccoli…'))
        title = 'Lecture · %s' % (self.document or 'Watermelon')
        # no "thread": every request is a conversation of its own in Broccoli (its Watermelon group), without the
        # memory of the earlier ones — one long conversation kept pulling the cards back to what was said before
        # (Ryan 2026-11-21: "卡片总是把前面的记忆影响过来，导致人感觉一直在说一个事情，但是实际上已经往前了")
        extra = {'id': request_id, 'reply_to': self.reply_dir}
        send = self._send

        def work():
            try:
                if picture:
                    image.save(picture, 'PNG')
                    extra['attachments'] = [picture]
                ok, detail = send(prompt, title=title, metadata={'watermelon_lecture': kind}, extra=extra)
            except Exception as error:
                logging.exception('Sending a lecture request to Broccoli failed.')
                ok, detail = False, str(error)
            self._sent.emit(request_id, bool(ok), str(detail))

        threading.Thread(target=work, daemon=True, name='watermelon-lecture-send').start()

    def _on_sent(self, request_id, ok, detail):
        request = self._pending.get(request_id)
        if request is None:
            return
        if ok:
            self._set_status(_tr('Broccoli is thinking…'))
            self._on_reply_folder()          # an answer that was written before this was noticed
            return
        self._finish(request_id)
        if request['kind'] == 'page':
            self._last_page_key = None       # the same page may be tried again
        self._set_status(_tr('Broccoli is not on this Mac') if detail == 'not_installed' else _tr("Couldn't reach Broccoli"))

    def _on_reply_folder(self, _path=''):
        try:
            names = os.listdir(self.reply_dir)
        except OSError:
            return
        for name in names:
            if not name.endswith('.json'):
                continue
            path = os.path.join(self.reply_dir, name)
            request_id = name[:-5]
            if request_id not in self._pending:
                try:
                    if time.time() - os.path.getmtime(path) > REPLY_TIMEOUT_SECONDS:
                        os.remove(path)      # an answer nobody waits for any more
                except OSError:
                    pass
                continue
            data = _read_json(path, {})
            try:
                os.remove(path)
            except OSError:
                pass
            self._on_reply(request_id, data)

    def _on_reply(self, request_id, data):
        request = self._pending.get(request_id) or {}
        self._finish(request_id)
        failed = str(data.get('status', '')) == 'failed'
        if request.get('kind') == 'ask':
            answer = answer_text(data.get('answer', '')) if not failed else ''
            merge, cards = False, ([{'title': request.get('question', ''), 'body': answer}] if answer else [])
        else:
            merge, cards = parse_reply(data.get('answer', '')) if not failed else (False, [])
        made = ''
        if request.get('document', '') == self.document or not self.active or request.get('kind') == 'ask':
            target = self.store.find(request.get('merge_into', '')) if merge else None
            if target is not None and not target.get('archived') and cards:
                self.store.update(target['id'], title=cards[0]['title'] or target['title'], body=cards[0]['body'],
                                  updated=datetime.datetime.now().isoformat(timespec='seconds'))
                made = target['id']
            else:
                for card in reversed(cards):
                    made = self.store.add(card['title'], card['body'], page=request.get('page', ''),
                                          source=request.get('kind', 'page'), document=request.get('document', ''))['id']
        if str(data.get('status', '')) == 'failed':
            self._set_status(_tr("Broccoli couldn't answer"))
        elif not self._pending:
            self._set_status('' if cards else _tr('Nothing new on this page') if request.get('kind') == 'page' else '')
        self.cards_changed.emit(made)
        if self._page_again and self.active:
            self._send_page()
        elif self.active and request.get('kind') in ('note', 'page') and self._new_notes():
            self._note_timer.start()               # notes written while this was answered
        if self.active and request.get('kind') == 'voice' and self._passage and not self._pause.isActive():
            self._pause.start()                    # speech gathered while Broccoli was behind

    def _finish(self, request_id):
        request = self._pending.pop(request_id, None)
        if request:
            self._remove_files(request.get('files'))
        if not self._pending:
            self._timeout.stop()

    @staticmethod
    def _remove_files(paths):
        paths = [path for path in (paths or []) if path]
        if paths:
            threading.Thread(target=lambda: [os.path.exists(p) and os.remove(p) for p in paths], daemon=True).start()

    def _drop_old_requests(self):
        now = time.time()
        old = [rid for rid, request in self._pending.items() if now - request['at'] > REPLY_TIMEOUT_SECONDS]
        for request_id in old:
            self._finish(request_id)
        if old and not self._pending:
            self._set_status(_tr("Broccoli couldn't answer"))

    def busy(self) -> bool:
        return bool(self._pending)


# ── the panel ────────────────────────────────────────────────────────────────────────────────────────
_TEXT = QColor('#1D1D1F')          # the panel is the light glass (Ryan 2026-11-21: "浅色的")
_TEXT_SOFT = QColor('#3A3A3C')
_TEXT_FAINT = QColor('#6E6E73')
_RED = QColor('#E5484D')
_VEIL = QColor(0, 0, 0, 16)


def _plain(text: str) -> str:
    """Markdown marks taken out for showing on a card (the note gets the original)."""
    text = re.sub(r'\*\*(.+?)\*\*|__(.+?)__', lambda m: m.group(1) or m.group(2), str(text or ''))
    text = re.sub(r'(?m)^\s{0,3}(?:#{1,6}\s+|[-*+]\s+|>\s?)', '', text)
    return text.replace('`', '').strip()


class _Glyph(QWidget):
    """A small line-drawn button of the panel's top row (22 high; hover = a rounded veil, like a list row)."""
    clicked = pyqtSignal()

    def __init__(self, kind, tip='', parent=None):
        super().__init__(parent)
        self.kind = kind
        self.on = True            # drawn at full strength
        self.lit = False          # drawn in red (the voice line is hearing something)
        self.selected = False     # the veil stays (the page it opens is shown)
        self._hover = False
        self.setFixedSize(20, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tip)

    def set_state(self, on=None, lit=None, selected=None, kind=None):
        before = (self.on, self.lit, self.selected, self.kind)
        self.on = self.on if on is None else bool(on)
        self.lit = self.lit if lit is None else bool(lit)
        self.selected = self.selected if selected is None else bool(selected)
        self.kind = self.kind if kind is None else kind
        if before != (self.on, self.lit, self.selected, self.kind):
            self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._hover or self.selected:
            veil = QPainterPath()
            veil.addRoundedRect(QRectF(self.rect()), 7, 7)
            painter.fillPath(veil, _VEIL)
        color = QColor(_RED if self.lit else _TEXT)
        color.setAlpha(255 if self.on else 90)
        pen = QPen(color, 1.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        if self.kind == 'now':                       # a four-pointed spark
            path = QPainterPath()
            path.moveTo(cx, cy - 6.5)
            path.quadTo(cx + 1.2, cy - 1.2, cx + 6.5, cy)
            path.quadTo(cx + 1.2, cy + 1.2, cx, cy + 6.5)
            path.quadTo(cx - 1.2, cy + 1.2, cx - 6.5, cy)
            path.quadTo(cx - 1.2, cy - 1.2, cx, cy - 6.5)
            painter.drawPath(path)
        elif self.kind == 'voice':                   # a microphone (struck through when off)
            painter.drawRoundedRect(QRectF(cx - 2.6, cy - 7, 5.2, 9), 2.6, 2.6)
            painter.drawArc(QRectF(cx - 5, cy - 4.5, 10, 9.5), 180 * 16, 180 * 16)
            painter.drawLine(QPointF(cx, cy + 5), QPointF(cx, cy + 7.5))
            if not self.on:
                painter.drawLine(QPointF(cx - 6, cy - 6.5), QPointF(cx + 6, cy + 6.5))
        elif self.kind == 'shot':                    # a camera
            painter.drawRoundedRect(QRectF(cx - 7, cy - 4, 14, 10), 2.2, 2.2)
            painter.drawLine(QPointF(cx - 2.5, cy - 4), QPointF(cx - 1.2, cy - 6.2))
            painter.drawLine(QPointF(cx - 1.2, cy - 6.2), QPointF(cx + 1.2, cy - 6.2))
            painter.drawLine(QPointF(cx + 1.2, cy - 6.2), QPointF(cx + 2.5, cy - 4))
            painter.drawEllipse(QPointF(cx, cy + 1), 2.6, 2.6)
        elif self.kind == 'archive':                 # a box with its lid
            painter.drawRoundedRect(QRectF(cx - 7, cy - 6, 14, 4), 1.2, 1.2)
            painter.drawRoundedRect(QRectF(cx - 6, cy - 2, 12, 8), 1.2, 1.2)
            painter.drawLine(QPointF(cx - 2, cy + 1.2), QPointF(cx + 2, cy + 1.2))
        painter.end()


class _Card(QWidget):
    """One knowledge point. Click = show all of it / fold it again; drag = take it into the note; the small
    box in its corner (while the pointer is on it) = archive. Right click = the system menu."""
    menu_requested = pyqtSignal(dict, object)
    archive_clicked = pyqtSignal(dict)
    insert_clicked = pyqtSignal(dict)
    used = pyqtSignal(dict)          # dropped into the note (or anywhere in this app that took it)
    FOLDED_BODY_LINES = 4

    def __init__(self, card, width, parent=None):
        super().__init__(parent)
        self.card = dict(card)
        self.expanded = False
        self._hover = False
        self._press = None
        self._reveal = 1.0
        self._animation = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFixedWidth(width)
        self._measure()

    # layout
    def _fonts(self):
        tag, title, body = QFont(self.font()), QFont(self.font()), QFont(self.font())
        tag.setPixelSize(10)
        title.setPixelSize(12)
        title.setBold(True)
        body.setPixelSize(11)
        return tag, title, body

    def _lines(self, text, font, width, limit):
        """The text broken into lines of this width; with a limit the last line ends in …"""
        layout = QTextLayout(text, font)
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(option)
        lines = []
        layout.beginLayout()
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(width)
            lines.append(text[line.textStart():line.textStart() + line.textLength()].rstrip('\n'))
        layout.endLayout()
        if limit and len(lines) > limit:
            rest = ''.join(lines[limit - 1:]).replace('\n', ' ')
            lines = lines[:limit - 1] + [QFontMetrics(font).elidedText(rest, Qt.TextElideMode.ElideRight, int(width))]
        return lines

    def _measure(self):
        tag, title, body = self._fonts()
        inner = self.width() - 16
        self._title_lines = self._lines(_plain(self.card.get('title', '')), title, inner, 0 if self.expanded else 2)
        self._body_lines = []
        for paragraph in _plain(self.card.get('body', '')).split('\n'):
            if paragraph.strip():
                self._body_lines += self._lines(paragraph.strip(), body, inner, 0)
        if not self.expanded and len(self._body_lines) > self.FOLDED_BODY_LINES:
            last = self._body_lines[self.FOLDED_BODY_LINES - 1]
            self._body_lines = self._body_lines[:self.FOLDED_BODY_LINES - 1] + [
                QFontMetrics(body).elidedText(last + ' …' * 40, Qt.TextElideMode.ElideRight, inner)]
        self._heights = (14, QFontMetrics(title).lineSpacing(), QFontMetrics(body).lineSpacing() + 1)
        self._full = 8 + 14 + 2 + len(self._title_lines) * self._heights[1] + (4 if self._body_lines else 0) \
            + len(self._body_lines) * self._heights[2] + 9
        self.setFixedHeight(max(1, int(round(self._full * self._reveal))))

    def set_width(self, width):
        if width != self.width():
            self.setFixedWidth(width)
            self._measure()
            self.update()

    def slide_in(self):
        """A card just made: it opens downwards from nothing while the ones below move down."""
        self._reveal = 0.0
        self.setFixedHeight(1)
        animation = QVariantAnimation(self)
        animation.setDuration(260)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        def step(value):
            self._reveal = float(value)
            self.setFixedHeight(max(1, int(round(self._full * self._reveal))))
            self.update()

        animation.valueChanged.connect(step)
        animation.finished.connect(lambda: step(1.0))
        self._animation = animation
        animation.start()

    def tag_text(self) -> str:
        created = str(self.card.get('created', ''))[11:16]
        if self.card.get('source') == 'voice':
            head = _tr('Voice')
        elif self.card.get('source') == 'ask':
            head = _tr('Question')
        else:
            head = self.card.get('page', '') or _tr('Notes')
        return ('%s · %s' % (head, created)) if created else head

    # the pointer
    def _archive_rect(self):
        return QRectF(self.width() - 22, 4, 18, 18)

    def _insert_rect(self):
        """Left of the archive box: put the card into the note (Ryan 2026-11-21: "在卡片上表面加一个插入的按钮，
        可以左边插入右边 archive")."""
        return QRectF(self.width() - 42, 4, 18, 18)

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
        if self._press is None or not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.position().toPoint() - self._press).manhattanLength() < QApplication.startDragDistance():
            return
        self._press = None
        drag = QDrag(self)
        data = QMimeData()
        data.setText('\n\n' + card_markdown(self.card) + '\n\n')
        drag.setMimeData(data)
        picture = self.grab()
        drag.setPixmap(picture)
        drag.setHotSpot(QPoint(picture.width() // (2 * max(1, int(picture.devicePixelRatio()))), 12))
        self._after_drop(drag.exec(Qt.DropAction.CopyAction), drag.target())

    def _after_drop(self, result, target):
        """Taken by a place in this app (the note): the card is used — it goes to the archive."""
        if result != Qt.DropAction.IgnoreAction and target is not None:
            self.used.emit(self.card)

    def mouseReleaseEvent(self, event):
        pressed, self._press = self._press, None
        if event.button() != Qt.MouseButton.LeftButton or pressed is None:
            return
        if self._archive_rect().contains(QPointF(event.position())):
            self.archive_clicked.emit(self.card)
            return
        if self._insert_rect().contains(QPointF(event.position())):
            self.insert_clicked.emit(self.card)
            return
        self.expanded = not self.expanded
        self._measure()
        self.update()

    def contextMenuEvent(self, event):
        self.menu_requested.emit(self.card, event.globalPos())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(max(0.0, min(1.0, self._reveal)))
        shape = QPainterPath()
        shape.addRoundedRect(QRectF(0.5, 0.5, self.width() - 1, max(1.0, self.height() - 1.0)), CARD_RADIUS, CARD_RADIUS)
        painter.fillPath(shape, QColor(255, 255, 255, 200 if self._hover else 150))
        painter.setClipPath(shape)
        painter.translate(0, -(1.0 - self._reveal) * 14)
        tag, title, body = self._fonts()
        y = 8
        painter.setFont(tag)
        painter.setPen(_TEXT_FAINT)
        tag_text = QFontMetrics(tag).elidedText(self.tag_text(), Qt.TextElideMode.ElideMiddle, self.width() - 16 - (40 if self._hover else 0))
        painter.drawText(QRectF(8, y, self.width() - 16, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tag_text)
        y += 16
        painter.setFont(title)
        painter.setPen(_TEXT)
        for line in self._title_lines:
            painter.drawText(QRectF(8, y, self.width() - 16, self._heights[1]), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, line)
            y += self._heights[1]
        if self._body_lines:
            y += 4
        painter.setFont(body)
        painter.setPen(_TEXT_SOFT)
        for line in self._body_lines:
            painter.drawText(QRectF(8, y, self.width() - 16, self._heights[2]), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, line)
            y += self._heights[2]
        if self._hover and self._reveal >= 1.0:      # the archive box (out again for an archived card)
            box = self._archive_rect()
            pen = QPen(_TEXT, 1.2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            cx, cy = box.center().x(), box.center().y()
            painter.drawRoundedRect(QRectF(cx - 5.5, cy - 5, 11, 3.2), 1, 1)
            painter.drawRoundedRect(QRectF(cx - 4.7, cy - 1.8, 9.4, 6.6), 1, 1)
            if self.card.get('archived'):
                painter.drawLine(QPointF(cx, cy + 3), QPointF(cx, cy - 0.2))
                painter.drawLine(QPointF(cx - 1.6, cy + 1.2), QPointF(cx, cy - 0.4))
                painter.drawLine(QPointF(cx + 1.6, cy + 1.2), QPointF(cx, cy - 0.4))
            box = self._insert_rect()                 # ←| : into the note, which is on the left
            cx, cy = box.center().x(), box.center().y()
            painter.drawLine(QPointF(cx - 5.5, cy - 5), QPointF(cx - 5.5, cy + 5))
            painter.drawLine(QPointF(cx - 4, cy), QPointF(cx + 5.5, cy))
            painter.drawLine(QPointF(cx - 4, cy), QPointF(cx - 0.8, cy - 3.2))
            painter.drawLine(QPointF(cx - 4, cy), QPointF(cx - 0.8, cy + 3.2))
        painter.end()


class _LightGreyButton(MacNormalButton):
    """The grey normal button in its light set whatever the system's appearance (it stands on the light glass)."""
    _TO_LIGHT = (('#404145', '#E7E7E7'), ('#4A4B4F', '#EEEEEE'), ('#343538', '#DCDCDC'), ('#2F3033', '#E1E1E1'),
                 ('#FFFFFF', '#111111'))

    def update_theme(self):
        super().update_theme()
        sheet = self.styleSheet()
        if '#404145' in sheet:
            self._updating_style = True
            try:
                for dark, light in self._TO_LIGHT:
                    sheet = sheet.replace(dark, light)
                self.setStyleSheet(sheet)
            finally:
                self._updating_style = False


class LecturePanel(QWidget):
    """The cards, newest on top. A Liquid Glass panel, always the light glass, as wide as the empty strip
    right of the editing column (never on the column), like the list on the left. Its top row: the voice
    line · the archive. Questions are asked from the right-click menus (a card's, the editor's) in AskDialog
    (Ryan 2026-11-21: "右侧底下的 ask 就去掉吧，能右键菜单就不要再多加入口了")."""
    insert_requested = pyqtSignal(str)       # a card's Markdown, to be put at the cursor
    show_requested = pyqtSignal(dict)        # a card made from a mark of an attachment: show that place
    ask_requested = pyqtSignal(str)          # the card's right-click "Ask About This Card…" (what it is about)
    clear_archive_requested = pyqtSignal()

    def __init__(self, session: LectureSession, parent=None):
        super().__init__(parent)
        self.session = session
        self.store = session.store
        self.settings = session.settings
        self.showing_archive = False
        self._cards = []
        self.setFixedWidth(PANEL_WIDTH)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(4)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(1)
        self.btn_voice = _Glyph('voice', '', self)
        self.btn_archive = _Glyph('archive', _tr('Archived cards'), self)
        row.addWidget(self.btn_voice)
        row.addStretch(1)
        row.addWidget(self.btn_archive)
        outer.addLayout(row)
        self.status_label = QLabel('', self)
        self.status_label.setStyleSheet('color: #6E6E73; font-size: 10px; background: transparent;')
        self.status_label.setFixedHeight(14)
        outer.addWidget(self.status_label)
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
        self._list.setContentsMargins(0, 0, 0, 0)
        self._list.setSpacing(6)
        self._list.addStretch(1)
        self._scroll.setWidget(self._holder)
        self._scroll.viewport().installEventFilter(self)
        outer.addWidget(self._scroll, 1)
        self.empty_label = QLabel('', self._holder)
        self.empty_label.setWordWrap(True)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.empty_label.setStyleSheet('color: #6E6E73; font-size: 11px; background: transparent; padding: 12px 2px;')
        self._list.insertWidget(0, self.empty_label)
        self.btn_clear = _LightGreyButton(_tr('Clear All'), self)
        self.btn_clear.clicked.connect(self.clear_archive_requested.emit)
        self.btn_clear.hide()
        outer.addWidget(self.btn_clear)

        self.btn_voice.clicked.connect(lambda: session.active and session.set_voice(not self.settings.get('voice')))
        self.btn_archive.clicked.connect(lambda: self.show_archive(not self.showing_archive))
        session.cards_changed.connect(self.refresh)
        session.status_changed.connect(lambda _text: self._show_status())
        session.voice_heard.connect(self._on_voice_heard)
        self._voice_fade = QTimer(self)
        self._voice_fade.setSingleShot(True)
        self._voice_fade.setInterval(8000)
        self._voice_fade.timeout.connect(self._show_voice)
        self.refresh('')

    # size
    def card_width(self) -> int:
        """As wide as the list's visible part: when the system shows a scroll bar the cards get narrower
        instead of being cut by it."""
        viewport = self._scroll.viewport().width()
        return max(60, min(PANEL_WIDTH - 16, viewport if viewport > 0 else PANEL_WIDTH - 16))

    def eventFilter(self, obj, event):
        if obj is self._scroll.viewport() and event.type() == QEvent.Type.Resize:
            width = self.card_width()
            for card in self._cards:
                card.set_width(width)
        return super().eventFilter(obj, event)

    def _gate_glass_now(self):
        """New cards are kept out of the window at once — not on the next turn of the event loop: a card's
        first frames (its slide-in) otherwise land in the window under the glass, and the glass shows them
        blurred, as a white haze (2026-11-21)."""
        helper = getattr(self, '_broccoli_inwindow_glass', None)
        if helper is not None and helper.active:
            helper.gate_new_children()

    # a card used
    def insert_card(self, card):
        """Into the note at the cursor; a card that was put into the note goes to the archive (Ryan 2026-11-21:
        "右边卡片插入了之后可以自动 archive")."""
        self.insert_requested.emit(card_markdown(card))
        self._card_used(card)

    def _card_used(self, card):
        self.session.note_seen(card_markdown(card))   # the card's words in the note are not new notes to send back
        if not card.get('archived'):
            self.store.update(card['id'], archived=True)
            self.refresh('')

    # what is shown
    def show_archive(self, on: bool):
        self.showing_archive = bool(on)
        self.refresh('')

    def shown_cards(self) -> list:
        return self.store.archived() if self.showing_archive else self.store.active(self.session.document)

    def refresh(self, new_id=''):
        cards = self.shown_cards()
        for widget in self._cards:
            self._list.removeWidget(widget)
            widget.hide()           # gone now, not at the next turn: the glass image is drawn before that (old and
            widget.setParent(None)  # new cards on top of each other)
            widget.deleteLater()
        self._cards = []
        for position, card in enumerate(cards):
            widget = _Card(card, self.card_width(), self._holder)
            widget.menu_requested.connect(self._card_menu)
            widget.archive_clicked.connect(self._toggle_archived)
            widget.used.connect(self._card_used)
            widget.insert_clicked.connect(self.insert_card)
            self._list.insertWidget(position + 1, widget)
            self._cards.append(widget)
            if new_id and card['id'] == new_id and self.isVisible():
                widget.slide_in()
        self._gate_glass_now()
        if self.showing_archive:
            self.empty_label.setText(_tr('No archived cards'))
        else:
            self.empty_label.setText(_tr('Cards appear here: what you highlighted or commented in the attachments, and the key points of Lecture Mode.'))
        self.empty_label.setVisible(not cards)
        self.btn_archive.set_state(selected=self.showing_archive)
        self.btn_clear.setVisible(self.showing_archive and bool(cards))
        self._show_voice()
        self._show_status()
        if new_id:
            self._scroll.verticalScrollBar().setValue(0)

    def _show_status(self):
        if self.showing_archive:
            text = _tr('Archived') + ' (%d)' % len(self.store.archived())
        else:
            text = self.session.status
            if not text and self.settings.get('voice') and self.session.voice_available and self._voice_fade.isActive():
                text = _tr('Voice is being sent to Broccoli')
        metrics = QFontMetrics(self.status_label.font())
        self.status_label.setText(metrics.elidedText(text, Qt.TextElideMode.ElideRight, max(40, PANEL_WIDTH - 18)))
        self.status_label.setToolTip(text)

    def _show_voice(self):
        lecture = bool(self.session.active)
        on = bool(self.settings.get('voice')) and lecture and not self.session.broccoli_missing
        hearing = on and self._voice_fade.isActive()
        self.btn_voice.set_state(on=on, lit=hearing)
        if not lecture:
            tip = _tr('Lecture Mode is off (turn it on in the menu bar menu)')
        elif self.session.broccoli_missing:
            tip = _tr('Broccoli is not on this Mac: the voice line needs it.')
        elif not on:
            tip = _tr('Voice line off: what Broccoli hears is not used. Click to turn on.')
        elif not self.session.voice_available:
            tip = _tr('Voice line on, but this Broccoli has no live transcript yet (update Broccoli).')
        else:
            tip = _tr('Voice line on: while Broccoli\'s voice input runs, what is said is sent to Broccoli for cards. Click to turn off.')
        self.btn_voice.setToolTip(tip)

    def _on_voice_heard(self):
        self._voice_fade.start()
        self._show_voice()
        self._show_status()

    # a card's actions
    def _toggle_archived(self, card):
        self.store.update(card['id'], archived=not card.get('archived'))
        self.refresh('')

    def _card_menu(self, card, where):
        menu = QMenu(self)
        style_broccoli_context_menu(menu)
        show = menu.addAction(_tr('Show in Attachment')) if card.get('file') else None
        ask = menu.addAction(_tr('Ask About This Card…'))
        insert = menu.addAction(_tr('Insert into Note'))
        copy = menu.addAction(_tr('Copy'))
        menu.addSeparator()
        archive = menu.addAction(_tr('Restore') if card.get('archived') else _tr('Archive'))
        delete = menu.addAction(_tr('Delete'))
        chosen = menu.exec(where)
        if chosen is None:
            return
        if chosen is show:
            self.show_requested.emit(card)
        elif chosen is ask:
            self.ask_requested.emit(card_markdown(card))
        elif chosen is insert:
            self.insert_card(card)
        elif chosen is copy:
            QApplication.clipboard().setText(card_markdown(card))
        elif chosen is archive:
            self._toggle_archived(card)
        elif chosen is delete:
            self.store.remove(card['id'])
            self.refresh('')

    # look
    def showEvent(self, event):
        super().showEvent(event)
        try:
            if getattr(self, '_broccoli_inwindow_glass', None) is None:
                attach_inwindow_liquid_glass(self, lambda w=self: float(PANEL_RADIUS), lambda w=self: False)
        except RuntimeError:
            pass

    def paintEvent(self, event):
        if getattr(self, '_liquid_glass_active', False) or getattr(self, '_glass_foreground_pass', False):
            return
        painter = QPainter(self)          # no system glass: the same shape, light and nearly solid
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), PANEL_RADIUS, PANEL_RADIUS)
        painter.fillPath(path, QColor(246, 246, 246, 238))
        painter.setPen(QColor(0, 0, 0, 30))
        painter.drawPath(path)
        painter.end()


class AskDialog(QWidget):
    """A question for Broccoli (an edit dialog, style book 5.7: the window is the card — window glass, corner
    16; a grey line saying what it is about, a normal input, grey normal buttons Cancel / Ask). Return = Ask,
    Esc = Cancel. Opened from the right-click menus only."""
    asked = pyqtSignal(str, str)          # question, what it is about

    def __init__(self, about: str = '', parent=None):
        super().__init__(parent)
        import watermelon_ui
        watermelon_ui.make_glass_dialog(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle(_tr('Ask Broccoli'))
        self.about = str(about or '').strip()
        dark = glass_kit.is_dark_theme(glass_kit.app)
        colour = '#F2F2F7' if dark else '#20242B'
        box = QVBoxLayout(self)
        box.setContentsMargins(20, 18, 20, 16)
        box.setSpacing(10)
        title = QLabel(_tr('Ask Broccoli'), self)
        title.setStyleSheet('font-size: 13px; font-weight: 600; color: %s; background: transparent;' % colour)
        box.addWidget(title)
        hint = ' '.join(_plain(self.about).split())
        self.about_label = QLabel(_tr('About: %s') % hint if hint else _tr('About what is in front of you now: this page, what was just said, the paragraph you are writing.'), self)
        self.about_label.setWordWrap(True)
        self.about_label.setMaximumHeight(52)
        self.about_label.setStyleSheet('font-size: 12px; color: #8E8E93; background: transparent;')
        self.about_label.setToolTip(self.about)
        box.addWidget(self.about_label)
        self.question = QLineEdit(self)
        self.question.setFixedHeight(22)
        self.question.setPlaceholderText(_tr('Your question'))
        self.question.setStyleSheet(glass_kit._settings_lineedit_stylesheet(dark))
        self.question.returnPressed.connect(self._ask)
        box.addWidget(self.question)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addStretch(1)
        self.btn_cancel = MacNormalButton(_tr('Cancel'), self)
        self.btn_cancel.setMinimumWidth(96)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_ask = MacNormalButton(_tr('Ask'), self)
        self.btn_ask.setMinimumWidth(96)
        self.btn_ask.clicked.connect(self._ask)
        row.addWidget(self.btn_cancel)
        row.addWidget(self.btn_ask)
        box.addLayout(row)
        self.resize(520, self.sizeHint().height())

    def _ask(self):
        question = self.question.text().strip()
        if question:
            self.asked.emit(question, self.about)
            self.close()

    def showEvent(self, event):
        super().showEvent(event)
        self.question.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)


import watermelon_ui as _watermelon_ui  # noqa: E402  (after the class: the dialog's glass and placing)
_watermelon_ui.install_glass_dialog_class(AskDialog)
