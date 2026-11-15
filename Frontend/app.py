import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-frontend-key")

PORT = int(os.getenv("PORT", 3000))
DEV_API_URL = os.getenv("DEV_API_URL", "http://backend-dev:3001/dev")
PROD_API_URL = os.getenv("PROD_API_URL", "http://backend-prod:3002/prod")
DEV_API_KEY = os.getenv("DEV_API_KEY", "dev-secret-key-change-me")
PROD_API_KEY = os.getenv("PROD_API_KEY", "prod-secret-key-change-me")


def get_env_config(env):
    if env == "prod":
        return PROD_API_URL, {"X-API-Key": PROD_API_KEY}
    return DEV_API_URL, {"X-API-Key": DEV_API_KEY}


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.route("/", methods=["GET"])
def index():
    env = request.args.get("env", "dev").lower()
    if env not in ("dev", "prod"):
        env = "dev"

    api_url, headers = get_env_config(env)
    tickets = []
    backend_status = "Connected"

    try:
        res = requests.get(f"{api_url}/tickets", headers=headers, timeout=5)
        if res.status_code == 200:
            tickets = res.json()
        else:
            backend_status = f"Error ({res.status_code})"
    except requests.RequestException as e:
        backend_status = f"Unreachable: {e}"

    return render_template(
        "index.html",
        env=env,
        tickets=tickets,
        backend_status=backend_status,
        api_url=api_url
    )


@app.route("/tickets/create", methods=["POST"])
def create_ticket():
    env = request.form.get("env", "dev")
    api_url, headers = get_env_config(env)
    payload = {
        "title": request.form.get("title", ""),
        "description": request.form.get("description", ""),
        "priority": request.form.get("priority", "Medium")
    }
    try:
        res = requests.post(f"{api_url}/tickets", json=payload, headers=headers, timeout=5)
        if res.status_code == 201:
            flash(f"Ticket created in {env.upper()} environment.", "success")
        else:
            flash("Failed to create ticket.", "error")
    except requests.RequestException:
        flash("Backend service unavailable.", "error")

    return redirect(url_for("index", env=env))


@app.route("/tickets/<ticket_id>/status", methods=["POST"])
def update_status(ticket_id):
    env = request.form.get("env", "dev")
    status = request.form.get("status", "Open")
    api_url, headers = get_env_config(env)
    try:
        requests.put(f"{api_url}/tickets/{ticket_id}", json={"status": status}, headers=headers, timeout=5)
        flash("Ticket status updated.", "success")
    except requests.RequestException:
        flash("Failed to update status.", "error")

    return redirect(url_for("index", env=env))


@app.route("/tickets/<ticket_id>/delete", methods=["POST"])
def delete_ticket(ticket_id):
    env = request.form.get("env", "dev")
    api_url, headers = get_env_config(env)
    try:
        requests.delete(f"{api_url}/tickets/{ticket_id}", headers=headers, timeout=5)
        flash("Ticket deleted.", "success")
    except requests.RequestException:
        flash("Failed to delete ticket.", "error")

    return redirect(url_for("index", env=env))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
