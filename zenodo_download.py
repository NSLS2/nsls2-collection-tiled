import argparse
import os
import re
import requests
import tqdm

BASE_URL = "https://zenodo.org/api"


def download_from_zenodo(
    conceptrecid,
    version=None,
    files_to_download=None,
    exclude_files=None,
    token=None,
    dry_run=False,
):
    """Download files from Zenodo.
    Args:
        conceptrecid (str): Zenodo concept record ID to identify the latest deposition to download from, e.g. 4057062.
        version (str, optional): Version of the deposition to download from (e.g., 2025-2.0). If None, the latest version will be used.
        files_to_download (list, optional): List of file names or regex patterns to download. If None, all files will be downloaded.
        exclude_files (list, optional): List of file names or regex patterns to exclude from download. If None, no files will be excluded.
        token (str): The Zenodo API token for authentication.
        dry_run (bool): If True, only print the files that would be downloaded without actually downloading them.
    """
    if token is None:
        token = ""

    headers = {"Authorization": f"Bearer {token}"}

    concept_rec = requests.get(
        f"{BASE_URL}/records/{conceptrecid}",
        headers=headers,
    )

    versions = requests.get(
        concept_rec.json()["links"]["versions"],
        headers=headers,
    )

    if version is not None:
        # Find the version with the specified version string
        for ver in versions.json()["hits"]["hits"]:
            if ver["metadata"]["version"] == version:
                record_id = ver["id"]
                break
        else:
            raise ValueError(f"Version '{version}' not found in the deposition.")
        rec = requests.get(
            f"{BASE_URL}/records/{record_id}",
            headers=headers,
        )
    else:
        rec = concept_rec
        record_id = rec.json()["id"]  # Latest version

    files = requests.get(
        f"{BASE_URL}/records/{record_id}/files",
        headers=headers,
    )

    files_dict = {file["key"]: file for file in files.json()["entries"]}
    files_names = sorted(files_dict.keys())

    print(f"Zenodo deposition: {record_id}")
    print(f"Title: {rec.json()['title']}")
    print("Files:")
    for file in files_names:
        print(f"  - {file}")

    downloaded = []

    for file_name in files_names:
        entry = files_dict[file_name]
        if files_to_download is not None:
            if not any(re.search(file, file_name) for file in files_to_download):
                print(f"Skipping file: {file_name}")
                continue

        if exclude_files is not None:
            if any(re.search(exclude, file_name) for exclude in exclude_files):
                print(f"Excluding file: {file_name}")
                continue

        if not dry_run:
            with requests.get(entry["links"]["content"], stream=True) as r:
                r.raise_for_status()
                print(f"Downloading file: {file_name}")
                total_size = int(entry.get("size", 0))

                with tqdm.tqdm(
                    total=total_size, unit="B", unit_scale=True
                ) as progress_bar:
                    with open(file_name, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8 * 1024):
                            progress_bar.update(len(chunk))
                            f.write(chunk)
                        downloaded.append(file_name)
        else:
            print(f"Would download file: {file_name}")
            downloaded.append(file_name)

    if not dry_run:
        print(f"\nDownloaded {len(downloaded)} file(s):")
    else:
        print(f"\nWould download {len(downloaded)} file(s):")
    for file in downloaded:
        print(f"  - {file}")


def main():
    parser = argparse.ArgumentParser(description="Download files from Zenodo")
    parser.add_argument(
        "-c",
        "--conceptrecid",
        required=True,
        help="Zenodo concept record ID to identify the latest deposition to download from, e.g. 4057062",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Version of the deposition to download from (e.g., 2025-2.0). If not provided, the latest version will be used",
    )
    parser.add_argument(
        "-f",
        "--files",
        nargs="*",
        help="List of file names or regex patterns to download. If not provided, all files will be downloaded",
    )
    parser.add_argument(
        "-e",
        "--exclude-files",
        nargs="*",
        help="List of file names or regex patterns to exclude from download. If not provided, no files will be excluded",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the files that would be downloaded without actually downloading them",
    )

    args = parser.parse_args()

    # Get token from environment
    token = os.environ.get("ZENODO_TOKEN", "")

    download_from_zenodo(
        conceptrecid=args.conceptrecid,
        version=args.version,
        files_to_download=args.files,
        exclude_files=args.exclude_files,
        token=token,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
