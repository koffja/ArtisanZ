"""Filter for tools/check_no_bare_artisan_plus.sh.

Consumes ripgrep -B 1 output on stdin and exits non-zero with a helpful
message on stderr if any violation remains after applying the
whitelists documented in the shell script.

Output stream from `rg -n -B 1`:
  Context line:   path-NUM-content   (separator before NUM is "-")
  Match line:     path:NUM:content   (separator before NUM is ":")
  Group sep:      "--"               (no other content)

We track a small deque of recent non-empty context lines so the
filter can recognize multi-line function calls and docstring
continuations.
"""
import re
import sys
from collections import deque

# Window of recent non-empty context lines we keep looking at. 3 is
# enough to span the longest pattern we whitelist (a docstring opener
# + 2 continuation lines). Larger windows are unnecessary and slow.
PREV_WINDOW = 3

triple_dq = chr(34) * 3
triple_sq = chr(39) * 3

lines = sys.stdin.read().splitlines()
keep = []
prev = deque(maxlen=PREV_WINDOW)
for line in lines:
    # Context line:   path-NUM-content
    m_ctx = re.match(r"^(\S+)-(\d+)-(.*)$", line)
    # Match line:     path:NUM:content
    m_mat = re.match(r"^(\S+):(\d+):(.*)$", line)
    if m_ctx:
        path, lineno, content = m_ctx.groups()
        if content.strip():
            prev.append(content)
        continue
    if m_mat:
        path, lineno, content = m_mat.groups()
    else:
        # Group separator ("--") or other unparseable line — clear
        # the window so a docstring opener doesn't leak across a long
        # gap.
        prev.clear()
        continue
    window = list(prev) + [content]
    if any("translatedServiceMessage(" in c for c in window):
        continue
    if any(".replace(" in c for c in window):
        continue
    if any(triple_dq in c or triple_sq in c for c in window):
        continue
    # Autogen help file: wrapped at the consumer (main.py:13405).
    if "keyboardshortcuts_help" in path:
        continue
    # Functional email recipient: literal 'logfile@artisan.plus' and
    # the f-string form f"{'logfile'}@{'artisan.plus'}".
    if "logfile" in content and "artisan.plus" in content:
        continue
    # Hardcoded __release_sponsor_* assignments in artisanlib/__init__.py.
    if "__release_sponsor_" in content:
        continue
    # Pure comment line: the actual code line starts with #.
    if re.match(r"^\S+:\d+:\s*#", line):
        continue
    keep.append(line)

if keep:
    sys.stderr.write("ERROR: Found bare 'artisan.plus' literal(s) that bypass translatedServiceMessage:\n")
    for v in keep:
        sys.stderr.write(v + "\n")
    sys.stderr.write("\n")
    sys.stderr.write("Fix options:\n")
    sys.stderr.write("  1. Wrap the call site: translatedServiceMessage('<your string>', context='<ctx>')\n")
    sys.stderr.write("  2. Use config.app_name in a format string\n")
    sys.stderr.write("  3. If the literal is intentional (e.g. URL), extract to a named constant\n")
    sys.stderr.write("     in plus.service_identity and add an exception to this script.\n")
    sys.exit(1)
sys.exit(0)
