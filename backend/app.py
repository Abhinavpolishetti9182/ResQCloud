
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "project": "ResQCloud",
        "message": "Cloud resilience platform is running",
        "status": "success"
    })


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "service": "ResQCloud API",
        "status": "healthy"
    })


@app.route("/api/v1/infrastructure", methods=["GET"])
def infrastructure_status():
    return jsonify({
        "status": "operational",
        "environment": "development",
        "resources": [
            {
                "name": "ResQCloud API",
                "type": "application",
                "status": "healthy"
            }
        ]
    })


@app.route("/api/v1/backups", methods=["GET"])
def backup_status():
    return jsonify({
        "status": "success",
        "message": "Backup status endpoint is working",
        "backups": []
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )