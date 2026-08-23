#!/usr/bin/env python3
"""Update the organization contributor section in the profile README."""

import json
import os
import re
import sys
from collections import defaultdict
from urllib.error import HTTPError
from urllib.request import Request, urlopen


START = "<!-- ORGANIZATION-CONTRIBUTORS:START -->"
END = "<!-- ORGANIZATION-CONTRIBUTORS:END -->"


def fetch_json(url, token):
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "miskatonic-expedition-contributors",
        },
    )
    with urlopen(request) as response:
        return json.load(response)


def fetch_all(api_url, path, token):
    items = []
    page = 1
    while True:
        batch = fetch_json(f"{api_url}{path}&page={page}", token)
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def collect_contributors(api_url, organization, token):
    repositories = fetch_all(
        api_url,
        f"/orgs/{organization}/repos?type=public&per_page=100",
        token,
    )
    totals = defaultdict(lambda: {"contributions": 0})

    for repository in repositories:
        try:
            contributors = fetch_all(
                api_url,
                f"/repos/{organization}/{repository['name']}/contributors"
                "?anon=false&per_page=100",
                token,
            )
        except HTTPError as error:
            print(
                f"Skipping {repository['name']} contributors ({error.code})",
                file=sys.stderr,
            )
            continue

        for contributor in contributors:
            login = contributor.get("login")
            if not login:
                continue
            key = login.lower()
            totals[key]["login"] = login
            totals[key]["html_url"] = contributor.get(
                "html_url", f"https://github.com/{login}"
            )
            totals[key]["avatar_url"] = contributor.get("avatar_url", "")
            totals[key]["contributions"] += contributor.get("contributions", 0)

    return sorted(
        totals.values(),
        key=lambda contributor: (-contributor["contributions"], contributor["login"].lower()),
    )


def render_contributors(contributors):
    contributors = sorted(
        contributors,
        key=lambda contributor: (-contributor["contributions"], contributor["login"].lower()),
    )
    if not contributors:
        body = "_No contributors yet._"
    else:
        avatars = []
        for contributor in contributors:
            login = contributor["login"]
            avatars.append(
                f'<a href="{contributor["html_url"]}" title="@{login}">'
                f'<img src="{contributor["avatar_url"]}" width="60" alt="@{login}" />'
                "</a>"
            )
        body = "\n".join(avatars)

    return f"{START}\n{body}\n{END}"


def update_readme(readme_path, contributors):
    readme = readme_path.read_text(encoding="utf-8")
    replacement = render_contributors(contributors)
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        flags=re.DOTALL,
    )
    updated, count = pattern.subn(replacement, readme, count=1)
    if count != 1:
        raise ValueError("Contributor markers were not found exactly once")
    readme_path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    from pathlib import Path

    token = os.environ["GITHUB_TOKEN"]
    organization = os.environ.get("GITHUB_ORG", "Miskatonic-Expedition")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    root = Path(__file__).resolve().parents[1]
    contributors = collect_contributors(api_url, organization, token)
    update_readme(root / "profile" / "README.md", contributors)
    print(f"Updated {len(contributors)} organization contributors")
