import os

import requests as req
from bs4 import BeautifulSoup


def download_github_data(gh_folder_url: str) -> None:
    if "blob" in gh_folder_url:
        raise ValueError("Use a folder (tree) URL, not a blob (file) URL.")
    elif not gh_folder_url.endswith("/"):
        gh_folder_url += "/"

    print(f"Fetching file list from: {gh_folder_url}")
    response = req.get(gh_folder_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch URL: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all data files in the folder
    file_links = soup.select("a.js-navigation-open.Link--primary")

    raw_base = "https://raw.githubusercontent.com"

    user_repo_branch = gh_folder_url.split("github.com/")[1].split("/tree/")
    if len(user_repo_branch) != 2:
        raise ValueError("Invalid Github folder URL format")

    user_repo, branch_path = user_repo_branch
    branch, path = branch_path.split("/", 1)

    for link in file_links:
        file_name = link.get_text(strip=True)
        file_href = link.get("href")

        if not file_href or "/blob/" not in file_href:
            continue  # skip folders or invalid links

        raw_path = file_href.replace("/blob/", "/")
        raw_url = f"{raw_base}/{raw_path}"

        print(f"Downloading {file_name} ...")
        file_data = req.get(raw_url)
        if file_data.status_code == 200:
            with open(file_name, "wb") as f:
                f.write(file_data.content)
        else:
            print(
                f"❌ Failed to download {file_name} ({file_data.status_code})"
            )


if __name__ == "__main__":
    # Example: run this script with the gh folder URL
    github_url = "https://github.com/matheusfacure/python-causaulity-handbook/tree/master/causal-inference-for-the-brave-and-True/data"
    download_github_data(github_url)
