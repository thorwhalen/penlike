"""MCP over stdio: the same verbs, for local MCP clients.

Run ``penlike-mcp`` after ``pip install 'penlike[mcp]'``. There is no second list of
verbs: the tools are :data:`penlike.tools.TOOLS`, minus those marked as reaching into
the host (gathering from arbitrary paths, deleting a model, linking skills), which
stay at the terminal. The data root is the server's: ``data_dir`` is removed from
every tool's schema. Point the server elsewhere with ``PENLIKE_DATA_DIR``.

>>> "brief" in tool_names(), "gather" in tool_names(), "install_skills" in tool_names()
(True, False, False)
"""

from __future__ import annotations

from penlike.tools import TOOLS, without

__all__ = ["INSTRUCTIONS", "main", "mk_server", "tool_names"]

INSTRUCTIONS = (
    "Models of how an author, a group or a corpus writes, register by register. Call "
    "`brief` before writing in someone's style: it chooses the register and returns the "
    "measured profile, the notes and examples. Call `check` on the draft and revise what "
    "it reports, at most twice. Examples are private: take the style from them, never "
    "quote them. Passing `check` does not mean a text would pass for the author's. Write "
    "in a person's style only for that person or with their agreement."
)


def tool_names() -> list[str]:
    """The verbs exposed over MCP: all of them but those that reach into the host."""
    return [t.__name__ for t in TOOLS if not getattr(t, "mutates_host", False)]


def mk_server():
    """A FastMCP server over the exposed verbs (not started)."""
    from py2mcp import mk_mcp_server

    exposed = set(tool_names())
    return mk_mcp_server(
        [without(t) for t in TOOLS if t.__name__ in exposed],
        name="penlike",
        instructions=INSTRUCTIONS,
    )


def main() -> None:  # pragma: no cover - a blocking server loop
    """Serve over stdio. The ``penlike-mcp`` console script."""
    try:
        server = mk_server()
    except ImportError as error:
        raise SystemExit("penlike-mcp needs the mcp extra: pip install 'penlike[mcp]'") from error
    server.run()


if __name__ == "__main__":  # pragma: no cover
    main()
