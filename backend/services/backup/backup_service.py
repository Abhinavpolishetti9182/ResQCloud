import os
import shutil
import tempfile
import uuid

from datetime import datetime, timezone
from pathlib import Path

import boto3

from .backup_verifier import calculate_sha256


class BackupService:

    def __init__(self):
        self.region = (
            os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
            or "ap-south-2"
        )

        self.bucket_name = (
            os.getenv("S3_BACKUP_BUCKET")
            or os.getenv("RESQCLOUD_BACKUP_BUCKET")
        )

        self.s3 = boto3.client(
            "s3",
            region_name=self.region
        )

    def _validate_bucket(self):
        if not self.bucket_name:
            raise ValueError(
                "S3_BACKUP_BUCKET or RESQCLOUD_BACKUP_BUCKET "
                "is not configured."
            )

    def create_backup(self, source_file: str) -> dict:

        self._validate_bucket()

        source = Path(source_file)

        if not source.exists():
            raise FileNotFoundError(
                f"Source file does not exist: {source_file}"
            )

        if not source.is_file():
            raise ValueError(
                f"Source path is not a file: {source_file}"
            )

        backup_id = str(uuid.uuid4())

        timestamp = datetime.now(
            timezone.utc
        ).strftime("%Y%m%dT%H%M%SZ")

        object_key = (
            f"resqcloud-backups/"
            f"{timestamp}/"
            f"{backup_id}-{source.name}"
        )

        checksum = calculate_sha256(
            str(source)
        )

        file_size = source.stat().st_size

        self.s3.upload_file(
            str(source),
            self.bucket_name,
            object_key,
            ExtraArgs={
                "ServerSideEncryption": "AES256",
                "Metadata": {
                    "backup-id": backup_id,
                    "checksum-sha256": checksum,
                    "created-at": timestamp,
                    "original-filename": source.name
                }
            }
        )

        return {
            "backup_id": backup_id,
            "source": str(source),
            "bucket": self.bucket_name,
            "object_key": object_key,
            "checksum": checksum,
            "size_bytes": file_size,
            "created_at": timestamp,
            "status": "uploaded"
        }

    def verify_s3_backup(
        self,
        object_key: str,
        expected_checksum: str
    ) -> dict:

        self._validate_bucket()

        response = self.s3.head_object(
            Bucket=self.bucket_name,
            Key=object_key
        )

        metadata = response.get(
            "Metadata",
            {}
        )

        stored_checksum = metadata.get(
            "checksum-sha256"
        )

        if not stored_checksum:

            return {
                "verified": False,
                "message": (
                    "Checksum metadata is missing "
                    "from the S3 object."
                )
            }

        if stored_checksum != expected_checksum:

            return {
                "verified": False,
                "message": (
                    "Stored checksum does not match "
                    "the expected checksum."
                ),
                "stored_checksum": stored_checksum,
                "expected_checksum": expected_checksum
            }

        return {
            "verified": True,
            "message": (
                "S3 object exists and checksum "
                "metadata matches."
            ),
            "bucket": self.bucket_name,
            "object_key": object_key,
            "size_bytes": response.get(
                "ContentLength"
            ),
            "checksum": stored_checksum
        }

    def verify_s3_backup_integrity(
        self,
        object_key: str,
        expected_checksum: str
    ) -> dict:

        self._validate_bucket()

        with tempfile.TemporaryDirectory() as temp_dir:

            downloaded_file = (
                Path(temp_dir) /
                "downloaded_backup"
            )

            self.s3.download_file(
                self.bucket_name,
                object_key,
                str(downloaded_file)
            )

            actual_checksum = calculate_sha256(
                str(downloaded_file)
            )

        verified = (
            actual_checksum ==
            expected_checksum
        )

        return {
            "verified": verified,
            "bucket": self.bucket_name,
            "object_key": object_key,
            "expected_checksum": expected_checksum,
            "actual_checksum": actual_checksum,
            "message": (
                "Backup integrity verified successfully."
                if verified
                else
                "Backup integrity check failed: "
                "checksums do not match."
            )
        }

    def restore_s3_backup(
        self,
        object_key: str,
        expected_checksum: str,
        destination_path: str
    ) -> dict:

        self._validate_bucket()

        if not object_key.startswith(
            "resqcloud-backups/"
        ):
            raise ValueError(
                "Invalid backup object key."
            )

        destination = Path(
            destination_path
        )

        if destination.exists():
            raise FileExistsError(
                f"Destination already exists: "
                f"{destination}"
            )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with tempfile.TemporaryDirectory() as temp_dir:

            temporary_file = (
                Path(temp_dir) /
                "restore_source"
            )

            self.s3.download_file(
                self.bucket_name,
                object_key,
                str(temporary_file)
            )

            actual_checksum = calculate_sha256(
                str(temporary_file)
            )

            if actual_checksum != expected_checksum:

                raise ValueError(
                    "Restore stopped because backup "
                    "integrity verification failed."
                )

            shutil.copy2(
                temporary_file,
                destination
            )

        return {
            "restored": True,
            "bucket": self.bucket_name,
            "object_key": object_key,
            "destination": str(destination),
            "checksum": actual_checksum,
            "message": (
                "Backup restored successfully."
            )
        }