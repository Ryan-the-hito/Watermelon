#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Qt Linguist .ts files for Watermelon's UI translation (same scheme as Broccoli's).

The app wraps every user-visible English string with _tr('...'), which resolves through
QCoreApplication.translate('Watermelon', text). This script is the extractor: it reads the _tr()
literals out of Watermelon_26new.py and glass_kit.py with ast, joins them with TRANSLATIONS
(translations_watermelon.py) and writes i18n/watermelon_zh_CN.ts + watermelon_ja_JP.ts. A source
string missing from the table is written as type="unfinished" (the UI then shows the English).

Usage:
    python3 i18n/gen_ts.py                    # regenerate the two .ts files, list what is missing
    lrelease i18n/watermelon_zh_CN.ts         # compile to .qm (repeat for ja_JP)
"""
import ast
import os
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = [os.path.join(HERE, '..', 'Watermelon_26new.py'), os.path.join(HERE, '..', 'glass_kit.py'), os.path.join(HERE, '..', 'watermelon_ui.py'),
           os.path.join(HERE, '..', 'watermelon_office.py'),
           os.path.join(HERE, '..', 'watermelon_attachments.py'), os.path.join(HERE, '..', 'watermelon_lecture.py'),
           os.path.join(HERE, '..', 'watermelon_courseware.py'), os.path.join(HERE, '..', 'watermelon_handles.py'),
           os.path.join(HERE, '..', 'watermelon_outline.py'), os.path.join(HERE, '..', 'watermelon_scan.py'),
           os.path.join(HERE, '..', 'watermelon_anki.py')]
CONTEXT = 'Watermelon'
sys.path.insert(0, HERE)
from translations_watermelon import TRANSLATIONS  # noqa: E402  {english: (zh_CN, ja_JP)}


# Strings translated through a VARIABLE (_tr(label)), which the ast pass cannot see: none in Watermelon.
EXTRA_SOURCE_STRINGS = []


def extract_source_strings():
    values = set()
    for path in SOURCES:
        tree = ast.parse(open(path, encoding='utf-8').read())
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_tr'
                    and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                values.add(node.args[0].value)
    values.update(EXTRA_SOURCE_STRINGS)
    return sorted(values)


def emit_ts(path, language, index):
    strings = extract_source_strings()
    out = ['<?xml version="1.0" encoding="utf-8"?>', '<!DOCTYPE TS>',
           '<TS version="2.1" language="%s" sourcelanguage="en_US">' % language,
           '<context>', '    <name>%s</name>' % CONTEXT]
    missing = []
    for source in strings:
        pair = TRANSLATIONS.get(source)
        translation = pair[index] if pair else ''
        out.append('    <message>')
        out.append('        <source>%s</source>' % escape(source))
        if translation:
            out.append('        <translation>%s</translation>' % escape(translation))
        else:
            out.append('        <translation type="unfinished"></translation>')
            missing.append(source)
        out.append('    </message>')
    out.extend(['</context>', '</TS>', ''])
    open(path, 'w', encoding='utf-8').write('\n'.join(out))
    return len(strings), missing


def main():
    total, missing_zh = emit_ts(os.path.join(HERE, 'watermelon_zh_CN.ts'), 'zh_CN', 0)
    _, missing_ja = emit_ts(os.path.join(HERE, 'watermelon_ja_JP.ts'), 'ja_JP', 1)
    stale = sorted(set(TRANSLATIONS) - set(extract_source_strings()))
    print('source strings: %d' % total)
    print('missing zh: %d  missing ja: %d' % (len(missing_zh), len(missing_ja)))
    for item in missing_zh[:40]:
        print('  MISSING:', repr(item))
    if stale:
        print('stale table entries (no longer in source): %d' % len(stale))
        for item in stale[:20]:
            print('  STALE:', repr(item))
    return 1 if missing_zh or missing_ja else 0


if __name__ == '__main__':
    sys.exit(main())
