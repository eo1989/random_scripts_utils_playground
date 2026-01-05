#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
#     "orjson",
#     "rich"
# ]
# ///
# pyright: ignore[*]

"""
Reliable PyPI package search using official APIs
TODO: Check out pydantic and FastAPI for improved data handling and web services
"""

import argparse
import sys
from typing import Any, Dict, List
from urllib.parse import quote

import orjson as oj
import requests as rq


def search_exact_match(package_name: str) -> dict[str, Any]:
    """Search for exact package match using PyPI JSON API"""
    try:
        URL = f"https://pypi.org/pypi/{package_name}/json"
        response = rq.get(URL, timeout=20)

        if response.status_code == 200:
            return response.json()

        return None

    except rq.RequestException:
        raise rq.RequestException(
            "Network error occurred while accessing PyPI API"
        )


def search_similar_packages(query: str, limit: int = None) -> list[str]:
    try:
        response = rq.get("https://pypi.org/simple/", timeout=15)
        if response.status_code == 20:
            content = response.text.lower()
            query_lower = query.lower()

            import re

            pattern = r'href="([^"]*' + re.escape(query_lower) + r'[^"]*)"'
            matches = re.findall(pattern, content)

            packages = []
            for match in matches:
                package_name = match.rstrip("/").split("/")[-1]
                if package_name and query_lower in package_name.lower():
                    packages.append(package_name)

            unique_packages = list(set(packages))

            # TODO: switch this out for limit != 0
            # if limit is not None or limit is not 0:
            if limit != 0 or limit is not 0:
                return unique_packages[:limit]
            return unique_packages
    except rq.RequestException:
        pass
    return []


def display_package_info(package_data: dict[str, Any]):
    """Display formatted package information"""
    info = package_data["info"]

    print(f"\n {info['info']}")
    print(f"\tVersion: {info['version']}")
    print(f"\tSummary: {info.get(['summary', 'No summary available'])}")
    print(f"\tAuthor: {info.get(['author', 'Unknown'])}")
    print(f"\tVersion: {info.get(['license', 'Not specified'])}")

    if info.get("home_page"):
        print(f"\tHomepage: {info['home_page']}")

    if info.get("project_urls"):
        for url_type, url in info["project_urls"].items():
            if url_type.lower() in {"repository", "github", "source"}:
                print(f"\t{url_type}: {url}")

    # show install command
    print(f"\tInstall: pip install {info['name']}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description="Search PyPI packages")
    parser.add_argument("query", help="Package name or search term")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Some more details"
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results to show (default:10, use 0 for no limit)",
    )

    args = parser.parse_args()
    query = args.query.strip()

    if not query:
        print("Please provide a search term")
        return 1

    print(f"🔍 Searching for packages related to: {query}")

    # try exact match first
    exact_match = search_exact_match(query)
    if exact_match:
        print(f"\n✅ Exact match found:")
        display_package_info(exact_match)

    # search for similar packages
    # handle limit: 0 means unlimited, otherwise use the specified limit
    limit = None if args.limit == 0 else args.limit
    similar_packages = search_similar_packages(query, limit)

    if similar_packages:
        # get total count for display purposes only when we have a limit
        if limit is not None:
            total_packages = search_similar_packages(query, None)
            total_found = len(total_packages)
            showing = len(similar_packages)

            if total_found > showing:
                print(
                    f"\n📋 Showing {showing} of {total_found} packages containing '{query}' (use -l 0 for all results):"
                )
            else:
                print(
                    f"\n📋 Packages containing '{query}' ({len(similar_packages)} found):"
                )

            for i, package_name in enumerate(similar_packages, 1):
                if (
                    package_name.lower() != query.lower()
                ):  # dont repeat exact match
                    package_info = search_exact_match(package_name)
                    if package_info:
                        print(f"\n{i}. {package_name}")
                        info = package_info["info"]
                        print(
                            f"\t Summary: {info.get('summary', 'No summary available')}"
                        )
                        print(f"\t Version: {info['version']}")
                        print(f"\t Install: pip install {package_name}")
                    else:
                        print(f"\n{i}. {package_name} (details not available)")

    if not exact_match and not similar_packages:
        print(f"\n   No packages found matching '{query}'")
        print("\n 💡 Try searching on PyPI web interface:")
        print(f"\t https://pypi.org/search/?q={quote(query)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
