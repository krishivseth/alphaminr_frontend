import os
import requests
import base64
import json
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = "krishivseth/Alphaminr" # Replace if your repo name is different
BASE_URL = f"https://api.github.com/repos/{REPO_NAME}"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_file_sha(path):
    """Get the SHA of a file to update it."""
    try:
        response = requests.get(f"{BASE_URL}/contents/{path}", headers=HEADERS)
        response.raise_for_status()
        return response.json()["sha"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None # File doesn't exist yet
        raise

def commit_file(file_path, file_content, commit_message):
    """Commits a file to the GitHub repository."""
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN not configured. Cannot commit to repo.")
        # In a real app, you'd return an error to the user
        return {"error": "Server is not configured to save files."}

    # Encode content to base64
    content_b64 = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")

    # Get the current SHA of the file, if it exists
    sha = get_file_sha(file_path)

    data = {
        "message": commit_message,
        "content": content_b64,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha # Add SHA if updating an existing file

    response = requests.put(
        f"{BASE_URL}/contents/{file_path}",
        headers=HEADERS,
        data=json.dumps(data)
    )

    if response.status_code in [200, 201]:
        return {"success": True, "commit_sha": response.json()["commit"]["sha"]}
    else:
        return {"error": response.json().get("message", "Unknown error")}