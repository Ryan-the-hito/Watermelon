"""Watermelon's functions as tools for AI apps (the family's rules: APP_MCP_SPEC.md, 2026-11-25).

The owner (2026-11-25): every app's main functions must be reachable as tools, so that an assistant app and
outside AI apps can operate the app. Watermelon runs a small MCP service on this Mac only (app_mcp_host.py,
the file every app of the family carries), leaves its card in the family's folder, and any AI app reaches it
through the bridge (Watermelon started with --mcp-stdio; the menu's "Use in other AI apps…" copies the setup).

    tools = WatermelonTools(main_window, globals())     # in the main file, once the windows are made
    QTimer.singleShot(2000, tools.start)
    app.aboutToQuit.connect(tools.stop)

Every tool goes through the same methods as the same thing done by hand (the editing box, the file list, the
panels stay in step). Tools that only read files or wait for something run on the service's thread and hand
their window work to the main thread; the window never waits for the network. No tool opens a dialog or a
file picker, reads a secret, changes what the app may do on this Mac, updates or quits the app.

`ns` is the main file's globals: its functions are looked up at each call (a test may put stand-ins there)."""
import datetime
import logging
import os
import re
import sys
import threading

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QApplication, QSlider

import app_mcp_host
import watermelon_anki
import watermelon_attachments
import watermelon_lecture
import watermelon_marks
import watermelon_notes
import watermelon_office
import watermelon_outline

TEXT_LIMIT = 20000            # a tool's text answer: this many characters at a time, the rest by "offset"
OFFICE_KINDS = {'.docx': 'word', '.xlsx': 'excel', '.pptx': 'powerpoint'}
MARKDOWN_EXTS = ('.md', '.markdown', '.txt')


class ToolError(Exception):
    """Words for the model: why the tool did not do it."""


class MainThreadRunner(QObject):
    """runner(fn): fn runs on the main thread, the calling thread gets what it returned (or its exception)."""
    _call = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._call.connect(self._run)      # emitted from another thread → queued to this object's (the main) thread

    def _run(self, job):
        job()

    def __call__(self, fn):
        if threading.current_thread() is threading.main_thread():
            return fn()
        box, done = {}, threading.Event()

        def job():
            try:
                box['value'] = fn()
            except BaseException as exc:
                box['error'] = exc
            done.set()
        self._call.emit(job)
        done.wait()
        if 'error' in box:
            raise box['error']
        return box.get('value')


def clip(text, arguments):
    """A long text a piece at a time: {'text', 'offset', 'total', 'remaining'}."""
    text = str(text or '')
    try:
        offset = max(0, int(arguments.get('offset') or 0))
        limit = int(arguments.get('limit') or TEXT_LIMIT)
    except (TypeError, ValueError):
        raise ToolError('offset and limit are whole numbers.')
    limit = max(1, min(limit, TEXT_LIMIT))
    piece = text[offset:offset + limit]
    out = {'text': piece, 'offset': offset, 'total': len(text), 'remaining': max(0, len(text) - offset - len(piece))}
    if out['remaining']:
        out['note'] = '%d more characters: call again with offset %d.' % (out['remaining'], offset + len(piece))
    return out


def _flag(value, name):
    if isinstance(value, bool):
        return value
    raise ToolError('%s is true or false.' % name)


def _words(text):
    return [word for word in str(text or '').lower().split() if word]


class WatermelonTools:
    def __init__(self, window, ns):
        self.w = window
        self.ns = ns
        self.host = None
        self.runner = MainThreadRunner()       # made on the main thread: what it is handed runs there

    # ── the service ───────────────────────────────────────────────────────────────────────────────────
    def start(self, card_dir=None):
        if self.host is not None:
            return True
        ns = self.ns
        host = app_mcp_host.AppMcpHost(
            ns['WATERMELON_BUNDLE_ID'], ns['NAME'], ns['VERSION'],
            description='The person\'s writing app: Markdown documents with a live preview, their notes in Apple Notes, '
                        'attachments, study cards, Anki decks, a web page beside the text.',
            instructions='Watermelon shows ONE document at a time in its editing box: a local Markdown file ("local" mode), a '
                         'note of Apple Notes ("notes" mode), or a web page ("web" mode). read_state first: it says what is '
                         'open. Look before you change (list_ / read_ / search_), and say what you are going to change. '
                         'A change to the open document is typed into the editing box like the person\'s own typing (they can '
                         'undo it) and is saved by the app. Long texts come a piece at a time: pass "offset" for the rest. '
                         'Lines are counted from 1.')
        obj = lambda **properties: {'type': 'object', 'properties': properties}
        text = lambda description: {'type': 'string', 'description': description}
        number = lambda description: {'type': 'number', 'description': description}
        flag = lambda description: {'type': 'boolean', 'description': description}
        choice = lambda values, description: {'type': 'string', 'enum': list(values), 'description': description}
        paths = lambda description: {'type': 'array', 'items': {'type': 'string'}, 'description': description}
        offset, limit = number('Start at this character (0).'), number('At most this many characters (%d).' % TEXT_LIMIT)
        doc_name = text('The document\'s name as in list_documents. Left out: the document that is open.')

        # the window
        host.tool('read_state', 'What Watermelon shows now: window shown or collapsed, mode (local / notes / web), the open '
                  'document, its length, the selected text, the line of the cursor, which panels and modes are on.',
                  obj(), self.read_state)
        host.tool('update_view', 'Changes what the window shows; every field is optional. window: shown / collapsed. '
                  'mode: local / notes / web. teleprompter, lecture_mode, typing_sound, attachments_panel, cards_panel: '
                  'true / false. go_to_line: puts the cursor on that line of the open document.',
                  obj(window=choice(('shown', 'collapsed'), 'The main window, or only its small bar.'),
                      mode=choice(('local', 'notes', 'web'), 'Local files, Apple Notes, or the web page.'),
                      teleprompter=flag('The narrow reading column.'), lecture_mode=flag('Cards made while a lecture runs.'),
                      typing_sound=flag('The typewriter sound.'), attachments_panel=flag('The list of attachments on the left.'),
                      cards_panel=flag('The cards on the right.'), go_to_line=number('A line number from read_outline (from 1).')),
                  self.update_view, mutating=True)

        # local documents
        host.tool('list_documents', 'The local documents in Watermelon\'s file list: name, file, kind (markdown / word / excel / '
                  'powerpoint), which one is open.', obj(), self.list_documents)
        host.tool('read_document', 'The text of a document (Markdown; of a Word / Excel / PowerPoint file its plain words). '
                  'Left without a name: the open document as it stands in the editing box (in notes mode: the open note).',
                  obj(name=doc_name, offset=offset, limit=limit), self.read_document, main_thread=False)
        host.tool('search_documents', 'Lines of the local Markdown documents that hold every word of "text". Gives document, '
                  'line number and the line.',
                  dict(obj(text=text('Words to look for.'), limit=number('At most this many lines (50).')), required=['text']),
                  self.search_documents, main_thread=False)
        host.tool('create_document', 'Makes a new local Markdown document in Watermelon\'s folder and adds it to the file list. '
                  'open true: also shows it in the editing box.',
                  obj(title=text('Its name (left out: "Note" and the time).'), text=text('Its Markdown text.'),
                      open=flag('Show it now (default false: the open document stays).')),
                  self.create_document, mutating=True)
        host.tool('update_document', 'Writes into a Markdown document. how: "append" (default, at the end), "replace" (the '
                  'whole text), "insert" (at the cursor, open document only). Or pass "find": that exact passage, which must '
                  'occur once, is replaced by "text". Left without a name: the open document (also the open note).',
                  dict(obj(name=doc_name, text=text('The Markdown to write.'),
                           how=choice(('append', 'replace', 'insert'), 'Where it goes.'),
                           find=text('An exact passage of the document to replace with "text".')), required=['text']),
                  self.update_document, mutating=True)
        host.tool('update_current_document', 'Shows another document in the editing box. One of: name (a document of '
                  'list_documents); path (a .md / .docx / .xlsx / .pptx file on this Mac: added to the file list, then shown); '
                  'note_title with note_folder (a note of list_notes: switches to notes mode).',
                  obj(name=text('A document of list_documents.'), path=text('The full path of a file.'),
                      note_folder=text('The note\'s folder as in list_notes.'), note_title=text('The note\'s title.')),
                  self.update_current_document, mutating=True)
        host.tool('remove_document', 'Takes a document out of Watermelon\'s file list. The file itself stays on the disk. The '
                  'first document of the list cannot be removed. Ask the person first.',
                  dict(obj(name=text('The document\'s name as in list_documents.')), required=['name']),
                  self.remove_document, destructive=True)
        host.tool('create_export', 'Exports the open document into a folder: "<name>.md" and "<name>_bionic.md" (the bold-'
                  'reading version). A file of that name already there is replaced: ask the person first.',
                  dict(obj(folder=text('The full path of a folder that exists.')), required=['folder']),
                  self.create_export, mutating=True)
        host.tool('read_bionic_text', 'Gives a text back as bold-reading Markdown (the first part of each word in bold), the way '
                  'Watermelon\'s right-hand preview shows it. Changes nothing.',
                  dict(obj(text=text('The text (at most %d characters).' % TEXT_LIMIT)), required=['text']),
                  self.read_bionic_text, main_thread=False)
        host.tool('read_outline', 'The headings of the open document: line, level, title.', obj(), self.read_outline)

        # attachments
        host.tool('list_attachments', 'The files the open document refers to (pictures, PDFs, Office files …) and the '
                  'screenshots kept for it that are not in its text yet.', obj(), self.list_attachments)
        host.tool('create_attachment', 'Puts files into the open document as attachments, each on its own line (a picture as an '
                  'image, any other file as a link). at: "cursor" (default, after the cursor\'s paragraph) or "end".',
                  dict(obj(paths=paths('Full paths of files on this Mac.'), at=choice(('cursor', 'end'), 'Where they go.')),
                       required=['paths']), self.create_attachment, mutating=True)
        host.tool('remove_attachment', 'Removes an attachment of list_attachments. One that is in the text: only its line leaves '
                  'the text, the file stays. A screenshot not yet in the text: its picture file is deleted. Ask the person first.',
                  dict(obj(path=text('The attachment\'s path as in list_attachments.'),
                           offset=number('Its "offset" from list_attachments, when the text names the file more than once.')),
                       required=['path']), self.remove_attachment, destructive=True)
        host.tool('read_attachment', 'What the person marked in an attachment of the open document (highlights, comments, '
                  'speaker notes of a PDF / Word / Excel / PowerPoint file) and, for an Office file, its plain words.',
                  dict(obj(path=text('The attachment\'s path as in list_attachments.'), offset=offset, limit=limit), required=['path']),
                  self.read_attachment, main_thread=False)
        host.tool('create_screenshots_pdf', 'Makes one PDF of the screenshots kept for the open document and puts it at the end of '
                  'the document; the screenshots used leave the list.',
                  obj(paths=paths('Only these screenshots (paths from list_attachments). Left out: all of them.')),
                  self.create_screenshots_pdf, mutating=True, main_thread=False, timeout=90)
        host.tool('update_screenshots_into_document', 'Puts the screenshots kept for the open document into its text as pictures '
                  '(at the end), in the order they were taken; they leave the list.',
                  obj(paths=paths('Only these screenshots (paths from list_attachments). Left out: all of them.')),
                  self.update_screenshots_into_document, mutating=True, main_thread=False, timeout=90)

        # the cards on the right
        host.tool('list_cards', 'The study cards of the panel on the right. which: "document" (default: the open document\'s), '
                  '"all", or "archived". text: words the card must hold.',
                  obj(which=choice(('document', 'all', 'archived'), 'Which cards.'), text=text('Words to look for.'),
                      limit=number('At most this many (50).')), self.list_cards)
        host.tool('create_card', 'Adds a study card to the panel on the right, for the open document: a short title and a few '
                  'lines of body (a key point, an explanation, an answer).',
                  dict(obj(title=text('A short title.'), body=text('A few lines.'), source=text('Where it is from, e.g. "slides.pdf p.3".')),
                       required=['title']), self.create_card, mutating=True)
        host.tool('update_card', 'Changes a card: title, body, archived (true / false), or insert_into_document true: the card is '
                  'put into the open document after the cursor\'s paragraph as a quote block and goes to the archive.',
                  dict(obj(id=text('The card\'s id from list_cards.'), title=text('New title.'), body=text('New body.'),
                           archived=flag('In the archive or back among the cards.'),
                           insert_into_document=flag('Put it into the open document.')), required=['id']),
                  self.update_card, mutating=True)
        host.tool('delete_card', 'Deletes one card for good. Ask the person first.',
                  dict(obj(id=text('The card\'s id from list_cards.')), required=['id']), self.delete_card, destructive=True)

        # Anki
        host.tool('list_anki_decks', 'The Anki decks Watermelon keeps: name, number of cards, the folder with the files to '
                  'import into Anki.', obj(), self.list_anki_decks, main_thread=False)
        host.tool('read_anki_deck', 'The cards of one deck.',
                  dict(obj(deck=text('The deck\'s name as in list_anki_decks.'), limit=number('At most this many (50).'),
                           skip=number('Leave out this many first.')), required=['deck']), self.read_anki_deck, main_thread=False)
        host.tool('create_anki_cards', 'Adds cards to a deck (made if it is not there); a card the deck already has is left out. '
                  'Each card: {"type": "basic", "front", "back"} or {"type": "cloze", "text": "… {{c1::hidden}} …", "extra"}. '
                  'Formulas as $…$.',
                  dict(obj(deck=text('The deck\'s name.'),
                           cards={'type': 'array', 'items': {'type': 'object'}, 'description': 'The cards.'}), required=['deck', 'cards']),
                  self.create_anki_cards, mutating=True, main_thread=False)

        # Apple Notes
        host.tool('list_notes', 'The person\'s notes in Apple Notes as Watermelon last listed them: folder, title, newest first. '
                  'text: words the title must hold; folder: only this folder.',
                  obj(text=text('Words of the title.'), folder=text('A folder as listed.'), limit=number('At most this many (50).')),
                  self.list_notes)
        host.tool('read_note', 'The text of one note of Apple Notes, as Markdown.',
                  dict(obj(folder=text('The note\'s folder as in list_notes.'), title=text('The note\'s title.'), offset=offset, limit=limit),
                       required=['title']), self.read_note, main_thread=False, timeout=90)
        host.tool('create_note', 'Makes a new note in Apple Notes from Markdown. (To change a note: open it with '
                  'update_current_document, then update_document.)',
                  dict(obj(title=text('The note\'s title.'), text=text('Its Markdown text.'),
                           folder=text('A folder as in list_notes (left out: the folder open in Watermelon, else Notes\' own).')),
                       required=['title']), self.create_note, mutating=True, main_thread=False, timeout=120)

        # the web page
        host.tool('read_web_page', 'The page in Watermelon\'s web mode: address, title, its text, and the tabs.',
                  obj(offset=offset, limit=limit), self.read_web_page, main_thread=False, timeout=40)
        host.tool('update_web_page', 'Web mode: goes to an address (or searches the words), or back / forward / reload, or '
                  'switches to a tab. Switches to web mode when it is not on. The page loads after the answer: read_web_page a '
                  'moment later.',
                  obj(url=text('An http(s) address, or words to search.'), new_tab=flag('Open the address in another tab.'),
                      action=choice(('back', 'forward', 'reload'), 'Instead of an address.'),
                      tab=number('Switch to this tab (its number in read_web_page).')), self.update_web_page, mutating=True)
        host.tool('create_document_from_web_page', 'Saves the web page (what is selected on it, else the whole page) as Markdown: '
                  'target "local" (default) = a new local document in the file list, "notes" = a new note in Apple Notes. '
                  'The page is copied the way a person copies it; the clipboard is put back afterwards.',
                  obj(target=choice(('local', 'notes'), 'Where it is saved.')), self.create_document_from_web_page,
                  mutating=True, main_thread=False, timeout=120)

        # settings
        host.tool('read_settings', 'Watermelon\'s settings: font, font size, always on top, eye-care background, scrolling '
                  'together, the cards\' language, how many backups are kept, Dock icon, all Spaces, interface language.',
                  obj(), self.read_settings)
        host.tool('update_settings', 'Changes settings; every field is optional. Not offered here: the interface language (needs '
                  'a restart) and the update checks.',
                  obj(font_size=number('14 to 50.'), font=text('A font family of this Mac, or "default" for Watermelon\'s own.'),
                      always_on_top=flag('The window above other windows.'), eye_care_background=flag('Cream instead of white.'),
                      scroll_together=flag('The previews follow the editing box.'),
                      card_language=text('The language cards are written in, one of read_settings\' "card_languages" ("" = the document\'s).'),
                      backup_limit=number('Backups kept per document.'), dock_icon=flag('Show the Dock icon.'),
                      all_spaces=flag('Show the windows on all Spaces.')), self.update_settings, mutating=True)

        # backups
        host.tool('list_backups', 'The backups Watermelon keeps of the open document (one a minute while it changes), newest first.',
                  obj(), self.list_backups, main_thread=False)
        host.tool('read_backup', 'The text of one backup of the open document. (To bring it back: update_document with how '
                  '"replace" — ask the person first.)',
                  dict(obj(file=text('The backup\'s file name from list_backups.'), offset=offset, limit=limit), required=['file']),
                  self.read_backup, main_thread=False)

        launch = None
        marker = '.app/Contents/MacOS/'
        if getattr(sys, 'frozen', False) and marker in sys.executable:      # the packaged app can be opened again by its card
            launch = {'bundle_id': ns['WATERMELON_BUNDLE_ID'], 'path': sys.executable.split(marker)[0] + '.app'}
        try:
            started = host.start(run_on_main=self.runner, launch=launch, card_dir=card_dir)
        except Exception:
            logging.exception('The tools service could not be started.')
            started = False
        self.host = host if started else None
        return started

    def stop(self):
        if self.host is not None:
            try:
                self.host.stop()
            except Exception:
                logging.exception('Stopping the tools service failed.')
            self.host = None

    # ── shared ────────────────────────────────────────────────────────────────────────────────────────
    def _mode(self):
        w = self.w
        return 'web' if w.web_mode_enabled else ('notes' if w.notes_mode_enabled else 'local')

    def _window_shown(self):
        return bool(self.w.qw0.isVisible())

    def _not_busy(self):
        """A question of the app is on the screen, or a window of the app is being moved by an animation: no change now."""
        if QApplication.activeModalWidget() is not None:
            raise ToolError('Watermelon is asking the person something right now. Try again in a moment.')

    def _entries(self):
        return [(str(name), str(path)) for name, path in self.w._local_file_list()]

    def _current_index(self):
        path = self.w._current_local_file_path()
        entries = self._entries()
        index = self.w.widget0.currentIndex()
        if 0 <= index < len(entries) and entries[index][1] == path:
            return index
        return next((i for i, entry in enumerate(entries) if entry[1] == path), -1)

    def _find_entry(self, name):
        """(index, name, path) of the local document called so."""
        wanted = str(name or '').strip()
        entries = self._entries()
        if not wanted:
            raise ToolError('Pass the document\'s name.')
        for test in (lambda n, p: n == wanted, lambda n, p: n.lower() == wanted.lower(), lambda n, p: p == wanted,
                     lambda n, p: os.path.basename(p).lower() == wanted.lower()):
            found = [(i, n, p) for i, (n, p) in enumerate(entries) if test(n, p)]
            if len(found) == 1:
                return found[0]
            if len(found) > 1:
                current = self._current_index()
                mine = [entry for entry in found if entry[0] == current]
                return mine[0] if mine else found[0]
        raise ToolError('No document is called %r. The documents: %s' % (wanted, ', '.join(n for n, _p in entries) or '(none)'))

    def _open_is_office(self):
        return self._mode() == 'local' and watermelon_office.is_office_path(self.w._current_local_file_path() or '')

    def _open_name(self):
        w = self.w
        if w.notes_mode_enabled:
            return w.notes_current_title or ''
        return w.widget0.currentText()

    def _text_document_open(self, to_change=False):
        """The editing box holds a text document (not a web page, not an Office file); to_change: and it can be typed into."""
        w = self.w
        if w.web_mode_enabled:
            raise ToolError('Watermelon is in web mode: no document is in the editing box. update_view with mode "local" or "notes" first.')
        if self._open_is_office():
            raise ToolError('The open document is an Office file; its content is not offered as a tool. Open a Markdown document first.')
        if w.notes_mode_enabled and not w.notes_active:
            raise ToolError('No note is open in notes mode. update_current_document with note_title first.')
        if to_change and w.bottom.isReadOnly():
            raise ToolError('The editing box cannot be typed into right now.')

    def _notes_save_allowed(self):
        """A note with things only Notes itself can make is saved only after the person said yes in the app."""
        w = self.w
        note = w._notes_open_note
        if not w.notes_mode_enabled or note is None:
            return
        folder = (note.get('folder') or 'Unfiled').strip() or 'Unfiled'
        title = note.get('title') or '(Untitled)'
        note_id = self.ns['_note_id_for'](folder, title, note.get('id'))
        key = self.ns['_note_storage_key'](folder, title, note_id)
        if key in w._notes_autosave_off:
            raise ToolError('The person chose not to save this note from Watermelon. It cannot be changed here.')
        if key in w._notes_drawing_confirmed:
            return
        try:
            native = watermelon_notes.note_native_only(folder, title, note_id=note_id)
        except Exception:
            native = []
        if native:
            raise ToolError('This note has %s, which only Notes itself can make; saving from Watermelon would turn it into plain '
                            'content. The person has to change this note in Watermelon once themselves (Watermelon asks them) before '
                            'a tool may.' % ', '.join(native))

    def _attachment_items(self):
        w = self.w
        items = watermelon_attachments.attachments_in(w.bottom.toPlainText(), w._attachment_base_dir())
        w._ensure_courseware()
        return items + w.courseware.items()

    def _wait_for(self, signal, begin, seconds, what):
        """On the service's thread: begin() on the main thread, then wait for `signal` (emitted on the main thread).
        → the signal's arguments."""
        box, done = {}, threading.Event()

        def slot(*args):
            box['args'] = args
            done.set()

        def connect_and_begin():
            signal.connect(slot)
            try:
                begin()
            except BaseException:
                signal.disconnect(slot)
                raise

        self.runner(connect_and_begin)
        finished = done.wait(seconds)
        try:
            self.runner(lambda: signal.disconnect(slot))
        except Exception:
            pass
        if not finished:
            raise ToolError('%s did not finish within %d seconds.' % (what, seconds))
        return box['args']

    # ── the window ────────────────────────────────────────────────────────────────────────────────────
    def read_state(self, a=None):
        w = self.w
        mode = self._mode()
        state = {'window': 'shown' if self._window_shown() else 'collapsed', 'mode': mode,
                 'teleprompter': bool(w._teleprompter_mode), 'lecture_mode': bool(w.lecture_mode_enabled),
                 'typing_sound': bool(w.sound_mode_enabled),
                 'attachments_panel': bool(w.attachment_rail.isVisible()) if hasattr(w, 'attachment_rail') else False,
                 'cards_panel': bool(w._panel_open)}
        if mode == 'web':
            view = w.web_panel.active_view() if w.web_panel is not None else None
            if view is not None and not bool(view.property('wm_start_page')):
                state['web_page'] = {'url': view.url().toString(), 'title': view.page().title()}
            else:
                state['web_page'] = None
            return state
        document = {'name': self._open_name()}
        if mode == 'notes':
            document.update(kind='note', folder=w.notes_current_folder or '', open=bool(w.notes_active),
                            saved={'': 'edited' if w.notes_dirty else 'yes', 'saving': 'saving', 'saved': 'yes',
                                   'failed': 'no'}.get(w._notes_save_state, 'yes'))
            if not w.notes_active:
                state['document'] = document if document['name'] else None
                return state
        else:
            path = w._current_local_file_path() or ''
            document.update(path=path, kind=OFFICE_KINDS.get(os.path.splitext(path)[1].lower(), 'markdown'))
            if document['kind'] != 'markdown':
                state['document'] = document
                return state
        text = w.bottom.toPlainText()
        cursor = w.bottom.textCursor()
        selected = cursor.selectedText().replace('\u2029', '\n')
        document.update(characters=w._count_visible_chars(text), words=w._count_words(text),
                        cursor_line=cursor.blockNumber() + 1, selected_text=selected[:4000])
        if len(selected) > 4000:
            document['selected_text_note'] = 'The selection is %d characters; the first 4000 are given.' % len(selected)
        state['document'] = document
        return state

    def update_view(self, a):
        w, ns = self.w, self.ns
        known = ('window', 'mode', 'teleprompter', 'lecture_mode', 'typing_sound', 'attachments_panel', 'cards_panel', 'go_to_line')
        if not any(a.get(key) is not None for key in known):
            raise ToolError('Pass at least one of: %s.' % ', '.join(known))
        self._not_busy()
        notes = []
        if a.get('window') is not None:
            if a['window'] not in ('shown', 'collapsed'):
                raise ToolError('window is "shown" or "collapsed".')
            if (a['window'] == 'shown') != self._window_shown():
                if len([key for key in known if a.get(key) is not None]) > 1:
                    raise ToolError('Showing or collapsing the window takes about a second: ask for it alone, then for the '
                                    'other changes in a call of their own.')
                w.pin_a_tab()
                return {'changed': ['The window is being %s (an animation of about a second).'
                                    % ('shown' if a['window'] == 'shown' else 'collapsed')]}
        others = [key for key in known[1:] if a.get(key) is not None]
        if others and not self._window_shown():
            raise ToolError('The window is collapsed. update_view with window "shown" first.')
        if a.get('mode') is not None:
            self._set_mode(a['mode'])
            notes.append('mode: %s' % self._mode())
        if a.get('teleprompter') is not None:
            want = _flag(a['teleprompter'], 'teleprompter')
            if want != bool(w._teleprompter_mode):
                if want and (w.web_mode_enabled or w._office_shown()):
                    raise ToolError('The teleprompter is for a text document (not a web page or an Office file).')
                w.toggle_teleprompter()
            notes.append('teleprompter: %s' % ('on' if w._teleprompter_mode else 'off'))
        if a.get('lecture_mode') is not None:
            want = _flag(a['lecture_mode'], 'lecture_mode')
            if want != bool(w.lecture_mode_enabled):
                if want and not ns['watermelon_broccoli'].broccoli_installed():
                    raise ToolError('Lecture mode makes its cards with an assistant app that is not on this Mac. '
                                    '(Cards can still be added with create_card.)')
                w.toggle_lecture_mode()
            notes.append('lecture mode: %s' % ('on' if w.lecture_mode_enabled else 'off'))
        if a.get('typing_sound') is not None:
            if _flag(a['typing_sound'], 'typing_sound') != bool(w.sound_mode_enabled):
                w.toggle_sound_mode()
            notes.append('typing sound: %s' % ('on' if w.sound_mode_enabled else 'off'))
        if a.get('attachments_panel') is not None:
            want = _flag(a['attachments_panel'], 'attachments_panel')
            if want != bool(w.attachment_rail.isVisible()):
                if not w._side_available('left'):
                    raise ToolError('The list of attachments is there only while a text document is shown.')
                w._on_side_handle('left')
            notes.append('attachments panel: %s' % ('shown' if w.attachment_rail.isVisible() else 'hidden'))
        if a.get('cards_panel') is not None:
            want = _flag(a['cards_panel'], 'cards_panel')
            if want != bool(w._panel_open):
                w._set_panel_open(want)
            notes.append('cards panel: %s' % ('shown' if w._panel_open else 'hidden'))
        if a.get('go_to_line') is not None:
            self._text_document_open()
            try:
                line = int(a['go_to_line'])
            except (TypeError, ValueError):
                raise ToolError('go_to_line is a line number.')
            if line < 1 or line > w.bottom.document().blockCount():
                raise ToolError('The document has %d lines.' % w.bottom.document().blockCount())
            w._jump_to_outline_line(line - 1)
            notes.append('cursor on line %d' % line)
        return {'changed': notes}

    def _set_mode(self, mode):
        w = self.w
        if mode not in ('local', 'notes', 'web'):
            raise ToolError('mode is "local", "notes" or "web".')
        if not self._window_shown():
            raise ToolError('The window is collapsed. update_view with window "shown" first.')
        if mode == self._mode():
            return
        if w.web_mode_enabled:
            w.toggle_web_mode()                      # back to the mode under it
        if mode == 'web':
            w.toggle_web_mode()
            if not w.web_mode_enabled:
                raise ToolError('The web page could not be opened.')
            return
        if (mode == 'notes') != bool(w.notes_mode_enabled):
            w.toggle_notes_mode()

    # ── local documents ───────────────────────────────────────────────────────────────────────────────
    def list_documents(self, a=None):
        current = self._current_index() if self._mode() != 'notes' else -1
        out = []
        for index, (name, path) in enumerate(self._entries()):
            entry = {'name': name, 'path': path, 'kind': OFFICE_KINDS.get(os.path.splitext(path)[1].lower(), 'markdown'),
                     'open': index == current and self._mode() == 'local'}
            try:
                entry['changed'] = datetime.datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec='seconds')
            except OSError:
                entry['missing'] = True
            out.append(entry)
        return {'mode': self._mode(), 'count': len(out), 'documents': out}

    def read_document(self, a):
        name = str(a.get('name') or '').strip()

        def look():
            w = self.w
            if not name:
                if w.web_mode_enabled:
                    raise ToolError('Watermelon is in web mode; pass the document\'s name, or use read_web_page.')
                if w.notes_mode_enabled:
                    if not w.notes_active:
                        raise ToolError('No note is open in notes mode.')
                    return {'name': self._open_name(), 'kind': 'note'}, w.bottom.toPlainText(), ''
                path = w._current_local_file_path() or ''
                index, entry_name = self._current_index(), w.widget0.currentText()
            else:
                index, entry_name, path = self._find_entry(name)
            kind = OFFICE_KINDS.get(os.path.splitext(path)[1].lower(), 'markdown')
            head = {'name': entry_name, 'path': path, 'kind': kind}
            if kind == 'markdown' and self._mode() == 'local' and index == self._current_index():
                return head, w.bottom.toPlainText(), ''          # as it stands in the editing box
            return head, None, path

        head, text, path = self.runner(look)
        if text is None:
            if not os.path.isfile(path):
                raise ToolError('The file of "%s" is not there any more: %s' % (head['name'], path))
            if head['kind'] == 'markdown':
                text = self.ns['_read_local_text'](path)
            else:
                text = watermelon_marks.office_plain_text(path, limit=400000)
                head['note'] = 'The plain words of the file, without its layout.'
        head.update(clip(text, a))
        return head

    def search_documents(self, a):
        words = _words(a.get('text'))
        if not words:
            raise ToolError('Pass the words to look for.')
        try:
            limit = max(1, min(int(a.get('limit') or 50), 200))
        except (TypeError, ValueError):
            raise ToolError('limit is a number.')

        def look():
            current = self._current_index() if self._mode() == 'local' else -1
            return self._entries(), current, self.w.bottom.toPlainText() if current >= 0 and not self._open_is_office() else None

        entries, current, open_text = self.runner(look)
        found, total = [], 0
        for index, (name, path) in enumerate(entries):
            if watermelon_office.is_office_path(path):
                continue
            if index == current and open_text is not None:
                text = open_text
            else:
                try:
                    text = self.ns['_read_local_text'](path)
                except (OSError, UnicodeError):
                    continue
            for number, line in enumerate(text.split('\n'), 1):
                low = line.lower()
                if all(word in low for word in words):
                    total += 1
                    if len(found) < limit:
                        found.append({'document': name, 'line': number, 'text': line.strip()[:300]})
        return {'count': total, 'lines': found}

    def create_document(self, a):
        w = self.w
        self._not_busy()
        title = str(a.get('title') or '').strip() or 'Note ' + datetime.datetime.now().strftime('%Y-%m-%d %H%M%S')
        text = str(a.get('text') or '')
        name = w._save_markdown_as_local_file(title, text)
        if not name:
            raise ToolError('The document could not be made.')
        index, _name, path = self._find_entry(name)
        out = {'created': name, 'path': path, 'open': False}
        if a.get('open') is not None and _flag(a['open'], 'open'):
            self._show_local(index)
            out['open'] = True
        return out

    def _show_local(self, index):
        """The local document at this place of the file list into the editing box, as picking it in the drop-down does."""
        w = self.w
        if not self._window_shown():
            raise ToolError('The window is collapsed. update_view with window "shown" first.')
        self._set_mode('local')
        path = self._entries()[index][1]
        if w.widget0.currentIndex() != index:
            w.widget0.setCurrentIndex(index)         # → index_change
        if w._current_local_file_path() != path:
            w.index_change(index)
        if w._current_local_file_path() != path:
            raise ToolError('Watermelon stayed on the document that was open (it could not be left, or the file is gone).')

    def update_document(self, a):
        self._not_busy()
        text = a.get('text')
        if not isinstance(text, str):
            raise ToolError('Pass "text".')
        how = str(a.get('how') or 'append')
        find = a.get('find')
        if how not in ('append', 'replace', 'insert'):
            raise ToolError('how is "append", "replace" or "insert".')
        if find is not None and (not isinstance(find, str) or not find):
            raise ToolError('"find" is the exact passage to replace.')
        name = str(a.get('name') or '').strip()
        in_box = True
        if name:
            index, entry_name, path = self._find_entry(name)
            in_box = self._mode() == 'local' and index == self._current_index()
        if in_box:
            return self._type_into_box(text, how, find)
        if watermelon_office.is_office_path(path):
            raise ToolError('"%s" is an Office file; its content is not offered as a tool.' % entry_name)
        if how == 'insert':
            raise ToolError('"insert" goes to the cursor of the open document; "%s" is not open.' % entry_name)
        try:
            before = self.ns['_read_local_text'](path)
        except (OSError, UnicodeError) as exc:
            raise ToolError('The file of "%s" could not be read: %s' % (entry_name, exc))
        after = self._changed_text(before, text, how, find)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(after)
        return {'document': entry_name, 'characters': len(after), 'saved': 'in its file (the document is not the open one)'}

    @staticmethod
    def _changed_text(before, text, how, find):
        if find is not None:
            count = before.count(find)
            if count != 1:
                raise ToolError('The passage to replace occurs %d times in the document; it must occur exactly once. '
                                'Read the document and pass a longer, exact passage.' % count)
            return before.replace(find, text)
        if how == 'replace':
            if not text.strip():
                raise ToolError('An empty text is not written (Watermelon does not save an empty document).')
            return text
        if not text:
            raise ToolError('There is nothing to add.')
        return before + ('' if not before or before.endswith('\n') else '\n') + text

    def _type_into_box(self, text, how, find):
        w = self.w
        self._text_document_open(to_change=True)
        self._notes_save_allowed()
        before = w.bottom.toPlainText()
        cursor = w.bottom.textCursor()
        cursor.beginEditBlock()                       # one step for the person's undo
        try:
            if find is not None:
                count = before.count(find)
                if count != 1:
                    raise ToolError('The passage to replace occurs %d times in the document; it must occur exactly once. '
                                    'Read the document and pass a longer, exact passage.' % count)
                start = before.index(find)
                cursor.setPosition(start)
                cursor.setPosition(start + len(find), QTextCursor.MoveMode.KeepAnchor)
                cursor.insertText(text)
            elif how == 'replace':
                if not text.strip():
                    raise ToolError('An empty text is not written (Watermelon does not save an empty document).')
                cursor.select(QTextCursor.SelectionType.Document)
                cursor.insertText(text)
            elif how == 'insert':
                if not text:
                    raise ToolError('There is nothing to add.')
                cursor.insertText(text)
            else:
                if not text:
                    raise ToolError('There is nothing to add.')
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText(('' if not before or before.endswith('\n') else '\n') + text)
        finally:
            cursor.endEditBlock()
        w.bottom.setTextCursor(cursor)
        after = w.bottom.toPlainText()
        saved = 'by Watermelon into Apple Notes, a few seconds after the last change' if w.notes_mode_enabled else 'in its file'
        return {'document': self._open_name(), 'characters': len(after), 'saved': saved,
                'note': 'Typed into the editing box; the person can undo it.'}

    def update_current_document(self, a):
        w = self.w
        self._not_busy()
        name, path = str(a.get('name') or '').strip(), str(a.get('path') or '').strip()
        note_title, note_folder = str(a.get('note_title') or '').strip(), str(a.get('note_folder') or '').strip()
        if sum(bool(x) for x in (name, path, note_title)) != 1:
            raise ToolError('Pass exactly one of: name, path, note_title (with note_folder).')
        if not self._window_shown():
            raise ToolError('The window is collapsed. update_view with window "shown" first.')
        if name:
            index, entry_name, _path = self._find_entry(name)
            self._show_local(index)
            return {'open': entry_name, 'mode': 'local'}
        if path:
            path = os.path.abspath(os.path.expanduser(path))
            if not os.path.isfile(path):
                raise ToolError('There is no file at %s.' % path)
            extension = os.path.splitext(path)[1].lower()
            office = watermelon_office.is_office_path(path)
            if not office and extension not in MARKDOWN_EXTS:
                raise ToolError('Watermelon opens .md, .docx, .xlsx and .pptx files.')
            if office and watermelon_office.load_component(self.ns['BasePath'])[0] is None:
                raise ToolError('This copy of Watermelon cannot show Office files.')
            if not office:
                try:
                    with open(path, encoding='utf-8') as handle:
                        handle.read()
                except (OSError, UnicodeError) as exc:
                    raise ToolError('The file could not be read as text: %s' % exc)
            listed = next((i for i, entry in enumerate(self._entries()) if entry[1] == path), -1)
            if listed >= 0:
                self._show_local(listed)
            else:
                self._set_mode('local')
                w.open_local_path(path)              # what Open does once the file is chosen
                if w._current_local_file_path() != path:
                    raise ToolError('The file was added to the list, but Watermelon stayed on the document that was open.')
            return {'open': w.widget0.currentText(), 'path': path, 'mode': 'local'}
        notes, error = self.ns['_read_notes_cache'](w.notes_cache_path)
        if error:
            raise ToolError('Watermelon has no list of the notes yet. update_view with mode "notes" first, then try again in a moment.')
        found = [note for note in notes if (note.get('title') or '(Untitled)') == note_title
                 and (not note_folder or ((note.get('folder') or 'Unfiled').strip() or 'Unfiled') == note_folder)]
        if not found:
            raise ToolError('No note is called %r%s. list_notes shows them.' % (note_title, (' in "%s"' % note_folder) if note_folder else ''))
        if len(found) > 1 and not note_folder:
            raise ToolError('Several notes are called %r; pass note_folder: %s' % (
                note_title, ', '.join(sorted({(n.get('folder') or 'Unfiled') for n in found}))))
        self._set_mode('notes')
        if not w.notes_data:
            w.notes_data = notes
        w.on_notes_note_selected(found[0])            # what picking the note in the notes window does
        if not w.notes_active:
            raise ToolError('The note could not be opened (Notes did not give its text).')
        return {'open': w.notes_current_title, 'folder': w.notes_current_folder, 'mode': 'notes'}

    def remove_document(self, a):
        w, ns = self.w, self.ns
        self._not_busy()
        index, name, path = self._find_entry(a.get('name'))
        if index == 0 or 'Note 001' in name:
            raise ToolError('The first document of the list stays (Watermelon always keeps it).')
        settings = ns.get('w4')
        if settings is not None and settings.isVisible():
            raise ToolError('The Settings window is open (it holds the same list). Try again when it is closed.')
        if w.office_panel is not None and self._mode() == 'local' and index == self._current_index():
            self._show_local(0)                      # an Office file saves itself before it is left
        entries = self._entries()
        current = self._current_index()
        keep = [entry for i, entry in enumerate(entries) if i != index]
        new_current = 0 if current == index or current < 0 else (current - 1 if current > index else current)
        data_dir = ns['WATERMELON_DATA_DIR']
        with open(os.path.join(data_dir, 'DoNotDelete.txt'), 'w', encoding='utf-8') as handle:
            handle.write(''.join('%s||%s\n' % entry for entry in keep))
        with open(os.path.join(data_dir, 'Current.txt'), 'w', encoding='utf-8') as handle:
            handle.write(str(new_current))
        w.widget0.blockSignals(True)
        w.widget0.clear()
        w.widget0.addItems([entry[0] for entry in keep])
        w.widget0.setCurrentIndex(new_current)
        w.widget0.blockSignals(False)
        if current == index and not w.notes_mode_enabled:
            w.index_change(new_current)              # the removed one was open: the first document is shown
        return {'removed_from_list': name, 'file_kept': path, 'open': keep[new_current][0] if not w.notes_mode_enabled else None}

    def create_export(self, a):
        w = self.w
        self._not_busy()
        folder = os.path.abspath(os.path.expanduser(str(a.get('folder') or '').strip()))
        if not a.get('folder') or not os.path.isdir(folder):
            raise ToolError('Pass the full path of a folder that exists.')
        self._text_document_open()
        title = (w.widget_notes.currentText().strip() or 'Note') if w.notes_mode_enabled else w.widget0.currentText()
        title = re.sub(r'[/:\n\r\t]+', ' ', title).strip() or 'Note'
        written = w.export_markdown_to(folder, title)
        return {'exported': written}

    def read_bionic_text(self, a):
        text = a.get('text')
        if not isinstance(text, str) or not text.strip():
            raise ToolError('Pass "text".')
        if len(text) > TEXT_LIMIT:
            raise ToolError('At most %d characters at a time.' % TEXT_LIMIT)
        return self.ns['_bionic_transform_text'](text.replace('*', ''))

    def read_outline(self, a=None):
        self._text_document_open()
        headings = [{'line': line + 1, 'level': level, 'title': title}
                    for line, level, title in watermelon_outline.headings_in(self.w.bottom.toPlainText())]
        return {'document': self._open_name(), 'count': len(headings), 'headings': headings}

    # ── attachments ───────────────────────────────────────────────────────────────────────────────────
    def list_attachments(self, a=None):
        self._text_document_open()
        out = []
        for item in self._attachment_items():
            entry = {'name': item['name'], 'path': item['path'], 'kind': item['kind']}
            if item.get('courseware'):
                entry['screenshot_not_in_text'] = True
            else:
                entry['offset'] = item['offset']
            if not os.path.isfile(item['path']):
                entry['missing'] = True
            out.append(entry)
        return {'document': self._open_name(), 'count': len(out), 'attachments': out}

    def create_attachment(self, a):
        w = self.w
        self._not_busy()
        paths = a.get('paths')
        if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p.strip() for p in paths):
            raise ToolError('Pass "paths": a list of full paths.')
        paths = [os.path.abspath(os.path.expanduser(p.strip())) for p in paths]
        missing = [p for p in paths if not os.path.isfile(p)]
        if missing:
            raise ToolError('Not a file on this Mac: %s' % ', '.join(missing))
        at = str(a.get('at') or 'cursor')
        if at not in ('cursor', 'end'):
            raise ToolError('at is "cursor" or "end".')
        self._text_document_open(to_change=True)
        self._notes_save_allowed()
        before = len(watermelon_attachments.attachments_in(w.bottom.toPlainText(), w._attachment_base_dir()))
        if at == 'end':
            cursor = w.bottom.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            w.bottom.setTextCursor(cursor)
        w.insert_files_as_attachments(paths)
        after = len(watermelon_attachments.attachments_in(w.bottom.toPlainText(), w._attachment_base_dir()))
        return {'document': self._open_name(), 'added': after - before, 'attachments_now': after}

    def remove_attachment(self, a):
        w = self.w
        self._not_busy()
        self._text_document_open()
        path = str(a.get('path') or '').strip()
        found = [item for item in self._attachment_items() if item['path'] == path]
        if a.get('offset') is not None:
            try:
                wanted = int(a['offset'])
            except (TypeError, ValueError):
                raise ToolError('offset is a number.')
            found = [item for item in found if int(item.get('offset', -1)) == wanted]
        if not found:
            raise ToolError('The open document has no such attachment. list_attachments shows them.')
        if len(found) > 1:
            raise ToolError('The text names this file %d times; pass the "offset" of the one to remove: %s'
                            % (len(found), ', '.join(str(item['offset']) for item in found)))
        item = found[0]
        if item.get('courseware'):
            w._remove_attachment(item)
            return {'removed': item['name'], 'what': 'the screenshot and its picture file'}
        if not w._attachment_removable(item):
            raise ToolError('The editing box cannot be changed right now.')
        self._notes_save_allowed()
        before = w.bottom.toPlainText()
        w._remove_attachment(item)
        if w.bottom.toPlainText() == before:
            raise ToolError('The text changed meanwhile; list_attachments again.')
        return {'removed': item['name'], 'what': 'its line in the text (the file stays on the disk; the person can undo it)'}

    def read_attachment(self, a):
        path = str(a.get('path') or '').strip()

        def look():
            self._text_document_open()
            return next((dict(item) for item in self._attachment_items() if item['path'] == path), None)

        item = self.runner(look)
        if item is None:
            raise ToolError('The open document has no such attachment. list_attachments shows them.')
        if not os.path.isfile(path):
            raise ToolError('The file is not there any more: %s' % path)
        out = {'name': item['name'], 'path': path, 'kind': item['kind']}
        if item['kind'] in ('pdf', 'office'):
            marks = watermelon_marks.read_marks(path)
            out['marks'] = [{'where': mark.get('where', ''), 'kind': watermelon_marks.KINDS.get(mark.get('kind'), mark.get('kind')),
                             'text': mark.get('text', ''), 'note': mark.get('note', ''), 'by': mark.get('who', '')}
                            for mark in marks[:200]]
            if len(marks) > 200:
                out['marks_note'] = '%d marks; the first 200 are given.' % len(marks)
        if item['kind'] == 'office':
            out.update(clip(watermelon_marks.office_plain_text(path, limit=400000), a))
        elif item['kind'] != 'pdf':
            out['note'] = 'Only PDF and Office attachments have marks or words to read here.'
        return out

    def _screenshots(self, a):
        """(on the main thread) the screenshots asked for, checked."""
        w = self.w
        self._not_busy()
        self._text_document_open(to_change=True)
        self._notes_save_allowed()
        w._ensure_courseware()
        shots = list(w.courseware.shots)
        if not shots:
            raise ToolError('No screenshots are kept for the open document.')
        paths = a.get('paths')
        if paths is None:
            return shots
        if not isinstance(paths, list) or not paths:
            raise ToolError('"paths" is a list of screenshot paths from list_attachments.')
        unknown = [p for p in paths if p not in shots]
        if unknown:
            raise ToolError('Not a screenshot kept for the open document: %s' % ', '.join(str(p) for p in unknown))
        return [p for p in shots if p in paths]

    def create_screenshots_pdf(self, a):
        w = self.w
        chosen = []

        def begin():
            chosen.extend(self._screenshots(a))
            w._save_courseware_pdf(None, list(chosen))

        ok, target, _existing = self._wait_for(self.runner(lambda: (w._ensure_courseware(), w.courseware.pdf_done)[1]),
                                               begin, 80, 'Making the PDF')
        if not ok:
            raise ToolError('The PDF could not be made; the screenshots are kept.')
        return {'pdf': target, 'pages': len(chosen), 'document': self.runner(self._open_name)}

    def update_screenshots_into_document(self, a):
        w = self.w
        chosen = []

        def begin():
            chosen.extend(self._screenshots(a))
            w._add_courseware_pictures(list(chosen))

        result = self._wait_for(self.runner(lambda: (w._ensure_courseware(), w.courseware.pictures_done)[1]),
                                begin, 80, 'Adding the screenshots')
        ok, copies = bool(result[0]), list(result[1] or [])
        if not ok and not copies:
            raise ToolError('The screenshots could not be added; they are kept.')
        return {'added': len(copies), 'files': copies, 'document': self.runner(self._open_name)}

    # ── the cards ─────────────────────────────────────────────────────────────────────────────────────
    def _cards(self):
        w = self.w
        w._ensure_lecture()
        return w.lecture_session.store

    @staticmethod
    def _card_out(card):
        return {key: card.get(key) for key in ('id', 'title', 'body', 'page', 'source', 'document', 'created', 'archived') if key in card}

    def _card(self, a):
        card = self._cards().find(str(a.get('id') or '').strip())
        if card is None:
            raise ToolError('There is no card with this id. list_cards shows them.')
        return card

    def list_cards(self, a):
        store = self._cards()
        which = str(a.get('which') or 'document')
        if which == 'document':
            cards = store.active(self.w._lecture_document_name())
        elif which == 'all':
            cards = store.active()
        elif which == 'archived':
            cards = store.archived()
        else:
            raise ToolError('which is "document", "all" or "archived".')
        words = _words(a.get('text'))
        if words:
            cards = [card for card in cards
                     if all(word in ('%s\n%s' % (card.get('title', ''), card.get('body', ''))).lower() for word in words)]
        try:
            limit = max(1, min(int(a.get('limit') or 50), 200))
        except (TypeError, ValueError):
            raise ToolError('limit is a number.')
        return {'document': self.w._lecture_document_name(), 'count': len(cards), 'cards': [self._card_out(card) for card in cards[:limit]]}

    def _cards_shown_again(self, new_id=''):
        w = self.w
        w.lecture_session.cards_changed.emit(new_id)
        if new_id and not (w.lecture_panel is not None and w.lecture_panel.isVisible()):
            w.side_handles.set_attention('right', True)      # a card nobody saw yet: the dot on the right handle

    def create_card(self, a):
        self._not_busy()
        title, body = str(a.get('title') or '').strip(), str(a.get('body') or '').strip()
        if not title:
            raise ToolError('A card needs a title.')
        store = self._cards()
        card = store.add(title[:300], body[:4000], page=str(a.get('source') or '').strip()[:120], source='page',
                         document=self.w._lecture_document_name())
        self._cards_shown_again(card['id'])
        return {'created': self._card_out(card)}

    def update_card(self, a):
        w = self.w
        self._not_busy()
        card = self._card(a)
        store = self._cards()
        changes = {}
        if a.get('title') is not None:
            if not str(a['title']).strip():
                raise ToolError('A card needs a title.')
            changes['title'] = str(a['title']).strip()[:300]
        if a.get('body') is not None:
            changes['body'] = str(a['body']).strip()[:4000]
        if a.get('archived') is not None:
            changes['archived'] = _flag(a['archived'], 'archived')
        insert = a.get('insert_into_document') is not None and _flag(a['insert_into_document'], 'insert_into_document')
        if not changes and not insert:
            raise ToolError('Pass what to change: title, body, archived or insert_into_document.')
        if insert:
            self._text_document_open(to_change=True)
            self._notes_save_allowed()
        if changes:
            card = store.update(card['id'], **changes)
        if insert:
            w.lecture_panel.insert_card(card)          # the card's own "Insert into Note": into the text, then archived
        self._cards_shown_again('')
        out = {'card': self._card_out(store.find(card['id']))}
        if insert:
            out['inserted_into'] = self._open_name()
        return out

    def delete_card(self, a):
        self._not_busy()
        card = self._card(a)
        self._cards().remove(card['id'])
        self._cards_shown_again('')
        return {'deleted': card.get('title', '')}

    # ── Anki ──────────────────────────────────────────────────────────────────────────────────────────
    def _anki(self):
        return watermelon_anki.AnkiStore(os.path.join(self.ns['WATERMELON_DATA_DIR'], 'Anki'))

    def list_anki_decks(self, a=None):
        store = self._anki()
        decks = []
        for deck in store.decks():
            cards = store.cards(deck)
            decks.append({'deck': deck, 'cards': len(cards), 'basic': sum(1 for c in cards if c.get('type') == 'basic'),
                          'cloze': sum(1 for c in cards if c.get('type') == 'cloze'), 'folder': store.folder(deck)})
        return {'count': len(decks), 'decks': decks}

    def _deck(self, store, name):
        wanted = watermelon_anki.deck_folder_name(name)
        decks = store.decks()
        found = next((deck for deck in decks if deck == wanted), None) or next((deck for deck in decks if deck.lower() == wanted.lower()), None)
        if not wanted or found is None:
            raise ToolError('There is no deck called %r. The decks: %s' % (str(name or ''), ', '.join(decks) or '(none)'))
        return found

    def read_anki_deck(self, a):
        store = self._anki()
        deck = self._deck(store, a.get('deck'))
        cards = store.cards(deck)
        try:
            skip, limit = max(0, int(a.get('skip') or 0)), max(1, min(int(a.get('limit') or 50), 200))
        except (TypeError, ValueError):
            raise ToolError('skip and limit are numbers.')
        keys = ('type', 'front', 'back', 'text', 'extra', 'source', 'created')
        return {'deck': deck, 'count': len(cards), 'folder': store.folder(deck),
                'cards': [{key: card[key] for key in keys if card.get(key)} for card in cards[skip:skip + limit]]}

    def create_anki_cards(self, a):
        store = self._anki()
        deck = watermelon_anki.deck_folder_name(a.get('deck'))
        if not deck:
            raise ToolError('Pass the deck\'s name.')
        deck = next((have for have in store.decks() if have.lower() == deck.lower()), deck)
        given = a.get('cards')
        if not isinstance(given, list) or not given:
            raise ToolError('Pass "cards": a list of cards.')
        if len(given) > 200:
            raise ToolError('At most 200 cards at a time.')
        cards = [card for card in (watermelon_anki._clean(item) for item in given) if card]
        if not cards:
            raise ToolError('No card was whole. A card is {"type": "basic", "front", "back"} or {"type": "cloze", "text" with '
                            '{{c1::…}}, "extra"}.')
        added = store.add(deck, cards, source='tools')
        return {'deck': deck, 'added': added, 'already_there': len(cards) - added, 'not_whole': len(given) - len(cards),
                'cards_now': len(store.cards(deck)), 'folder': store.folder(deck),
                'note': 'To use them, the person imports the files in the folder into Anki (File › Import).'}

    # ── Apple Notes ───────────────────────────────────────────────────────────────────────────────────
    def _note_list(self):
        notes, error = self.ns['_read_notes_cache'](self.w.notes_cache_path)
        if error:
            raise ToolError('Watermelon has no list of the notes yet. update_view with mode "notes" first, then try again in a moment.')
        return notes

    @staticmethod
    def _note_folder(note):
        return (note.get('folder') or 'Unfiled').strip() or 'Unfiled'

    def list_notes(self, a):
        notes = self._note_list()
        folder, words = str(a.get('folder') or '').strip(), _words(a.get('text'))
        try:
            limit = max(1, min(int(a.get('limit') or 50), 500))
        except (TypeError, ValueError):
            raise ToolError('limit is a number.')
        folders = sorted({self._note_folder(note) for note in notes})
        chosen = [note for note in notes if (not folder or self._note_folder(note) == folder)
                  and all(word in (note.get('title') or '').lower() for word in words)]
        chosen.sort(key=lambda note: -(note.get('created') or 0))
        out = []
        for note in chosen[:limit]:
            entry = {'folder': self._note_folder(note), 'title': note.get('title') or '(Untitled)'}
            if note.get('created'):
                entry['created'] = datetime.datetime.fromtimestamp(float(note['created'])).isoformat(timespec='seconds')
            out.append(entry)
        return {'count': len(chosen), 'folders': folders, 'notes': out}

    def read_note(self, a):
        title, folder = str(a.get('title') or '').strip(), str(a.get('folder') or '').strip()
        if not title:
            raise ToolError('Pass the note\'s title.')

        def look():
            w = self.w
            notes = self._note_list()
            found = [note for note in notes if (note.get('title') or '(Untitled)') == title
                     and (not folder or self._note_folder(note) == folder)]
            if not found:
                raise ToolError('No note is called %r%s. list_notes shows them.' % (title, (' in "%s"' % folder) if folder else ''))
            if len(found) > 1 and not folder:
                raise ToolError('Several notes are called %r; pass folder: %s' % (title, ', '.join(sorted({self._note_folder(n) for n in found}))))
            note = found[0]
            if w.notes_mode_enabled and w.notes_active and w.notes_current_title == title \
                    and (w.notes_current_folder or 'Unfiled') == self._note_folder(note):
                return note, w.bottom.toPlainText()      # the open note, as it stands in the editing box
            return note, None

        note, text = self.runner(look)
        if text is None:
            text, _fingerprint = self.ns['_load_note_markdown'](self._note_folder(note), title, note.get('id'))
            if text is None:
                raise ToolError('Notes did not give this note\'s text (it may have been deleted or renamed).')
        out = {'folder': self._note_folder(note), 'title': title}
        out.update(clip(text, a))
        return out

    def _make_note(self, folder, title, markdown):
        """On the service's thread (it asks Notes, which takes a moment). → the folder the note is in."""
        w = self.w
        html = watermelon_notes.markdown_to_notes_html(markdown)
        made_in = w._create_note_in_folder(folder, title, html)
        self.runner(w._request_notes_cache_refresh)
        return made_in or folder or 'Notes'

    def create_note(self, a):
        title = re.sub(r'\s+', ' ', str(a.get('title') or '')).strip()
        if not title:
            raise ToolError('Pass the note\'s title.')
        text = str(a.get('text') or '')
        folder = str(a.get('folder') or '').strip()

        def look():
            self._not_busy()
            return folder or self.w.notes_current_folder or ''

        folder = self.runner(look)
        try:
            made_in = self._make_note(folder, title, text)
        except ToolError:
            raise
        except Exception as exc:
            raise ToolError('Notes did not make the note: %s' % (str(exc)[:300] or type(exc).__name__))
        return {'created': title, 'folder': made_in,
                'note': 'It appears in list_notes once Watermelon has listed the notes again (a few seconds).'}

    # ── the web page ──────────────────────────────────────────────────────────────────────────────────
    def _tabs(self):
        panel = self.w.web_panel
        tabs = []
        for index, site in enumerate(panel._sites):
            view = panel._views[index] if index < len(panel._views) else None
            url = site.get('url') or ''
            if view is not None and not bool(view.property('wm_start_page')) and view.url().toString().startswith('http'):
                url = view.url().toString()
            tabs.append({'tab': index + 1, 'label': site.get('label') or '', 'url': url, 'shown': index == panel._active_idx})
        return tabs

    def read_web_page(self, a):
        w = self.w
        box, done = {}, threading.Event()

        def begin():
            panel = w.web_panel
            if panel is None:
                raise ToolError('The web page has not been opened in this run. update_web_page first.')
            box['tabs'] = self._tabs()
            box['in_web_mode'] = bool(w.web_mode_enabled)
            view = panel.active_view()
            if view is None or bool(view.property('wm_start_page')):
                box['empty'] = True
                done.set()
                return
            box['url'], box['title'] = view.url().toString(), view.page().title()
            box['selected'] = view.page().selectedText() or ''

            def got(text):
                box['text'] = text
                done.set()
            view.page().toPlainText(got)

        self.runner(begin)
        if not done.wait(30):
            raise ToolError('The page did not give its text within 30 seconds (it may still be loading).')
        out = {'in_web_mode': box['in_web_mode'], 'tabs': box['tabs']}
        if box.get('empty'):
            out['page'] = None
            out['note'] = 'The shown tab is the start page: no web page is open in it.'
            return out
        out.update(url=box['url'], title=box['title'])
        if box['selected']:
            out['selected_text'] = box['selected'][:4000]
        out.update(clip(box.get('text') or '', a))
        return out

    def update_web_page(self, a):
        w, ns = self.w, self.ns
        self._not_busy()
        url, action, tab = str(a.get('url') or '').strip(), a.get('action'), a.get('tab')
        if sum(1 for x in (url, action, tab) if x) != 1:
            raise ToolError('Pass exactly one of: url, action, tab.')
        if action is not None and action not in ('back', 'forward', 'reload'):
            raise ToolError('action is "back", "forward" or "reload".')
        address = ''
        if url:
            address = ns['_normalize_web_input'](url)
            if not re.match(r'^https?://', address, re.I):
                raise ToolError('Only http and https addresses are opened.')
        self._set_mode('web')
        panel = w.web_panel
        if url:
            if a.get('new_tab') is not None and _flag(a['new_tab'], 'new_tab'):
                panel.open_saved_url(address)
            else:
                w.web_address.setText(url)
                w._web_address_submitted()            # what Return in the address field does
            return {'going_to': address, 'tabs': self._tabs(), 'note': 'The page is loading; read_web_page in a moment.'}
        if action:
            {'back': w.web_go_back, 'forward': w.web_go_forward, 'reload': w.web_reload}[action]()
            return {'done': action, 'note': 'read_web_page in a moment.'}
        try:
            index = int(tab) - 1
        except (TypeError, ValueError):
            raise ToolError('tab is a number from read_web_page.')
        if not 0 <= index < len(panel._views):
            raise ToolError('There are %d tabs.' % len(panel._views))
        panel._nav._select(index)                     # what a click on the tab does
        return {'tabs': self._tabs()}

    def create_document_from_web_page(self, a):
        w = self.w
        target = str(a.get('target') or 'local')
        if target not in ('local', 'notes'):
            raise ToolError('target is "local" or "notes".')
        box, done = {}, threading.Event()

        def begin():
            self._not_busy()
            if w.web_panel is None or not w.web_mode_enabled:
                raise ToolError('Watermelon is not in web mode. update_web_page first.')

            def got(title, markdown, error):
                box.update(title=title, markdown=markdown, error=error)
                done.set()
            w.web_panel.extract_active_markdown(got)   # what Save to Local / Save to Notes take from the page

        self.runner(begin)
        if not done.wait(60):
            raise ToolError('The page did not give its content within 60 seconds.')
        if box.get('error') or not str(box.get('markdown') or '').strip():
            raise ToolError(str(box.get('error') or 'Nothing to save.'))
        title, markdown = box.get('title') or 'Web Clip', box['markdown']
        if target == 'local':
            name = self.runner(lambda: w._save_markdown_as_local_file(title, markdown))
            if not name:
                raise ToolError('The file could not be saved.')
            return {'created': name, 'where': 'local documents', 'characters': len(markdown)}
        folder = self.runner(lambda: w.notes_current_folder or '')
        try:
            made_in = self._make_note(folder, title, markdown)
        except Exception as exc:
            raise ToolError('Notes did not make the note: %s' % (str(exc)[:300] or type(exc).__name__))
        return {'created': title, 'where': 'Apple Notes', 'folder': made_in, 'characters': len(markdown)}

    # ── settings ──────────────────────────────────────────────────────────────────────────────────────
    def _settings_window(self):
        window = self.ns.get('w4')
        if window is None:
            raise ToolError('The settings are not ready yet. Try again in a moment.')
        return window

    def _card_language(self):
        return watermelon_lecture.LectureSettings(self.ns['SettingsPath'] + 'lecture.json').get('language') or ''

    def read_settings(self, a=None):
        w, ns = self.w, self.ns
        s = self._settings_window()
        fonts = [s.widget1.itemText(i) for i in range(2, s.widget1.count())]
        return {'font': w._current_font_family, 'font_size': w._current_font_size,
                'always_on_top': bool(w.is_always_on_top()), 'eye_care_background': ns['_read_bg_pref']() == 'cream',
                'scroll_together': bool(s.checkBox0.isChecked()),
                'card_language': self._card_language(), 'card_languages': [code for code, _name in watermelon_lecture.LANGUAGES],
                'backup_limit': ns['load_mode_backup_limit'](),
                'backup_limit_range': [ns['MODE_BACKUP_LIMIT_MIN'], ns['MODE_BACKUP_LIMIT_MAX']],
                'dock_icon': bool(ns['action_dock_icon'].isChecked()), 'all_spaces': bool(ns['action_all_spaces'].isChecked()),
                'interface_language': ns['UI_LANGUAGE'], 'fonts_available': len(fonts),
                'note': 'update_settings takes a font family installed on this Mac (or "default").'}

    def update_settings(self, a):
        w, ns = self.w, self.ns
        self._not_busy()
        s = self._settings_window()
        known = ('font_size', 'font', 'always_on_top', 'eye_care_background', 'scroll_together', 'card_language',
                 'backup_limit', 'dock_icon', 'all_spaces')
        if not any(a.get(key) is not None for key in known):
            raise ToolError('Pass at least one of: %s.' % ', '.join(known))
        # everything is checked before anything is changed
        size = font_index = language_index = backups = None
        if a.get('font_size') is not None:
            try:
                size = int(a['font_size'])
            except (TypeError, ValueError):
                raise ToolError('font_size is a number.')
            slider = s.findChild(QSlider)
            if slider is None or not slider.minimum() <= size <= slider.maximum():
                raise ToolError('font_size is from 14 to 50.')
        if a.get('font') is not None:
            wanted = str(a['font']).strip()
            if wanted.lower() == 'default':
                font_index = 1
            else:
                names = [s.widget1.itemText(i) for i in range(s.widget1.count())]
                font_index = next((i for i in range(2, len(names)) if names[i] == wanted), None)
                if font_index is None:
                    font_index = next((i for i in range(2, len(names)) if names[i].lower() == wanted.lower()), None)
                if font_index is None:
                    close = [name for name in names[2:] if wanted.lower() in name.lower()][:12]
                    raise ToolError('This Mac has no font family called %r.%s' % (wanted, (' Close: ' + ', '.join(close)) if close else ''))
        codes = [code for code, _name in watermelon_lecture.LANGUAGES]
        if a.get('card_language') is not None:
            if a['card_language'] not in codes:
                raise ToolError('card_language is one of: %s' % ', '.join(repr(code) for code in codes))
            language_index = codes.index(a['card_language'])
        if a.get('backup_limit') is not None:
            try:
                backups = int(a['backup_limit'])
            except (TypeError, ValueError):
                raise ToolError('backup_limit is a number.')
            if not ns['MODE_BACKUP_LIMIT_MIN'] <= backups <= ns['MODE_BACKUP_LIMIT_MAX']:
                raise ToolError('backup_limit is from %d to %d.' % (ns['MODE_BACKUP_LIMIT_MIN'], ns['MODE_BACKUP_LIMIT_MAX']))
        flags = {key: _flag(a[key], key) for key in ('always_on_top', 'eye_care_background', 'scroll_together', 'dock_icon', 'all_spaces')
                 if a.get(key) is not None}
        changed = []
        # the same controls the Settings window and the menu use, so both keep showing what is set
        if size is not None and size != w._current_font_size:
            s.findChild(QSlider).setValue(size)                   # → value_change
            changed.append('font_size')
        if font_index is not None:
            if s.widget1.currentIndex() != font_index:
                s.widget1.setCurrentIndex(font_index)             # → font_change
            else:
                s.font_change(font_index)
            changed.append('font')
        if 'always_on_top' in flags and flags['always_on_top'] != bool(w.is_always_on_top()):
            s.checkBox_top.setChecked(flags['always_on_top'])
            s.toggle_on_top()
            changed.append('always_on_top')
        if 'eye_care_background' in flags and flags['eye_care_background'] != (ns['_read_bg_pref']() == 'cream'):
            s.checkBox_eye_care.setChecked(flags['eye_care_background'])
            s.toggle_bg_color()
            changed.append('eye_care_background')
        if 'scroll_together' in flags and flags['scroll_together'] != bool(s.checkBox0.isChecked()):
            s.checkBox0.setChecked(flags['scroll_together'])
            s.auto_scroll()
            changed.append('scroll_together')
        if language_index is not None and codes[language_index] != self._card_language():
            if s.widget_lecture_language.currentIndex() != language_index:
                s.widget_lecture_language.setCurrentIndex(language_index)     # → lecture_language_change
            else:
                s.lecture_language_change(language_index)
            changed.append('card_language')
        if backups is not None and backups != ns['load_mode_backup_limit']():
            ns['_set_backup_limit_from_menu'](backups)
            changed.append('backup_limit')
        if 'dock_icon' in flags and flags['dock_icon'] != bool(ns['action_dock_icon'].isChecked()):
            ns['action_dock_icon'].setChecked(flags['dock_icon'])
            ns['_toggle_dock_icon'](flags['dock_icon'])
            changed.append('dock_icon')
        if 'all_spaces' in flags and flags['all_spaces'] != bool(ns['action_all_spaces'].isChecked()):
            ns['action_all_spaces'].setChecked(flags['all_spaces'])
            ns['_toggle_all_spaces'](flags['all_spaces'])
            changed.append('all_spaces')
        out = self.read_settings()
        out['changed'] = changed
        return out

    # ── backups ───────────────────────────────────────────────────────────────────────────────────────
    def _backup_folder(self):
        """(on the main thread) (the open document's name, the folder its backups are in or '')."""
        w = self.w
        if w.web_mode_enabled:
            raise ToolError('Watermelon is in web mode: no document is open.')
        if w.notes_mode_enabled:
            key = w._current_notes_key()
            if not key or not w.notes_mode_backup_root:
                raise ToolError('No note is open.')
            return w.notes_current_title, w._backup_target_dir(w.notes_mode_backup_root, w.notes_current_title or 'Untitled', key)
        path = w._current_local_file_path()
        if not path or not w.local_mode_backup_root:
            raise ToolError('No document is open.')
        return w.widget0.currentText(), w._backup_target_dir(w.local_mode_backup_root, os.path.splitext(os.path.basename(path))[0], path)

    def list_backups(self, a=None):
        name, folder = self.runner(self._backup_folder)
        files = []
        try:
            names = os.listdir(folder)
        except OSError:
            names = []
        for entry in names:
            full = os.path.join(folder, entry)
            if entry.startswith('.') or not os.path.isfile(full):
                continue
            files.append({'file': entry, 'saved': datetime.datetime.fromtimestamp(os.path.getmtime(full)).isoformat(timespec='seconds'),
                          'size': os.path.getsize(full), 'text': entry.lower().endswith('.md')})
        files.sort(key=lambda item: (item['saved'], item['file']), reverse=True)      # the file's name is its time, to the microsecond
        return {'document': name, 'count': len(files), 'backups': files}

    def read_backup(self, a):
        wanted = os.path.basename(str(a.get('file') or '').strip())
        name, folder = self.runner(self._backup_folder)
        full = os.path.join(folder, wanted)
        if not wanted or wanted.startswith('.') or not os.path.isfile(full):
            raise ToolError('The open document has no backup called %r. list_backups shows them.' % wanted)
        if not wanted.lower().endswith('.md'):
            raise ToolError('This backup is a whole Office file, not text.')
        with open(full, encoding='utf-8') as handle:
            text = handle.read()
        out = {'document': name, 'file': wanted}
        out.update(clip(text, a))
        return out
