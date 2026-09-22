from pathlib import Path

from flask import (
    Flask,
    jsonify,
    render_template,
    request
)

from models import (
    Backup,
    Incident,
    InfrastructureResource,
    RecoveryRequest,
    db
)


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

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

    resources = InfrastructureResource.query.order_by(
        InfrastructureResource.id
    ).all()

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

    data = request.get_json(silent=True) or {}

    name = data.get("name")
    resource_type = data.get("resource_type")
    status = data.get("status")
    environment = data.get(
        "environment",
        "development"
    )

    if not name or not resource_type or not status:
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
        "resource": resource_to_dict(resource)
    }), 201


# --------------------------------------------------
# BACKUP ROUTES
# --------------------------------------------------

@app.route(
    "/api/v1/backups",
    methods=["GET"]
)
def get_backups():

    backups = Backup.query.order_by(
        Backup.id.desc()
    ).all()

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

    data = request.get_json(silent=True) or {}

    name = data.get("name")
    storage_location = data.get(
        "storage_location"
    )
    status = data.get("status")
    backup_type = data.get(
        "backup_type",
        "manual"
    )

    if not name or not storage_location or not status:
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
        "backup": backup_to_dict(backup)
    }), 201


# --------------------------------------------------
# INCIDENT ROUTES
# --------------------------------------------------

@app.route(
    "/api/v1/incidents",
    methods=["GET"]
)
def get_incidents():

    incidents = Incident.query.order_by(
        Incident.id.desc()
    ).all()

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

    data = request.get_json(silent=True) or {}

    title = data.get("title")
    severity = data.get("severity")
    status = data.get("status")
    description = data.get("description")

    if not title or not severity or not status:
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
        "incident": incident_to_dict(incident)
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

    data = request.get_json(silent=True) or {}

    if "title" in data:
        incident.title = data["title"]

    if "severity" in data:
        incident.severity = data["severity"]

    if "status" in data:
        incident.status = data["status"]

    if "description" in data:
        incident.description = data["description"]

    db.session.commit()

    return jsonify({
        "message": (
            "Incident updated successfully"
        ),
        "incident": incident_to_dict(incident)
    })


# --------------------------------------------------
# RECOVERY REQUEST ROUTES
# --------------------------------------------------

@app.route(
    "/api/v1/recovery-requests",
    methods=["GET"]
)
def get_recovery_requests():

    recovery_requests = RecoveryRequest.query.order_by(
        RecoveryRequest.id.desc()
    ).all()

    return jsonify({
        "status": "success",
        "count": len(recovery_requests),
        "recovery_requests": [
            recovery_request_to_dict(
                recovery_request
            )
            for recovery_request in recovery_requests
        ]
    })


@app.route(
    "/api/v1/recovery-requests",
    methods=["POST"]
)
def create_recovery_request():

    data = request.get_json(silent=True) or {}

    resource_name = data.get("resource_name")
    recovery_type = data.get("recovery_type")
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

    if not resource_name or not recovery_type:
        return jsonify({
            "error": (
                "resource_name and "
                "recovery_type are required"
            )
        }), 400

    if status not in allowed_statuses:
        return jsonify({
            "error": (
                "Invalid status. Allowed statuses are: "
                "pending, in_progress, completed, failed"
            )
        }), 400

    recovery_request = RecoveryRequest(
        resource_name=resource_name,
        recovery_type=recovery_type,
        status=status,
        reason=reason
    )

    db.session.add(recovery_request)
    db.session.commit()

    return jsonify({
        "message": (
            "Recovery request "
            "created successfully"
        ),
        "recovery_request": (
            recovery_request_to_dict(
                recovery_request
            )
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
            "error": "Recovery request not found"
        }), 404

    data = request.get_json(silent=True) or {}

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
        recovery_request.reason = data["reason"]

    if "status" in data:

        if data["status"] not in allowed_statuses:
            return jsonify({
                "error": (
                    "Invalid status. Allowed statuses are: "
                    "pending, in_progress, completed, failed"
                )
            }), 400

        recovery_request.status = data["status"]

    db.session.commit()

    return jsonify({
        "message": (
            "Recovery request "
            "updated successfully"
        ),
        "recovery_request": (
            recovery_request_to_dict(
                recovery_request
            )
        )
    })


# --------------------------------------------------
# APPLICATION STARTUP
# --------------------------------------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )