# penlike.mcp

MCP over stdio: the same verbs, for local MCP clients.

Run `penlike-mcp` after `pip install 'penlike[mcp]'`. There is no second list of
verbs: the tools are [`penlike.tools.TOOLS`](penlike.tools.md#penlike.tools.TOOLS), minus those marked as reaching into
the host (gathering from arbitrary paths, deleting a model, linking skills), which
stay at the terminal. The data root is the server’s: `data_dir` is removed from
every tool’s schema. Point the server elsewhere with `PENLIKE_DATA_DIR`.

```pycon
>>> "brief" in tool_names(), "gather" in tool_names(), "install_skills" in tool_names()
(True, False, False)
```

### Functions

| [`main`](#penlike.mcp.main)()       | Serve over stdio.                                                           |
|---------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`mk_server`](#penlike.mcp.mk_server)()  | A FastMCP server over the exposed verbs (not started).                      |
| [`tool_names`](#penlike.mcp.tool_names)() | The verbs exposed over MCP: all of them but those that reach into the host. |

### penlike.mcp.main()

Serve over stdio. The `penlike-mcp` console script.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### penlike.mcp.mk_server()

A FastMCP server over the exposed verbs (not started).

### penlike.mcp.tool_names()

The verbs exposed over MCP: all of them but those that reach into the host.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
