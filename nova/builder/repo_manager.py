"""Repository management utilities for Nova's builder agent."""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List

LOGGER = logging.getLogger("nova.builder.repo")


@dataclass(slots=True)
class BranchSummary:
    """Summary information about a git branch."""

    name: str
    head: str | None = None
    ahead: int | None = None
    behind: int | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "head": self.head,
            "ahead": self.ahead,
            "behind": self.behind,
        }


@dataclass(slots=True)
class CommitSummary:
    """Short description of a commit entry."""

    sha: str
    author: str
    relative_time: str
    title: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "sha": self.sha,
            "author": self.author,
            "relative_time": self.relative_time,
            "title": self.title,
        }


@dataclass(slots=True)
class RepositorySnapshot:
    """Represents the state of a repository at a point in time."""

    path: Path
    repository: str
    root: Path
    current_branch: str | None
    default_branch: str | None
    latest_commit: str | None
    status: List[str] = field(default_factory=list)
    branches: List[BranchSummary] = field(default_factory=list)
    commits: List[CommitSummary] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository": self.repository,
            "path": str(self.path),
            "root": str(self.root),
            "current_branch": self.current_branch,
            "default_branch": self.default_branch,
            "latest_commit": self.latest_commit,
            "status": list(self.status),
            "branches": [branch.to_dict() for branch in self.branches],
            "commits": [commit.to_dict() for commit in self.commits],
        }


class RepoManager:
    """Wrapper around git that extracts repository insights for Nova."""

    def __init__(
        self,
        *,
        workspace: str | Path = ".",
        git_command: str = "git",
        report_dir: str | Path | None = None,
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.git_command = git_command
        self.report_dir = Path(report_dir) if report_dir else Path("nova/output/reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def scan(
        self,
        repository: str | Path,
        *,
        include_branches: bool = True,
        include_commits: bool = True,
    ) -> RepositorySnapshot:
        """Inspect a git repository and return a structured snapshot."""

        path = self._resolve_repository(repository)
        root = Path(self._run_git(["rev-parse", "--show-toplevel"], cwd=path)).resolve()
        current_branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path, check=False)
        default_branch = self._run_git(["symbolic-ref", "refs/remotes/origin/HEAD"], cwd=path, check=False)
        latest_commit = self._run_git(["rev-parse", "HEAD"], cwd=path, check=False)
        status = self._run_git(["status", "--short"], cwd=path, check=False)
        snapshot = RepositorySnapshot(
            path=path,
            repository=str(repository),
            root=root,
            current_branch=current_branch or None,
            default_branch=self._parse_default_branch(default_branch),
            latest_commit=latest_commit or None,
            status=[line for line in status.splitlines() if line],
        )
        if include_branches:
            snapshot.branches = self._read_branches(path)
        if include_commits:
            snapshot.commits = self._read_recent_commits(path)
        LOGGER.info("Scanned repository at %s", path)
        return snapshot

    # ------------------------------------------------------------------
    def write_status_report(self, snapshot: RepositorySnapshot, *, filename: str = "repo_status.json") -> Path:
        """Persist ``snapshot`` as JSON in the report directory."""

        payload = snapshot.to_dict()
        path = self.report_dir / filename
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        LOGGER.debug("Repository status report written to %s", path)
        return path

    # ------------------------------------------------------------------
    def simulate_pull_request(
        self,
        repository: str | Path,
        *,
        title: str = "Builder Sync",
        base: str | None = None,
        head: str | None = None,
    ) -> Dict[str, Any]:
        """Generate a minimal pull request summary from the local diff."""

        path = self._resolve_repository(repository)
        diff = self._run_git(["diff", base or "HEAD"], cwd=path, check=False)
        pr_payload = {
            "repository": str(repository),
            "title": title,
            "base": base,
            "head": head,
            "changes_detected": bool(diff.strip()),
            "diff_preview": diff[:5000],
        }
        LOGGER.debug("Generated PR simulation for %s", repository)
        return pr_payload

    # ------------------------------------------------------------------
    def _resolve_repository(self, repository: str | Path) -> Path:
        candidate = Path(repository)
        if candidate.is_dir():
            return candidate.resolve()
        workspace_candidate = self.workspace / repository
        if workspace_candidate.is_dir():
            return workspace_candidate.resolve()
        raise FileNotFoundError(f"Repository '{repository}' not found in workspace {self.workspace}.")

    def _read_branches(self, path: Path) -> List[BranchSummary]:
        output = self._run_git([
            "for-each-ref",
            "--format=%(refname:short)|%(objectname:short)|%(upstream:track)",
            "refs/heads",
        ], cwd=path, check=False)
        branches: List[BranchSummary] = []
        for line in output.splitlines():
            if not line:
                continue
            parts = line.split("|")
            name = parts[0]
            head = parts[1] if len(parts) > 1 and parts[1] else None
            ahead = behind = None
            if len(parts) > 2 and parts[2]:
                ahead, behind = self._parse_tracking(parts[2])
            branches.append(BranchSummary(name=name, head=head, ahead=ahead, behind=behind))
        return branches

    def _read_recent_commits(self, path: Path, *, limit: int = 5) -> List[CommitSummary]:
        output = self._run_git(
            ["log", f"-{limit}", "--pretty=format:%H|%an|%ar|%s"],
            cwd=path,
            check=False,
        )
        commits: List[CommitSummary] = []
        for line in output.splitlines():
            if not line:
                continue
            sha, author, relative_time, title = (line.split("|", 3) + [""] * 4)[:4]
            commits.append(CommitSummary(sha=sha, author=author, relative_time=relative_time, title=title))
        return commits

    def _run_git(
        self,
        args: Iterable[str],
        *,
        cwd: Path,
        check: bool = True,
    ) -> str:
        command = [self.git_command, *args]
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                check=check,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            LOGGER.warning("Git command failed: %s", exc)
            return (exc.stdout or "").strip()
        return (completed.stdout or "").strip()

    @staticmethod
    def _parse_default_branch(ref: str | None) -> str | None:
        if not ref:
            return None
        if ref.startswith("refs/remotes/origin/"):
            return ref.split("/")[-1]
        return ref

    @staticmethod
    def _parse_tracking(tracking: str) -> tuple[int | None, int | None]:
        ahead = behind = None
        tracking = tracking.strip()
        if "ahead" in tracking:
            try:
                ahead = int(tracking.split("ahead ")[1].split(",")[0].strip())
            except (IndexError, ValueError):
                ahead = None
        if "behind" in tracking:
            try:
                behind = int(tracking.split("behind ")[1].split(")")[0].strip())
            except (IndexError, ValueError):
                behind = None
        return ahead, behind


__all__ = [
    "BranchSummary",
    "CommitSummary",
    "RepoManager",
    "RepositorySnapshot",
]
