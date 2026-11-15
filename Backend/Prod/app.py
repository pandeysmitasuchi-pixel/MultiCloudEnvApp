import os
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

ENV_NAME = "prod"
PORT = int(os.getenv("PORT", 3002))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/tickets_prod")
API_KEY = os.getenv("API_KEY", "dev-secret-key-change-me")

client = MongoClient(MONGO_URI)
db = client.get_default_database() if "/" in MONGO_URI.rsplit("://", 1)[-1] and MONGO_URI.rsplit("/", 1)[-1] else client["tickets_prod"]
tickets_collection = db["tickets"]


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        provided_key = request.headers.get("X-API-Key")
        if API_KEY and provided_key != API_KEY:
            return jsonify({"error": "Unauthorized: Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated


def serialize_ticket(ticket):
    return {
        "id": str(ticket["_id"]),
        "title": ticket.get("title", ""),
        "description": ticket.get("description", ""),
        "priority": ticket.get("priority", "Medium"),
        "status": ticket.get("status", "Open"),
        "environment": ENV_NAME,
        "created_at": ticket.get("created_at", "")
    }


@app.route("/prod", methods=["GET"])
def health_check():
    return jsonify({
        "status": "running",
        "environment": ENV_NAME,
        "port": PORT,
        "database": db.name
    }), 200


@app.route("/prod/tickets", methods=["GET"])
@require_api_key
def get_tickets():
    tickets = list(tickets_collection.find().sort("_id", -1))
    return jsonify([serialize_ticket(t) for t in tickets]), 200


@app.route("/prod/tickets", methods=["POST"])
@require_api_key
def create_ticket():
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    ticket = {
        "title": title,
        "description": data.get("description", "").strip(),
        "priority": data.get("priority", "Medium"),
        "status": "Open",
        "environment": ENV_NAME,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    result = tickets_collection.insert_one(ticket)
    ticket["_id"] = result.inserted_id
    return jsonify(serialize_ticket(ticket)), 201


@app.route("/prod/tickets/<ticket_id>", methods=["PUT"])
@require_api_key
def update_ticket(ticket_id):
    data = request.get_json() or {}
    update_fields = {}
    for field in ["title", "description", "priority", "status"]:
        if field in data:
            update_fields[field] = data[field]

    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400

    result = tickets_collection.update_one(
        {"_id": ObjectId(ticket_id)},
        {"$set": update_fields}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Ticket not found"}), 404

    updated = tickets_collection.find_one({"_id": ObjectId(ticket_id)})
    return jsonify(serialize_ticket(updated)), 200


@app.route("/prod/tickets/<ticket_id>", methods=["DELETE"])
@require_api_key
def delete_ticket(ticket_id):
    result = tickets_collection.delete_one({"_id": ObjectId(ticket_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Ticket not found"}), 404
    return jsonify({"message": "Ticket deleted"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=(ENV_NAME == "dev"))
