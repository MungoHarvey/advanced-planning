# -*- coding: utf-8 -*-
"""Shell scripts must be committed with LF endings. This is executable, not advisory.

The repository itself is clean: 0 of 257 tracked blobs contain CRLF. The
working tree on a Windows machine is the opposite -- 231 of them do -- and with
core.autocrlf=false and no attributes, git committed whatever bytes it was
handed. So the exposure is not what is stored, it is what the next commit from
such a working tree would store. For prose, JSON and Python that is harmless.
For a POSIX shell script it is not:

  * The kernel reads the shebang line literally, so ``#!/bin/sh\\r`` asks for an
    interpreter named ``/bin/sh<CR>``, and direct execution fails with "bad
    interpreter: No such file or directory".
  * Where the script is invoked as ``sh script.sh`` instead, the shebang is
    bypassed and the failure moves inward: every line ends in a carriage return,
    so quoted values silently gain one and ``$'\\r': command not found`` appears
    at unpredictable places.

This is not hypothetical. Two of the four tracked shell scripts were sitting in
this working tree with ``#!/bin/sh\\r`` shebangs -- committed correctly, then
converted locally -- and were one ``git add`` away from entering the repository
that way. Separately, the session that wrote the shared-runtime fix had its
editing tools convert LF to CRLF in eleven files, three of them ``#!/bin/sh``
installers; that was caught by an implausible diff stat rather than by anything
in the repository, because there was nothing in the repository to catch it.

``.gitattributes`` now normalises on commit, which is the prevention half and
costs no churn because the stored blobs are already LF. This test is the
detection half, and it is not redundant: it fails on what is in the *working
tree*, which is what actually gets executed locally, and which git's attributes
say nothing about until something is staged.
"""

import os
import subprocess
import sys
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _tracked(pattern):
    out = subprocess.check_output(
        ["git", "ls-files", "-z", pattern], cwd=str(_REPO_ROOT))
    names = out.decode("utf-8").split("\0")
    return [n for n in names if n and (_REPO_ROOT / n).is_file()]


def _shell_scripts():
    scripts = _tracked("*.sh")
    assert scripts, (
        "no tracked *.sh files found -- this test has silently stopped "
        "covering anything, which is worse than failing")
    return scripts


@pytest.mark.parametrize("rel", _shell_scripts())
def test_a_shell_script_has_no_carriage_returns(rel):
    with open(str(_REPO_ROOT / rel), "rb") as handle:
        data = handle.read()
    assert b"\r" not in data, (
        "%s contains carriage returns. A POSIX shell script with CRLF endings "
        "fails in two different ways depending on how it is invoked, and "
        "neither error names the line ending as the cause. Strip them: "
        "sed -i 's/\\r$//' %s" % (rel, rel))


@pytest.mark.parametrize("rel", _shell_scripts())
def test_a_shell_script_shebang_names_a_real_interpreter(rel):
    """The specific failure: the kernel does not strip the carriage return."""
    with open(str(_REPO_ROOT / rel), "rb") as handle:
        first = handle.readline()
    if not first.startswith(b"#!"):
        pytest.skip("%s has no shebang" % rel)
    interpreter = first[2:].strip(b"\n").split(b" ")[0]
    assert not interpreter.endswith(b"\r"), (
        "%s asks for the interpreter %r. The trailing carriage return is part "
        "of the path as far as execve is concerned, so this script cannot be "
        "run directly on any POSIX system -- it fails with 'bad interpreter: "
        "No such file or directory', which names neither the carriage return "
        "nor the file that carries it." % (rel, interpreter))


def test_gitattributes_pins_the_shell_scripts():
    """The prevention half. Without it, the next CRLF write commits verbatim.

    ``core.autocrlf`` is false in this repository and there was no
    ``.gitattributes`` at all, so git had no opinion about line endings and
    committed whatever a tool happened to write.
    """
    path = _REPO_ROOT / ".gitattributes"
    assert path.exists(), (
        "no .gitattributes. With core.autocrlf=false and no attributes, git "
        "commits whatever line endings a tool wrote, which is how two shell "
        "scripts came to have CRLF shebangs.")
    with open(str(path), encoding="utf-8") as handle:
        text = handle.read()
    assert "*.sh" in text and "eol=lf" in text, (
        ".gitattributes does not pin *.sh to eol=lf, which is the one rule "
        "in it that is load-bearing rather than tidy.")
