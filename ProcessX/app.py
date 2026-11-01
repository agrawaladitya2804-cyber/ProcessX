"""ProcessX 2.0 - CPU Scheduling Visualizer (Flask application).

Run with:   python app.py      then open http://127.0.0.1:5000
"""

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException, MethodNotAllowed, NotFound

from backend.algorithms import ALGORITHMS
from backend.simulator import compare_all, simulate
from backend.utils.validation import (
    ValidationError,
    parse_algorithm,
    parse_processes,
    parse_time_quantum,
)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


def create_app():
    app = Flask(__name__, static_folder=None)   # static files are served by the route below
    app.json.sort_keys = False
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0   # always show the latest files while developing

    def read_body():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValidationError("Request body must be a JSON object.")
        return body

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    POST_ONLY = {"/api/simulate", "/api/compare"}

    @app.get("/<path:filename>")
    def frontend_files(filename):
        """Serve css/js/etc. from the frontend folder. API paths never fall through to files."""
        if request.path.startswith("/api/"):
            if request.path in POST_ONLY:
                raise MethodNotAllowed(valid_methods=["POST"])
            raise NotFound()
        return send_from_directory(FRONTEND_DIR, filename)

    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "app": "ProcessX 2.0",
            "engine": "Python",
            "algorithms": list(ALGORITHMS),
        })

    @app.post("/api/simulate")
    def api_simulate():
        body = read_body()
        algorithm = parse_algorithm(body.get("algorithm"))
        processes = parse_processes(body.get("processes"))
        quantum = None
        if ALGORITHMS[algorithm]["uses_quantum"]:
            quantum = parse_time_quantum(body.get("time_quantum"), required=True)
        return jsonify(simulate(processes, algorithm, quantum))

    @app.post("/api/compare")
    def api_compare():
        body = read_body()
        processes = parse_processes(body.get("processes"))
        quantum = parse_time_quantum(body.get("time_quantum"))   # defaults to 2
        return jsonify(compare_all(processes, quantum))

    @app.errorhandler(ValidationError)
    def handle_validation(err):
        return jsonify({"error": "Invalid input.", "details": err.errors}), 400

    @app.errorhandler(HTTPException)
    def handle_http(err):
        if request.path.startswith("/api/"):
            return jsonify({"error": err.name, "details": [err.description]}), err.code
        return err

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Unexpected error")
        return jsonify({"error": "Internal server error.",
                        "details": ["Something went wrong while running the simulation."]}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"\n  ProcessX is running at http://127.0.0.1:{port}  (press Ctrl+C to stop)\n")
    app.run(host="127.0.0.1", port=port, debug=False)
