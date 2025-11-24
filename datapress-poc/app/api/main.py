from flask import Flask, jsonify
import os
import time

app = Flask(__name__)


@app.route("/")
def root():
    """
    Endpoint principal de l'API.
    Renvoie un JSON simple avec quelques informations.
    """
    return jsonify({
        "service": "api",
        "timestamp": int(time.time()),
        "app_name": os.getenv("APP_NAME", "DataPress API"),
        "environment": os.getenv("APP_ENV", "development"),
        "secret_configured": bool(os.getenv("API_SECRET_TOKEN"))
    })


@app.route("/health")
def health():
    """
    Endpoint de healthcheck utilisé par Kubernetes (liveness/readiness).
    """
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Mode dev local (Docker Compose)
    app.run(host="0.0.0.0", port=8000)
