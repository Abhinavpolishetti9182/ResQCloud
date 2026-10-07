from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class InfrastructureResource(db.Model):
    __tablename__ = "infrastructure_resources"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    resource_type = db.Column(
        db.String(50),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False
    )

    environment = db.Column(
        db.String(30),
        default="development"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Backup(db.Model):
    __tablename__ = "backups"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    storage_location = db.Column(
        db.String(255),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False
    )

    backup_type = db.Column(
        db.String(30),
        default="manual"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    severity = db.Column(
        db.String(30),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class RecoveryRequest(db.Model):
    __tablename__ = "recovery_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    resource_name = db.Column(
        db.String(100),
        nullable=False
    )

    recovery_type = db.Column(
        db.String(50),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    reason = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class BackupVerification(db.Model):
    """Persistent record of a backup integrity verification attempt."""

    __tablename__ = "backup_verifications"

    id = db.Column(db.Integer, primary_key=True)

    object_key = db.Column(
        db.String(1024),
        nullable=False,
        index=True
    )

    expected_checksum = db.Column(
        db.String(64),
        nullable=False
    )

    actual_checksum = db.Column(
        db.String(64),
        nullable=True
    )

    verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    message = db.Column(
        db.Text,
        nullable=True
    )

    verified_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp()
    )

class BackupArtifact(db.Model):
    """Stores the trusted metadata for an uploaded S3 backup."""

    __tablename__ = "backup_artifacts"

    id = db.Column(db.Integer, primary_key=True)
    backup_id = db.Column(db.Integer, nullable=False, index=True)
    bucket = db.Column(db.String(255), nullable=False)
    object_key = db.Column(db.String(1024), nullable=False, unique=True)
    checksum = db.Column(db.String(64), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="uploaded")
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp()
    )