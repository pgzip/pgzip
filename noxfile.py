import os
import shutil
from pathlib import Path

import nox

DIR = Path(__file__).parent.resolve()


if os.environ.get("CI", None):
    nox.options.error_on_missing_interpreters = True


# -----------------------------------------------------------------------------
# Development Commands
# -----------------------------------------------------------------------------
@nox.session(
    python=[
        "3.7",
        "3.8",
        "3.9",
        "3.10",
        "3.11",
        "3.12",
    ]
)
def test(session: nox.Session) -> None:
    session.install(".")
    session.run("pytest")


@nox.session
def lint(session: nox.Session) -> None:
    """
    Run the linter.
    """
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session
def build(session: nox.Session) -> None:
    """
    Build an SDist and wheel.
    """

    build_p = DIR.joinpath("build")
    if build_p.exists():
        shutil.rmtree(build_p)

    dist_p = DIR.joinpath("dist")
    if dist_p.exists():
        shutil.rmtree(dist_p)

    session.install("build")
    session.run("python", "-m", "build")
