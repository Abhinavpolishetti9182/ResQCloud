import hashlib
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import boto3


class BackupService:
    def __init__(self, bucket_name=None, region=None):
        # Support explicit configuration and environment variables.
        self.bucket_name = (
            bucket_name
            or os.getenv("S3_BACKUP_BUCKET")
            or os.getenv("RESQCLOUD_BACKUP_BUCKET")
        )

        self.region = (
            region
            or os.getenv("AWS_DEFAULT_REGION")
            or os.getenv("AWS_REGION")
            or "ap-south-2"
        )

        self.s3 = boto3.client(
            "s3",
            region_name=self.region
        )

    @staticmethod
    def calculate_sha256(file_path):
        """
        Calculate the SHA-256 checksum of a file.
        """

        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b""
            ):
                sha256.update(chunk)

        return sha256.hexdigest()

    def upload_backup(self, file_path):
        """
        Upload a local backup file to S3.
        """

        if not self.bucket_name:
            raise ValueError(
                "S3 backup bucket is not configured."
            )

        if not os.path.isfile(file_path):
            raise FileNotFoundError(
                f"Backup source not found: {file_path}"
            )

        checksum = self.calculate_sha256(file_path)

        timestamp = datetime.now(timezone.utc)

        backup_id = timestamp.strftime(
            "bkp-%Y%m%d-%H%M%S"
        )

        file_name = os.path.basename(file_path)

        s3_key = (
            "backups/"
            f"{timestamp.strftime('%Y/%m/%d')}/"
            f"{backup_id}-{file_name}"
        )

        self.s3.upload_file(
            file_path,
            self.bucket_name,
            s3_key,
            ExtraArgs={
                "ServerSideEncryption": "AES256",
                "Metadata": {
                    "checksum-sha256": checksum,
                    "backup-id": backup_id,
                    "created-at": timestamp.strftime(
                        "%Y%m%dT%H%M%SZ"
                    )
                }
            }
        )

        return {
            "backup_id": backup_id,
            "file_name": file_name,
            "s3_key": s3_key,
            "checksum": checksum,
            "status": "UPLOADED",
            "timestamp": timestamp.isoformat()
        }

    def verify_s3_backup_integrity(
        self,
        object_key,
        expected_checksum
    ):
        """
        Download an S3 backup and verify its SHA-256 checksum.
        """

        if not self.bucket_name:
            raise ValueError(
                "S3 backup bucket name is not configured."
            )

        if not isinstance(object_key, str) or not object_key:
            raise ValueError(
                "A valid S3 object key is required."
            )

        if (
            not isinstance(expected_checksum, str)
            or len(expected_checksum) != 64
            or any(
                character not in
                "0123456789abcdefABCDEF"
                for character in expected_checksum
            )
        ):
            raise ValueError(
                "Expected checksum must be a 64-character "
                "SHA-256 hex digest."
            )

        expected_checksum = expected_checksum.lower()

        # Confirm that the object exists
        # and retrieve its metadata.
        head = self.s3.head_object(
            Bucket=self.bucket_name,
            Key=object_key
        )

        metadata = head.get("Metadata", {})

        stored_checksum = metadata.get(
            "checksum-sha256"
        )

        if stored_checksum:
            stored_checksum = stored_checksum.lower()

        # Download the actual S3 object to a temporary file.
        with tempfile.TemporaryDirectory() as temp_dir:
            downloaded_file = os.path.join(
                temp_dir,
                "downloaded_backup"
            )

            self.s3.download_file(
                self.bucket_name,
                object_key,
                downloaded_file
            )

            # Calculate checksum from actual contents.
            actual_checksum = self.calculate_sha256(
                downloaded_file
            )

            size_bytes = os.path.getsize(
                downloaded_file
            )

        verified = (
            actual_checksum == expected_checksum
        )

        metadata_matches = (
            stored_checksum is None
            or stored_checksum == actual_checksum
        )

        if verified and metadata_matches:
            message = (
                "Backup integrity verified successfully."
            )
        elif verified:
            message = (
                "Actual backup contents match the "
                "expected checksum, but stored checksum "
                "metadata is missing or inconsistent."
            )
        else:
            message = (
                "Backup integrity verification failed: "
                "actual file checksum does not match "
                "the expected checksum."
            )

        return {
            "verified": verified,
            "bucket": self.bucket_name,
            "object_key": object_key,
            "expected_checksum": expected_checksum,
            "actual_checksum": actual_checksum,
            "stored_checksum": stored_checksum,
            "metadata_matches": metadata_matches,
            "size_bytes": size_bytes,
            "status": (
                "VERIFIED"
                if verified
                else "FAILED"
            ),
            "message": message,
            "verified_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

    def verify_s3_backup(
        self,
        object_key,
        expected_checksum
    ):
        """
        Compatibility wrapper for existing API calls.
        """

        return self.verify_s3_backup_integrity(
            object_key=object_key,
            expected_checksum=expected_checksum
        )

    def restore_s3_backup(
        self,
        object_key: str,
        expected_checksum: str,
        destination_path: str
    ) -> dict:
        """
        Download an S3 backup only after verifying
        its integrity.
        """

        if not self.bucket_name:
            raise ValueError(
                "S3_BACKUP_BUCKET is not configured"
            )

        if (
            not isinstance(object_key, str)
            or not object_key.startswith(
                "resqcloud-backups/"
            )
        ):
            raise ValueError(
                "Invalid ResQCloud backup object key"
            )

        if (
            not isinstance(expected_checksum, str)
            or len(expected_checksum) != 64
            or any(
                character not in
                "0123456789abcdefABCDEF"
                for character in expected_checksum
            )
        ):
            raise ValueError(
                "Expected checksum must be a 64-character "
                "SHA-256 hex digest."
            )

        expected_checksum = expected_checksum.lower()

        destination = Path(destination_path)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Download the S3 object to a temporary location first.
        with tempfile.TemporaryDirectory() as temp_dir:

            temporary_file = (
                Path(temp_dir) / "backup_download"
            )

            self.s3.download_file(
                self.bucket_name,
                object_key,
                str(temporary_file)
            )

            # Calculate checksum from the downloaded object.
            actual_checksum = self.calculate_sha256(
                str(temporary_file)
            )

            # Never restore a file that fails
            # the integrity check.
            if actual_checksum != expected_checksum:
                return {
                    "restored": False,
                    "verified": False,
                    "message": (
                        "Checksum mismatch. "
                        "Restoration rejected."
                    ),
                    "object_key": object_key,
                    "expected_checksum": (
                        expected_checksum
                    ),
                    "actual_checksum": (
                        actual_checksum
                    )
                }

            # Do not silently overwrite an existing
            # restored file.
            if destination.exists():
                raise FileExistsError(
                    "Restore destination already exists: "
                    f"{destination.name}"
                )

            # Copy only after successful
            # checksum verification.
            with temporary_file.open("rb") as source:
                with destination.open("xb") as target:

                    while True:
                        chunk = source.read(
                            1024 * 1024
                        )

                        if not chunk:
                            break

                        target.write(chunk)

        return {
            "restored": True,
            "verified": True,
            "message": (
                "Backup downloaded, verified, "
                "and restored successfully."
            ),
            "object_key": object_key,
            "restored_filename": destination.name,
            "checksum": actual_checksum,
            "size_bytes": os.path.getsize(
                destination
            )
        }