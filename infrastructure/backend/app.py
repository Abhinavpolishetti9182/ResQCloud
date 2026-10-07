import os
from datetime import datetime

from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    base_dir = os.path.abspath(os.path.dirname(__file__))
    default_database = os.path.join(base_dir, "data", "resqcloud.db")

    database_path = os.getenv(
        "DATABASE_PATH",
        default_database
    )

    os.makedirs(
        os.path.dirname(database_path),
        exist_ok=True
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{database_path}"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.route("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/health")
    def health():
        return jsonify({
            "status": "healthy",
            "service": "resqcloud",
            "timestamp": datetime.utcnow().isoformat()
        })

    @app.route("/api/infrastructure")
    def infrastructure():
        return jsonify({
            "status": "healthy",
            "ec2": "unknown",
            "database": "unknown",
            "backup": "unknown",
            "monitoring": "unknown"
        })

    @app.route("/api/backups")
    def backups():
        return jsonify({
            "status": "success",
            "backups": []
        })

    @app.route("/api/incidents")
    def incidents():
        return jsonify({
            "status": "success",
            "incidents": []
        })

    @app.route("/api/recovery")
    def recovery():
        return jsonify({
            "status": "success",
            "recoveries": []
        })

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(
        host=host,
        port=port,
        debug=debug
    )