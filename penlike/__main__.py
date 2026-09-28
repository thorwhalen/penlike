# PYTHON_ARGCOMPLETE_OK
"""``penlike`` on the command line: every verb of :data:`penlike.tools.TOOLS`.

    penlike new me
    penlike gather me mbox ~/mail/sent.mbox --until 2023-01-01
    penlike build me
    penlike brief --like me --channel email --to ada@example.org
    penlike check draft.md --like me --style email.one

``--json`` anywhere prints the whole result instead of its text. Where a verb takes
a text, ``-`` reads it from standard input and the name of a file reads the file.
The exit status is 0 when the result is ok and 1 when it is not.
"""

import functools
import json
import sys
from pathlib import Path

import cw

from penlike import tools
from penlike.base import PenlikeError


def _command(func):
    func = tools.without(func, ("files",))

    @functools.wraps(func)
    def command(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PenlikeError as error:
            raise cw.CommandError(str(error)) from error

    return command


def _text(value):
    """``-`` is standard input, the name of an existing file is its content, else the text itself."""
    if value == "-":
        return sys.stdin.read()
    try:
        path = Path(value).expanduser()
        if len(value) < 1024 and path.is_file():
            return path.read_text(encoding="utf-8")
    except OSError:
        pass
    return value


def _egress(as_json):
    def egress(result, *, out, err):
        if as_json or not isinstance(result, dict):
            print(json.dumps(result, indent=2, ensure_ascii=False), file=out)
        else:
            print(result.get("text") or result.get("summary") or "", file=out)
        return 0 if not isinstance(result, dict) or result.get("ok", True) else 1

    return egress


def main(argv=None):
    """Run the command line. The ``penlike`` console script."""
    for stream in (sys.stdout, sys.stderr):
        getattr(stream, "reconfigure", lambda **_: None)(errors="backslashreplace")
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    commands = {f.__name__.replace("_", "-"): _command(f) for f in tools.TOOLS}
    config = {name: {"text": {"codec": _text}} for name in ("check", "measure")}
    code = cw.dispatch(
        commands,
        [a for a in argv if a != "--json"],
        prog="penlike",
        convention=cw.MODERN,
        egress=_egress(as_json),
        config=config,
    )
    raise SystemExit(code)


if __name__ == "__main__":
    main()
