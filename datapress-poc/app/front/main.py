from flask import Flask, render_template_string
import os
import requests

app = Flask(__name__)


@app.route("/")
def index():
    front_version = os.getenv("FRONT_VERSION", "v1.0 POC")
    api_base_url = os.getenv("API_BASE_URL", "http://api:8000")           # pour les appels internes
    api_public_url = os.getenv("API_PUBLIC_URL", "http://localhost:8000")  # pour l’URL affichée au user

    api_status = "inconnu"
    api_health_url = f"{api_base_url.rstrip('/')}/health"

    try:
        resp = requests.get(api_health_url, timeout=2)
        if resp.status_code == 200:
            api_status = "OK"
        else:
            api_status = f"KO (HTTP {resp.status_code})"
    except Exception as e:
        api_status = f"Erreur: {str(e)}"

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>DataPress – POC</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: #ffffff;
                padding: 20px 30px;
                border-radius: 8px;
                max-width: 600px;
                box-shadow: 0 0 8px rgba(0,0,0,0.1);
            }
            h1 {
                color: #1e88e5;
            }
            .version {
                font-weight: bold;
                color: #555;
            }
            .api-status {
                margin-top: 20px;
                padding: 10px;
                border-radius: 4px;
            }
            .ok {
                background-color: #c8e6c9;
                color: #2e7d32;
            }
            .ko {
                background-color: #ffcdd2;
                color: #b71c1c;
            }
            code {
                background: #eee;
                padding: 2px 4px;
                border-radius: 3px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>DataPress – POC</h1>
            <p class="version">Version : {{ front_version }}</p>
            <p>Ce front est connecté à l'API DataPress.</p>

            <h2>API</h2>
            <p>URL de base de l'API (utilisée par le front, interne au réseau Docker/Kubernetes) :</p>
            <p><code>{{ api_base_url }}</code></p>

            <div class="api-status {% if api_status == 'OK' %}ok{% else %}ko{% endif %}">
                <strong>Statut de l'API (/health) :</strong> {{ api_status }}
            </div>

            <p style="margin-top:20px;">
                Vous pouvez aussi tester directement l'API depuis votre navigateur :</br>
                <code>{{ api_public_url }}/</code>
            </p>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        html,
        front_version=front_version,
        api_base_url=api_base_url,
        api_public_url=api_public_url,
        api_status=api_status
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
