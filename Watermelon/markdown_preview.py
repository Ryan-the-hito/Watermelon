# -*- coding: utf-8 -*-
"""The Markdown preview shared by Watermelon, Tomato and Strawberry (2026-11-20).

Ryan 2026-11-20: Broccoli's rendering update (formulas vs. the dollar sign, snapshot 379) had not reached
the other apps; "该更新的就更新"; and the new Markdown forms of the Notes table (==highlight==, task
lists, "+ " lists, quotes, alignment …) "在渲染里面应该要做一些新的对应"; the look: "在我们现在现有的这个
样式的基础上…符合风格的一个样式，这个风格比较重要，我们自己的风格" — not an imitation of Notes.

Three parts:
  1. formulas  — Broccoli's code, copied unchanged (Broccoli_26new.py, "protect_markdown_math"): a formula is
     decided ONCE, before Markdown runs ($…$ by Pandoc's rule, $$…$$, \(…\), \[…\], \begin{align}…); a price
     ($5, US$10, $9.99 and $19.99) stays text; code is never touched. Each formula becomes
     <script type="math/tex"> and the page's MathJax is told NOT to look for $ itself (MATHJAX_CONFIG).
     The old way removed every blank and line break between any two $: prices glued table rows together.
  2. the extra forms — ==highlight== → <mark>, "- [ ]" tasks, "+ item" = a dashed list.
  3. the page — one style sheet (light / dark) in the apps' own look: the existing table colours, and
     quote / code / task / highlight / rule drawn to match them.
No Qt in this file. Keep the copies in the three apps identical (as glass_kit.py).
"""
import html
import json
import re
import uuid

import markdown2

MATH_DISPLAY_ENVIRONMENTS = frozenset({
    'equation', 'equation*', 'align', 'align*', 'alignat', 'alignat*', 'gather', 'gather*',
    'multline', 'multline*', 'flalign', 'flalign*', 'eqnarray', 'eqnarray*', 'displaymath',
})
MATH_HTML_MARK = 'type="math/tex'
# MathJax 只排 <script type="math/tex">：不在页面文字里找 $ \( \[ \begin、也不把反引号当 AsciiMath
MATHJAX_CONFIG = {
    'skipStartupTypeset': True,
    'tex2jax': {'inlineMath': [], 'displayMath': [], 'processEscapes': False,
                'processEnvironments': False, 'processRefs': False},
    'asciimath2jax': {'delimiters': []},
}
_MATH_BLANK_LINE_RE = re.compile(r'\n[ \t]*\n')
_MATH_TEX_HINT_RE = re.compile(r'[A-Za-z0-9\\^_{}=+\-*/<>|]')
_MATH_TEXT_GROUP_RE = re.compile(r'\\(?:text|textrm|textbf|textit|mathrm|mathbf|mbox|operatorname)\s*\{[^{}]*\}')
_MATH_CJK_PUNCT_RE = re.compile(r'[，。；：！？、（）【】「」『』《》“”]')
_MATH_ENV_BEGIN_RE = re.compile(r'\\begin\{([A-Za-z]+\*?)\}')
_MATH_FENCE_RE = re.compile(r'[ \t]*(`{3,}|~{3,})')


def _markdown_code_regions(text: str) -> list[tuple[int, int]]:
    """(start, end) of fenced code blocks (an unclosed fence runs to the end) and inline code
    spans (a backtick run closed by a run of the same length within the paragraph), in order."""
    regions = []
    fence = None   # (fence char, run length, start offset)
    pos = 0
    for line in text.splitlines(keepends=True):
        match = _MATH_FENCE_RE.match(line)
        if fence is None:
            if match:
                fence = (match.group(1)[0], len(match.group(1)), pos)
        else:
            stripped = line.strip()
            if stripped and set(stripped) == {fence[0]} and len(stripped) >= fence[1]:
                regions.append((fence[2], pos + len(line)))
                fence = None
        pos += len(line)
    if fence is not None:
        regions.append((fence[2], len(text)))
    spans = []
    edges = [(0, 0)] + regions + [(len(text), len(text))]
    for (_s, gap_start), (gap_end, _e) in zip(edges, edges[1:]):
        i = gap_start
        while i < gap_end:
            ch = text[i]
            if ch == '\\':
                i += 2
                continue
            if ch != '`':
                i += 1
                continue
            run_end = i
            while run_end < gap_end and text[run_end] == '`':
                run_end += 1
            run = run_end - i
            k, close = run_end, -1
            while k < gap_end:
                if text[k] == '`':
                    m = k
                    while m < gap_end and text[m] == '`':
                        m += 1
                    if m - k == run:
                        close = m
                        break
                    k = m
                    continue
                if text[k] == '\n' and _MATH_BLANK_LINE_RE.match(text, k):
                    break
                k += 1
            if close >= 0:
                spans.append((i, close))
                i = close
            else:
                i = run_end
    return sorted(regions + spans)


def _math_body_ok(body: str, inline_dollar: bool = False) -> bool:
    if not body.strip() or not _MATH_TEX_HINT_RE.search(body):
        return False
    if inline_dollar:
        # $5，公式$ / $9.99 买断）**。…$ is prose between two prices, not a formula
        outside_text = _MATH_TEXT_GROUP_RE.sub('', body)
        if _MATH_CJK_PUNCT_RE.search(outside_text) or '**' in body:
            return False
    return True


def _find_math_close(text: str, close: str, start: int) -> int:
    """Index of the next `close` at or after `start` (backslash pairs skipped), or -1 when a
    blank line (end of the paragraph) or the end comes first."""
    i, n = start, len(text)
    while i < n:
        if text.startswith(close, i):
            return i
        if text[i] == '\\':
            i += 2
            continue
        if text[i] == '\n' and _MATH_BLANK_LINE_RE.match(text, i):
            return -1
        i += 1
    return -1


def _inline_dollar_close(text: str, i: int) -> int:
    """Pandoc's rule for $…$: the closing $ of the formula opened at `i`, or -1 (a money sign)."""
    n = len(text)
    if i + 1 >= n or text[i + 1].isspace():
        return -1
    if i > 0 and text[i - 1].isascii() and text[i - 1].isalnum():
        return -1
    j = i + 1
    while j < n:
        ch = text[j]
        if ch == '\\':
            j += 2
            continue
        if ch == '\n':
            return -1
        if ch == '$':
            if text[j - 1].isspace() or (j + 1 < n and (text[j + 1].isdigit() or text[j + 1] == '$')):
                return -1
            return j if _math_body_ok(text[i + 1:j], inline_dollar=True) else -1
        j += 1
    return -1


def _protect_math_in_text(text: str, formulas: list[dict], nonce: str) -> str:
    out = []
    i, n = 0, len(text)

    def token(tex: str, display: bool, source: str) -> str:
        formulas.append({'tex': tex, 'display': display, 'source': source})
        return f'BRXMATH{nonce}N{len(formulas) - 1}X'

    while i < n:
        ch = text[i]
        if ch == '\\' and i + 1 < n:
            nxt = text[i + 1]
            if nxt == '$':                       # \$ : a plain dollar sign
                out.append('$')
                i += 2
                continue
            if nxt in '([':
                close = '\\)' if nxt == '(' else '\\]'
                end = _find_math_close(text, close, i + 2)
                if end >= 0 and _math_body_ok(text[i + 2:end]):
                    out.append(token(text[i + 2:end], nxt == '[', text[i:end + 2]))
                    i = end + 2
                    continue
            match = _MATH_ENV_BEGIN_RE.match(text, i)
            if match and match.group(1) in MATH_DISPLAY_ENVIRONMENTS:
                end_tag = '\\end{' + match.group(1) + '}'
                end = _find_math_close(text, end_tag, match.end())
                if end >= 0:
                    whole = text[i:end + len(end_tag)]
                    out.append(token(whole, True, whole))
                    i = end + len(end_tag)
                    continue
            out.append(text[i:i + 2])            # any other escape stays for markdown2
            i += 2
            continue
        if ch == '$':
            run = 1
            while i + run < n and text[i + run] == '$':
                run += 1
            if run == 2:
                end = _find_math_close(text, '$$', i + 2)
                if end >= 0 and _math_body_ok(text[i + 2:end]):
                    out.append(token(text[i + 2:end], True, text[i:end + 2]))
                    i = end + 2
                    continue
            elif run == 1:
                end = _inline_dollar_close(text, i)
                if end >= 0:
                    out.append(token(text[i + 1:end], False, text[i:end + 1]))
                    i = end + 1
                    continue
            out.append(text[i:i + run])          # a money sign ($$$ too)
            i += run
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def protect_markdown_math(text: str) -> tuple[str, list[dict], str]:
    """Model markdown with every formula replaced by a placeholder markdown2 leaves alone, the
    formulas ({'tex', 'display', 'source'}), and the placeholders' nonce. Code is left as written."""
    text = str(text or '')
    formulas = []
    nonce = uuid.uuid4().hex[:8].upper()
    if '$' not in text and '\\' not in text:
        return text, formulas, nonce
    out, last = [], 0
    for start, end in _markdown_code_regions(text):
        if start < last:
            continue
        out.append(_protect_math_in_text(text[last:start], formulas, nonce))
        out.append(text[start:end])
        last = end
    out.append(_protect_math_in_text(text[last:], formulas, nonce))
    return ''.join(out), formulas, nonce


def render_math_formula_html(tex: str, display: bool, source: str = '') -> str:
    """A formula for MathJax: its TeX in <script type="math/tex">, and the source as written
    shown until MathJax replaces it (MathJax removes the MathJax_Preview element)."""
    script_tex = re.sub(r'(?i)</(script)', r'< /\1', str(tex or ''))
    shown = source or (('$$%s$$' if display else '$%s$') % tex)
    kind = 'math/tex; mode=display' if display else 'math/tex'
    css = 'md-math md-math-display' if display else 'md-math'
    return (f'<span class="{css}"><span class="MathJax_Preview">{html.escape(shown)}</span>'
            f'<script type="{kind}">{script_tex}</script></span>')


def restore_markdown_math(rendered_html: str, formulas: list[dict], nonce: str) -> str:
    if not formulas:
        return rendered_html
    pattern = re.compile(f'BRXMATH{nonce}N(\\d+)X')
    parts = re.split(r'(<[^>]*>)', str(rendered_html))
    for index, part in enumerate(parts):
        if 'BRXMATH' not in part:
            continue
        if part.startswith('<'):   # inside a tag (an alt or title text): the source as plain text
            parts[index] = pattern.sub(
                lambda m: html.escape(formulas[int(m.group(1))]['source'], quote=True), part)
        else:
            parts[index] = pattern.sub(
                lambda m: render_math_formula_html(**formulas[int(m.group(1))]), part)
    return ''.join(parts)


def html_has_math(html_text: str) -> bool:
    return MATH_HTML_MARK in str(html_text or '')


# markdown2 2.5.5 reads **bold** by GitHub's rule: a closing ** right after punctuation must be
# followed by a space or punctuation, so "**我的判断：**这里" / "**「引用」**は" stay literal stars —
# common in model answers. markdown2_html marks each **…** the way 2.5.4 read it (per line, outside
# code) before markdown2 runs and puts <strong> there afterwards (2026-11-10). Checked on all 652
# saved answers: bold as before, plus the ** that 2.5.4 left as stars after an HTML block.
_MARKDOWN_BOLD_RE = re.compile(r'\*\*(?=\S)(.+?[*_]?)(?<=\S)\*\*')   # 2.5.4's rule, ** only (code-friendly: no __)
_MARKDOWN_RULE_LINE_RE = re.compile(r'^ {0,3}([*\-_])([ \t]*\1){2,}[ \t]*$')   # *** --- ___ lines
_MARKDOWN_CODE_RE = re.compile(r'(^[ \t]*(?:```|~~~).*?^[ \t]*(?:```|~~~)[ \t]*$|`+[^`\n]*?`+)', re.S | re.M)


def markdown2_html(text, **kwargs) -> str:
    """markdown2.markdown with **bold** read as markdown2 2.5.4 did (see above). The marks are
    full-width brackets around a random code: no markdown syntax, never part of a link, not escaped."""
    nonce = uuid.uuid4().hex[:12]
    opening, closing = f'【{nonce}o】', f'【{nonce}c】'

    def bold(segment):
        lines = segment.split('\n')
        for i, line in enumerate(lines):
            if '**' in line and not _MARKDOWN_RULE_LINE_RE.match(line):
                lines[i] = _MARKDOWN_BOLD_RE.sub(lambda match: opening + match.group(1) + closing, line)
        return '\n'.join(lines)

    parts = _MARKDOWN_CODE_RE.split(str(text or ''))   # odd parts are code: left as they are
    marked = ''.join(part if i % 2 else bold(part) for i, part in enumerate(parts))
    html = markdown2.markdown(marked, **kwargs)
    if nonce not in html:
        return html
    # inside code markdown2 found itself (an indented block) the marks are the plain ** again
    html = re.sub(r'<(pre|code)\b.*?</\1>',
                  lambda match: match.group(0).replace(opening, '**').replace(closing, '**'), html, flags=re.S)
    # a heading's id is made from its letters: the marks' letters go
    html = re.sub(r'\b(?:id|href)="[^"]*"',
                  lambda match: match.group(0).replace(opening, '').replace(closing, '')
                  .replace(nonce + 'o', '').replace(nonce + 'c', ''), html)
    return html.replace(opening, '<strong>').replace(closing, '</strong>')

# ── the extra forms ───────────────────────────────────────────────────────────────────────────────────
_HIGHLIGHT_RE = re.compile(r'(?<![=\w])==(?=\S)(.+?)(?<=\S)==(?![=\w])')
_DASH_ITEM_RE = re.compile(r'^(\s*)\+ (?=\S)')
_DASH_MARK = ''
PREVIEW_EXTRAS = ['code-friendly', 'fenced-code-blocks', 'footnotes', 'tables', 'code-color', 'pyshell', 'nofollow',
                  'cuddled-lists', 'header-ids', 'strike', 'task_list']


def _extra_forms(text: str) -> str:
    """==highlight== → <mark>; "+ item" marked as a dashed-list item. Code is left as written."""
    out, last = [], 0

    def convert(segment):
        lines = segment.split('\n')
        for index, line in enumerate(lines):
            if '==' in line:
                line = _HIGHLIGHT_RE.sub(r'<mark>\1</mark>', line)
            lines[index] = _DASH_ITEM_RE.sub(lambda m: m.group(1) + '- ' + _DASH_MARK, line)
        return '\n'.join(lines)

    for start, end in _markdown_code_regions(text):
        if start < last:
            continue
        out.append(convert(text[last:start]))
        out.append(text[start:end])
        last = end
    out.append(convert(text[last:]))
    return ''.join(out)


def _finish_extra_forms(rendered: str) -> str:
    """Each item carries its own look (markdown2 puts "- " and "+ " items that follow each other into one
    list, and wraps an item in <p> when a blank line is near)."""
    if _DASH_MARK in rendered:
        rendered = re.sub(r'<li>(\s*<p>)?' + _DASH_MARK, lambda m: '<li class="md-dash-item">' + (m.group(1) or ''), rendered)
        rendered = rendered.replace(_DASH_MARK, '')
    if 'task-list-item-checkbox' in rendered:
        # a box drawn as text: it shows the same in a web view and in Qt's own text view
        rendered = re.sub(r'<li>(\s*<p>)?\s*<input type="checkbox" class="task-list-item-checkbox" checked disabled>\s*',
                          lambda m: '<li class="md-task md-task-done">' + (m.group(1) or '') + '<span class="md-box">☑</span> ', rendered)
        rendered = re.sub(r'<li>(\s*<p>)?\s*<input type="checkbox" class="task-list-item-checkbox" disabled>\s*',
                          lambda m: '<li class="md-task">' + (m.group(1) or '') + '<span class="md-box">☐</span> ', rendered)
        rendered = rendered.replace('<ul class="contains-task-list">', '<ul>')
    return rendered


def render_markdown_body(text: str, extras=None) -> str:
    """Markdown → the HTML of the body (formulas protected, the extra forms understood)."""
    text = str(text or '')
    protected, formulas, nonce = protect_markdown_math(_extra_forms(text))
    protected = re.sub(r'\|(\n(\t)*\n(\t)*)\|', '|\n|', protected)      # a blank line inside a table (as the apps always did)
    rendered = markdown2_html(protected, extras=list(extras or PREVIEW_EXTRAS))
    return restore_markdown_math(_finish_extra_forms(rendered), formulas, nonce)


# the colours of highlighted code (the "code-color" extra; the apps' sheet since their first versions)
CODE_COLOR_CSS = """
    .hll { background-color: #ffffcc }
    .c { color: #0099FF; font-style: italic } /* Comment */
    .err { color: #AA0000; background-color: #FFAAAA } /* Error */
    .k { color: #006699; font-weight: bold } /* Keyword */
    .o { color: #555555 } /* Operator */
    .ch { color: #0099FF; font-style: italic } /* Comment.Hashbang */
    .cm { color: #0099FF; font-style: italic } /* Comment.Multiline */
    .cp { color: #009999 } /* Comment.Preproc */
    .cpf { color: #0099FF; font-style: italic } /* Comment.PreprocFile */
    .c1 { color: #0099FF; font-style: italic } /* Comment.Single */
    .cs { color: #0099FF; font-weight: bold; font-style: italic } /* Comment.Special */
    .gd { background-color: #FFCCCC; border: 1px solid #CC0000 } /* Generic.Deleted */
    .ge { font-style: italic } /* Generic.Emph */
    .gr { color: #FF0000 } /* Generic.Error */
    .gh { color: #003300; font-weight: bold } /* Generic.Heading */
    .gi { background-color: #CCFFCC; border: 1px solid #00CC00 } /* Generic.Inserted */
    .go { color: #AAAAAA } /* Generic.Output */
    .gp { color: #000099; font-weight: bold } /* Generic.Prompt */
    .gs { font-weight: bold } /* Generic.Strong */
    .gu { color: #003300; font-weight: bold } /* Generic.Subheading */
    .gt { color: #99CC66 } /* Generic.Traceback */
    .kc { color: #006699; font-weight: bold } /* Keyword.Constant */
    .kd { color: #006699; font-weight: bold } /* Keyword.Declaration */
    .kn { color: #006699; font-weight: bold } /* Keyword.Namespace */
    .kp { color: #006699 } /* Keyword.Pseudo */
    .kr { color: #006699; font-weight: bold } /* Keyword.Reserved */
    .kt { color: #007788; font-weight: bold } /* Keyword.Type */
    .m { color: #FF6600 } /* Literal.Number */
    .s { color: #CC3300 } /* Literal.String */
    .na { color: #330099 } /* Name.Attribute */
    .nb { color: #336666 } /* Name.Builtin */
    .nc { color: #00AA88; font-weight: bold } /* Name.Class */
    .no { color: #336600 } /* Name.Constant */
    .nd { color: #9999FF } /* Name.Decorator */
    .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .ne { color: #CC0000; font-weight: bold } /* Name.Exception */
    .nf { color: #CC00FF } /* Name.Function */
    .nl { color: #9999FF } /* Name.Label */
    .nn { color: #00CCFF; font-weight: bold } /* Name.Namespace */
    .nt { color: #330099; font-weight: bold } /* Name.Tag */
    .nv { color: #003333 } /* Name.Variable */
    .ow { color: #000000; font-weight: bold } /* Operator.Word */
    .w { color: #bbbbbb } /* Text.Whitespace */
    .mb { color: #FF6600 } /* Literal.Number.Bin */
    .mf { color: #FF6600 } /* Literal.Number.Float */
    .mh { color: #FF6600 } /* Literal.Number.Hex */
    .mi { color: #FF6600 } /* Literal.Number.Integer */
    .mo { color: #FF6600 } /* Literal.Number.Oct */
    .sa { color: #CC3300 } /* Literal.String.Affix */
    .sb { color: #CC3300 } /* Literal.String.Backtick */
    .sc { color: #CC3300 } /* Literal.String.Char */
    .dl { color: #CC3300 } /* Literal.String.Delimiter */
    .sd { color: #CC3300; font-style: italic } /* Literal.String.Doc */
    .s2 { color: #CC3300 } /* Literal.String.Double */
    .se { color: #CC3300; font-weight: bold } /* Literal.String.Escape */
    .sh { color: #CC3300 } /* Literal.String.Heredoc */
    .si { color: #AA0000 } /* Literal.String.Interpol */
    .sx { color: #CC3300 } /* Literal.String.Other */
    .sr { color: #33AAAA } /* Literal.String.Regex */
    .s1 { color: #CC3300 } /* Literal.String.Single */
    .ss { color: #FFCC33 } /* Literal.String.Symbol */
    .bp { color: #336666 } /* Name.Builtin.Pseudo */
    .fm { color: #CC00FF } /* Name.Function.Magic */
    .vc { color: #003333 } /* Name.Variable.Class */
    .vg { color: #003333 } /* Name.Variable.Global */
    .vi { color: #003333 } /* Name.Variable.Instance */
    .vm { color: #003333 } /* Name.Variable.Magic */
    .il { color: #FF6600 } /* Literal.Number.Integer.Long */
"""


# ── the page ──────────────────────────────────────────────────────────────────────────────────────────
import os
import urllib.parse

# MathJax: the app's own copy (MathJax-2.7.1/, the trimmed 28 MB one Strawberry ships — no network); only
# when an app has none, the public copy.
MATHJAX_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-MML-AM_CHTML'
_MATHJAX_FOLDER = ['']


def set_mathjax_folders(*folders) -> str:
    """The first of `folders` that holds MathJax.js becomes the page's MathJax; returns it ('' = none)."""
    _MATHJAX_FOLDER[0] = next((folder for folder in folders if folder and os.path.isfile(os.path.join(folder, 'MathJax.js'))), '')
    return _MATHJAX_FOLDER[0]


def mathjax_source() -> str:
    folder = _MATHJAX_FOLDER[0] or set_mathjax_folders(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MathJax-2.7.1'))
    if folder:
        return 'file://' + urllib.parse.quote(os.path.join(folder, 'MathJax.js')) + '?config=TeX-MML-AM_CHTML'
    return MATHJAX_CDN


def preview_palette(dark: bool) -> dict:
    """The apps' own colours: the table they always had, and what is drawn to go with it."""
    if dark:
        return {'line': '#5A5A5E', 'head': '#3A3A3A', 'cell': '#343436', 'soft': '#343436', 'muted': '#A0A0A6',
                'mark': 'rgba(180, 95, 230, 0.38)', 'link': '#6CB6FF', 'bar': '#6A8F95'}
    return {'line': '#999999', 'head': '#b5cfd2', 'cell': '#dcddc0', 'soft': '#EEF0E4', 'muted': '#6E6E73',
            'mark': 'rgba(180, 95, 230, 0.24)', 'link': '#0A66C2', 'bar': '#8FB3B8'}


def preview_css(dark: bool, text_color: str) -> str:
    p = preview_palette(dark)
    return """
    table { font-family: verdana, arial, sans-serif; font-size: 11px; color: %(text)s; border: 1px solid %(line)s;
            border-collapse: collapse; margin: 0.6em 0; }
    th { background: %(head)s; border: 1px solid %(line)s; padding: 8px; }
    td { background: %(cell)s; border: 1px solid %(line)s; padding: 8px; }
    table, th, td { color: %(text)s !important; }
    blockquote { margin: 0.6em 0; padding: 2px 0 2px 12px; border-left: 3px solid %(bar)s; color: %(muted)s; }
    blockquote p { margin: 0.25em 0; white-space: pre-line; }
    hr { border: none; border-top: 1px solid %(line)s; height: 0; margin: 1em 0; }
    mark { background-color: %(mark)s; color: inherit; padding: 0 2px; border-radius: 3px; }
    code { font-family: Menlo, Courier, monospace; font-size: 0.88em; background-color: %(soft)s; padding: 1px 4px; border-radius: 4px; }
    pre { background-color: %(soft)s; border: 1px solid %(line)s; border-radius: 4px; padding: 8px 10px; overflow-x: auto; }
    pre code { background: none; padding: 0; border-radius: 0; font-size: 0.88em; }
    a { color: %(link)s; }
    img, video { max-width: 100%%; height: auto; }
    li.md-task { list-style-type: none; margin-left: -1.2em; }
    li.md-task p, li.md-dash-item p { margin: 0.2em 0; }
    li.md-task .md-box { font-family: "Apple Symbols", Menlo, sans-serif; margin-right: 2px; }
    li.md-task-done { color: %(muted)s; }
    li.md-dash-item { list-style-type: "–  "; }
    sup, sub { font-size: 0.75em; }
    .md-math-display { display: block; margin: 0.6em 0; }
    """ % dict(p, text=text_color)


def mathjax_head(rendered_body: str) -> str:
    """The MathJax scripts — only when the page has a formula. MathJax typesets our formula scripts and
    never looks for $ in the text itself."""
    if not html_has_math(rendered_body):
        return ''
    config = dict(MATHJAX_CONFIG, displayAlign='left', displayIndent='4em', skipStartupTypeset=False,
                  TeX={'equationNumbers': {'autoNumber': 'AMS'}})
    return ('<script type="text/x-mathjax-config">MathJax.Hub.Config(%s);</script>\n<script src="%s"></script>'
            % (json.dumps(config), mathjax_source()))


def preview_page(rendered_body: str, *, font_family: str, font_size: int, background: str, text_color: str,
                 dark: bool, extra_css: str = '') -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    html, body { margin: 0; padding: 0; font-size: %dpx; font-family: "%s"; background-color: %s; color: %s; }
%s
%s
</style>
%s
</head>
<body>
%s
</body>
</html>
""" % (int(font_size), font_family, background, text_color, preview_css(dark, text_color) + CODE_COLOR_CSS, extra_css,
       mathjax_head(rendered_body), rendered_body)


# ── "bold reading" (the first part of every word in bold) on a rendered page ─────────────────────────
# ── quick ways for typing in a long text (2026-11-21) ────────────────────────────────────────────────
# Ryan: the bold reading view "放到长文档上速度非常慢。会影响所有输入框的输入速度". Measured on 45 000
# characters: the bold took 406 ms and the Markdown 73 ms on EVERY key, and while that ran on its thread the
# interface got its turn only every 14 ms. Both now remember what they made: a key changes one piece, the
# rest is taken from memory (2 ms and 0.3 ms). The results are the same as before, piece for piece.
_BIONIC_MEMORY = {}
_BIONIC_MEMORY_MAX = 60000
_BLOCK_MEMORY = {}
_BLOCK_MEMORY_MAX = 20000
_TAG_SPLIT = re.compile(r'(<!--.*?-->|<[^>]+>)', re.S)
_TAG_NAME = re.compile(r'</?\s*([a-zA-Z][a-zA-Z0-9]*)')
_VOID_TAGS = frozenset(('br', 'img', 'hr', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'))
_NO_BOLD_TAGS = frozenset(('pre', 'code', 'script', 'style', 'kbd'))
_NO_BOLD_CLASS = re.compile(r'class\s*=\s*["\'][^"\']*\b(?:md-math|md-box)\b')


def bionic_html(rendered_body: str, transform) -> str:
    """Applies `transform` (plain text → the same text with **…** around what is to be bold) to the TEXT of
    a rendered page: tags, code, formulas and addresses are never touched. The page is walked tag by tag
    (no tree is built) and what was made for a piece of text is remembered, so typing in a long text only
    costs the piece that changed."""
    try:
        return _bionic_html_quick(rendered_body or '', transform)
    except Exception:
        return _bionic_html_tree(rendered_body, transform)


def _bionic_html_quick(body: str, transform) -> str:
    memory = _BIONIC_MEMORY
    if len(memory) > _BIONIC_MEMORY_MAX:
        memory.clear()
    out, stack = [], []          # stack: (tag name, text under it is left alone)
    blocked = 0
    for piece in _TAG_SPLIT.split(body):
        if not piece:
            continue
        if piece[0] == '<' and piece[-1] == '>':
            if piece.startswith('<!'):
                out.append(piece)
                continue
            found = _TAG_NAME.match(piece)
            name = found.group(1).lower() if found else ''
            if name in ('strong', 'b'):
                continue                             # the bold of this view is the reading aid, not the author's
            if name and name not in _VOID_TAGS and not piece.endswith('/>'):
                if piece[1] == '/':
                    for index in range(len(stack) - 1, -1, -1):
                        if stack[index][0] == name:
                            blocked -= sum(1 for _n, b in stack[index:] if b)
                            del stack[index:]
                            break
                else:
                    no_bold = name in _NO_BOLD_TAGS or bool(_NO_BOLD_CLASS.search(piece))
                    stack.append((name, no_bold))
                    blocked += no_bold
            out.append(piece)
            continue
        if blocked or not piece.strip():
            out.append(piece)
            continue
        marked = memory.get(piece)
        if marked is None:
            marked = html.escape(transform(html.unescape(piece)), quote=False)
            marked = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', marked, flags=re.S).replace('**', '')
            memory[piece] = marked
        out.append(marked)
    return ''.join(out)


_FENCE_LINE = re.compile(r'^ {0,3}(```|~~~)')
_NOT_A_PLAIN_START = re.compile(r'^(?:[ \t]|[-*+][ \t]|\d+[.)][ \t]|>|\||<|:|\[\^|={3,}\s*$|-{3,}\s*$|\*{3,}\s*$|_{3,}\s*$)')
_WHOLE_ONLY = re.compile(r'(?m)^ {0,3}\[[^\]]+\]:[ \t]|\[\^[^\]]+\]|^ {0,3}<(?!!--)[a-zA-Z]')


def _markdown_blocks(text: str):
    """The text cut where one part cannot change how the next is read: at blank lines before a heading or
    before an ordinary paragraph — never inside a code block or a $$ formula. None = this text must be
    rendered whole (footnotes, link definitions, raw HTML blocks reach across such cuts)."""
    if _WHOLE_ONLY.search(text):
        return None
    blocks, current, fence, formula, blank = [], [], None, False, False
    for line in text.split('\n'):
        mark = _FENCE_LINE.match(line)
        if mark and not formula:
            fence = None if fence == mark.group(1) else (fence or mark.group(1))
        elif not fence and line.count('$$') % 2 == 1:
            formula = not formula
        if not line.strip():
            blank = True
            current.append(line)
            continue
        if blank and current and not fence and not formula and not mark and (
                line.startswith('#') or not _NOT_A_PLAIN_START.match(line)) and line.count('$$') % 2 == 0:
            blocks.append('\n'.join(current))
            current = []
        blank = False
        current.append(line)
    if current:
        blocks.append('\n'.join(current))
    return None if (fence or formula) else blocks


def render_markdown_body_quick(text: str) -> str:
    """render_markdown_body for a text that is being typed in: every block is rendered by itself and
    remembered, so a key costs the block it is in. A text that cannot be cut safely is rendered whole."""
    text = str(text or '')
    blocks = _markdown_blocks(text) if len(text) > 4000 else None
    if not blocks or len(blocks) < 2:
        return render_markdown_body(text)
    memory = _BLOCK_MEMORY
    if len(memory) > _BLOCK_MEMORY_MAX:
        memory.clear()
    out, used = [], {}
    for block in blocks:
        got = memory.get(block)
        if got is None:
            got = memory[block] = _heading_id_parts(render_markdown_body(block))
        pieces, names = got
        if not names:
            out.append(pieces[0])
            continue
        made = []
        for piece, name in zip(pieces, names):      # a heading name used before gets -2, -3 … as in a whole render
            count = used.get(name, 0) + 1
            used[name] = count
            made.append(piece)
            made.append(name if count == 1 else '%s-%d' % (name, count))
        made.append(pieces[-1])
        out.append(''.join(made))
    return '\n'.join(out)


_HEADING_ID = re.compile(r'(<h[1-6]\b[^>]*?\bid=")([^"]*)(")')


def _heading_id_parts(rendered: str):
    """A rendered block as (the text around its heading names, the names) — the names without the -2, -3
    the block gave to names it holds twice."""
    pieces, names, seen, last = [], [], {}, 0
    for found in _HEADING_ID.finditer(rendered):
        name = found.group(2)
        for base, count in seen.items():
            if name == '%s-%d' % (base, count + 1):
                name = base
                break
        seen[name] = seen.get(name, 0) + 1
        pieces.append(rendered[last:found.start(2)])
        names.append(name)
        last = found.end(2)
    pieces.append(rendered[last:])
    return pieces, names


def _bionic_html_tree(rendered_body: str, transform) -> str:
    """Applies `transform` (plain text → the same text with **…** around what is to be bold) to the TEXT of
    a rendered page: tags, code, formulas and addresses are never touched. (Doing it on the Markdown
    source broke everything that is not plain words: formulas, <sup>, tables, task boxes.)"""
    from bs4 import BeautifulSoup, NavigableString
    soup = BeautifulSoup(rendered_body or '', 'html.parser')
    for strong in soup.find_all(['strong', 'b']):
        strong.unwrap()                      # the bold of this view is the reading aid, not the author's
    for node in list(soup.find_all(string=True)):
        if not isinstance(node, NavigableString) or type(node) is not NavigableString:
            continue                         # comments, doctype …
        if not str(node).strip() or node.find_parent(['pre', 'code', 'script', 'style', 'kbd']) is not None:
            continue
        if node.find_parent(class_='md-math') is not None or node.find_parent(class_='md-box') is not None:
            continue
        marked = html.escape(transform(str(node)), quote=False)
        marked = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', marked, flags=re.S).replace('**', '')
        node.replace_with(BeautifulSoup(marked, 'html.parser'))
    return str(soup)

