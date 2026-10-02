#!/usr/bin/env python3
"""Print the JSON shape (keys and value types, never values) of a session file. Use '-' for stdin."""
import json
import sys


def shape(o, depth=0):
    if isinstance(o, dict):
        return {k: shape(v, depth + 1) for k, v in list(o.items())[:30]} if depth < 4 else "{...}"
    if isinstance(o, list):
        return [shape(o[0], depth + 1)] if o else []
    return type(o).__name__


src = sys.stdin if sys.argv[1] == "-" else open(sys.argv[1])
text = src.read()
try:
    print(json.dumps(shape(json.loads(text)), indent=1)[:4000])
except json.JSONDecodeError:
    for i, line in enumerate(text.splitlines()[:12]):
        try:
            print(i, json.dumps(shape(json.loads(line)))[:800])
        except json.JSONDecodeError:
            print(i, "NOT JSON:", line[:60])
