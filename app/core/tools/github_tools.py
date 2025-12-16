from __future__ import annotations

import os
from typing import Any, Dict, Literal, Optional

from github import Github
from langchain_core.tools import tool


def _gh() -> Github:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set.")
    return Github(token)


def _owner_default() -> Optional[str]:
    return os.getenv("GITHUB_DEFAULT_OWNER")


def _get_repo_full_name(owner: Optional[str], repo: str) -> str:
    if "/" in repo:
        return repo
    if owner:
        return f"{owner}/{repo}"
    default_owner = _owner_default()
    if default_owner:
        return f"{default_owner}/{repo}"
    raise RuntimeError("owner is required if repo is not in 'owner/name' form.")


def _ok(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": True, **payload}


def _err(msg: str) -> Dict[str, Any]:
    return {"success": False, "error": msg}


@tool
def github_whoami() -> dict:
    """Return authenticated GitHub user's login and id."""
    try:
        g = _gh()
        me = g.get_user()
        return _ok({"login": me.login, "id": me.id})
    except Exception as e:
        return _err(str(e))


@tool
def github_list_repos(
    visibility: Literal["all", "public", "private"] = "all", limit: int = 50
) -> dict:
    """
    List authenticated user's repositories.
    Returns: {success, repos: [{full_name, private, description}]}
    """
    try:
        g = _gh()
        me = g.get_user()
        repos = []
        for r in me.get_repos():
            if visibility == "public" and r.private:
                continue
            if visibility == "private" and not r.private:
                continue
            repos.append(
                {
                    "full_name": r.full_name,
                    "private": bool(r.private),
                    "description": r.description,
                }
            )
            if len(repos) >= max(1, min(limit, 200)):
                break
        return _ok({"repos": repos})
    except Exception as e:
        return _err(str(e))


@tool
def github_create_repo(
    name: str,
    description: str = "",
    private: bool = False,
    auto_init: bool = True,
) -> dict:
    """
    Create a new repository under the authenticated user.
    Returns: {success, repo: {full_name, private, url}}
    """
    try:
        g = _gh()
        me = g.get_user()
        repo = me.create_repo(
            name=name,
            description=description,
            private=private,
            auto_init=auto_init,
        )
        return _ok(
            {
                "repo": {
                    "full_name": repo.full_name,
                    "private": repo.private,
                    "url": repo.html_url,
                }
            }
        )
    except Exception as e:
        return _err(str(e))


@tool
def github_delete_repo(owner: Optional[str], repo: str) -> dict:
    """
    Delete a repository. DESTRUCTIVE.
    Returns: {success, full_name}
    """
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        r.delete()
        return _ok({"full_name": full_name})
    except Exception as e:
        return _err(str(e))


@tool
def github_list_commits(
    owner: Optional[str], repo: str, branch: str = "main", limit: int = 20
) -> dict:
    """
    List commits on a branch.
    Returns: {success, commits:[{sha, date, message, author}]}
    """
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        commits = []
        for c in r.get_commits(sha=branch):
            commits.append(
                {
                    "sha": c.sha,
                    "date": (
                        c.commit.author.date.isoformat()
                        if c.commit and c.commit.author
                        else None
                    ),
                    "message": (
                        c.commit.message.splitlines()[0]
                        if c.commit and c.commit.message
                        else ""
                    ),
                    "author": (
                        c.commit.author.name if c.commit and c.commit.author else None
                    ),
                }
            )
            if len(commits) >= max(1, min(limit, 100)):
                break
        return _ok({"repo": full_name, "branch": branch, "commits": commits})
    except Exception as e:
        return _err(str(e))


@tool
def github_list_branches(owner: Optional[str], repo: str, limit: int = 100) -> dict:
    """List branches. Returns: {success, branches:[{name}]}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        out = []
        for b in r.get_branches():
            out.append({"name": b.name})
            if len(out) >= max(1, min(limit, 300)):
                break
        return _ok({"repo": full_name, "branches": out})
    except Exception as e:
        return _err(str(e))


@tool
def github_create_branch(
    owner: Optional[str], repo: str, new_branch: str, source_branch: str = "main"
) -> dict:
    """
    Create a branch from source_branch.
    Returns: {success, repo, new_branch, source_branch, sha}
    """
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        source = r.get_branch(source_branch)
        sha = source.commit.sha
        r.create_git_ref(ref=f"refs/heads/{new_branch}", sha=sha)
        return _ok(
            {
                "repo": full_name,
                "new_branch": new_branch,
                "source_branch": source_branch,
                "sha": sha,
            }
        )
    except Exception as e:
        return _err(str(e))


@tool
def github_delete_branch(owner: Optional[str], repo: str, branch: str) -> dict:
    """Delete a branch. DESTRUCTIVE. Returns: {success, repo, branch}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        r.get_git_ref(f"heads/{branch}").delete()
        return _ok({"repo": full_name, "branch": branch})
    except Exception as e:
        return _err(str(e))


@tool
def github_create_file(
    owner: Optional[str],
    repo: str,
    path: str,
    message: str,
    content: str,
    branch: str = "main",
) -> dict:
    """Create a file. Returns: {success, repo, path, branch, commit_sha}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        res = r.create_file(path, message, content, branch=branch)
        return _ok(
            {
                "repo": full_name,
                "path": path,
                "branch": branch,
                "commit_sha": res["commit"].sha,
            }
        )
    except Exception as e:
        return _err(str(e))


@tool
def github_update_file(
    owner: Optional[str],
    repo: str,
    path: str,
    message: str,
    content: str,
    branch: str = "main",
) -> dict:
    """Update a file. Returns: {success, repo, path, branch, commit_sha}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        f = r.get_contents(path, ref=branch)
        res = r.update_file(f.path, message, content, f.sha, branch=branch)
        return _ok(
            {
                "repo": full_name,
                "path": path,
                "branch": branch,
                "commit_sha": res["commit"].sha,
            }
        )
    except Exception as e:
        return _err(str(e))


@tool
def github_delete_file(
    owner: Optional[str],
    repo: str,
    path: str,
    message: str,
    branch: str = "main",
) -> dict:
    """Delete a file. DESTRUCTIVE. Returns: {success, repo, path, branch, commit_sha}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        f = r.get_contents(path, ref=branch)
        res = r.delete_file(f.path, message, f.sha, branch=branch)
        return _ok(
            {
                "repo": full_name,
                "path": path,
                "branch": branch,
                "commit_sha": res["commit"].sha,
            }
        )
    except Exception as e:
        return _err(str(e))


@tool
def github_list_issues(
    owner: Optional[str],
    repo: str,
    state: Literal["open", "closed", "all"] = "open",
    limit: int = 20,
) -> dict:
    """List issues. Returns: {success, repo, issues:[{number,title,state,url}]}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        out = []
        for i in r.get_issues(state=state):
            out.append(
                {
                    "number": i.number,
                    "title": i.title,
                    "state": i.state,
                    "url": i.html_url,
                }
            )
            if len(out) >= max(1, min(limit, 200)):
                break
        return _ok({"repo": full_name, "issues": out})
    except Exception as e:
        return _err(str(e))


@tool
def github_create_issue(
    owner: Optional[str], repo: str, title: str, body: str = ""
) -> dict:
    """Create issue. Returns: {success, repo, issue:{number,title,url}}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        issue = r.create_issue(title=title, body=body)
        return _ok(
            {
                "repo": full_name,
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.html_url,
                },
            }
        )
    except Exception as e:
        return _err(str(e))


@tool
def github_close_issue(owner: Optional[str], repo: str, number: int) -> dict:
    """Close an issue. Returns: {success, repo, number}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        issue = r.get_issue(number=number)
        issue.edit(state="closed")
        return _ok({"repo": full_name, "number": number})
    except Exception as e:
        return _err(str(e))


@tool
def github_list_prs(
    owner: Optional[str],
    repo: str,
    state: Literal["open", "closed", "all"] = "open",
    limit: int = 20,
) -> dict:
    """List pull requests. Returns: {success, repo, prs:[{number,title,state,url,head,base}]}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        out = []
        for pr in r.get_pulls(state=state):
            out.append(
                {
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "url": pr.html_url,
                    "head": pr.head.ref,
                    "base": pr.base.ref,
                }
            )
            if len(out) >= max(1, min(limit, 200)):
                break
        return _ok({"repo": full_name, "prs": out})
    except Exception as e:
        return _err(str(e))


@tool
def github_create_pr(
    owner: Optional[str],
    repo: str,
    title: str,
    body: str,
    head: str,
    base: str = "main",
) -> dict:
    """Create pull request. Returns: {success, repo, pr:{number,title,url}}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        pr = r.create_pull(title=title, body=body, head=head, base=base)
        return _ok(
            {
                "repo": full_name,
                "pr": {"number": pr.number, "title": pr.title, "url": pr.html_url},
            }
        )
    except Exception as e:
        return _err(str(e))


@tool
def github_merge_pr(
    owner: Optional[str], repo: str, number: int, commit_message: str = ""
) -> dict:
    """Merge a PR. DESTRUCTIVE-ish. Returns: {success, repo, number, merged}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        pr = r.get_pull(number)
        res = pr.merge(commit_message=commit_message or None)
        return _ok(
            {
                "repo": full_name,
                "number": number,
                "merged": bool(res.merged),
                "message": res.message,
            }
        )
    except Exception as e:
        return _err(str(e))


@tool
def github_add_collaborator(
    owner: Optional[str],
    repo: str,
    username: str,
    permission: Literal["pull", "triage", "push", "maintain", "admin"] = "push",
) -> dict:
    """Add collaborator. Returns: {success, repo, username, permission}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        r.add_to_collaborators(username, permission=permission)
        return _ok({"repo": full_name, "username": username, "permission": permission})
    except Exception as e:
        return _err(str(e))


@tool
def github_remove_collaborator(owner: Optional[str], repo: str, username: str) -> dict:
    """Remove collaborator. Returns: {success, repo, username}"""
    try:
        g = _gh()
        full_name = _get_repo_full_name(owner, repo)
        r = g.get_repo(full_name)
        r.remove_from_collaborators(username)
        return _ok({"repo": full_name, "username": username})
    except Exception as e:
        return _err(str(e))


@tool
def github_search_repositories(query: str, limit: int = 10) -> dict:
    """Search repositories. Returns: {success, repos:[{full_name, stars, url}]}"""
    try:
        g = _gh()
        out = []
        for r in g.search_repositories(query):
            out.append(
                {
                    "full_name": r.full_name,
                    "stars": r.stargazers_count,
                    "url": r.html_url,
                }
            )
            if len(out) >= max(1, min(limit, 50)):
                break
        return _ok({"query": query, "repos": out})
    except Exception as e:
        return _err(str(e))


@tool
def github_search_issues(query: str, limit: int = 10) -> dict:
    """Search issues/PRs. Returns: {success, items:[{title, url, repo, number}]}"""
    try:
        g = _gh()
        out = []
        for i in g.search_issues(query):
            repo_full = i.repository.full_name if i.repository else None
            out.append(
                {
                    "title": i.title,
                    "url": i.html_url,
                    "repo": repo_full,
                    "number": i.number,
                }
            )
            if len(out) >= max(1, min(limit, 50)):
                break
        return _ok({"query": query, "items": out})
    except Exception as e:
        return _err(str(e))


@tool
def github_rate_limit() -> dict:
    """Return current rate limit info. Returns: {success, core:{remaining,limit,reset}}"""
    try:
        g = _gh()
        rate = g.get_rate_limit()
        core = rate.core
        return _ok(
            {
                "core": {
                    "remaining": core.remaining,
                    "limit": core.limit,
                    "reset": core.reset.isoformat() if core.reset else None,
                }
            }
        )
    except Exception as e:
        return _err(str(e))


github_tools = [
    github_whoami,
    github_list_repos,
    github_create_repo,
    github_delete_repo,
    github_list_commits,
    github_list_branches,
    github_create_branch,
    github_delete_branch,
    github_create_file,
    github_update_file,
    github_delete_file,
    github_list_issues,
    github_create_issue,
    github_close_issue,
    github_list_prs,
    github_create_pr,
    github_merge_pr,
    github_add_collaborator,
    github_remove_collaborator,
    github_search_repositories,
    github_search_issues,
    github_rate_limit,
]
