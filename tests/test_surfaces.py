"""The surfaces are built from one list of verbs, and the core imports none of them."""

import json
import os
import subprocess
import sys

import pytest

from penlike import tools


def _run(*args, data_dir, stdin=None):
    return subprocess.run(
        [sys.executable, "-m", "penlike", *args],
        input=stdin,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PENLIKE_DATA_DIR": str(data_dir),
            "PYTHONPATH": os.pathsep.join(p for p in sys.path if p),
            "PYTHONIOENCODING": "utf-8",
        },
    )


def test_the_one_command_path(tmp_path):
    """v1 in one line: new, gather, build, brief, check, all from the command line."""
    from tests.corpus import fictional_corpus

    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text("\n".join(json.dumps(d) for d in fictional_corpus()))
    data = tmp_path / "data"
    assert _run("new", "quinn", data_dir=data).returncode == 0
    assert "added 42" in _run("gather", "quinn", "jsonl", str(corpus), data_dir=data).stdout
    assert _run("build", "quinn", data_dir=data).returncode == 0
    brief = _run("brief", "--like", "quinn", "--channel", "github", "--reply", data_dir=data)
    assert "register github.reply" in brief.stdout
    draft = "Dear Sir,\n\nIt is with considerable regret that I must inform you.\n\nRegards,\nQ"
    check = _run("check", "-", "--style", "email.one", "--json", data_dir=data, stdin=draft)
    assert check.returncode == 1 and json.loads(check.stdout)["discrepancies"]
    assert (data / "models" / "quinn" / "docs.jsonl").is_file()


def test_errors_say_what_to_do(tmp_path):
    result = _run("build", "nobody", data_dir=tmp_path)
    assert result.returncode != 0 and "penlike new nobody" in result.stderr


def test_importing_the_package_loads_no_surface_library():
    code = (
        "import sys, penlike; "
        "bad = [m for m in ('cw', 'py2mcp', 'fastmcp', 'ductus', 'correspond', 'torch') "
        "if m in sys.modules]; print(bad)"
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert done.stdout.strip() == "[]", done.stderr


def test_every_verb_has_a_docstring_a_stranger_could_use():
    for verb in tools.TOOLS:
        assert verb.__doc__ and len(verb.__doc__.strip().split("\n")[0]) >= 15, verb.__name__


def test_mcp_exposes_the_same_verbs_without_host_reach():
    pytest.importorskip("py2mcp")
    from penlike import mcp

    names = mcp.tool_names()
    assert "brief" in names and "check" in names
    assert not {"gather", "remove", "batches", "install_skills"} & set(names)
    assert mcp.mk_server() is not None


def test_shipped_skills_are_well_formed():
    import re
    from importlib.resources import files
    from pathlib import Path

    root = Path(str(files("penlike.data"))) / "skills"
    skills = sorted(p for p in root.iterdir() if (p / "SKILL.md").is_file() and p.name != "x")
    assert {p.name for p in skills} >= {"penlike", "penlike-model", "penlike-source"}
    verbs = {t.__name__.replace("_", "-") for t in tools.TOOLS}
    for skill in skills:
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        front = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL).group(1)
        name = re.search(r"^name: (.+)$", front, re.MULTILINE).group(1).strip()
        description = re.search(r"^description: (.+)$", front, re.MULTILINE).group(1)
        assert name == skill.name and len(description) <= 1024
        assert len(text.splitlines()) < 500
        # Every command a skill tells an agent to run is a verb that exists.
        blocks = re.findall(r"```bash\n(.*?)```", text, re.DOTALL)
        for used in re.findall(r"^penlike ([a-z-]+)", "\n".join(blocks), re.MULTILINE):
            assert used in verbs, f"{skill.name} names an unknown verb: {used}"
