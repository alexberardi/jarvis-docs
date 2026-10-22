"""CLAUDE.md's Verify section must stay runnable on the dev box and in the loop (#463, reopens #290).

The proof command of a merged docs PR started with `python3.11 -m venv .venv`. On the dev
box every Python shim (`python`, `python3`, `python3.11`, `pip`, `mkdocs`) is a mise shim
with no version set, so the command exited 1 in 0 s before any docs step ran. The loop
runner creates `.venv` itself, so verify and proof commands must start with `.venv/bin/...`
and never create the venv; `python3.11 -m venv .venv` is for use outside the loop only.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def verify_section():
    text = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    start = text.index("## Verify")
    end = text.index("\n## ", start + 1)
    return text[start:end]


def _bash_blocks(section):
    return re.findall(r"```(?:bash)?\n(.*?)```", section, re.S)


def _proof_block(section):
    blocks = _bash_blocks(section)
    # The proof command is the single-line, `&&`-joined block.
    proofs = [b for b in blocks if "&&" in b and "pytest" in b]
    assert len(proofs) == 1, "expected exactly one verify/proof command block"
    return proofs[0]


def test_proof_command_never_creates_the_venv(verify_section):
    cmd = _proof_block(verify_section)
    assert "-m venv" not in cmd
    assert "python3.11" not in cmd
    assert cmd.startswith(".venv/bin/python -m pip install -q -r requirements.txt -r requirements-dev.txt")
    assert ".venv/bin/mkdocs build --strict" in cmd
    assert ".venv/bin/python -m pytest" in cmd


def test_no_claim_that_only_python311_resolves(verify_section):
    # The old, false claim: `python3.11` was the only shim that worked.
    assert "Only `python3.11` resolves" not in verify_section


def test_says_every_shim_can_fail(verify_section):
    # All the shims can fail, not just the bare ones: `python3.11` must be named
    # among the failing shims, not as the one that works.
    assert "`python3.11`" in verify_section
    assert "mise ERROR" in verify_section


def test_venv_creation_is_labelled_out_of_loop(verify_section):
    lines = verify_section.splitlines()
    for i, line in enumerate(lines):
        if "python3.11 -m venv" in line:
            context = "\n".join(lines[max(0, i - 6):i + 1]).lower()
            assert "outside the loop" in context or "laptop" in context or "ci" in context, (
                "the venv-creation line must be labelled for use outside the loop (a laptop or CI)"
            )


def test_says_the_runner_creates_the_venv(verify_section):
    assert "creates `.venv`" in verify_section


def test_keeps_the_no_mise_toml_warning(verify_section):
    assert "Do not add a `mise.toml`" in verify_section
