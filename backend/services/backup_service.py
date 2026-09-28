import hashlib
import os
from datetime import datetime, timezone

import boto3


class BackupService:
    def __init__(self, bucket_name, region=None):
        self.bucket_name = bucket_name

        self.s3 = boto3.client(
            "s3",
            region_name=region
        )

    @staticmethod
    def calculate_sha256(file_path):
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def upload_backup(self, file_path):

        if not os.path.exists(file_path):
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
            f"backups/"
            f"{timestamp.strftime('%Y/%m/%d')}/"
            f"{backup_id}-{file_name}"
        )

        self.s3.upload_file(
            file_path,
            self.bucket_name,
            s3_key,
            ExtraArgs={
                "ServerSideEncryption": "AES256"
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