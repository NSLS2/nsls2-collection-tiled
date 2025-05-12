import datetime
import json
import os
import pprint
import sys
import argparse
from pathlib import Path

import requests


# BASE_URL = "https://sandbox.zenodo.org/api"
BASE_URL = "https://zenodo.org/api"


def print_now(*args):
    print(*args, file=sys.stdout, flush=True)


def upload_files(bucket_url, files, token):
    if files is None:
        raise ValueError(
            "Files cannot be None, specify a dict with file names "
            "as keys and access mode as values"
        )

    ret_declare = requests.post(
        bucket_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        data=json.dumps([{"key": os.path.basename(file)} for file in files]),
    )
    print_now(ret_declare.status_code, ret_declare.text)

    for file, mode in files.items():
        print_now(f"Uploading {file}...")

        basename = os.path.basename(file)

        ret_content = requests.put(
            f"{bucket_url}/{basename}/content",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/octet-stream",
                "Authorization": f"Bearer {token}",
            },
            data=open(file, mode),
        )
        print_now(ret_content.status_code, ret_content.text)

        ret_commit = requests.post(
            f"{bucket_url}/{basename}/commit",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        print_now(ret_commit.status_code, ret_commit.text)


def create_new_version(conceptrecid=None, version=None, extra_files=None, token=None):
    rec = requests.get(
        f"{BASE_URL}/records/{conceptrecid}/versions/latest",
        headers={"Authorization": f"Bearer {token}"},
    )

    ret_newver = requests.post(
        f"{BASE_URL}/records/{rec.json()['id']}/versions",
        params={"access_token": token},
    )
    print_now(ret_newver.url, ret_newver.status_code, ret_newver.json())

    newver_draft = ret_newver.json()["links"]["self"]

    notes_urls = [
        f"https://github.com/NSLS2/nsls2-collection-tiled/releases/tag/{version}"
    ]
    notes_urls_strs = "<br>\n".join(
        [f'<a href="{url}">Release notes</a>' if url else "" for url in notes_urls]
    )

    unpack_instructions = """
Unpacking instructions:
<br>
<pre>
mkdir -p ~/conda_envs/&lt;env-name&gt;
cd ~/conda_envs/&lt;env-name&gt;
wget &lt;url-to&gt;/&lt;env-name&gt;.tar.gz
tar -xvf &lt;env-name&gt;.tar.gz
conda activate $PWD
conda-unpack
</pre>
"""
    data = {
        "metadata": {
            "version": version,
            "title": f"NSLS-II collection conda environment {version} with Python 3.10, 3.11, and 3.12",
            "description": f"NSLS-II collection environment deployed to the experimental floor.<br><br>{notes_urls_strs}",
            "resource_type": {"id": "software"},
            "publication_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "publisher": "NSLS-II, Brookhaven National Laboratory",
            "prereserve_doi": True,
            "keywords": [
                "conda",
                "NSLS-II",
                "bluesky",
                "data acquisition",
                "conda-forge",
                "conda-pack",
            ],
            "additional_descriptions": [
                {
                    "description": unpack_instructions,
                    "type": {"id": "notes", "title": {"en": "Unpacking instructions"}},
                },
            ],
            "creators": [
                {
                    "person_or_org": {
                        "name": "Rakitin, Max",
                        "given_name": "Max",
                        "family_name": "Rakitin",
                        "type": "personal",
                        "identifiers": [
                            {
                                "scheme": "orcid",
                                "identifier": "0000-0003-3685-852X",
                            }
                        ],
                    },
                    "affiliations": [
                        {
                            "id": "01q47ea17",
                            "name": "NSLS-II, Brookhaven National Laboratory",
                        }
                    ],
                },
                {
                    "person_or_org": {
                        "name": "Bischof, Garrett",
                        "given_name": "Bischof",
                        "family_name": "Garrett",
                        "type": "personal",
                        "identifiers": [
                            {
                                "scheme": "orcid",
                                "identifier": "0000-0001-9351-274X",
                            }
                        ],
                    },
                    "affiliations": [
                        {
                            "id": "01q47ea17",
                            "name": "NSLS-II, Brookhaven National Laboratory",
                        }
                    ],
                },
                {
                    "person_or_org": {
                        "name": "Aishima, Jun",
                        "given_name": "Jun",
                        "family_name": "Aishima",
                        "type": "personal",
                        "identifiers": [
                            {
                                "scheme": "orcid",
                                "identifier": "0000-0003-4710-2461",
                            }
                        ],
                    },
                    "affiliations": [
                        {
                            "id": "01q47ea17",
                            "name": "NSLS-II, Brookhaven National Laboratory",
                        }
                    ],
                },
            ],
        }
    }

    resp_update = requests.put(
        newver_draft,
        params={"access_token": token},
        headers={"Content-Type": "application/json"},
        data=json.dumps(data),
    )
    print_now(newver_draft, resp_update.status_code, resp_update.text)

    for file in resp_update.json()["files"]:
        self_file = file["links"]["self"]
        r = requests.delete(self_file, params={"access_token": token})
        print_now(r.status_code, r.text)

    bucket_url = resp_update.json()["links"]["files"]

    all_files = {}
    if extra_files is not None:
        all_files.update(**extra_files)

    upload_files(bucket_url, files=all_files, token=token)

    # ret = requests.post(
    #     resp_update.json()["links"]["publish"], params={"access_token": token}
    # )
    # print_now(ret.status_code, ret.text)
    # return ret.json()


def update_deposition_with_files(conceptrecid=None, files=None, token=None):
    headers = {"Authorization": f"Bearer {token}"}

    rec = requests.get(
        f"{BASE_URL}/records/{conceptrecid}",
        headers=headers,
    )
    latest_published_id = rec.json()["id"]

    deposition = requests.get(
        f"{BASE_URL}/deposit/depositions/{latest_published_id}",
        headers=headers,
    )

    latest_draft_url = deposition.json()["links"]["latest_draft"]
    latest_draft = requests.get(
        latest_draft_url,
        headers=headers,
    )

    bucket_url = latest_draft.json()["links"]["bucket"]

    upload_files(bucket_url, files=files, token=token)


def get_files_from_artifacts(artifacts_dir):
    """Get all files from the artifacts directory and prepare them for upload."""
    files = {}
    artifacts_path = Path(artifacts_dir)

    print(f"Looking for files in: {artifacts_path.absolute()}")
    if not artifacts_path.exists():
        print(f"ERROR: Directory {artifacts_path} does not exist!")
        return files

    print("Directory contents:")
    for item in artifacts_path.iterdir():
        print(f"  - {item.name} ({'file' if item.is_file() else 'directory'})")

    # Find all files in the artifacts directory
    for file_path in artifacts_path.glob("*"):
        if file_path.is_file():
            # Determine the access mode based on file extension
            if file_path.suffix == ".gz":
                mode = "rb"
            else:
                mode = "r"
            files[str(file_path)] = mode

    return files


def main():
    parser = argparse.ArgumentParser(description="Upload files to Zenodo")
    parser.add_argument(
        "--conceptrecid", required=True, help="Zenodo concept record ID"
    )
    parser.add_argument(
        "--version", required=True, help="Version string for the upload"
    )
    parser.add_argument(
        "--artifacts-dir",
        required=True,
        help="Directory containing the files to upload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making any HTTP requests",
    )

    args = parser.parse_args()

    # Get token from environment
    token = os.environ.get("ZENODO_TOKEN", "")

    # Ensure token is not empty during non-dry-run executions
    if not token and not args.dry_run:
        print_now("Error: ZENODO_TOKEN environment variable is not set or is empty.")
        sys.exit(1)

    # Get files from artifacts directory
    files = get_files_from_artifacts(args.artifacts_dir)

    if args.dry_run:
        print("DRY RUN: Would upload the following files:")
        for file in files:
            print(f"  - {file}")
        print(f"  - Version: {args.version}")
        print(f"  - Concept record ID: {args.conceptrecid}")
        return

    # Create new version and upload files
    resp = create_new_version(
        conceptrecid=args.conceptrecid,
        version=args.version,
        token=token,
        extra_files=files,
    )
    pprint.pprint(resp)


if __name__ == "__main__":
    main()
