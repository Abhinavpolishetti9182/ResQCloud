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