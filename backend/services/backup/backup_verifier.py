import hashlib
from pathlib import Path


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    """

    sha256 = hashlib.sha256()

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Backup file not found: {file_path}"
        )

    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def verify_file(
    file_path: str,
    expected_checksum: str
) -> bool:
    """
    Verify a file against an expected SHA-256 checksum.
    """

    actual_checksum = calculate_sha256(file_path)

    return actual_checksum == expected_checksum