import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from flask import (
    Flask,
    jsonify,
    render_template,
    request
)

from werkzeug.utils import secure_filename

from models import (
    Backup,
    Incident,
    InfrastructureResource,
    RecoveryRequest,
    BackupVerification,
    db,
)

# BackupArtifact is optional for projects whose models.py
# does not define it.
try:
    from models import BackupArtifact
except ImportError:
    BackupArtifact = None

from services.backup.backup_service import BackupService

from services.incident.incident_detector import (
    evaluate_status,
    send_sns_alert,
)

from services.monitoring.cloudwatch_monitor import (
    CloudWatchMonitor
)


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

# Load the single project-level .env file:
# ResQCloud/.env
ENV_FILE = BASE_DIR.parent / ".env"
load_dotenv(dotenv_path=ENV_FILE)

DATABASE_PATH = BASE_DIR / "resqcloud.db"

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{DATABASE_PATH}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MAX_CONTENT_LENGTH"] = (
    26 * 1024 * 1024
)


# Support the bucket variable names used by the project.
if not os.getenv("S3_BACKUP_BUCKET"):
    if os.getenv("BACKUP_BUCKET_NAME"):
        os.environ["S3_BACKUP_BUCKET"] = os.getenv(
            "BACKUP_BUCKET_NAME"
        )
    elif os.getenv("RESQCLOUD_BACKUP_BUCKET"):
        os.environ["S3_BACKUP_BUCKET"] = os.getenv(
            "RESQCLOUD_BACKUP_BUCKET"
        )


RESQCLOUD_MONITORING_TOKEN = os.getenv(
    "RESQCLOUD_MONITORING_TOKEN",
    ""
).strip()


if (
    not os.getenv("AWS_REGION")
    and os.getenv("AWS_DEFAULT_REGION")
):
    os.environ["AWS_REGION"] = (
        os.environ["AWS_DEFAULT_REGION"]
    )


db.init_app(app)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def resource_to_dict(resource):
    return {
        "id": resource.id,
        "name": resource.name,
        "resource_type": resource.resource_type,
        "status": resource.status,
        "environment": resource.environment,
        "created_at": (
            resource.created_at.isoformat()
            if resource.created_at
            else None
        )
    }


def backup_to_dict(backup):
    return {
        "id": backup.id,
        "name": backup.name,
        "storage_location": backup.storage_location,
        "status": backup.status,
        "backup_type": backup.backup_type,
        "created_at": (
            backup.created_at.isoformat()
            if backup.created_at
            else None
        )
    }


def incident_to_dict(incident):
    return {
        "id": incident.id,
        "title": incident.title,
        "severity": incident.severity,
        "status": incident.status,
        "description": incident.description,
        "created_at": (
            incident.created_at.isoformat()
            if incident.created_at
            else None
        )
    }


def recovery_request_to_dict(recovery_request):
    return {
        "id": recovery_request.id,
        "resource_name": recovery_request.resource_name,
        "recovery_type": recovery_request.recovery_type,
        "status": recovery_request.status,
        "reason": recovery_request.reason,
        "created_at": (
            recovery_request.created_at.isoformat()
            if recovery_request.created_at
            else None
        )
    }


# --------------------------------------------------
# FRONTEND ROUTE
# --------------------------------------------------

@app.route("/")
def dashboard():
    return render_template("index.html")


# --------------------------------------------------
# HEALTH CHECK ROUTE
# --------------------------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "ResQCloud Backend"
    })


# --------------------------------------------------
# INFRASTRUCTURE ROUTES
# --------------------------------------------------

@app.route(
    "/api/v1/infrastructure",
    methods=["GET"]
)
def infrastructure_status():

    resources = (
        InfrastructureResource.query
        .order_by(InfrastructureResource.id)
        .all()
    )

    return jsonify({
        "status": "operational",
        "environment": "development",
        "resources": [
            resource_to_dict(resource)
            for resource in resources
        ]
    })


@app.route(
    "/api/v1/infrastructure",
    methods=["POST"]
)
def create_infrastructure_resource():

    data = request.get_json(
        silent=True
    ) or {}

    name = data.get("name")

    resource_type = data.get(
        "resource_type"
    )

    status = data.get("status")

    environment = data.get(
        "environment",
        "development"
    )

    if (
        not name
        or not resource_type
        or not status
    ):
        return jsonify({
            "error": (
                "name, resource_type, "
                "and status are required"
            )
        }), 400

    resource = InfrastructureResource(
        name=name,
        resource_type=resource_type,
        status=status,
        environment=environment
    )

    db.session.add(resource)

    db.session.commit()

    return jsonify({
        "message": (
            "Infrastructure resource "
            "created successfully"
        ),
        "resource": resource_to_dict(
            resource
        )
    }), 201


# --------------------------------------------------
# BACKUP ROUTES
# --------------------------------------------------

@app.route(
    "/api/v1/backups",
    methods=["GET"]
)
def get_backups():

    backups = (
        Backup.query
        .order_by(Backup.id.desc())
        .all()
    )

    return jsonify({
        "status": "success",
        "count": len(backups),
        "backups": [
            backup_to_dict(backup)
            for backup in backups
        ]
    })


@app.route(
    "/api/v1/backups",
    methods=["POST"]
)
def create_backup():

    data = request.get_json(
        silent=True
    ) or {}

    name = data.get("name")

    storage_location = data.get(
        "storage_location"
    )

    status = data.get("status")

    backup_type = data.get(
        "backup_type",
        "manual"
    )

    if (
        not name
        or not storage_location
        or not status
    ):
        return jsonify({
            "error": (
                "name, storage_location, "
                "and status are required"
            )
        }), 400

    backup = Backup(
        name=name,
        storage_location=storage_location,
        status=status,
        backup_type=backup_type
    )

    db.session.add(backup)

    db.session.commit()

    return jsonify({
        "message": (
            "Backup created successfully"
        ),
        "backup": backup_to_dict(
            backup
        )
    }), 201


# --------------------------------------------------
# S3 BACKUP VERIFICATION ROUTE
# --------------------------------------------------

@app.route(
    "/api/v1/backups/verify",
    methods=["POST"]
)
def verify_backup():

    data = request.get_json(
        silent=True
    ) or {}

    object_key = data.get(
        "object_key"
    )

    expected_checksum = data.get(
        "checksum"
    )

    if (
        not isinstance(object_key, str)
        or not object_key.strip()
    ):
        return jsonify({
            "success": False,
            "message": "object_key is required"
        }), 400

    if (
        not isinstance(
            expected_checksum,
            str
        )
        or not expected_checksum.strip()
    ):
        return jsonify({
            "success": False,
            "message": "checksum is required"
        }), 400

    try:

        result = (
            BackupService()
            .verify_s3_backup(
                object_key=object_key,
                expected_checksum=expected_checksum
            )
        )

        status_code = (
            200
            if result["verified"]
            else 422
        )

        return jsonify({
            "success": result["verified"],
            "verification": result
        }), status_code

    except Exception:

        app.logger.exception(
            "Backup verification failed"
        )

        return jsonify({
            "success": False,
            "message": (
                "Backup verification failed. "
                "Check the application logs."
            )
        }), 500


# --------------------------------------------------
# INCIDENT ROUTES
# --------------------------------------------------

@app.route(
    "/api/v1/incidents",
    methods=["GET"]
)
def get_incidents():

    incidents = (
        Incident.query
        .order_by(Incident.id.desc())
        .all()
    )

    return jsonify({
        "status": "success",
        "count": len(incidents),
        "incidents": [
            incident_to_dict(incident)
            for incident in incidents
        ]
    })


@app.route(
    "/api/v1/incidents",
    methods=["POST"]
)
def create_incident():

    data = request.get_json(
        silent=True
    ) or {}

    title = data.get("title")

    severity = data.get("severity")

    status = data.get("status")

    description = data.get(
        "description"
    )

    if (
        not title
        or not severity
        or not status
    ):
        return jsonify({
            "error": (
                "title, severity, "
                "and status are required"
            )
        }), 400

    incident = Incident(
        title=title,
        severity=severity,
        status=status,
        description=description
    )

    db.session.add(incident)

    db.session.commit()

    return jsonify({
        "message": (
            "Incident created successfully"
        ),
        "incident": incident_to_dict(
            incident
        )
    }), 201


@app.route(
    "/api/v1/incidents/<int:incident_id>",
    methods=["PUT"]
)
def update_incident(incident_id):

    incident = db.session.get(
        Incident,
        incident_id
    )

    if incident is None:
        return jsonify({
            "error": "Incident not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    if "title" in data:
        incident.title = data["title"]

    if "severity" in data:
        incident.severity = data["severity"]

    if "status" in data:
        incident.status = data["status"]

    if "description" in data:
        incident.description = data[
            "description"
        ]

    db.session.commit()

    return jsonify({
        "message": (
            "Incident updated successfully"
        ),
        "incident": incident_to_dict(
            incident
        )
    })


# --------------------------------------------------
# RECOVERY REQUEST ROUTES
# --------------------------------------------------

@app.route(
    "/api/v1/recovery-requests",
    methods=["GET"]
)
def get_recovery_requests():

    recovery_requests = (
        RecoveryRequest.query
        .order_by(
            RecoveryRequest.id.desc()
        )
        .all()
    )

    return jsonify({
        "status": "success",
        "count": len(recovery_requests),
        "recovery_requests": [
            recovery_request_to_dict(
                recovery_request
            )
            for recovery_request
            in recovery_requests
        ]
    })


@app.route(
    "/api/v1/recovery-requests",
    methods=["POST"]
)
def create_recovery_request():

    data = request.get_json(
        silent=True
    ) or {}

    resource_name = data.get(
        "resource_name"
    )

    recovery_type = data.get(
        "recovery_type"
    )

    status = data.get(
        "status",
        "pending"
    )

    reason = data.get("reason")

    allowed_statuses = [
        "pending",
        "in_progress",
        "completed",
        "failed"
    ]

    if (
        not resource_name
        or not recovery_type
    ):
        return jsonify({
            "error": (
                "resource_name and "
                "recovery_type are required"
            )
        }), 400

    if status not in allowed_statuses:
        return jsonify({
            "error": (
                "Invalid status. Allowed "
                "statuses are: pending, "
                "in_progress, completed, failed"
            )
        }), 400

    recovery_request = RecoveryRequest(
        resource_name=resource_name,
        recovery_type=recovery_type,
        status=status,
        reason=reason
    )

    db.session.add(
        recovery_request
    )

    db.session.commit()

    return jsonify({
        "message": (
            "Recovery request created "
            "successfully"
        ),
        "recovery_request":
            recovery_request_to_dict(
                recovery_request
            )
    }), 201


@app.route(
    "/api/v1/recovery-requests/<int:request_id>",
    methods=["PUT"]
)
def update_recovery_request(request_id):

    recovery_request = db.session.get(
        RecoveryRequest,
        request_id
    )

    if recovery_request is None:
        return jsonify({
            "error": (
                "Recovery request not found"
            )
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    allowed_statuses = [
        "pending",
        "in_progress",
        "completed",
        "failed"
    ]

    if "resource_name" in data:
        recovery_request.resource_name = (
            data["resource_name"]
        )

    if "recovery_type" in data:
        recovery_request.recovery_type = (
            data["recovery_type"]
        )

    if "reason" in data:
        recovery_request.reason = (
            data["reason"]
        )

    if "status" in data:

        if (
            data["status"]
            not in allowed_statuses
        ):
            return jsonify({
                "error": (
                    "Invalid status. Allowed "
                    "statuses are: pending, "
                    "in_progress, completed, failed"
                )
            }), 400

        recovery_request.status = (
            data["status"]
        )

    db.session.commit()

    return jsonify({
        "message": (
            "Recovery request updated "
            "successfully"
        ),
        "recovery_request":
            recovery_request_to_dict(
                recovery_request
            )
    })


# --------------------------------------------------
# BACKUP VERIFICATION HISTORY
# --------------------------------------------------

@app.route(
    "/api/v1/backups/verify-integrity",
    methods=["POST"]
)
def verify_backup_integrity():

    data = request.get_json(
        silent=True
    ) or {}

    object_key = data.get(
        "object_key"
    )

    checksum = data.get(
        "checksum"
    )

    if (
        not isinstance(object_key, str)
        or not object_key.startswith(
            "resqcloud-backups/"
        )
    ):
        return jsonify({
            "success": False,
            "message": (
                "A valid ResQCloud backup "
                "object key is required."
            )
        }), 400

    if (
        not isinstance(checksum, str)
        or not re.fullmatch(
            r"[a-fA-F0-9]{64}",
            checksum
        )
    ):
        return jsonify({
            "success": False,
            "message": (
                "A valid 64-character "
                "SHA-256 checksum is required."
            )
        }), 400

    record = BackupVerification(
        object_key=object_key,
        expected_checksum=checksum.lower(),
        status="pending",
        verified=False,
    )

    db.session.add(record)

    try:

        result = (
            BackupService()
            .verify_s3_backup_integrity(
                object_key=object_key,
                expected_checksum=checksum.lower()
            )
        )

        record.actual_checksum = (
            result.get("actual_checksum")
        )

        record.verified = (
            result["verified"]
        )

        record.status = (
            "verified"
            if result["verified"]
            else "mismatch"
        )

        record.message = result.get(
            "message",
            ""
        )

        record.verified_at = (
            datetime.now(timezone.utc)
            .replace(tzinfo=None)
        )

        db.session.commit()

        return jsonify({
            "success": record.verified,
            "verification": {
                "id": record.id,
                "object_key": record.object_key,
                "expected_checksum":
                    record.expected_checksum,
                "actual_checksum":
                    record.actual_checksum,
                "verified":
                    record.verified,
                "status":
                    record.status,
                "message":
                    record.message,
                "verified_at": (
                    record.verified_at.isoformat()
                ),
            }
        }), (
            200
            if record.verified
            else 422
        )

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Backup integrity verification failed"
        )

        return jsonify({
            "success": False,
            "message": (
                "Verification could not be "
                "completed. Check application "
                "logs and AWS permissions."
            )
        }), 500


@app.route(
    "/api/v1/backup-verifications",
    methods=["GET"]
)
def list_backup_verifications():

    try:

        records = (
            BackupVerification.query
            .order_by(
                BackupVerification.id.desc()
            )
            .limit(100)
            .all()
        )

        return jsonify({
            "success": True,
            "count": len(records),
            "verifications": [
                {
                    "id": item.id,
                    "object_key":
                        item.object_key,
                    "expected_checksum":
                        item.expected_checksum,
                    "actual_checksum":
                        item.actual_checksum,
                    "verified":
                        item.verified,
                    "status":
                        item.status,
                    "message":
                        item.message,
                    "verified_at": (
                        item.verified_at.isoformat()
                        if item.verified_at
                        else None
                    ),
                }
                for item in records
            ]
        }), 200

    except Exception:

        app.logger.exception(
            "Could not retrieve verification history"
        )

        return jsonify({
            "success": False,
            "message": (
                "Could not retrieve "
                "verification history."
            )
        }), 500


@app.route(
    "/api/v1/backup-verifications/<int:verification_id>",
    methods=["GET"]
)
def get_backup_verification(
    verification_id
):

    record = db.session.get(
        BackupVerification,
        verification_id
    )

    if record is None:
        return jsonify({
            "success": False,
            "message": (
                "Verification record not found."
            )
        }), 404

    return jsonify({
        "success": True,
        "verification": {
            "id": record.id,
            "object_key":
                record.object_key,
            "expected_checksum":
                record.expected_checksum,
            "actual_checksum":
                record.actual_checksum,
            "verified":
                record.verified,
            "status":
                record.status,
            "message":
                record.message,
            "verified_at": (
                record.verified_at.isoformat()
                if record.verified_at
                else None
            ),
        }
    }), 200


# --------------------------------------------------
# BACKUP UPLOAD ROUTE
# --------------------------------------------------

@app.route(
    "/api/v1/backups/upload",
    methods=["POST"]
)
def upload_backup():

    data = request.get_json(
        silent=True
    ) or {}

    filename = data.get(
        "filename"
    )

    if (
        not isinstance(filename, str)
        or not filename.strip()
    ):
        return jsonify({
            "success": False,
            "message": (
                "filename is required"
            )
        }), 400

    # Permit a simple filename only.
    # Do not allow paths or traversal.
    if (
        filename != Path(filename).name
        or filename in {".", ".."}
    ):
        return jsonify({
            "success": False,
            "message": (
                "Only a filename is allowed"
            )
        }), 400

    data_dir = (
        Path(__file__).resolve().parent
        / "data"
    ).resolve()

    source = (
        data_dir / filename
    ).resolve()

    if (
        source.parent != data_dir
        or not source.is_file()
    ):
        return jsonify({
            "success": False,
            "message": (
                "File not found in the "
                "permitted backup directory"
            )
        }), 404

    try:

        result = BackupService().create_backup(
            str(source)
        )

        # Save application backup history.
        backup = Backup(
            name=source.name,
            storage_location=(
                f"s3://{result['bucket']}/"
                f"{result['object_key']}"
            ),
            status="completed",
            backup_type="file"
        )

        db.session.add(backup)

        db.session.flush()

        artifact_data = None

        if BackupArtifact is not None:

            artifact = BackupArtifact(
                backup_id=backup.id,
                bucket=result["bucket"],
                object_key=result["object_key"],
                checksum=result["checksum"],
                size_bytes=source.stat().st_size,
                status="uploaded"
            )

            db.session.add(artifact)

            db.session.flush()

            artifact_data = {
                "id": artifact.id,
                "object_key":
                    artifact.object_key,
                "checksum":
                    artifact.checksum,
                "size_bytes":
                    artifact.size_bytes
            }

        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                "Backup uploaded and "
                "saved successfully"
            ),
            "backup": {
                "id": backup.id,
                "name": backup.name,
                "status": backup.status,
                "storage_location":
                    backup.storage_location
            },
            "artifact": artifact_data
        }), 201

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Backup upload or database persistence failed"
        )

        return jsonify({
            "success": False,
            "message": (
                "Backup operation failed. "
                "Check application logs and "
                "reconcile any S3 object created "
                "before the database failure."
            )
        }), 500


# --------------------------------------------------
# BROWSER BACKUP UPLOAD ROUTE
# --------------------------------------------------

@app.route(
    "/api/v1/backups/upload-file",
    methods=["POST"]
)
def upload_backup_file():

    if BackupArtifact is None:
        return jsonify({
            "success": False,
            "message": (
                "BackupArtifact model is unavailable. "
                "Define it in models.py first."
            ),
        }), 503

    uploaded = request.files.get(
        "file"
    )

    if (
        uploaded is None
        or not uploaded.filename
    ):
        return jsonify({
            "success": False,
            "message": (
                "Select a file to upload."
            )
        }), 400

    filename = secure_filename(
        uploaded.filename
    )

    if not filename:
        return jsonify({
            "success": False,
            "message": (
                "Invalid filename."
            )
        }), 400

    max_size = (
        25 * 1024 * 1024
    )

    content_length = (
        request.content_length
        or 0
    )

    if (
        content_length
        > max_size + 1024 * 1024
    ):
        return jsonify({
            "success": False,
            "message": (
                "Upload exceeds the "
                "25 MiB limit."
            )
        }), 413

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            source = (
                Path(temp_dir)
                / filename
            )

            uploaded.save(source)

            size_bytes = source.stat().st_size

            if size_bytes > max_size:
                return jsonify({
                    "success": False,
                    "message": (
                        "Upload exceeds the "
                        "25 MiB limit."
                    )
                }), 413

            if size_bytes == 0:
                return jsonify({
                    "success": False,
                    "message": (
                        "Empty files are "
                        "not accepted."
                    )
                }), 400

            result = BackupService().create_backup(
                str(source)
            )

            backup = Backup(
                name=filename,
                storage_location=(
                    f"s3://{result['bucket']}/"
                    f"{result['object_key']}"
                ),
                status="completed",
                backup_type="file"
            )

            db.session.add(backup)

            db.session.flush()

            artifact = BackupArtifact(
                backup_id=backup.id,
                bucket=result["bucket"],
                object_key=result["object_key"],
                checksum=result["checksum"],
                size_bytes=size_bytes,
                status="uploaded"
            )

            db.session.add(artifact)

            db.session.commit()

            return jsonify({
                "success": True,
                "message": (
                    "File uploaded and "
                    "backup record saved."
                ),
                "backup": {
                    "id": backup.id,
                    "name": backup.name,
                    "status": backup.status,
                    "storage_location":
                        backup.storage_location
                },
                "artifact": {
                    "id": artifact.id,
                    "object_key":
                        artifact.object_key,
                    "checksum":
                        artifact.checksum,
                    "size_bytes":
                        artifact.size_bytes
                }
            }), 201

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Browser backup upload failed"
        )

        return jsonify({
            "success": False,
            "message": (
                "Backup upload failed. "
                "Check application logs and "
                "reconcile any S3 upload if "
                "database persistence failed."
            )
        }), 500


# --------------------------------------------------
# BACKUP RESTORE ROUTE
# --------------------------------------------------

@app.route(
    "/api/v1/backups/<int:backup_id>/restore",
    methods=["POST"]
)
def restore_backup(backup_id):
    """
    Restore a verified ResQCloud backup.

    The restore destination is controlled
    by the application.
    """

    if BackupArtifact is None:
        return jsonify({
            "success": False,
            "message": (
                "BackupArtifact model is unavailable."
            )
        }), 503

    # Find the original backup record.
    backup = db.session.get(
        Backup,
        backup_id
    )

    if backup is None:
        return jsonify({
            "success": False,
            "message": (
                f"Backup {backup_id} "
                "was not found."
            )
        }), 404

    # Find the S3 artifact associated
    # with this backup.
    artifact = (
        BackupArtifact.query
        .filter_by(
            backup_id=backup_id
        )
        .order_by(
            BackupArtifact.id.desc()
        )
        .first()
    )

    if artifact is None:
        return jsonify({
            "success": False,
            "message": (
                "No backup artifact found "
                "for this backup ID."
            )
        }), 404

    # Only allow appropriate artifact states.
    if artifact.status not in (
        "uploaded",
        "verified",
        "restored"
    ):
        return jsonify({
            "success": False,
            "message": (
                "Backup artifact is not "
                "eligible for restoration."
            ),
            "status": artifact.status
        }), 409

    # Fixed application-controlled directory.
    # Never accept destination from the request.
    restore_directory = (
        Path(app.root_path)
        / "restored"
    ).resolve()

    restore_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # Generate destination filename from
    # the backup ID.
    destination = (
        restore_directory
        / f"backup-{backup_id}.restored"
    )

    try:

        result = BackupService().restore_s3_backup(
            object_key=artifact.object_key,
            expected_checksum=artifact.checksum,
            destination_path=str(destination)
        )

        # Service rejects restoration if
        # checksum verification fails.
        if not result.get("restored"):
            return jsonify({
                "success": False,
                **result
            }), 422

        # Mark as restored only after
        # successful restoration.
        artifact.status = "restored"

        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                "Backup restored and "
                "integrity verified successfully."
            ),
            "backup_id": backup_id,
            **result
        }), 200

    except FileExistsError:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                "A restored file already exists. "
                "Preserve it or move it before "
                "retrying."
            )
        }), 409

    except ValueError as exc:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(exc)
        }), 400

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Backup restoration failed "
            "for backup ID %s",
            backup_id
        )

        return jsonify({
            "success": False,
            "message": (
                "Restoration failed. "
                "Check the application logs "
                "for details."
            )
        }), 500
# --------------------------------------------------
# CLOUDWATCH DASHBOARD METRICS
# --------------------------------------------------

@app.route(
    "/api/v1/monitoring/metrics",
    methods=["GET"]
)
def cloudwatch_dashboard_metrics():

    try:
        import boto3
        from datetime import datetime, timedelta, timezone

        region = (
            os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
            or "ap-south-2"
        )

        instance_id = os.getenv(
            "RESQCLOUD_EC2_INSTANCE_ID",
            ""
        ).strip()

        if not instance_id:
            return jsonify({
                "success": False,
                "message": (
                    "RESQCLOUD_EC2_INSTANCE_ID "
                    "is not configured."
                )
            }), 400

        cloudwatch = boto3.client(
            "cloudwatch",
            region_name=region
        )

        end_time = datetime.now(timezone.utc)

        start_time = (
            end_time - timedelta(minutes=30)
        )

        def get_metric(
            namespace,
            metric_name,
            dimensions,
            statistics=("Average",)
        ):
            response = cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=list(statistics)
            )

            datapoints = response.get(
                "Datapoints",
                []
            )

            datapoints.sort(
                key=lambda point: point["Timestamp"]
            )

            return [
                {
                    "timestamp": point[
                        "Timestamp"
                    ].isoformat(),
                    "value": round(
                        float(
                            point.get(
                                "Average",
                                point.get(
                                    "Sum",
                                    0
                                )
                            )
                        ),
                        2
                    )
                }
                for point in datapoints
            ]

        ec2_dimensions = [
            {
                "Name": "InstanceId",
                "Value": instance_id
            }
        ]

        cpu = get_metric(
            "AWS/EC2",
            "CPUUtilization",
            ec2_dimensions
        )

        network_in = get_metric(
            "AWS/EC2",
            "NetworkIn",
            ec2_dimensions
        )

        network_out = get_metric(
            "AWS/EC2",
            "NetworkOut",
            ec2_dimensions
        )

               # --------------------------------------------------
        # --------------------------------------------------
        # MEMORY METRICS
        # --------------------------------------------------

        memory = []

        image_id = os.getenv(
            "RESQCLOUD_EC2_IMAGE_ID",
            ""
        ).strip()

        instance_type = os.getenv(
            "RESQCLOUD_EC2_INSTANCE_TYPE",
            ""
        ).strip()

        # Actual CloudWatch Agent dimensions found in AWS:
        # ImageId + InstanceId + InstanceType
        memory_dimensions = [
            {
                "Name": "ImageId",
                "Value": image_id
            },
            {
                "Name": "InstanceId",
                "Value": instance_id
            },
            {
                "Name": "InstanceType",
                "Value": instance_type
            }
        ]

        if all(
            dimension["Value"]
            for dimension in memory_dimensions
        ):
            memory = get_metric(
                "CWAgent",
                "mem_used_percent",
                memory_dimensions
            )


        # --------------------------------------------------
        # DISK METRICS
        # --------------------------------------------------

        disk = []

        # Actual CloudWatch Agent disk dimensions found in AWS:
        # ImageId + InstanceId + InstanceType +
        # device=nvme0n1p1 + fstype=ext4 + path=/
        disk_dimensions = [
            {
                "Name": "ImageId",
                "Value": image_id
            },
            {
                "Name": "InstanceId",
                "Value": instance_id
            },
            {
                "Name": "InstanceType",
                "Value": instance_type
            },
            {
                "Name": "device",
                "Value": "nvme0n1p1"
            },
            {
                "Name": "fstype",
                "Value": "ext4"
            },
            {
                "Name": "path",
                "Value": "/"
            }
        ]

        if all(
            dimension["Value"]
            for dimension in disk_dimensions
        ):
            disk = get_metric(
                "CWAgent",
                "disk_used_percent",
                disk_dimensions
            )

        latest_cpu = (
            cpu[-1]["value"]
            if cpu
            else None
        )

        return jsonify({
            "success": True,
            "instance_id": instance_id,
            "region": region,
            "period_minutes": 30,
            "generated_at": (
                end_time.isoformat()
            ),
            "metrics": {
                "cpu": cpu,
                "memory": memory,
                "disk": disk,
                "network_in": network_in,
                "network_out": network_out
            },
            "latest": {
                "cpu": latest_cpu,
                "memory": (
                    memory[-1]["value"]
                    if memory
                    else None
                ),
                "disk": (
                    disk[-1]["value"]
                    if disk
                    else None
                )
            }
        }), 200

    except Exception:
        app.logger.exception(
            "CloudWatch dashboard metrics failed"
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to retrieve CloudWatch "
                "dashboard metrics."
            )
        }), 500


# --------------------------------------------------
# CLOUDWATCH EC2 CPU MONITORING ROUTE
# --------------------------------------------------

# --------------------------------------------------
# CLOUDWATCH EC2 CPU MONITORING ROUTE
# --------------------------------------------------

@app.route(
    "/api/v1/monitoring/cloudwatch-check",
    methods=["POST"]
)
def cloudwatch_check():

    try:

        monitor = CloudWatchMonitor()

        metrics = (
            monitor.get_ec2_cpu_utilization()
        )

        if not metrics.get(
            "data_available"
        ):
            return jsonify({
                "success": False,
                "message": metrics.get(
                    "message",
                    "CloudWatch metric "
                    "data is unavailable."
                ),
                "metrics": metrics
            }), 200

        if metrics["healthy"]:
            return jsonify({
                "success": True,
                "message": (
                    "EC2 CPU utilization "
                    "is within the threshold."
                ),
                "metrics": metrics,
                "incident": None
            }), 200

        incident_title = (
            "High CPU utilization on "
            f"{metrics['instance_id']}"
        )

        existing_incident = (
            Incident.query
            .filter_by(
                title=incident_title,
                status="open"
            )
            .first()
        )

        if existing_incident:
            return jsonify({
                "success": True,
                "message": (
                    "An open incident "
                    "already exists."
                ),
                "metrics": metrics,
                "incident_id":
                    existing_incident.id,
                "duplicate_incident": True
            }), 200

        incident = Incident(
            title=incident_title,
            severity="high",
            status="open",
            description=(
                "EC2 CPU utilization reached "
                f"{metrics['cpu_average_percent']}%. "
                "Configured threshold: "
                f"{metrics['threshold_percent']}%. "
                "Instance: "
                f"{metrics['instance_id']}. "
                "Region: "
                f"{metrics['region']}."
            )
        )

        db.session.add(incident)

        db.session.commit()

        try:

            notification = send_sns_alert(
                component=metrics[
                    "instance_id"
                ],
                status="critical",
                message=incident.description,
                incident_id=incident.id
            )

        except Exception:

            app.logger.exception(
                "SNS alert failed for "
                "CloudWatch incident %s",
                incident.id
            )

            notification = {
                "sent": False,
                "reason": (
                    "SNS delivery failed. "
                    "Check application logs."
                )
            }

        return jsonify({
            "success": True,
            "message": (
                "High CPU detected; "
                "incident recorded."
            ),
            "metrics": metrics,
            "incident_id": incident.id,
            "notification": notification,
            "duplicate_incident": False
        }), 201

    except (
        ValueError,
        RuntimeError
    ) as exc:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(exc)
        }), 400

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "CloudWatch monitoring check failed"
        )

        return jsonify({
            "success": False,
            "error": (
                "CloudWatch monitoring "
                "check failed. Check "
                "server logs."
            )
        }), 500


# --------------------------------------------------
# AUTOMATED MONITORING / INCIDENT DETECTION
# --------------------------------------------------

@app.route(
    "/api/v1/monitoring/check",
    methods=["POST"]
)
def monitoring_check():

    data = request.get_json(
        silent=True
    ) or {}

    component = str(
        data.get(
            "component",
            ""
        )
    ).strip()

    status = str(
        data.get(
            "status",
            ""
        )
    ).strip()

    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    if (
        not component
        or not status
    ):
        return jsonify({
            "success": False,
            "message": (
                "component and status "
                "are required."
            ),
        }), 400

    if (
        len(component) > 200
        or len(status) > 30
        or len(message) > 4000
    ):
        return jsonify({
            "success": False,
            "message": (
                "One or more input fields "
                "exceed the allowed length."
            ),
        }), 400

    try:

        evaluation = evaluate_status(
            status
        )

    except ValueError as exc:

        return jsonify({
            "success": False,
            "message": str(exc)
        }), 400

    if evaluation["healthy"]:

        return jsonify({
            "success": True,
            "healthy": True,
            "component": component,
            "status":
                evaluation["status"],
            "message": (
                "Component is healthy. "
                "No incident created."
            ),
        }), 200

    incident = Incident(
        title=(
            f"{component} reported "
            f"{evaluation['status']}"
        ),
        severity=(
            "critical"
            if evaluation["status"]
            in {
                "critical",
                "down",
                "failed"
            }
            else "high"
        ),
        status="open",
        description=(
            message
            or (
                "Monitoring reported "
                f"status: {status}"
            )
        ),
    )

    try:

        db.session.add(incident)

        db.session.commit()

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Failed to create "
            "monitoring incident"
        )

        return jsonify({
            "success": False,
            "message": (
                "Failed to save "
                "the incident."
            ),
        }), 500

    # Save incident first.
    # Notification failure must not lose it.
    try:

        notification = send_sns_alert(
            component=component,
            status=evaluation["status"],
            message=(
                message
                or "No additional "
                "details provided."
            ),
            incident_id=incident.id,
        )

    except Exception:

        app.logger.exception(
            "SNS alert failed for "
            "incident %s",
            incident.id
        )

        notification = {
            "sent": False,
            "reason": (
                "SNS delivery failed. "
                "Check application logs."
            )
        }

    return jsonify({
        "success": True,
        "healthy": False,
        "incident_id":
            incident.id,
        "component":
            component,
        "status":
            evaluation["status"],
        "severity":
            incident.severity,
        "incident_status":
            incident.status,
        "notification":
            notification,
    }), 201


# --------------------------------------------------
# UNIFIED CLOUDWATCH HEALTH MONITORING
# --------------------------------------------------

@app.route(
    "/api/v1/monitoring/run",
    methods=["POST"]
)
def monitoring_run():

    try:
        monitor = CloudWatchMonitor()

        evaluation = (
            monitor.run_health_check()
        )

        if not evaluation.get(
            "data_available"
        ):
            return jsonify({
                "success": False,
                "healthy": False,
                "message": (
                    "No CloudWatch monitoring "
                    "data is currently available."
                ),
                "evaluation": evaluation
            }), 200

        failed_checks = evaluation.get(
            "failed_checks",
            []
        )

        if not failed_checks:
            return jsonify({
                "success": True,
                "healthy": True,
                "message": (
                    "All available monitored "
                    "resources are within thresholds."
                ),
                "evaluation": evaluation,
                "incident": None
            }), 200

        metric_names = ", ".join(
            item["metric"]
            for item in failed_checks
        )

        incident_title = (
            "CloudWatch threshold breach: "
            f"{metric_names} on "
            f"{evaluation['instance_id']}"
        )

        existing_incident = (
            Incident.query
            .filter_by(
                title=incident_title,
                status="open"
            )
            .first()
        )

        if existing_incident:
            return jsonify({
                "success": True,
                "healthy": False,
                "message": (
                    "Threshold breach detected. "
                    "An open incident already exists."
                ),
                "evaluation": evaluation,
                "incident_id":
                    existing_incident.id,
                "duplicate_incident": True,
                "notification": None
            }), 200

        failure_details = []

        for failure in failed_checks:
            failure_details.append(
                f"{failure['metric'].upper()} = "
                f"{failure['value']}% "
                f"(threshold: "
                f"{failure['threshold']}%)"
            )

        description = (
            "ResQCloud detected one or more "
            "CloudWatch threshold breaches. "
            f"Instance: "
            f"{evaluation['instance_id']}. "
            f"Region: "
            f"{evaluation['region']}. "
            "Failures: "
            + "; ".join(
                failure_details
            )
        )

        incident = Incident(
            title=incident_title,
            severity="high",
            status="open",
            description=description
        )

        try:
            db.session.add(incident)
            db.session.commit()
        except Exception:
            db.session.rollback()
            app.logger.exception(
                "Failed to create automated "
                "CloudWatch incident"
            )
            return jsonify({
                "success": False,
                "healthy": False,
                "message": (
                    "Monitoring detected a "
                    "threshold breach, but "
                    "the incident could not "
                    "be saved."
                ),
                "evaluation": evaluation
            }), 500

        try:
            notification = send_sns_alert(
                component=
                    evaluation["instance_id"],
                status="critical",
                message=description,
                incident_id=incident.id
            )
        except Exception:
            app.logger.exception(
                "SNS alert failed for "
                "automated monitoring incident %s",
                incident.id
            )
            notification = {
                "sent": False,
                "reason": (
                    "SNS delivery failed. "
                    "Check application logs."
                )
            }

        return jsonify({
            "success": True,
            "healthy": False,
            "message": (
                "CloudWatch threshold breach "
                "detected and incident recorded."
            ),
            "evaluation": evaluation,
            "incident_id": incident.id,
            "duplicate_incident": False,
            "notification": notification
        }), 201

    except (
        ValueError,
        RuntimeError
    ) as exc:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(exc)
        }), 400

    except Exception:
        db.session.rollback()
        app.logger.exception(
            "Unified CloudWatch monitoring "
            "failed"
        )
        return jsonify({
            "success": False,
            "message": (
                "Unified CloudWatch monitoring "
                "failed. Check server logs."
            )
        }), 500


# --------------------------------------------------
# SCHEDULED CLOUDWATCH MONITORING
# --------------------------------------------------

@app.route(
    "/api/v1/monitoring/scheduled-run",
    methods=["POST"]
)
def scheduled_monitoring_run():

    configured_token = (
        RESQCLOUD_MONITORING_TOKEN
    )

    if not configured_token:
        app.logger.error(
            "RESQCLOUD_MONITORING_TOKEN is not configured."
        )

        return jsonify({
            "success": False,
            "message": (
                "Scheduled monitoring is not configured."
            )
        }), 503

    supplied_token = (
        request.headers
        .get(
            "X-ResQCloud-Monitoring-Token",
            ""
        )
        .strip()
    )

    if not supplied_token:
        return jsonify({
            "success": False,
            "message": "Monitoring token is required."
        }), 401

    if supplied_token != configured_token:
        app.logger.warning(
            "Unauthorized scheduled monitoring request."
        )

        return jsonify({
            "success": False,
            "message": "Invalid monitoring token."
        }), 401

    try:
        monitor = CloudWatchMonitor()
        evaluation = monitor.run_health_check()

        failed_checks = evaluation.get(
            "failed_checks",
            []
        )

        if not evaluation.get("data_available"):
            return jsonify({
                "success": False,
                "healthy": False,
                "message": (
                    "CloudWatch monitoring "
                    "data is unavailable."
                ),
                "evaluation": evaluation
            }), 200

        if not failed_checks:
            return jsonify({
                "success": True,
                "healthy": True,
                "message": (
                    "Scheduled monitoring completed. "
                    "All available metrics are healthy."
                ),
                "evaluation": evaluation,
                "incident": None
            }), 200

        metric_names = ", ".join(
            item["metric"]
            for item in failed_checks
        )

        incident_title = (
            "CloudWatch threshold breach: "
            f"{metric_names} on "
            f"{evaluation['instance_id']}"
        )

        existing_incident = (
            Incident.query
            .filter_by(
                title=incident_title,
                status="open"
            )
            .first()
        )

        if existing_incident:
            return jsonify({
                "success": True,
                "healthy": False,
                "message": (
                    "Scheduled monitoring detected "
                    "an existing open incident."
                ),
                "evaluation": evaluation,
                "incident_id":
                    existing_incident.id,
                "duplicate_incident": True
            }), 200

        failure_details = []

        for failure in failed_checks:
            failure_details.append(
                f"{failure['metric'].upper()} = "
                f"{failure['value']}% "
                f"(threshold: "
                f"{failure['threshold']}%)"
            )

        description = (
            "Scheduled ResQCloud monitoring detected "
            "a CloudWatch threshold breach. "
            f"Instance: "
            f"{evaluation['instance_id']}. "
            f"Region: "
            f"{evaluation['region']}. "
            "Failures: "
            + "; ".join(
                failure_details
            )
        )

        incident = Incident(
            title=incident_title,
            severity="high",
            status="open",
            description=description
        )

        db.session.add(incident)
        db.session.commit()

        try:
            notification = send_sns_alert(
                component=
                    evaluation["instance_id"],
                status="critical",
                message=description,
                incident_id=incident.id
            )
        except Exception:
            app.logger.exception(
                "SNS alert failed for scheduled "
                "monitoring incident %s",
                incident.id
            )
            notification = {
                "sent": False,
                "reason": (
                    "SNS delivery failed. "
                    "Check application logs."
                )
            }

        return jsonify({
            "success": True,
            "healthy": False,
            "message": (
                "Scheduled monitoring detected "
                "a threshold breach and created "
                "an incident."
            ),
            "evaluation": evaluation,
            "incident_id": incident.id,
            "notification": notification,
            "duplicate_incident": False
        }), 201

    except Exception:
        db.session.rollback()
        app.logger.exception(
            "Scheduled monitoring failed."
        )
        return jsonify({
            "success": False,
            "message": (
                "Scheduled monitoring failed."
            )
        }), 500


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

with app.app_context():
    db.create_all()


# --------------------------------------------------
# APPLICATION START
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )