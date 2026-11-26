# -*- coding: utf-8 -*-
"""Watermelon ↔ Apple Notes: every Markdown format, both ways (2026-11-20).

Ryan 2026-11-20: "与 apple notes 联通的部分…手动转译一些格式，但是不全…把所有的都加上…分隔线…超链接";
"图片和文件视频等重点是插入的位置要保持不变"; stand-ins for what Notes cannot keep: "用替身没问题，改".

What Notes keeps through AppleScript's `body` was measured on macOS 27.2.1 (five test notes); the facts
this file relies on:
  - kept: <hr>, <a href>, bold / italic / strike / underline, text colour, h1 (24 px) h2 (18 px) h3 (bold in
    the system bold font), inline code (Courier 12 px), code lines (<font face="Courier"><tt>), tables,
    nested lists (the nested list is the SIBLING of its <li>), ☐ ☑ as characters;
  - not kept: block quotes, task check boxes, highlight, sub / superscript, alignment, anything hidden,
    <br> inside <p>; two lists in a row are merged into one unless something stands between them;
  - a file named by <img src="file://…"> becomes a real attachment AT THAT PLACE, whatever its type
    (picture, PDF, Word, zip, video) — but only when Notes may read it: /Volumes/<UUID>/ is such a place
    (Broccoli's finding, 2026-11-14). Reading back: a picture is <img src="data:…">, any other file is
    <div><br><br></div>; `attachments of note` come in the order they stand in the text and can be
    saved byte for byte. PDFs appear in that list a few seconds late.
  - setting the body again replaces the attachments by the ones the new body names.

Three parts:
  markdown_to_notes_html(md)            Markdown → the HTML Notes keeps (stand-ins: ▎ grey line = quote,
                                        ☐ ☑ = task); local files are marked for run_with_attachments
  notes_html_to_markdown(html, refs)    what Notes gives back → Markdown (refs: one Markdown reference per
                                        attachment place, in order)
  NoteMemory                            the Markdown a note was written from, kept with the fingerprint of
                                        the body Notes then had: a note nobody changed in Notes comes back
                                        exactly as it was typed (highlight, alignment, code language …).
No Qt in this file.
"""
import hashlib
import html as html_lib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import uuid

import markdown2
from bs4 import BeautifulSoup, NavigableString, Tag

QUOTE_BAR = '▎'
QUOTE_COLOR = '#8E8E93'
TASK_OPEN, TASK_DONE = '☐', '☑'
H3_MARK = '\u200b'                # (was tried as a heading mark; Notes drops it — only stripped when met)
JOINER = '\u2060'                 # (stripped when met)
DASH_MARK = '\ue000'              # private, only inside this file: an item typed with "+ " (Notes' dashed list)
HIGHLIGHT_COLOR = '#B45FE6'       # the stand-in for ==highlight== (no door into Notes writes its real highlight)
ATTACH_SCHEME = 'wm-attach://'
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.heic', '.heif', '.webp', '.tiff', '.tif', '.bmp', '.svg')
_MONO_FACES = ('courier', 'menlo', 'monaco', 'sf mono', 'sfmono', 'andale mono', 'consolas')
_MD_EXTRAS = ['fenced-code-blocks', 'tables', 'strike', 'task_list', 'cuddled-lists', 'code-friendly']


# ── Markdown → Notes ──────────────────────────────────────────────────────────────────────────────────
def local_path_of(reference: str) -> str:
    """The existing local file a Markdown image / link target names, or ''."""
    ref = str(reference or '').strip()
    if ref.startswith('file://'):
        ref = urllib.parse.unquote(urllib.parse.urlparse(ref).path)
    elif ref.startswith('~'):
        ref = os.path.expanduser(ref)
    elif ref.startswith('/'):
        ref = urllib.parse.unquote(ref) if not os.path.exists(ref) else ref
    else:
        return ''
    return ref if os.path.isfile(ref) else ''


def _attach_tag(soup, path):
    tag = soup.new_tag('img')
    tag['src'] = ATTACH_SCHEME + urllib.parse.quote(path)
    return tag


def _split_at_breaks(soup, block, make_line):
    """The inline content of `block`, cut at every <br>, each piece handed to make_line(list of nodes)."""
    lines, current = [], []
    for child in list(block.contents):
        if isinstance(child, Tag) and child.name == 'br':
            lines.append(current)
            current = []
            continue
        current.append(child.extract())
    lines.append(current)
    out = []
    for nodes in lines:
        while nodes and isinstance(nodes[0], NavigableString) and not str(nodes[0]).strip():
            nodes.pop(0)
        if nodes and isinstance(nodes[0], NavigableString):
            nodes[0] = NavigableString(str(nodes[0]).lstrip('\n'))
        if not any((isinstance(n, Tag) or str(n).strip()) for n in nodes):
            continue
        out.append(make_line(nodes))
    return out


def _plain_div(soup, nodes):
    div = soup.new_tag('div')
    for node in nodes:
        div.append(node)
    return div


def _quote_div(soup, nodes):
    """The stand-in for a quoted line: a grey bar and grey text (Notes has no quote through this door)."""
    div = soup.new_tag('div')
    font = soup.new_tag('span')
    font['style'] = 'color: %s' % QUOTE_COLOR
    font.append(NavigableString(QUOTE_BAR + ' '))
    for node in nodes:
        font.append(node)
    div.append(font)
    return div


def _convert_block(soup, node, quoted=False):
    """One top-level node of markdown2's HTML → the nodes Notes should get."""
    make_line = (lambda nodes: _quote_div(soup, nodes)) if quoted else (lambda nodes: _plain_div(soup, nodes))
    if isinstance(node, NavigableString):
        return [make_line([NavigableString(str(node).strip())])] if str(node).strip() else []
    name = node.name.lower()
    if quoted and name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        bold = soup.new_tag('b')      # a heading inside a quote: a quoted line in the heading's size
        holder = bold
        size = {'h1': 24, 'h2': 18}.get(name)
        if size:
            holder = soup.new_tag('span')
            holder['style'] = 'font-size: %dpx' % size
            bold.append(holder)
        for child in list(node.contents):
            holder.append(child.extract())
        return [_quote_div(soup, [bold])]
    if name == 'blockquote':
        out = []
        for child in list(node.contents):
            out.extend(_convert_block(soup, child.extract(), quoted=True))
        return out
    if name == 'p':
        if quoted:      # every source line of a quote is a line of its own in Notes
            for text in list(node.find_all(string=True)):
                if '\n' in text and text.parent is not None and text.parent.name != 'code':
                    pieces = str(text).split('\n')
                    fresh = []
                    for position, piece in enumerate(pieces):
                        if position:
                            fresh.append(soup.new_tag('br'))
                        fresh.append(NavigableString(piece))
                    for item in reversed(fresh):
                        text.insert_after(item)
                    text.extract()
        if not quoted and node.find('br') is not None:
            return [node]      # a line break inside a paragraph: Notes keeps <p>…<br>…</p> as its own soft break
        return _split_at_breaks(soup, node, make_line)
    if name == 'div' and 'margin-left' in str(node.get('style', '')) and not quoted:
        node.name = 'p'        # an indented paragraph: Notes takes the indent from a <p>, not from a <div>
        return [node]
    if name == 'div' and 'codehilite' in (node.get('class') or []):
        pre = node.find('pre')
        return _convert_block(soup, pre.extract(), quoted) if pre is not None else []
    if name == 'pre':
        text = node.get_text().replace('\t', '    ').rstrip('\n')   # Notes drops tabs
        pre = soup.new_tag('pre')
        pre.string = text
        return [pre]
    if name in ('h4', 'h5', 'h6') and not quoted:
        node.name = 'h3'          # Notes has three heading levels
        return [node]
    if name in ('ul', 'ol'):
        _native_check_lists(soup, node)
        for found in [node] + node.find_all('ul'):
            marked = [text for text in found.find_all(string=True) if DASH_MARK in text]
            if found.name == 'ul' and any(text.find_parent('ul') is found for text in marked):
                found['style'] = 'list-style-type: hyphen'
        for text in node.find_all(string=True):
            if DASH_MARK in text:
                text.replace_with(NavigableString(str(text).replace(DASH_MARK, '')))
        if quoted:
            return [_quote_div(soup, [NavigableString(item.get_text(' ', strip=True))]) for item in node.find_all('li')]
        return [node]
    return [node]


def _native_check_lists(soup, top):
    """Task lists become Notes' own check lists (measured 2026-11-20: a list whose list-style-type is
    `check` is stored as a real check list; an item counts as done when the item itself is struck through)."""
    for found in [top] + top.find_all(['ul', 'ol']):
        items = found.find_all('li', recursive=False)
        if not any(item.find('input', recursive=False) is not None for item in items):
            continue
        found.name = 'ul'
        found.attrs = {'style': 'list-style-type: check'}
        for item in items:
            box = item.find('input', recursive=False)
            done = box is not None and box.has_attr('checked')
            if box is not None:
                box.extract()
            nested = [child.extract() for child in item.find_all(['ul', 'ol'], recursive=False)]
            if item.contents and isinstance(item.contents[0], NavigableString):
                item.contents[0].replace_with(NavigableString(str(item.contents[0]).lstrip()))
            item.attrs = {}
            if done:
                inner = soup.new_tag('span')
                inner['style'] = 'text-decoration: none'
                for child in list(item.contents):
                    inner.append(child.extract())
                item.append(inner)
                item['style'] = 'text-decoration: line-through'
            for child in nested:
                item.append(child)


def _dash_lists(md: str) -> str:
    """`+ item` (Notes' dashed list; `- item` is its bulleted list) → a mark the HTML step turns into the dashed style."""
    out, fenced = [], False
    for line in (md or '').split('\n'):
        if line.lstrip().startswith('```'):
            fenced = not fenced
        if not fenced:
            line = re.sub(r'^(\s*)\+ (?=\S)', lambda m: m.group(1) + '- ' + DASH_MARK, line)
        out.append(line)
    return '\n'.join(out)


def _highlight_stand_in(md: str) -> str:
    """==text== → text in the stand-in colour (outside code)."""
    out, fenced = [], False
    for line in (md or '').split('\n'):
        if line.lstrip().startswith('```'):
            fenced = not fenced
        if not fenced and '==' in line:
            parts = re.split(r'(`[^`]*`)', line)
            parts = [part if part.startswith('`') else re.sub(
                r'(?<![=\w])==(?=\S)(.+?)(?<=\S)==(?![=\w])', r'<font color="%s">\1</font>' % HIGHLIGHT_COLOR, part)
                     for part in parts]
            line = ''.join(parts)
        out.append(line)
    return '\n'.join(out)


def markdown_to_notes_html(md: str) -> str:
    """Markdown → HTML for Notes. Local files (an image `![name](path)` of any type, or a link to a local
    file standing alone in its paragraph) are marked with wm-attach:// — send the result through
    run_with_attachments, which turns the marks into real attachments at those places."""
    soup = BeautifulSoup(markdown2.markdown(_highlight_stand_in(_dash_lists(md)), extras=_MD_EXTRAS), 'html.parser')
    for image in soup.find_all('img'):
        path = local_path_of(image.get('src', ''))
        if path:
            image.replace_with(_attach_tag(soup, path))
    for paragraph in soup.find_all('p'):
        children = [c for c in paragraph.contents if isinstance(c, Tag) or str(c).strip()]
        if len(children) == 1 and isinstance(children[0], Tag) and children[0].name == 'a':
            path = local_path_of(children[0].get('href', ''))
            if path:
                children[0].replace_with(_attach_tag(soup, path))
    for font in soup.find_all('font'):
        color = str(font.get('color', '') or '').strip()
        font.name = 'span'
        font.attrs = {'style': 'color: %s' % color} if color else {}
    out = soup.new_tag('div')
    previous_list = previous_table = False
    for node in list(soup.contents):
        for converted in _convert_block(soup, node.extract()):
            is_list = isinstance(converted, Tag) and converted.name in ('ul', 'ol')
            if is_list and previous_list:
                gap = soup.new_tag('div')        # or Notes merges the two lists into one
                gap.append(soup.new_tag('br'))
                out.append(gap)
            previous_list = is_list
            if previous_table:
                out.append(soup.new_tag('div'))   # an empty block (no line of its own): without it Notes forgets that a heading right after a table is a heading
            previous_table = isinstance(converted, Tag) and converted.name == 'table'
            out.append(converted)
    return ''.join(str(child) for child in out.contents)


def attachment_paths(html: str) -> list:
    """The local files marked in `html`, in order (one entry per mark)."""
    return [urllib.parse.unquote(found) for found in re.findall(re.escape(ATTACH_SCHEME) + r'([^"\'>\s]+)', html or '')]


# ── files inside a note: a private volume Notes may read (Broccoli's way, 2026-11-14) ─────────────────
VOLUME_SETTLE_SECONDS = 2.0


class AttachmentVolume:
    """Copies of `paths` on a small disk image mounted at /Volumes/<UUID> (-nobrowse: Finder never shows
    it). open() → {path: copy} or None; close_later() detaches and deletes it once Notes has copied the
    files into its own storage (in the background: the caller is not kept waiting)."""

    def __init__(self, paths):
        self.paths = list(dict.fromkeys(str(p) for p in paths or [] if os.path.isfile(str(p))))
        self.folder = ''
        self.mount = ''
        self.copies = {}

    def open(self):
        if not self.paths or sys.platform != 'darwin' or not os.path.exists('/usr/bin/hdiutil'):
            return None
        total = sum(os.path.getsize(path) for path in self.paths)
        size_mb = int(total * 1.2 / 1_000_000) + 32
        self.folder = tempfile.mkdtemp(prefix='watermelon-notes-files-')
        image = os.path.join(self.folder, 'files.sparseimage')
        self.mount = '/Volumes/' + str(uuid.uuid4()).upper()
        try:
            subprocess.run(['/usr/bin/hdiutil', 'create', '-size', '%dm' % size_mb, '-fs', 'APFS', '-volname',
                            'Watermelon', '-type', 'SPARSE', '-quiet', image], check=True, capture_output=True, timeout=120)
            subprocess.run(['/usr/bin/hdiutil', 'attach', '-nobrowse', '-noautoopen', '-quiet', '-mountpoint',
                            self.mount, image], check=True, capture_output=True, timeout=120)
            used = set()
            for path in self.paths:
                name = os.path.basename(path).replace('/', '_') or 'file'
                stem, suffix = os.path.splitext(name)
                counter = 2
                while name.casefold() in used:
                    name = '%s %d%s' % (stem, counter, suffix)
                    counter += 1
                used.add(name.casefold())
                target = os.path.join(self.mount, name)
                shutil.copyfile(path, target)
                self.copies[path] = target
            return self.copies
        except Exception:
            logging.exception('No private volume for the note\'s files.')
            self._cleanup()
            self.copies = {}
            return None

    def _cleanup(self):
        if self.mount and os.path.ismount(self.mount):
            for flags in ([], ['-force']):
                result = subprocess.run(['/usr/bin/hdiutil', 'detach', '-quiet', *flags, self.mount],
                                        capture_output=True, timeout=60)
                if result.returncode == 0:
                    break
        if self.folder:
            shutil.rmtree(self.folder, ignore_errors=True)

    def close_later(self):
        if not self.folder:
            return
        total = sum(os.path.getsize(path) for path in self.copies.values() if os.path.exists(path))
        wait = VOLUME_SETTLE_SECONDS + total / 200_000_000

        def work():
            time.sleep(wait)
            self._cleanup()

        thread = threading.Thread(target=work, daemon=False, name='watermelon-notes-volume')
        thread.start()
        return thread


def run_with_attachments(html: str, write):
    """write(final_html) with every wm-attach:// mark turned into a file Notes may read. A file that is
    gone, or cannot be offered, leaves a line with its name instead (never a broken attachment)."""
    paths = attachment_paths(html)
    volume = AttachmentVolume(paths) if paths else None
    copies = (volume.open() if volume else None) or {}

    def bind(match):
        path = urllib.parse.unquote(match.group(1))
        copy = copies.get(path)
        if copy:
            return '<img src="file://%s">' % html_lib.escape(urllib.parse.quote(copy), quote=True)
        return html_lib.escape('📎 ' + os.path.basename(path))

    final = re.sub(r'<img[^>]*src="' + re.escape(ATTACH_SCHEME) + r'([^"]+)"[^>]*/?>', bind, html or '')
    try:
        return write(final)
    finally:
        if volume is not None:
            volume.close_later()


# ── Notes → Markdown ──────────────────────────────────────────────────────────────────────────────────
def _text_of(node) -> str:
    return node.get_text().replace(' ', ' ')


def _is_blank_div(node) -> bool:
    return (isinstance(node, Tag) and node.name == 'div' and not _text_of(node).strip()
            and not node.find(['img', 'hr', 'table', 'object']))


def _slot_kind(node):
    """'image' / 'file' when this block is the place of an attachment, else None."""
    if not isinstance(node, Tag) or node.name not in ('div', 'li') or _text_of(node).strip():
        return None
    children = [c for c in node.contents if isinstance(c, Tag)]
    if len(children) == 1 and children[0].name == 'img':
        return 'image'
    if node.name == 'div' and len(children) == 2 and all(c.name == 'br' for c in children):
        return 'file'
    return None


def count_attachment_slots(html: str) -> int:
    soup = BeautifulSoup(html or '', 'html.parser')
    return sum(1 for node in soup.find_all(['div', 'li']) if _slot_kind(node)) + sum(
        1 for image in soup.find_all('img') if _slot_kind(image.parent) is None)


def _font_face(tag) -> str:
    return str(tag.get('face', '') or '').lower()


def _is_mono(tag) -> bool:
    if tag.name in ('tt', 'code', 'kbd'):
        return True
    if tag.name != 'font':
        return False
    if any(face in _font_face(tag) for face in _MONO_FACES):
        return True
    # code in Chinese / Japanese: Courier has no such glyphs, Notes stores another font at code's 12 px
    face = _font_face(tag)
    return bool(face) and not face.startswith('.') and 'font-size: 12px' in str(tag)


def _merge_adjacent(parent):
    """<b>a </b><b><i>b</i></b> → <b>a <i>b</i></b>: Notes cuts one run into several."""
    node = parent.contents[0] if parent.contents else None
    while node is not None:
        if isinstance(node, Tag):
            if node.name in ('b', 'strong', 'i', 'em', 'strike', 's', 'del', 'u'):
                while True:
                    following = node.next_sibling
                    if isinstance(following, NavigableString) and not str(following).strip() and isinstance(
                            following.next_sibling, Tag) and following.next_sibling.name == node.name:
                        node.append(following.extract())
                        continue
                    if isinstance(following, Tag) and following.name == node.name:
                        for item in list(following.contents):
                            node.append(item)
                        following.decompose()
                        continue
                    break
            _merge_adjacent(node)
        node = node.next_sibling


def _wrap(token_open, inner, token_close=None):
    token_close = token_open if token_close is None else token_close
    core = inner.strip()
    if not core:
        return inner
    lead = inner[:len(inner) - len(inner.lstrip())]
    trail = inner[len(inner.rstrip()):]
    return '%s%s%s%s%s' % (lead, token_open, core, token_close, trail)


class _Reader:
    def __init__(self, refs):
        self.refs = list(refs or [])
        self.used = 0

    def attachment(self, kind):
        index = self.used
        self.used += 1
        if index < len(self.refs) and self.refs[index]:
            return self.refs[index]
        return '📎'   # its file could not be fetched from Notes

    def inline(self, node, in_code=False) -> str:
        if isinstance(node, NavigableString):
            return str(node).replace(' ', ' ')
        if not isinstance(node, Tag):
            return ''
        name = node.name.lower()
        if name == 'br':
            return ''
        if name == 'img':
            return self.attachment('image')
        if _is_mono(node) and not in_code:
            inner = ''.join(self.inline(child, in_code=True) for child in node.contents)
            return _wrap('`', inner) if inner.strip() else inner
        inner = ''.join(self.inline(child, in_code) for child in node.contents)
        if not inner:
            return ''
        if in_code:
            return inner
        if name in ('b', 'strong'):
            return _wrap('**', inner)
        if name in ('i', 'em'):
            return _wrap('*', inner)
        if name in ('s', 'strike', 'del'):
            return _wrap('~~', inner)
        if name == 'u':
            only = [c for c in node.contents if isinstance(c, Tag) or str(c).strip()]
            if len(only) == 1 and isinstance(only[0], Tag) and only[0].name == 'a':
                return inner                      # Notes underlines every link
            if node.find('font', attrs={'color': re.compile('^#0000EE$', re.I)}):
                return inner                      # a link that lost its address
            return _wrap('<u>', inner, '</u>')
        if name == 'a':
            href = str(node.get('href', '') or '').strip()
            return '[%s](%s)' % (inner.strip(), href) if href and inner.strip() else inner
        if name == 'font':
            color = str(node.get('color', '') or '').strip()
            if color.upper() == HIGHLIGHT_COLOR:
                return _wrap('==', inner)
            if color and color.upper() not in (QUOTE_COLOR, '#0000EE', '#000000'):
                return _wrap('<font color="%s">' % color, inner, '</font>')
        return inner

    def line(self, node) -> str:
        _merge_adjacent(node)
        text = ''.join(self.inline(child) for child in node.contents)
        return re.sub(r'[ \t]+', ' ', text).strip()

    # blocks
    def heading_level(self, div):
        text = _text_of(div).strip()
        if not text:
            return 0
        if text.startswith(H3_MARK) and div.find('b') is not None:
            return 3
        font = div.find('font', attrs={'face': re.compile(r'^\.AppleSystemUIFontBold', re.I)})
        if font is None or _text_of(font).strip() != text or div.find('b') is None:
            return 0
        sizes = [int(found) for found in re.findall(r'font-size:\s*(\d+)', str(div))]
        if 24 in sizes:
            return 1
        if 18 in sizes:
            return 2
        return 0 if sizes else 3

    def is_code_line(self, div) -> bool:
        text = _text_of(div)
        if not text.strip():
            return False
        tts = div.find_all('tt')
        return bool(tts) and ''.join(_text_of(t) for t in tts).strip() == text.strip()

    def table(self, table) -> str:
        rows = []
        for tr in table.find_all('tr'):
            cells = [self.line(td).replace('|', '\\|') for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(cells)
        if not rows:
            return ''
        if all(re.fullmatch(r'\*\*[^*]+\*\*', cell) for cell in rows[0] if cell):
            rows[0] = [cell[2:-2] if cell else cell for cell in rows[0]]
        width = max(len(row) for row in rows)
        rows = [row + [''] * (width - len(row)) for row in rows]
        out = ['| ' + ' | '.join(rows[0]) + ' |', '| ' + ' | '.join(['---'] * width) + ' |']
        out.extend('| ' + ' | '.join(row) + ' |' for row in rows[1:])
        return '\n'.join(out)

    def list_block(self, node, depth=0) -> list:
        lines = []
        ordered = node.name == 'ol'
        number = 0
        for child in node.contents:
            if not isinstance(child, Tag):
                continue
            if child.name in ('ul', 'ol'):
                lines.extend(self.list_block(child, depth + 1))
                continue
            if child.name != 'li':
                continue
            nested = [c.extract() for c in child.find_all(['ul', 'ol'], recursive=False)]
            if _slot_kind(child):
                text = self.attachment(_slot_kind(child))
            else:
                text = self.line(child)
            marker = '-'
            if ordered:
                number += 1
                marker = '%d.' % number
            task = re.match(r'^([%s%s])\s*' % (TASK_OPEN, TASK_DONE), text)
            if task:
                text = ('[x] ' if task.group(1) == TASK_DONE else '[ ] ') + text[task.end():]
                marker = '-'
            lines.append('%s%s %s' % ('    ' * depth, marker, text))
            for inner in nested:
                lines.extend(self.list_block(inner, depth + 1))
        return lines

    def convert(self, html: str) -> str:
        html = re.sub(r'&(quot|lt|gt|amp|nbsp|apos)(?!;)', r'&\1;', html or '')   # Notes drops the semicolon
        soup = BeautifulSoup(html, 'html.parser')
        nodes = [n for n in soup.contents if isinstance(n, Tag) or str(n).strip()]
        parts = []
        index = 0
        while index < len(nodes):
            node = nodes[index]
            index += 1
            if isinstance(node, NavigableString):
                parts.append(str(node).strip())
                continue
            name = node.name.lower()
            if name in ('ul', 'ol'):
                lines = self.list_block(node)
                if lines:
                    parts.append('\n'.join(lines))
                continue
            if name == 'hr':
                parts.append('---')
                continue
            if name != 'div':
                text = self.line(node)
                if text:
                    parts.append(text)
                continue
            table = node.find('table')
            if table is not None:
                converted = self.table(table)
                if converted:
                    parts.append(converted)
                continue
            if node.find('hr') is not None and not _text_of(node).strip():
                parts.append('---')
                continue
            kind = _slot_kind(node)
            if kind:
                parts.append(self.attachment(kind))
                continue
            if _is_blank_div(node):
                continue
            if self.is_code_line(node):
                code = [_text_of(node).rstrip('\n')]
                while index < len(nodes):
                    following = nodes[index]
                    if isinstance(following, Tag) and following.name == 'div' and self.is_code_line(following):
                        code.append(_text_of(following).rstrip('\n'))
                        index += 1
                        continue
                    # an empty line inside the code: a blank block with a code line right after it
                    if (_is_blank_div(following) and _slot_kind(following) is None and index + 1 < len(nodes)
                            and isinstance(nodes[index + 1], Tag) and nodes[index + 1].name == 'div'
                            and self.is_code_line(nodes[index + 1])):
                        code.append('')
                        index += 1
                        continue
                    break
                parts.append('```\n' + '\n'.join(code) + '\n```')
                continue
            if _text_of(node).strip().startswith(QUOTE_BAR):
                quote = []
                index -= 1
                while index < len(nodes) and isinstance(nodes[index], Tag) and nodes[index].name == 'div' and _text_of(
                        nodes[index]).strip().startswith(QUOTE_BAR):
                    text = self.line(nodes[index])
                    quote.append('> ' + text[len(QUOTE_BAR):].strip() if text.startswith(QUOTE_BAR) else '> ' + text.replace(QUOTE_BAR, '', 1).strip())
                    index += 1
                parts.append('\n'.join(quote))
                continue
            level = self.heading_level(node)
            if level:
                parts.append('#' * level + ' ' + re.sub(r'\s+', ' ', _text_of(node).replace(H3_MARK, '')).strip())
                continue
            text = self.line(node)
            if text:
                parts.append(text)
        md = '\n\n'.join(part for part in parts if part).replace(H3_MARK, '').replace(JOINER, '')
        return re.sub(r'\n{3,}', '\n\n', md).strip()


def notes_html_to_markdown(html: str, refs=None) -> str:
    """The body Notes gives back → Markdown. refs: one Markdown reference per attachment place, in the
    order they stand in the note (see attachment_reference); a place without one shows 📎."""
    return _Reader(refs).convert(html)


def attachment_reference(path: str, name: str = '') -> str:
    """How a fetched attachment stands in the Markdown: a picture is an image, any other file a link —
    both alone on their line, so they go back into Notes as attachments at the same place."""
    name = name or os.path.basename(path)
    url = 'file://' + urllib.parse.quote(path)
    label = name.replace('[', '(').replace(']', ')')
    if name.lower().endswith(IMAGE_EXTS):
        return '![%s](%s)' % (label, url)
    return '[%s](%s)' % (label, url)


# ── a note nobody changed in Notes comes back exactly as typed ────────────────────────────────────────
def body_fingerprint(html: str) -> str:
    return hashlib.sha256((html or '').strip().encode('utf-8')).hexdigest()


class NoteMemory:
    """One small file per note: the Markdown it was written from (or converted to) and the fingerprint of
    the body Notes had at that moment."""

    def __init__(self, folder: str):
        self.folder = folder

    def _path(self, note_key: str) -> str:
        safe = re.sub(r'[^A-Za-z0-9._-]+', '_', note_key).strip('_')[:60] or 'note'
        digest = hashlib.sha256(note_key.encode('utf-8')).hexdigest()[:12]
        return os.path.join(self.folder, '%s_%s.json' % (safe, digest))

    def remember(self, note_key: str, body_html: str, md: str, fingerprint=None) -> None:
        """fingerprint: the store's fingerprint of the note (note_state); without one, the body's."""
        try:
            os.makedirs(self.folder, exist_ok=True)
            path = self._path(note_key)
            with open(path + '.tmp', 'w', encoding='utf-8') as handle:
                json.dump({'fingerprint': fingerprint or body_fingerprint(body_html), 'markdown': md}, handle, ensure_ascii=False)
            os.replace(path + '.tmp', path)
        except OSError:
            logging.exception('Remembering the note\'s Markdown failed.')

    def recall(self, note_key: str, body_html: str, fingerprint=None):
        """The remembered Markdown when the note's body is still the one it was remembered with, else None."""
        try:
            with open(self._path(note_key), encoding='utf-8') as handle:
                record = json.load(handle)
        except (OSError, ValueError):
            return None
        if isinstance(record, dict) and record.get('fingerprint') == (fingerprint or body_fingerprint(body_html)):
            return str(record.get('markdown', ''))
        return None

    def forget(self, note_key: str) -> None:
        try:
            os.remove(self._path(note_key))
        except OSError:
            pass


# ── what Notes itself stores (read only) ──────────────────────────────────────────────────────────────
# AppleScript's `body` leaves out part of what a note holds: whether a check-list item is done, alignment,
# sub / superscript, highlight, Notes' own block quote and heading styles. They are all in Notes' own
# store, ~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite (needs "Full Disk Access";
# Ryan 2026-11-20: "给完全磁盘访问权限当然是完全可以的"). It is only ever READ here, never written.
# A note = gzip'ed protobuf (2 → 3): field 2 = the text, field 5 = the runs. A run: 1 length (UTF-16 units),
# 2 paragraph {1 style: 0 title 1 heading 2 subheading 4 monostyled 100 bullet 101 dash 102 number 103 check;
# 2 alignment: 1 centre 2 right 3 justified; 4 indent; 5 check item {2 done}; 8 block quote},
# 3 font {1 name, 2 size}, 5 weight (1 bold 2 italic 3 both), 6 underline, 7 strike, 8 super(+1)/sub(−1),
# 9 link, 10 colour, 12 attachment {1 id, 2 type}, 14 highlight (1 = purple … ). Measured on macOS 27.2.1.
NOTES_STORE = os.path.expanduser('~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite')
_OBJECT = '￼'
_DIVIDER_TYPE = 'com.apple.notes.inlinetextattachment.div'
_TABLE_TYPE = 'com.apple.notes.table'


def _varint(data, index):
    value = shift = 0
    while True:
        byte = data[index]
        index += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return value, index


def _pb(data):
    """[(field, wire type, value)] of one protobuf message."""
    out, index = [], 0
    while index < len(data):
        key, index = _varint(data, index)
        field, wire = key >> 3, key & 7
        if wire == 0:
            value, index = _varint(data, index)
        elif wire == 2:
            size, index = _varint(data, index)
            value = data[index:index + size]
            index += size
        elif wire == 5:
            value = data[index:index + 4]
            index += 4
        elif wire == 1:
            value = data[index:index + 8]
            index += 8
        else:
            raise ValueError('unknown wire type %d' % wire)
        out.append((field, wire, value))
    return out


def _pb_first(data, field, default=None):
    for found, _wire, value in _pb(data):
        if found == field:
            return value
    return default


def _signed(value):
    return value - (1 << 64) if value >= (1 << 63) else value


class StoreUnavailable(Exception):
    """Notes' store cannot be read (no Full Disk Access, or it is not there)."""


def _open_store(path=None):
    path = path or NOTES_STORE
    if not os.path.exists(path):
        raise StoreUnavailable('not found')
    import sqlite3
    try:
        connection = sqlite3.connect('file:' + urllib.parse.quote(path) + '?mode=ro', uri=True, timeout=2.0)
        connection.execute('select 1 from ZICNOTEDATA limit 1').fetchone()
        return connection
    except Exception as exc:
        raise StoreUnavailable(str(exc))


def _stored_note(connection, folder, title, note_id=None):
    """(runs-message bytes, {attachment id: alt text}) of the note, or None. The note is found by its own
    number (note_id = AppleScript's id, x-coredata://…/ICNote/p<number>); only without one, by folder and
    title — and then only when exactly one note has them."""
    wanted_folder = str(folder or '').split('/')[-1].strip()
    number = re.search(r'/ICNote/p(\d+)$', str(note_id or ''))
    rows = []
    if number:
        rows = connection.execute('select Z_PK, null from ZICCLOUDSYNCINGOBJECT where Z_PK = ? and ifnull(ZMARKEDFORDELETION, 0) != 1 '
                                  'and Z_PK in (select ZNOTE from ZICNOTEDATA)', (int(number.group(1)),)).fetchall()
    if len(rows) == 1:
        return _note_record(connection, rows[0][0])
    rows = connection.execute(
        'select n.Z_PK, f.ZTITLE2 from ZICCLOUDSYNCINGOBJECT n left join ZICCLOUDSYNCINGOBJECT f on f.Z_PK = n.ZFOLDER '
        'where n.ZTITLE1 = ? and ifnull(n.ZMARKEDFORDELETION, 0) != 1', (title,)).fetchall()
    in_folder = [row for row in rows if (row[1] or '') == wanted_folder]
    rows = in_folder or (rows if wanted_folder in ('', 'Unfiled') else [])
    if len(rows) != 1:
        return None
    return _note_record(connection, rows[0][0])


def _note_record(connection, key):
    rows = [(key, None)]
    data = connection.execute('select ZDATA from ZICNOTEDATA where ZNOTE = ?', (rows[0][0],)).fetchone()
    if not data or not data[0]:
        return None
    import gzip
    note = _pb_first(_pb_first(gzip.decompress(data[0]), 2, b''), 3, b'')
    alt = {}
    for identifier, text in connection.execute(
            'select ZIDENTIFIER, ZALTTEXT from ZICCLOUDSYNCINGOBJECT where ZNOTE1 = ? and ZALTTEXT is not null'
            if _has_column(connection, 'ZNOTE1') else 'select ZIDENTIFIER, ZALTTEXT from ZICCLOUDSYNCINGOBJECT where 0 and ? is null',
            (rows[0][0],)):
        alt[str(identifier)] = str(text)
    return note, alt


def _has_column(connection, name):
    return any(row[1] == name for row in connection.execute('pragma table_info(ZICCLOUDSYNCINGOBJECT)'))


def _parse_runs(note):
    """The note as paragraphs: [{'style', 'align', 'indent', 'done', 'quote', 'runs': [run]}]; a run =
    {'text', and what it carries}."""
    text = (_pb_first(note, 2, b'') or b'').decode('utf-8', 'replace')
    units = text.encode('utf-16-le')
    position = 0
    paragraphs = [{'runs': [], 'para': None}]
    for field, _wire, value in _pb(note):
        if field != 5:
            continue
        parts = _pb(value)
        length = next((v for f, w, v in parts if f == 1), 0)
        piece = units[position * 2:(position + length) * 2].decode('utf-16-le', 'replace')
        position += length
        run = {}
        para = None
        for f, w, v in parts:
            if f == 2 and w == 2:
                para = {}
                for pf, pw, pv in _pb(v):
                    if pf == 1:
                        para['style'] = pv
                    elif pf == 2:
                        para['align'] = pv
                    elif pf == 4:
                        para['indent'] = pv
                    elif pf == 5 and pw == 2:
                        para['done'] = bool(_pb_first(pv, 2, 0))
                        para['check'] = True
                    elif pf == 8 and pw == 0:
                        para['quote'] = bool(pv)
            elif f == 3 and w == 2:
                run['font'] = (_pb_first(v, 1, b'') or b'').decode('utf-8', 'replace')
                size = _pb_first(v, 2)
                if isinstance(size, (bytes, bytearray)) and len(size) == 4:
                    import struct
                    run['size'] = struct.unpack('<f', size)[0]
            elif f == 5 and w == 0:
                run['bold'], run['italic'] = v in (1, 3), v in (2, 3)
            elif f == 6 and w == 0:
                run['underline'] = bool(v)
            elif f == 7 and w == 0:
                run['strike'] = bool(v)
            elif f == 8 and w == 0:
                run['baseline'] = 1 if _signed(v) > 0 else (-1 if _signed(v) < 0 else 0)
            elif f == 9 and w == 2:
                run['link'] = v.decode('utf-8', 'replace')
            elif f == 10 and w == 2:
                import struct
                rgb = [struct.unpack('<f', x)[0] for ff, ww, x in _pb(v) if ww == 5 and ff in (1, 2, 3)]
                if len(rgb) == 3:
                    run['color'] = '#%02X%02X%02X' % tuple(max(0, min(255, int(round(c * 255)))) for c in rgb)
            elif f == 12 and w == 2:
                identifier = _pb_first(v, 1, b'')
                kind = _pb_first(v, 2, b'')
                run['attachment'] = (identifier.decode('utf-8', 'replace') if isinstance(identifier, (bytes, bytearray)) else '',
                                     kind.decode('utf-8', 'replace') if isinstance(kind, (bytes, bytearray)) and kind[:1].isalpha() else '')
            elif f == 14 and w == 0:
                run['highlight'] = v
        lines = piece.split('\n')
        for index, line in enumerate(lines):
            if index:
                paragraphs.append({'runs': [], 'para': None})
            current = paragraphs[-1]
            if line:
                current['runs'].append(dict(run, text=line))
            if para is not None and (line or index < len(lines) - 1 or current['para'] is None):
                if current['para'] is None or line:
                    current['para'] = para
    return paragraphs


def stored_plain_text(note) -> str:
    return (_pb_first(note, 2, b'') or b'').decode('utf-8', 'replace')


_MARK_ORDER = ('highlight', 'link', 'color', 'size', 'underline', 'sup', 'sub', 'strike', 'bold', 'italic')


def _run_marks(run, heading=False, drop_strike=False):
    font = str(run.get('font', '')).lower()
    color = str(run.get('color', '')).upper()
    highlighted = color == HIGHLIGHT_COLOR or bool(run.get('highlight'))
    mono = any(face in font for face in _MONO_FACES) or (bool(font) and not font.startswith('.') and round(run.get('size') or 0) == 12)
    if mono:
        return (('highlight', ''), 'code') if highlighted else ('code',)
    marks = []
    if run.get('link'):
        marks.append(('link', run['link']))
    if highlighted:
        marks.append(('highlight', ''))
    if color and color not in (HIGHLIGHT_COLOR, QUOTE_COLOR, '#000000', '#FFFFFF') and not run.get('link'):
        marks.append(('color', color))
    size = round(run.get('size') or 0)
    if size and size != 12 and not heading and not font.startswith('.applesystemuifontbold'):
        marks.append(('size', size))
    if run.get('underline') and not run.get('link'):
        marks.append(('underline', ''))
    if run.get('baseline', 0) > 0:
        marks.append(('sup', ''))
    if run.get('baseline', 0) < 0:
        marks.append(('sub', ''))
    if run.get('strike') and not drop_strike:
        marks.append(('strike', ''))
    if run.get('bold') and not heading:
        marks.append(('bold', ''))
    if run.get('italic'):
        marks.append(('italic', ''))
    order = {name: index for index, name in enumerate(_MARK_ORDER)}
    return tuple(sorted(marks, key=lambda mark: order[mark[0]]))   # outer → inner


def _mark_tokens(mark):
    if mark == 'code':
        return '`', '`'
    name, value = mark
    return {'link': ('[', '](%s)' % value), 'color': ('<font color="%s">' % value, '</font>'), 'highlight': ('==', '=='),
            'size': ('<span style="font-size: %spx">' % value, '</span>'),
            'underline': ('<u>', '</u>'), 'sup': ('<sup>', '</sup>'), 'sub': ('<sub>', '</sub>'), 'strike': ('~~', '~~'),
            'bold': ('**', '**'), 'italic': ('*', '*')}[name]


def _inline_from_runs(pieces):
    """[(marks, text)] → Markdown: marks stay open across neighbouring runs, and blanks never end up just
    inside a mark (`**bold **` is not bold in Markdown)."""
    out, opened, pending = [], [], ''
    for marks, text in pieces:
        marks = list(marks)
        core = text.strip()
        if not core:
            pending += text
            continue
        lead = text[:len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        keep = 0
        while keep < len(opened) and keep < len(marks) and opened[keep] == marks[keep] and opened[keep] != 'code':
            keep += 1
        for mark in reversed(opened[keep:]):
            out.append(_mark_tokens(mark)[1])
        out.append(pending + lead)
        fresh = [mark for mark in marks if mark not in opened[:keep]]
        for mark in fresh:
            out.append(_mark_tokens(mark)[0])
        opened = opened[:keep] + fresh
        out.append(core)
        pending = trail
    for mark in reversed(opened):
        out.append(_mark_tokens(mark)[1])
    out.append(pending)
    return re.sub(r'[ \t]+', ' ', ''.join(out)).strip(' \t\n')


def stored_note_to_markdown(note, tables=None, refs=None, alt_text=None) -> str:
    """Notes' own record of a note → Markdown. tables: the note's tables as Markdown, in order (they are
    separate objects in the store; the body has them). refs: one Markdown reference per file attachment,
    in order."""
    tables, refs, alt_text = list(tables or []), list(refs or []), dict(alt_text or {})
    counters = {'table': 0, 'file': 0}

    def attachment_text(run):
        identifier, kind = run['attachment']
        if kind.startswith(_DIVIDER_TYPE):      # '…div' and '…dividerline' were both seen
            return '\n---\n'
        if kind == _TABLE_TYPE:
            counters['table'] += 1
            return '\n' + (tables[counters['table'] - 1] if counters['table'] <= len(tables) else '') + '\n'
        if kind.startswith('com.apple.notes.inlinetextattachment'):
            return alt_text.get(identifier, '')
        counters['file'] += 1
        index = counters['file'] - 1
        return '\n' + (refs[index] if index < len(refs) and refs[index] else '📎') + '\n'

    blocks = []          # (kind, text)
    numbers = {}
    for paragraph in _parse_runs(note):
        para = paragraph['para'] or {}
        runs = paragraph['runs']
        style = para.get('style', -1)
        text_runs = [run for run in runs if 'attachment' not in run]
        plain = ''.join(run['text'] for run in text_runs)
        if not runs or (not plain.strip() and not any('attachment' in run for run in runs)):
            blocks.append(('blank', ''))
            if style not in (100, 101, 102, 103):
                numbers.clear()
            continue
        if style == 4:
            blocks.append(('code', ''.join(run['text'] for run in runs).replace(_OBJECT, '')))
            continue
        fonts_bold = text_runs and all(str(run.get('font', '')).startswith('.AppleSystemUIFontBold') for run in text_runs if run['text'].strip())
        level = {0: 1, 1: 2, 2: 3}.get(style, 0)
        if not level and plain.startswith(H3_MARK) and all(run.get('bold') for run in text_runs if run['text'].strip(H3_MARK + ' ')):
            level = 3
        if not level and fonts_bold and plain.strip():
            sizes = [run.get('size') for run in text_runs if run['text'].strip()]
            level = 1 if all(size and round(size) == 24 for size in sizes) else 2 if all(size and round(size) == 18 for size in sizes) else 3 if not any(sizes) else 0
        if not level and plain.lstrip().startswith(QUOTE_BAR):     # the quote stand-in holding a heading
            inner = [run for run in text_runs if run['text'].strip() and run['text'].strip() != QUOTE_BAR]
            sizes = {round(run.get('size') or 0) for run in inner}
            if inner and all(run.get('bold') for run in inner) and sizes in ({24}, {18}):
                level = 1 if sizes == {24} else 2
        done = bool(para.get('done'))
        all_struck = bool(text_runs) and all(run.get('strike') for run in text_runs if run['text'].strip())
        pieces = []
        for run in runs:
            if 'attachment' in run:
                pieces.append(((), attachment_text(run)))
            else:
                pieces.append((_run_marks(run, heading=bool(level), drop_strike=(style == 103 and done and all_struck)), run['text']))
        if all(piece[1].startswith('\n') for piece in pieces if piece[1].strip()) and any('attachment' in run for run in runs) and not plain.strip():
            for piece in pieces:
                if piece[1].strip():
                    blocks.append(('object', piece[1].strip()))
            continue
        text = _inline_from_runs([(marks, body.replace('\n', ' ') if not body.startswith('\n') else body.strip()) for marks, body in pieces])
        text = re.sub(r' *\u2028 *', '  \n', text)      # Notes' line break inside a paragraph = Markdown's hard break
        if style in (100, 101, 102, 103):
            depth = int(para.get('indent', 0) or 0)
            if style == 102:
                for deeper in [key for key in numbers if key > depth]:
                    numbers.pop(deeper)
                numbers[depth] = numbers.get(depth, 0) + 1
                marker = '%d.' % numbers[depth]
            else:
                for deeper in [key for key in numbers if key >= depth]:
                    numbers.pop(deeper)
                marker = '+' if style == 101 else '-'
            stand_in = re.match(r'^([%s%s])\s*' % (TASK_OPEN, TASK_DONE), text)
            if style == 103:
                text = ('[x] ' if done else '[ ] ') + text
            elif stand_in and style in (100, 101):      # a task written before Notes' own check list was used
                text = ('[x] ' if stand_in.group(1) == TASK_DONE else '[ ] ') + text[stand_in.end():]
            line = '    ' * depth + marker + ' ' + text
            if para.get('quote'):
                blocks.append(('quote', '> ' + line))
            else:
                blocks.append(('list:%d' % (102 if style == 102 else 103 if style == 103 else 100), line))
            continue
        numbers.clear()
        quoted = bool(para.get('quote')) or plain.lstrip().startswith(QUOTE_BAR)
        if quoted:      # Notes' own block quote (paragraph field 8, seen 2026-11-20) or the stand-in; a heading inside stays a heading
            blocks.append(('quote', '> ' + ('#' * level + ' ' if level else '') + text.lstrip(QUOTE_BAR).strip()))
        elif level:
            blocks.append(('heading', '#' * level + ' ' + text))
        else:
            css = []
            align = {1: 'center', 2: 'right', 3: 'justify'}.get(para.get('align', 0))
            if align:
                css.append('text-align: %s' % align)
            if int(para.get('indent', 0) or 0) > 0:
                css.append('margin-left: %dem' % (2 * int(para['indent'])))
            if css:
                text = '<div style="%s">%s</div>' % ('; '.join(css), text)
            blocks.append(('text', text))
    parts = []
    index = 0
    while index < len(blocks):
        kind, text = blocks[index]
        if kind == 'blank':
            index += 1
            continue
        if kind == 'code':
            lines = [text]
            index += 1
            while index < len(blocks):
                if blocks[index][0] == 'code':
                    lines.append(blocks[index][1])
                elif blocks[index][0] == 'blank' and index + 1 < len(blocks) and blocks[index + 1][0] == 'code':
                    lines.append('')
                else:
                    break
                index += 1
            parts.append('```\n' + '\n'.join(lines) + '\n```')
            continue
        if kind == 'quote' or kind.startswith('list:'):
            lines = [text]
            index += 1
            while index < len(blocks) and (blocks[index][0] == kind or (kind.startswith('list:') and blocks[index][0].startswith('list:')
                                                                      and blocks[index][1].startswith(' '))):
                lines.append(blocks[index][1])
                index += 1
            parts.append('\n'.join(lines))
            continue
        parts.append(text)
        index += 1
    return re.sub(r'\n{3,}', '\n\n', '\n\n'.join(part for part in parts if part)).replace(H3_MARK, '').replace(JOINER, '').strip()


def _comparable(text: str) -> str:
    text = (text or '').replace(_OBJECT, '').replace('\u00a0', '').replace(JOINER, '').replace(H3_MARK, '')
    return re.sub(r'\s+', '', text)


def markdown_from_store(body_html: str, folder: str, title: str, refs=None, store_path=None, wait=1.5, note_id=None):
    """(Markdown, '') from Notes' own record of the note, or (None, reason): 'no-access' (no Full Disk
    Access), 'not-found', 'behind' (the store does not hold this body yet). The body is still needed: it
    says which state of the note is meant, and it holds the tables."""
    try:
        connection = _open_store(store_path)
    except StoreUnavailable:
        return None, 'no-access'
    try:
        soup = BeautifulSoup(re.sub(r'&(quot|lt|gt|amp|nbsp|apos)(?!;)', r'&\1;', body_html or ''), 'html.parser')
        reader = _Reader([])
        tables = [reader.table(table) for table in soup.find_all('table')]
        for table in soup.find_all('table'):
            table.decompose()
        wanted = _comparable(soup.get_text())
        deadline = time.time() + wait
        while True:
            found = _stored_note(connection, folder, title, note_id)
            if found is None:
                return None, 'not-found'
            note, alt_text = found
            # a link preview is an object in the store, but the body shows its address as text
            expected = wanted
            for identifier, kind in _file_attachments(note):
                if kind == 'public.url':
                    row = connection.execute('select ZURLSTRING from ZICCLOUDSYNCINGOBJECT where ZIDENTIFIER = ? and ZURLSTRING is not null', (identifier,)).fetchone()
                    if row and row[0]:
                        expected = expected.replace(_comparable(row[0]), '', 1)
            if _comparable(stored_plain_text(note)) == expected:
                return stored_note_to_markdown(note, tables, refs, alt_text), ''
            if time.time() >= deadline:
                return None, 'behind'
            time.sleep(0.25)
    except Exception:
        logging.exception('Reading the note from Notes\' store failed.')
        return None, 'error'
    finally:
        connection.close()


# ── the files of a note, straight from Notes' own storage (read only) ─────────────────────────────────
# `attachments of note` (AppleScript) is not complete: a drawing is not in it, a PDF sometimes is not, and
# then every later file would be put one place too early. The store names each attachment at its place;
# its file is at Accounts/<account>/Media/<media id>/<…>/<file name>, the picture of a drawing at
# Accounts/<account>/FallbackImages/<attachment id>/<…>/FallbackImage.png.
_DRAWING_TYPES = ('com.apple.paper', 'com.apple.drawing', 'com.apple.drawing.2')


def _file_attachments(note):
    """[(identifier, type)] of the attachments that stand for a file / picture / drawing, in text order —
    the same ones, in the same order, stored_note_to_markdown asks a reference for."""
    out = []
    for paragraph in _parse_runs(note):
        for run in paragraph['runs']:
            if 'attachment' not in run:
                continue
            identifier, kind = run['attachment']
            if kind.startswith(_DIVIDER_TYPE) or kind == _TABLE_TYPE or kind.startswith('com.apple.notes.inlinetextattachment'):
                continue
            out.append((identifier, kind))
    return out


def fetch_attachments_from_store(folder: str, title: str, target_dir: str, store_path=None, note_id=None):
    """Copies of the note's files in target_dir/f1, f2 … and their Markdown references, in text order.
    None when the store cannot be read or the note is not found (the caller then asks Notes itself)."""
    import glob
    try:
        connection = _open_store(store_path)
    except StoreUnavailable:
        return None
    try:
        found = _stored_note(connection, folder, title, note_id)
        if found is None:
            return None
        root = os.path.join(os.path.dirname(store_path or NOTES_STORE), 'Accounts')
        refs = []
        drawings = 0
        for number, (identifier, kind) in enumerate(_file_attachments(found[0]), 1):
            row = connection.execute(
                'select ZTITLE, ZMEDIA, ZURLSTRING from ZICCLOUDSYNCINGOBJECT where ZIDENTIFIER = ? and ZTYPEUTI is not null',
                (identifier,)).fetchone() or (None, None, None)
            name, media, url = row
            if kind == 'public.url' and url:
                refs.append('[%s](%s)' % ((name or url).replace('[', '(').replace(']', ')'), url))
                continue
            source = ''
            if kind in _DRAWING_TYPES:
                drawings += 1
                pictures = sorted(glob.glob(os.path.join(glob.escape(root), '*', 'FallbackImages', identifier, '*', 'FallbackImage.*')),
                                  key=os.path.getmtime)
                source = pictures[-1] if pictures else ''
                name = 'Drawing %d%s' % (drawings, os.path.splitext(source)[1] or '.png')
            elif media:
                media_row = connection.execute('select ZIDENTIFIER, ZFILENAME from ZICCLOUDSYNCINGOBJECT where Z_PK = ?', (media,)).fetchone()
                if media_row and media_row[0] and media_row[1]:
                    files = glob.glob(os.path.join(glob.escape(root), '*', 'Media', media_row[0], '*', glob.escape(media_row[1])))
                    source = files[0] if files else ''
                    name = name or media_row[1]
            if not source or not os.path.isfile(source):
                refs.append('')
                continue
            holder = os.path.join(target_dir, 'f%d' % number)
            os.makedirs(holder, exist_ok=True)
            name = str(name or os.path.basename(source)).replace('/', '_')
            copy = os.path.join(holder, name)
            shutil.copyfile(source, copy)
            refs.append(attachment_reference(copy, name))
        return refs
    except Exception:
        logging.exception('Fetching the note\'s files from Notes\' store failed.')
        return None
    finally:
        connection.close()


def note_native_only(folder: str, title: str, store_path=None, note_id=None) -> list:
    """What this note holds that only Notes itself can make — writing the note again keeps the content at its
    place but not the thing: 'drawing' (becomes a picture), 'link preview' (a plain link), 'tag', 'mention'
    (plain text). Measured 2026-11-20: no HTML makes any of them, and a body cannot refer to the old ones."""
    try:
        connection = _open_store(store_path)
    except StoreUnavailable:
        return []
    try:
        found = _stored_note(connection, folder, title, note_id)
        kinds = []
        if found:
            for paragraph in _parse_runs(found[0]):
                for run in paragraph['runs']:
                    kind = run.get('attachment', ('', ''))[1]
                    name = ('drawing' if kind in _DRAWING_TYPES else 'link preview' if kind == 'public.url'
                            else 'tag' if kind.endswith('.hashtag') else 'mention' if kind.endswith('.mention') else '')
                    if name and name not in kinds:
                        kinds.append(name)
        return kinds
    except Exception:
        return []
    finally:
        connection.close()


# ── fast reading, and two sides changing one note (2026-11-21) ───────────────────────────────────────
# Ryan 2026-11-21: switching to a note should be faster; and "不希望…做了一些修改然后因为读取速度不够然后没保存
# 下来，特别是两边同时操作修改的时候…参考 tomato 和 calendar…不要轮询". Measured on his Mac: asking Notes for
# the list takes 0.7 s and for one body 0.27 s; the store answers both in under 0.01 s; a write made through
# AppleScript is in the store when the call returns; and the store's files change the moment a note does
# (so the app is told by the file system instead of asking every few seconds).
# Writing the store directly is NOT done: a note's record is mostly edit history (a CRDT), version clocks and
# iCloud state that Notes and its sync process also hold in memory — text written past them corrupts the note
# or is merged away by iCloud. Writes keep going through Notes itself.
def _entity_numbers(connection) -> dict:
    return {name: number for number, name in connection.execute('select Z_ENT, Z_NAME from Z_PRIMARYKEY')}


def list_notes_from_store(store_path=None):
    """Every note as Notes' own list gives it: [{'folder': 'Account/Folder', 'title', 'id', 'body': ''}], or
    None when the store cannot be read. 'id' is the id AppleScript uses (x-coredata://<store>/ICNote/p<n>)."""
    try:
        connection = _open_store(store_path)
    except StoreUnavailable:
        return None
    try:
        entities = _entity_numbers(connection)
        uuid_row = connection.execute('select Z_UUID from Z_METADATA').fetchone()
        if not uuid_row or 'ICNote' not in entities:
            return None
        columns = [row[1] for row in connection.execute('pragma table_info(ZICCLOUDSYNCINGOBJECT)')]
        account_columns = [c for c in columns if c == 'ZOWNER' or (c.startswith('ZACCOUNT') and c[8:].isdigit()) or c == 'ZACCOUNT']
        names = {}       # pk → (name, parent pk or None)
        for row in connection.execute('select Z_PK, ZNAME from ZICCLOUDSYNCINGOBJECT where Z_ENT = ?', (entities.get('ICAccount', -1),)):
            names[row[0]] = (row[1] or '', None)
        select = 'select Z_PK, ZTITLE2, ZPARENT, %s from ZICCLOUDSYNCINGOBJECT where Z_ENT = ?' % ', '.join(account_columns)
        for row in connection.execute(select, (entities.get('ICFolder', -1),)):
            parent = row[2] or next((value for value in row[3:] if value), None)
            names[row[0]] = (row[1] or '', parent)

        def folder_path(key):
            name, parent = names.get(key, ('Unfiled', None))
            parent_name = names.get(parent, ('', None))[0] if parent else ''
            return (parent_name + '/' + name) if parent_name else (name or 'Unfiled')

        # when the note was made (Core Data seconds since 2001; on macOS 27 the note's own is ZCREATIONDATE3):
        # the picker lists the newest first (Ryan 2026-11-24: "把最新建的那个笔记放在上面")
        made = [c for c in ('ZCREATIONDATE3', 'ZCREATIONDATE1', 'ZCREATIONDATE') if c in columns]
        made_sql = ('coalesce(%s)' % ', '.join(made)) if made else 'null'
        notes = []
        for key, title, folder, created in connection.execute(
                'select Z_PK, ZTITLE1, ZFOLDER, %s from ZICCLOUDSYNCINGOBJECT where Z_ENT = ? and ifnull(ZMARKEDFORDELETION, 0) != 1 '
                'and ZFOLDER is not null and Z_PK in (select ZNOTE from ZICNOTEDATA) order by Z_PK' % made_sql, (entities['ICNote'],)):
            # (a note without a folder is a placeholder still waiting for iCloud: Notes does not list it either)
            note = {'folder': folder_path(folder).strip(), 'title': (title or '').strip(), 'body': '',
                    'id': 'x-coredata://%s/ICNote/p%d' % (uuid_row[0], key)}
            if created is not None:
                note['created'] = float(created) + 978307200.0      # → seconds since 1970
            notes.append(note)
        return notes
    except Exception:
        logging.exception('Listing the notes from Notes\' store failed.')
        return None
    finally:
        connection.close()


def note_state(folder: str, title: str, note_id=None, store_path=None):
    """(fingerprint, has tables) of the note as it is in the store right now, or None (no access / not found).
    The fingerprint changes whenever the note's record does."""
    try:
        connection = _open_store(store_path)
    except StoreUnavailable:
        return None
    try:
        found = _stored_note(connection, folder, title, note_id)
        if found is None:
            return None
        return hashlib.sha256(found[0]).hexdigest(), any(kind == _TABLE_TYPE for _i, kind in _all_attachments(found[0]))
    except Exception:
        return None
    finally:
        connection.close()


def _all_attachments(note):
    return [run['attachment'] for paragraph in _parse_runs(note) for run in paragraph['runs'] if 'attachment' in run]


def read_note_from_store(folder: str, title: str, note_id=None, attachments_dir='', body_html=None, store_path=None):
    """{'markdown', 'fingerprint', 'needs_body'} of the note read from the store alone — no question to Notes —
    or None (no access / not found). A note with tables needs the body Notes gives (the store keeps a table
    as a separate object): then 'needs_body' is True and 'markdown' is None unless body_html was passed."""
    try:
        connection = _open_store(store_path)
    except StoreUnavailable:
        return None
    try:
        found = _stored_note(connection, folder, title, note_id)
        if found is None:
            return None
        note, alt_text = found
        fingerprint = hashlib.sha256(note).hexdigest()
        tables = []
        if any(kind == _TABLE_TYPE for _i, kind in _all_attachments(note)):
            if body_html is None:
                return {'markdown': None, 'fingerprint': fingerprint, 'needs_body': True}
            soup = BeautifulSoup(re.sub(r'&(quot|lt|gt|amp|nbsp|apos)(?!;)', r'&\1;', body_html or ''), 'html.parser')
            reader = _Reader([])
            tables = [reader.table(table) for table in soup.find_all('table')]
    finally:
        connection.close()
    refs = []
    if _file_attachments(note) and attachments_dir:
        refs = fetch_attachments_from_store(folder, title, attachments_dir, store_path=store_path, note_id=note_id) or []
    return {'markdown': stored_note_to_markdown(note, tables, refs, alt_text), 'fingerprint': fingerprint, 'needs_body': False}


# ── both sides changed: merge by paragraph (what Tomato does with Calendar: remember what was last seen,
#    then compare the three) ──
def _blocks(markdown: str) -> list:
    """Paragraph-sized pieces; a fenced code block stays one piece."""
    blocks, current, fenced = [], [], False
    for line in (markdown or '').split('\n'):
        if line.lstrip().startswith('```'):
            fenced = not fenced
        if not line.strip() and not fenced:
            if current:
                blocks.append('\n'.join(current))
                current = []
            continue
        current.append(line)
    if current:
        blocks.append('\n'.join(current))
    return blocks


def merge_markdown(base: str, mine: str, theirs: str, prefer=None):
    """(merged Markdown, number of conflicts). base = what both sides started from. A paragraph only one side
    changed takes that side's text; a paragraph both changed differently is a conflict: with prefer = 'mine' /
    'theirs' that side is taken, with prefer = None my text is kept and the conflict is counted."""
    import difflib
    a, o, b = _blocks(mine), _blocks(base), _blocks(theirs)
    if a == b or o == b:
        return '\n\n'.join(a), 0
    if o == a:
        return '\n\n'.join(b), 0
    match_a = difflib.SequenceMatcher(None, o, a, autojunk=False).get_matching_blocks()
    match_b = difflib.SequenceMatcher(None, o, b, autojunk=False).get_matching_blocks()
    regions, ia, ib = [], 0, 0
    while ia < len(match_a) and ib < len(match_b):
        o_a, a_at, len_a = match_a[ia]
        o_b, b_at, len_b = match_b[ib]
        start, end = max(o_a, o_b), min(o_a + len_a, o_b + len_b)
        if start < end:
            regions.append((start, end, a_at + (start - o_a), b_at + (start - o_b)))
        if o_a + len_a < o_b + len_b:
            ia += 1
        else:
            ib += 1
    regions.append((len(o), len(o), len(a), len(b)))
    merged, conflicts = [], 0
    at_o = at_a = at_b = 0
    for start, end, a_start, b_start in regions:
        part_o, part_a, part_b = o[at_o:start], a[at_a:a_start], b[at_b:b_start]
        if part_a == part_b or part_b == part_o:
            merged.extend(part_a)
        elif part_a == part_o:
            merged.extend(part_b)
        else:
            conflicts += 1
            merged.extend(part_b if prefer == 'theirs' else part_a)
        merged.extend(o[start:end])
        at_o, at_a, at_b = end, a_start + (end - start), b_start + (end - start)
    return '\n\n'.join(merged), conflicts

