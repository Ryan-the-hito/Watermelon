# -*- coding: utf-8 -*-
"""Watermelon → Broccoli (2026-11-21): the public door Tomato uses.

Ryan 2026-11-21: "我希望在编辑区右键可以有一个选项去把东西发给 broccoli，就像 tomato 一样用那个公开的接口".
Broccoli's "Agent automation" door: POST 127.0.0.1:<port>/agent/tasks with the token from Broccoli's own
agent_automation_server.json (in its data folder). Broccoli not running → it is opened in the background
and waited for. No Qt in this file; send() blocks (call it from a background thread).

The payload: prompt (required), title, source, metadata, group (the conversation goes into the group of that
name), show (open it in front). Fields a Broccoli does not know are ignored by it, so newer optional fields
(attachments, a folder to write the answer to) can be sent to an older Broccoli without harm.
"""
import http.client
import json
import logging
import os
import subprocess
import time

BROCCOLI_BUNDLE_ID = 'com.ryanthehito.broccoli'
BROCCOLI_APP_NAME = 'Broccoli'
DEFAULT_PORT = 49153
PING_SERVICE = 'broccoli-agent-automation'
SOURCE = 'Watermelon'
GROUP = 'Watermelon'             # every conversation started from Watermelon goes into this Broccoli group
LAUNCH_WAIT_SECONDS = 120
# Where Broccoli is downloaded (its own update check uses this page). Ryan 2026-11-21: when Broccoli is not on
# the Mac, "先推荐下载" — the first thing offered is to download it.
DOWNLOAD_URL = 'https://github.com/Ryan-the-hito/Broccoli/releases/latest'


def open_download_page() -> bool:
    """The download page in the default browser."""
    try:
        return subprocess.run(['/usr/bin/open', DOWNLOAD_URL], capture_output=True, timeout=20).returncode == 0
    except Exception:
        logging.exception('opening the Broccoli download page failed')
        return False


def info_path():
    return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', BROCCOLI_BUNDLE_ID,
                        'BroccoliAppPath', 'agent_automation_server.json')


def broccoli_installed() -> bool:
    if os.path.isdir(os.path.dirname(info_path())):
        return True
    try:
        from AppKit import NSWorkspace
        return NSWorkspace.sharedWorkspace().URLForApplicationWithBundleIdentifier_(BROCCOLI_BUNDLE_ID) is not None
    except Exception:
        return False


def read_info(path=None):
    """(port, token) from the file Broccoli writes for other programs."""
    try:
        with open(path or info_path(), encoding='utf-8') as handle:
            data = json.load(handle)
        return int(data.get('port') or DEFAULT_PORT), str(data.get('token') or '').strip()
    except Exception:
        return DEFAULT_PORT, ''


def live_transcript_paths(path=None):
    """(file, subscribers folder) of Broccoli's live voice transcript, as its own description file names
    them; None = this Broccoli has none (older than 2026-11-21) or has never run on this Mac."""
    try:
        with open(path or info_path(), encoding='utf-8') as handle:
            block = (json.load(handle) or {}).get('live_transcript') or {}
        file, subscribers = str(block.get('file') or ''), str(block.get('subscribers') or '')
        return (file, subscribers) if os.path.isabs(file) and os.path.isabs(subscribers) else None
    except Exception:
        return None


def _request(port, method, route, body=None, token='', timeout=5):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=timeout)   # this Mac only, never a proxy
    try:
        headers = {}
        if body is not None:
            headers['Content-Type'] = 'application/json; charset=utf-8'
        if token:
            headers['X-Broccoli-Agent-Token'] = token
        connection.request(method, route, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        try:
            data = json.loads(raw.decode('utf-8'))
        except Exception:
            data = {}
        return response.status, data if isinstance(data, dict) else {}
    finally:
        connection.close()


def ping(port) -> bool:
    try:
        status, data = _request(port, 'GET', '/ping', timeout=2)
        return status == 200 and data.get('service') == PING_SERVICE
    except Exception:
        return False


def launch_broccoli() -> bool:
    """Open Broccoli without bringing it to the front. False = it is not on this Mac."""
    for arguments in (['-b', BROCCOLI_BUNDLE_ID], ['-a', BROCCOLI_APP_NAME]):
        try:
            if subprocess.run(['/usr/bin/open', '-g'] + arguments, capture_output=True, timeout=20).returncode == 0:
                return True
        except Exception:
            logging.exception('opening Broccoli failed')
    return False


def send(prompt, title='', group=GROUP, metadata=None, show=False, extra=None, info=None, launch=None,
         wait=LAUNCH_WAIT_SECONDS, sleep=time.sleep):
    """Hand one piece of text to Broccoli as a new conversation.
    → (True, 'sent') or (False, 'not_installed' | 'no_answer' | 'refused …'). extra: further optional fields."""
    port, token = read_info(info)
    if not ping(port):
        if not (launch or launch_broccoli)():
            return False, 'not_installed'
        deadline = time.time() + wait
        while True:
            sleep(1.0)
            port, token = read_info(info)      # a first start writes the file
            if ping(port):
                break
            if time.time() >= deadline:
                return False, 'no_answer'
    payload = {'prompt': str(prompt or ''), 'source': SOURCE, 'metadata': dict(metadata or {})}
    if title:
        payload['title'] = str(title)
    if group:
        payload['group'] = str(group)
    if show:
        payload['show'] = True
    payload.update(dict(extra or {}))
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    try:
        status, data = _request(port, 'POST', '/agent/tasks', body, token, timeout=15)
        if status == 401:                      # Broccoli made a new token since the file was read
            port, token = read_info(info)
            status, data = _request(port, 'POST', '/agent/tasks', body, token, timeout=15)
    except Exception as error:
        return False, 'no_answer (%s)' % error
    if status == 202 and data.get('ok'):
        return True, 'sent'
    return False, 'refused %s %s' % (status, data.get('error') or '')


def stage(paths, title='', group=GROUP, metadata=None, extra_fields=None, **more):
    """Hand files to Broccoli as material to ask about — NOT a question (Ryan 2026-11-24: "不是要你当成问题直接
    发送，而是…当成背景语境，然后用户再去 broccoli 里问问题"): Broccoli comes out with a blank conversation, the
    files in its attachment tray, the cursor in the prompt; nothing runs until the person asks.
    extra_fields: more door fields, e.g. "write_back" + "reply_to" + "id" (2026-11-25, Write Here with Broccoli:
    the first answer in that conversation comes back to <reply_to>/<id>.json; Broccoli 566 or newer).
    → as send()."""
    extra = dict(extra_fields or {})
    extra.update({'stage': True, 'attachments': [str(path) for path in paths]})
    return send('', title=title, group=group, metadata=metadata, extra=extra, **more)
