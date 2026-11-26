# -*- coding: utf-8 -*-
"""Write Here with Broccoli (2026-11-25) — the SAME file in Watermelon/build and Strawberry/0-main; keep them identical.

Ryan 2026-11-25: "让 broccoli 在此处续写，然后和 ask 差不多，也是把内容加为背景，然后弹出 broccoli 窗口，用户输入写作需求，
然后完成之后 broccoli 内有记录，而且还自动把输出的内容 type 到对应的 watermelon 的位置。可以参考小圆点打字的 type 方式。"

How it goes:
1. The app hands the whole text to Broccoli with MARKER at the spot (Broccoli's door: "stage" + "write_back", with
   "reply_to" and "id"). Broccoli comes out with a blank conversation, the text in its attachment tray, the cursor in
   its prompt. Nothing runs.
2. The person says there what to write. Broccoli answers in that conversation (it stays in Broccoli's history) and,
   when the answer is finished, writes <reply folder>/<id>.json {status, answer}.
3. WriteBack (here) notices the file and types the answer into the editor at the remembered spot, a few characters at
   a time — like the circle's dictation, which types into another app about 20 characters per step. Here the app
   types into its own editor, so the text lands at the spot even when the cursor has moved since, the app is
   behind Broccoli, or another note is open (then it waits until that note is opened again). One ⌘Z takes it out.

No file reading or network here blocks the window: the reply file is tiny and only looked for once a second while a
request is open.
"""
import json
import logging
import math
import os
import re
import time
import uuid

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCursor

MARKER = '⟦WRITE HERE⟧'
SNIPPET = 80                 # characters kept on each side of the spot, to find it again after the note was reloaded
POLL_MS = 1000
STEP_MS = 30                 # one typing step
STEPS = 40                   # an answer is typed in at most about this many steps (≈ 1.2 s)
KEEP_REPLIES_SECONDS = 2 * 24 * 3600
FINISHED = ('finished', 'completed', 'done', 'success', 'succeeded', 'ok')


def material(text, position):
    """The text with MARKER at `position` (a Python index)."""
    text = str(text or '')
    position = max(0, min(int(position), len(text)))
    return text[:position] + MARKER + text[position:]


def to_qt(text, index):
    """Python index → position in a QTextDocument (Qt counts UTF-16 units: an emoji is 2)."""
    return len(str(text)[:max(0, int(index))].encode('utf-16-le')) // 2


def to_py(text, position):
    """Position in a QTextDocument → Python index."""
    text = str(text)
    units = 0
    for index, char in enumerate(text):
        if units >= position:
            return index
        units += 2 if ord(char) > 0xFFFF else 1
    return len(text)


def locate(text, guess, before, after):
    """Where the spot is in `text` now (Python index), or None. `guess` = where the anchored cursor is (or None)."""
    if guess is not None and 0 <= guess <= len(text) and text[max(0, guess - len(before)):guess] == before \
            and text[guess:guess + len(after)] == after:
        return guess
    if before or after:
        both = text.find(before + after)
        if both >= 0 and (before + after):
            return both + len(before)
    if guess is not None and 0 <= guess <= len(text) and before and text[max(0, guess - len(before)):guess] == before:
        return guess                                      # what came after was changed: the spot itself is still right
    for piece, end in ((before, True), (after, False)):
        if len(piece) < 12:                               # too short to be sure it is the same spot
            continue
        found, start = [], text.find(piece)
        while start >= 0:
            found.append(start + (len(piece) if end else 0))
            start = text.find(piece, start + 1)
        if found:
            return min(found, key=lambda at: abs(at - (guess or 0)))
    return None


class WriteBack(QObject):
    """Open "write here" requests of one app: where each goes, the reply file, the typing.

    current_key(): which document is open now (Watermelon: 'notes:<id>' / 'file:<path>'); current_edit(key): the
    editor of that document when it is open, else None (Strawberry has one editor per kind of note)."""
    typed = pyqtSignal(str, int)          # key, characters typed in
    waiting = pyqtSignal(str)             # key: finished, but that document is not open — typed when it is
    dropped = pyqtSignal(str)             # status: Broccoli did not write anything (cancelled / failed / empty)

    def __init__(self, reply_dir, current_key, current_edit, parent=None):
        super().__init__(parent)
        self.reply_dir = reply_dir
        self.current_key = current_key
        self.current_edit = current_edit
        self.requests = {}                # id → {'key', 'cursor', 'before', 'after', 'answer' (when it came)}
        # Optional (2026-11-26, Strawberry): transform(key, answer) → the text to type. The app's own look at a
        # finished answer just before it is typed into the open document (e.g. taking a list of sources off its
        # end). It may change the document; the spot is found again afterwards. None = the answer as it came.
        self.transform = None
        self._typing = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(POLL_MS)
        self._poll_timer.timeout.connect(self.poll)
        self._type_timer = QTimer(self)
        self._type_timer.setInterval(STEP_MS)
        self._type_timer.timeout.connect(self._type_step)

    # ── asking ──
    def begin(self, edit, position, key):
        """Remember the spot (Qt position in `edit`) → the request id to send to Broccoli."""
        text = edit.toPlainText()
        index = to_py(text, position)
        cursor = QTextCursor(edit.document())
        cursor.setPosition(max(0, min(int(position), edit.document().characterCount() - 1)))
        request_id = 'wb-%s-%s' % (time.strftime('%Y%m%d-%H%M%S'), uuid.uuid4().hex[:8])
        self.requests[request_id] = {'key': str(key or ''), 'cursor': cursor, 'edit': edit,
                                     'before': text[max(0, index - SNIPPET):index], 'after': text[index:index + SNIPPET],
                                     'answer': None}
        self._tidy_reply_dir()
        self._poll_timer.start()
        return request_id

    def forget(self, request_id):
        self.requests.pop(request_id, None)
        if not self.requests:
            self._poll_timer.stop()

    def pending(self):
        return bool(self.requests)

    # ── the reply ──
    def poll(self):
        for request_id in list(self.requests):
            request = self.requests.get(request_id)
            if request is None or request['answer'] is not None:
                continue
            path = os.path.join(self.reply_dir, request_id + '.json')
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding='utf-8') as handle:
                    data = json.load(handle) or {}
            except Exception:
                continue                              # half written: next time
            status = str(data.get('status', '') or '').strip().lower()
            if status == 'staged':                    # it arrived; the person has not asked yet
                continue
            try:
                os.remove(path)
            except OSError:
                pass
            answer = _clean(str(data.get('answer', '') or ''))
            if status not in FINISHED or not answer.strip():
                self.forget(request_id)
                self.dropped.emit(status or 'empty')
                continue
            request['answer'] = answer
        self.try_waiting()
        if not any(request['answer'] is None for request in self.requests.values()):
            self._poll_timer.stop()

    def try_waiting(self):
        """Type every finished answer whose document is open now (called after a reply and when a document opens)."""
        if self._typing is not None:
            return
        key = str(self.current_key() or '')
        for request_id, request in list(self.requests.items()):
            if request['answer'] is None:
                continue
            if request['key'] != key:
                if not request.get('told'):
                    request['told'] = True
                    self.waiting.emit(request['key'])
                continue
            edit = self.current_edit(key)
            if edit is None or edit.isReadOnly():
                continue
            if self.transform is not None and not request.get('transformed'):
                request['transformed'] = True
                try:
                    request['answer'] = str(self.transform(key, request['answer']) or '')
                except Exception:
                    logging.exception('the transform of a written answer failed; it is typed as it came')
                if not request['answer'].strip():
                    self.forget(request_id)
                    self.dropped.emit('empty')
                    continue
            text = edit.toPlainText()
            same_document = request['cursor'].document() is edit.document()
            guess = to_py(text, request['cursor'].position()) if same_document else None
            index = locate(text, guess, request['before'], request['after'])
            if index is None:
                index = guess if guess is not None else len(text)
            self.forget(request_id)
            request['answer'] = join(text, index, request['answer'])
            self._start_typing(edit, to_qt(text, index), request, request_id)
            return

    # ── typing ──
    def _start_typing(self, edit, position, request, request_id):
        cursor = QTextCursor(edit.document())
        cursor.setPosition(position)
        answer = request['answer']
        step = max(2, int(math.ceil(len(answer) / float(STEPS))))
        self._typing = {'edit': edit, 'cursor': cursor, 'left': answer, 'step': step, 'first': True, 'done': 0,
                        'key': request['key'], 'before': request['before'], 'after': request['after'], 'typed': '',
                        'at': position}
        self._type_step()
        if self._typing is not None:
            self._type_timer.start()

    def _type_step(self):
        job = self._typing
        if job is None:
            self._type_timer.stop()
            return
        edit = job['edit']
        try:
            alive = edit.document() is job['cursor'].document() and not edit.isReadOnly()
        except RuntimeError:
            alive = False
        if not alive or str(self.current_key() or '') != job['key']:
            # the document was closed / swapped while typing: what is left waits for it, found again by its text
            self._typing = None
            self._type_timer.stop()
            if job['left']:
                request_id = 'wb-rest-%s' % uuid.uuid4().hex[:8]
                self.requests[request_id] = {'key': job['key'], 'cursor': job['cursor'], 'edit': edit,
                                             'before': (job['before'] + job['typed'])[-SNIPPET:], 'after': job['after'],
                                             'answer': job['left']}
            return
        piece, job['left'] = job['left'][:job['step']], job['left'][job['step']:]
        cursor = job['cursor']
        # An editor that shows its text anew after every change (Strawberry's script editor does: it saves and
        # reloads) throws this cursor to the end of the document. Each step goes back to where the last one ended.
        cursor.setPosition(max(0, min(int(job['at']), edit.document().characterCount() - 1)))
        if job['first']:
            cursor.beginEditBlock()               # all steps = one undo
            job['first'] = False
        else:
            cursor.joinPreviousEditBlock()
        cursor.insertText(piece)
        cursor.endEditBlock()
        job['at'] += len(piece.encode('utf-16-le')) // 2
        cursor.setPosition(max(0, min(int(job['at']), edit.document().characterCount() - 1)))
        job['typed'] += piece
        job['done'] += len(piece)
        try:
            edit.setTextCursor(cursor)            # the caret goes along, as when someone types
            edit.ensureCursorVisible()
        except RuntimeError:
            pass
        if not job['left']:
            self._typing = None
            self._type_timer.stop()
            self.typed.emit(job['key'], job['done'])
            QTimer.singleShot(0, self.try_waiting)

    def typing(self):
        return self._typing is not None

    def _tidy_reply_dir(self):
        """Reply files nobody waits for any more (the app was quit before Broccoli answered) go after two days."""
        try:
            now = time.time()
            for name in os.listdir(self.reply_dir):
                path = os.path.join(self.reply_dir, name)
                if name.endswith('.json') and now - os.path.getmtime(path) > KEEP_REPLIES_SECONDS:
                    os.remove(path)
        except OSError:
            pass
        except Exception:
            logging.exception('tidying the write-back replies failed')


def join(text, index, answer):
    """Blank lines around the answer when it is paragraphs of its own (more than one paragraph, or it starts with a
    heading / list / quote / table / code) and the spot is not already at a paragraph break; a piece of a sentence
    goes in as it is."""
    stripped = answer.lstrip()
    block = '\n\n' in answer.strip() or bool(re.match(r'(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||```)', stripped))
    if not block:
        return answer
    before, after = text[:index], text[index:]
    lead = '' if not before.strip() or before.endswith('\n\n') else ('\n' if before.endswith('\n') else '\n\n')
    tail = '' if not after.strip() or after.startswith('\n\n') else ('\n' if after.startswith('\n') else '\n\n')
    return lead + answer.strip('\n') + tail


def _clean(answer):
    """The answer as text to type: no marker left in it, no fence wrapped around the whole of it."""
    text = str(answer or '').replace(MARKER, '').strip('\n')
    lines = text.split('\n')
    if len(lines) >= 2 and lines[0].strip().startswith('```') and lines[-1].strip() == '```':
        text = '\n'.join(lines[1:-1])
    return text
