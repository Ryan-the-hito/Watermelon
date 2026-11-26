# -*- coding: utf-8 -*-
"""Watermelon: what a reader marked in an attachment — highlights, comments, notes (2026-11-21).

UI STYLE BOOK: /Users/ryanshen/Documents/A-workingfilewithp3.11/UI_STYLEBOOK_macOS27.md (5.14)
Ryan 2026-11-21: "打开一些 PDF 的时候，PDF 里面有注释或者用户自己加的 notes。这个应该是可以读出来的，比如用户高亮了
什么文字之类的，我希望这些在附件里如果添加的时候读出来了，显示在右边 panel…但是只有一开始的时候，意思是不要重复跳，
或者后面附件我加了什么笔记之后，它跳一次。不要每次打开都跳"; Word / Excel / PowerPoint too ("希望都做"),
PowerPoint's speaker notes count ("算"); drawings by hand are skipped ("手写的跳过可，高亮、批注有文字的需要做").

  read_marks(path)     [{'where', 'page', 'kind', 'text', 'note', 'who'}] of a PDF (the system's PDF kit) or a
                       .docx / .xlsx / .pptx (read straight from the file, no library)
  office_plain_text    the text of a Word / Excel / PowerPoint file (for the AI panel)
  SeenMarks            which marks were shown already — a mark is shown ONCE; one added or changed later is
                       shown once more. Known by the file's NAME and the mark itself, not by the folder the
                       file is in (a note's attachment is fetched to a new place every time).
  MarkWatcher          reads the files given to it on a thread, again when one of them changes (the files
                       are watched, nothing is polled), and hands out the marks not shown before
Import this module AFTER the QApplication exists.
"""
import hashlib
import json
import logging
import os
import posixpath
import re
import threading
import zipfile
import xml.etree.ElementTree as ET

from PyQt6.QtCore import QFileSystemWatcher, QObject, pyqtSignal

KINDS = {'Highlight': 'Highlight', 'Underline': 'Underline', 'StrikeOut': 'Strikethrough', 'Squiggly': 'Underline',
         'Text': 'Note', 'FreeText': 'Note', 'Comment': 'Comment', 'Speaker notes': 'Speaker notes'}
OFFICE_EXTS = ('.docx', '.xlsx', '.pptx')
MAX_MARKS_PER_FILE = 300
_W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
_P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
_S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
_R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
_REL = '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'
_RADICALS = None


def _plain(text) -> str:
    """One line, the look-alike radical signs some PDFs give back (⽜ ⼒ ⽐) as ordinary characters."""
    global _RADICALS
    if _RADICALS is None:
        import unicodedata
        _RADICALS = {code: unicodedata.normalize('NFKC', chr(code)) for code in list(range(0x2F00, 0x2FD6)) + list(range(0x2E80, 0x2EF4))
                     if unicodedata.normalize('NFKC', chr(code)) != chr(code)}
    return re.sub(r'[\x00-\x20\x7f]+', ' ', str(text or '').translate(_RADICALS)).strip()


def _mark(where, kind, text='', note='', who='', page=-1):
    return {'where': str(where or ''), 'page': int(page), 'kind': kind, 'text': _plain(text), 'note': str(note or '').strip(),
            'who': str(who or '').strip()}


def _other_person(name) -> str:
    """Who wrote a mark — '' when it is the person at this Mac (their own marks need no name on them)."""
    name = str(name or '').strip()
    try:
        from Foundation import NSFullUserName, NSUserName
        mine = {str(NSFullUserName() or '').strip().lower(), str(NSUserName() or '').strip().lower()}
    except Exception:
        mine = set()
    return '' if name.lower() in mine else name


# ── PDF ──────────────────────────────────────────────────────────────────────────────────────────────
def _read_pdf(path):
    import objc
    import Quartz
    from Foundation import NSURL
    out = []
    with objc.autorelease_pool():
        document = Quartz.PDFDocument.alloc().initWithURL_(NSURL.fileURLWithPath_(path))
        if document is None:
            return out
        for index in range(document.pageCount()):
            page = document.pageAtIndex_(index)
            for annotation in page.annotations() or []:
                kind = str(annotation.type() or '')
                if kind not in ('Highlight', 'Underline', 'StrikeOut', 'Squiggly', 'Text', 'FreeText'):
                    continue                      # links, form fields, drawings by hand, stamps …
                under = ''
                if kind in ('Highlight', 'Underline', 'StrikeOut', 'Squiggly'):
                    bounds = annotation.bounds()      # a little inside the mark: the lines above and below are not taken along
                    inner = Quartz.CGRectInset(bounds, min(1.0, bounds.size.width / 4.0), bounds.size.height * 0.3)
                    selection = page.selectionForRect_(inner)
                    under = str(selection.string() or '') if selection is not None else ''
                note = str(annotation.contents() or '')
                if not _plain(under) and not note.strip():
                    continue
                if out and out[-1]['page'] == index and out[-1]['kind'] == kind and kind != 'Text' \
                        and out[-1]['note'] == note.strip() and kind != 'FreeText':
                    out[-1]['text'] = (out[-1]['text'] + ' ' + _plain(under)).strip()   # one highlight over several lines
                    continue
                out.append(_mark('p.%d' % (index + 1), kind, under, note, _other_person(annotation.userName()), index))
                if len(out) >= MAX_MARKS_PER_FILE:
                    return out
    return out


# ── Word / Excel / PowerPoint: the files are zip folders of XML ─────────────────────────────────────
def _xml(archive, name):
    try:
        return ET.fromstring(archive.read(name))
    except Exception:
        return None


def _texts(node, tag) -> str:
    return ''.join(part.text or '' for part in node.iter(tag))


def _relations(archive, part: str) -> list:
    """[(type's last word, target part)] of a part of the file."""
    folder, name = posixpath.split(part)
    root = _xml(archive, posixpath.join(folder, '_rels', name + '.rels')) if posixpath.join(folder, '_rels', name + '.rels') in archive.namelist() else None
    out = []
    for relation in (root.iter(_REL) if root is not None else []):
        target = relation.get('Target') or ''
        if relation.get('TargetMode') == 'External' or not target:
            continue
        target = target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(folder, target))
        out.append(((relation.get('Type') or '').rsplit('/', 1)[-1], target, relation.get('Id') or ''))
    return out


def _read_docx(archive):
    out = []
    body = _xml(archive, 'word/document.xml')
    if body is None:
        return out
    notes = {}
    comments = _xml(archive, 'word/comments.xml') if 'word/comments.xml' in archive.namelist() else None
    for comment in (comments.iter(_W + 'comment') if comments is not None else []):
        paragraphs = [_texts(p, _W + 't') for p in comment.iter(_W + 'p')]
        notes[comment.get(_W + 'id')] = ('\n'.join(p for p in paragraphs if p.strip()), _other_person(comment.get(_W + 'author')))
    open_ids, marked, order = set(), {}, []
    highlight = None
    for node in body.iter():
        if node.tag == _W + 'commentRangeStart':
            open_ids.add(node.get(_W + 'id'))
            order.append(node.get(_W + 'id'))
        elif node.tag == _W + 'commentRangeEnd':
            open_ids.discard(node.get(_W + 'id'))
        elif node.tag == _W + 'p':
            highlight = None                       # a highlight does not run on into the next paragraph
        elif node.tag == _W + 'r':
            text = _texts(node, _W + 't')
            for comment_id in open_ids:
                marked[comment_id] = marked.get(comment_id, '') + text
            properties = node.find(_W + 'rPr')
            lit = properties is not None and properties.find(_W + 'highlight') is not None \
                and properties.find(_W + 'highlight').get(_W + 'val') != 'none'
            if lit and text.strip():
                if highlight is None:
                    highlight = _mark('', 'Highlight', text)
                    highlight['_raw'] = text
                    out.append(highlight)
                else:
                    highlight['_raw'] += text
                    highlight['text'] = _plain(highlight['_raw'])
            elif text:
                highlight = None
    for item in out:
        item.pop('_raw', None)
    for comment_id in order + [key for key in notes if key not in order]:
        if comment_id in notes and notes[comment_id][0].strip():
            note, who = notes.pop(comment_id)
            out.append(_mark('', 'Comment', marked.get(comment_id, ''), note, who))
    return out


def _read_xlsx(archive):
    out = []
    book = _xml(archive, 'xl/workbook.xml')
    if book is None:
        return out
    targets = {rel_id: target for _kind, target, rel_id in _relations(archive, 'xl/workbook.xml')}
    for sheet in book.iter(_S + 'sheet'):
        part = targets.get(sheet.get(_R + 'id') or '')
        if not part:
            continue
        for kind, target, _id in _relations(archive, part):
            if kind not in ('comments', 'threadedComment') or target not in archive.namelist():
                continue
            root = _xml(archive, target)
            for comment in (root.iter() if root is not None else []):
                if comment.tag.endswith('}comment') or comment.tag.endswith('}threadedComment'):
                    text = ''.join(part.text or '' for part in comment.iter() if part.tag.endswith('}t') or part.tag.endswith('}text'))
                    if text.strip():
                        out.append(_mark('%s!%s' % (sheet.get('name') or '', comment.get('ref') or ''), 'Comment', '', text))
    seen, unique = set(), []
    for item in out:                              # a threaded comment is also kept as an old-style one
        key = (item['where'], re.sub(r'\s+', '', item['note'])[-40:])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _read_pptx(archive):
    out = []
    deck = _xml(archive, 'ppt/presentation.xml')
    if deck is None:
        return out
    targets = {rel_id: target for _kind, target, rel_id in _relations(archive, 'ppt/presentation.xml')}
    number = 0
    for slide in deck.iter(_P + 'sldId'):
        part = targets.get(slide.get(_R + 'id') or '')
        if not part:
            continue
        number += 1
        where = 'slide %d' % number
        for kind, target, _id in _relations(archive, part):
            if target not in archive.namelist():
                continue
            root = _xml(archive, target)
            if root is None:
                continue
            if kind == 'comments':                 # the old kind (p:cm with p:text) and the new (…:cm with a text body)
                for comment in root.iter():
                    if comment.tag.endswith('}cm'):
                        text = ''.join(part.text or '' for part in comment.iter() if part.tag.endswith('}text') or part.tag.endswith('}t'))
                        if text.strip():
                            out.append(_mark(where, 'Comment', '', text, '', number - 1))
            elif kind == 'notesSlide':
                for shape in root.iter(_P + 'sp'):
                    holder = shape.find('.//' + _P + 'ph')
                    if holder is not None and holder.get('type') == 'body':
                        paragraphs = [_texts(p, _A + 't') for p in shape.iter(_A + 'p')]
                        text = '\n'.join(p for p in paragraphs if p.strip())
                        if text.strip():
                            out.append(_mark(where, 'Speaker notes', '', text, '', number - 1))
    return out


def read_marks(path: str) -> list:
    """What was marked in the file; [] for a file without marks, of another type, or unreadable. Blocks."""
    extension = os.path.splitext(path)[1].lower()
    try:
        if extension == '.pdf':
            return _read_pdf(path)
        if extension in OFFICE_EXTS:
            with zipfile.ZipFile(path) as archive:
                reader = {'.docx': _read_docx, '.xlsx': _read_xlsx, '.pptx': _read_pptx}[extension]
                return reader(archive)[:MAX_MARKS_PER_FILE]
    except Exception:
        logging.exception('Reading the marks in %s failed.', os.path.basename(path))
    return []


def office_plain_text(path: str, limit: int = 20000) -> str:
    """The words of a Word / Excel / PowerPoint file, in order."""
    extension = os.path.splitext(path)[1].lower()
    parts = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if extension == '.docx':
                body = _xml(archive, 'word/document.xml')
                parts = [_texts(p, _W + 't') for p in (body.iter(_W + 'p') if body is not None else [])]
            elif extension == '.pptx':
                for name in sorted((n for n in names if re.match(r'ppt/slides/slide\d+\.xml$', n)), key=lambda n: int(re.findall(r'\d+', n)[-1])):
                    root = _xml(archive, name)
                    parts += [_texts(p, _A + 't') for p in (root.iter(_A + 'p') if root is not None else [])]
            elif extension == '.xlsx':
                shared = _xml(archive, 'xl/sharedStrings.xml') if 'xl/sharedStrings.xml' in names else None
                parts = [_texts(item, _S + 't') for item in (shared.iter(_S + 'si') if shared is not None else [])]
    except Exception:
        logging.exception('Reading the text of %s failed.', os.path.basename(path))
    return '\n'.join(part for part in parts if part.strip())[:limit]


def mark_key(path: str, mark: dict) -> str:
    """What makes a mark the same mark the next time: the file's name, where it is, what kind, the words."""
    parts = (os.path.basename(path), mark.get('where', ''), mark.get('kind', ''), mark.get('text', ''), mark.get('note', ''))
    return hashlib.sha1('\x1f'.join(parts).encode('utf-8')).hexdigest()[:20]


class SeenMarks:
    MAX = 50000

    def __init__(self, path: str):
        self.path = path
        try:
            with open(path, encoding='utf-8') as handle:
                self._keys = list(json.load(handle).get('seen', []))
        except Exception:
            self._keys = []
        self._set = set(self._keys)
        self._lock = threading.Lock()

    def unseen(self, path: str, marks: list) -> list:
        return [mark for mark in marks if mark_key(path, mark) not in self._set]

    def remember(self, path: str, marks: list):
        new = [key for key in (mark_key(path, mark) for mark in marks) if key not in self._set]
        if not new:
            return
        self._keys = (self._keys + new)[-self.MAX:]
        self._set = set(self._keys)
        snapshot = {'seen': list(self._keys)}

        def work():
            with self._lock:
                try:
                    os.makedirs(os.path.dirname(self.path), exist_ok=True)
                    with open(self.path + '.tmp', 'w', encoding='utf-8') as handle:
                        json.dump(snapshot, handle)
                    os.replace(self.path + '.tmp', self.path)
                except Exception:
                    logging.exception('Saving which marks were shown failed.')

        threading.Thread(target=work, daemon=True, name='watermelon-marks-seen').start()


class MarkWatcher(QObject):
    """`new_marks(path, marks)`: marks of this file that were never shown (already remembered as shown)."""
    new_marks = pyqtSignal(str, list)
    _read = pyqtSignal(str, object, list)

    def __init__(self, seen: SeenMarks, parent=None):
        super().__init__(parent)
        self.seen = seen
        self._files = {}                 # path → (mtime, size) it was last read at
        self._reading = set()
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._check)
        self._read.connect(self._on_read)

    def set_files(self, paths):
        """The files to look at now (the attachments of the open note, an Office file open in the editor)."""
        paths = [path for path in dict.fromkeys(paths) if os.path.splitext(path)[1].lower() in ('.pdf',) + OFFICE_EXTS]
        for gone in [path for path in self._files if path not in paths]:
            del self._files[gone]
            if gone in self._watcher.files():
                self._watcher.removePath(gone)
        for path in paths:
            self._files.setdefault(path, None)
            self._check(path)

    def _check(self, path):
        if path not in self._files:
            return
        if os.path.exists(path) and path not in self._watcher.files():
            self._watcher.addPath(path)          # a file saved by replacing it is a new file: watch that one
        try:
            status = os.stat(path)
        except OSError:
            return
        stamp = (status.st_mtime_ns, status.st_size)
        if self._files.get(path) == stamp or path in self._reading:
            return
        self._reading.add(path)

        def work():
            self._read.emit(path, stamp, read_marks(path))

        threading.Thread(target=work, daemon=True, name='watermelon-marks-read').start()

    def _on_read(self, path, stamp, marks):
        self._reading.discard(path)
        if path not in self._files:
            return
        self._files[path] = stamp
        fresh = self.seen.unseen(path, marks)
        if fresh:
            self.seen.remember(path, fresh)
            self.new_marks.emit(path, fresh)
        self._check(path)                        # it changed again while it was read
