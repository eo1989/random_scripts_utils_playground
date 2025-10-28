#!/Users/eo/.local/bin/uv run python3
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
        response = rq.get(URL, timeout=200)
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

            if limit is not None:
                return unique_packages[:limit]
            return unique_packages
    except rq.RequestException:
        pass
    return []


def display_package_info(package_data: dict[str, Any]):
    pass
