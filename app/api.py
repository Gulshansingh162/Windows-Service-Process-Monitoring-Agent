from flask import (
    Flask,
    jsonify,
    request,
    session,
    redirect,
    send_from_directory
)

from functools import wraps

import os
import subprocess
import time
import psutil

from .database import (
    get_recent_events,
    get_recent_alerts,
    get_alert_count,
    get_recent_processes,
    get_recent_services,
    acknowledge_alert
)

from .config import (
    BASE_DIR,
    load_config
)


app = Flask(__name__)

config = load_config()

app.secret_key = config.get(
    "session_secret",
    "CHANGE_ME"
)

DASHBOARD_DIR = os.path.join(
    BASE_DIR,
    "dashboard"
)


SERVICE_NAME = (
    "WindowsMonitoringAgent"
)


def login_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        if not session.get("authenticated"):

            if request.path.startswith("/api/"):

                return jsonify({
                    "error": "Authentication required"
                }), 401

            return redirect("/login")

        return function(*args, **kwargs)

    return decorated


@app.route("/login")
def login_page():

    if session.get("authenticated"):

        return redirect("/")

    return send_from_directory(
        DASHBOARD_DIR,
        "login.html"
    )


@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(
        silent=True
    ) or {}

    username = data.get(
        "username",
        ""
    )

    password = data.get(
        "password",
        ""
    )

    expected_username = config.get(
        "dashboard_username",
        "admin"
    )

    expected_password = config.get(
        "dashboard_password",
        "Admin@12345"
    )

    if (
        username == expected_username
        and
        password == expected_password
    ):

        session["authenticated"] = True

        session["username"] = username

        return jsonify({
            "success": True
        })

    return jsonify({
        "success": False,
        "error": "Invalid username or password"
    }), 401


@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True
    })


@app.route("/")
@login_required
def dashboard():

    return send_from_directory(
        DASHBOARD_DIR,
        "index.html"
    )


@app.route("/style.css")
def style():

    return send_from_directory(
        DASHBOARD_DIR,
        "style.css"
    )


@app.route("/app.js")
@login_required
def javascript():

    return send_from_directory(
        DASHBOARD_DIR,
        "app.js"
    )


@app.route("/api/me")
@login_required
def current_user():

    return jsonify({
        "username": session.get(
            "username"
        ),
        "authenticated": True
    })


@app.route("/api/system")
@login_required
def system_info():

    memory = psutil.virtual_memory()

    return jsonify({
        "cpu_percent": psutil.cpu_percent(
            interval=0.2
        ),
        "memory_percent": memory.percent,
        "memory_total": memory.total,
        "memory_available": memory.available,
        "boot_time": psutil.boot_time(),
        "process_count": len(
            list(
                psutil.process_iter()
            )
        ),
        "timestamp": time.time()
    })


@app.route("/api/processes")
@login_required
def processes():

    search = request.args.get(
        "search",
        ""
    ).lower().strip()

    processes = []

    for process in psutil.process_iter([
        "pid",
        "name",
        "status",
        "username",
        "memory_percent"
    ]):

        try:

            info = process.info

            name = (
                info.get("name")
                or "Unknown"
            )

            if (
                search
                and
                search not in name.lower()
                and
                search not in str(
                    info.get("pid")
                )
            ):

                continue

            processes.append({
                "pid": info["pid"],
                "name": name,
                "status": info.get(
                    "status",
                    "unknown"
                ),
                "username": info.get(
                    "username",
                    ""
                ),
                "memory_percent": round(
                    info.get(
                        "memory_percent",
                        0
                    ) or 0,
                    2
                ),
                "cpu_percent": round(
                    process.cpu_percent(
                        interval=0.01
                    ),
                    2
                )
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):

            continue

    processes.sort(
        key=lambda item:
        item["cpu_percent"],
        reverse=True
    )

    return jsonify(
        processes[:200]
    )


@app.route("/api/services")
@login_required
def services():

    search = request.args.get(
        "search",
        ""
    ).lower().strip()

    result = []

    try:

        for service in psutil.win_service_iter():

            try:

                info = service.as_dict()

                name = info.get(
                    "name",
                    ""
                )

                display_name = info.get(
                    "display_name",
                    ""
                )

                if (
                    search
                    and
                    search not in name.lower()
                    and
                    search not in display_name.lower()
                ):

                    continue

                result.append({
                    "name": name,
                    "display_name": display_name,
                    "status": info.get(
                        "status",
                        "unknown"
                    ),
                    "start_type": info.get(
                        "start_type",
                        "unknown"
                    )
                })

            except Exception:

                continue

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500

    result.sort(
        key=lambda item:
        item["display_name"].lower()
    )

    return jsonify(result)


@app.route("/api/events")
@login_required
def events():

    return jsonify(
        get_recent_events(100)
    )


@app.route("/api/alerts")
@login_required
def alerts():

    return jsonify(
        get_recent_alerts(50)
    )


@app.route("/api/alerts/count")
@login_required
def alert_count():

    return jsonify({
        "count": get_alert_count()
    })


@app.route(
    "/api/alerts/<int:alert_id>/acknowledge",
    methods=["POST"]
)
@login_required
def acknowledge(alert_id):

    acknowledge_alert(
        alert_id
    )

    return jsonify({
        "success": True
    })


@app.route("/api/history/processes")
@login_required
def process_history():

    return jsonify(
        get_recent_processes(100)
    )


@app.route("/api/history/services")
@login_required
def service_history():

    return jsonify(
        get_recent_services(100)
    )


def run_service_command(
    service_name,
    action
):

    if not service_name:

        return False, "Service name is required."

    if action not in [
        "start",
        "stop"
    ]:

        return False, "Invalid action."

    if (
        service_name
        == SERVICE_NAME
    ):

        return False, (
            "The monitoring agent "
            "cannot control itself."
        )

    try:

        result = subprocess.run(
            [
                "sc.exe",
                action,
                service_name
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        output = (
            result.stdout
            +
            result.stderr
        ).strip()

        if result.returncode != 0:

            return False, output

        return True, output

    except Exception as error:

        return False, str(error)


@app.route(
    "/api/services/control",
    methods=["POST"]
)
@login_required
def service_control():

    data = request.get_json(
        silent=True
    ) or {}

    service_name = data.get(
        "name",
        ""
    )

    action = data.get(
        "action",
        ""
    ).lower()

    success, message = (
        run_service_command(
            service_name,
            action
        )
    )

    if success:

        return jsonify({
            "success": True,
            "message": (
                f"Service {service_name} "
                f"{action} command sent."
            ),
            "details": message
        })

    return jsonify({
        "success": False,
        "error": message
    }), 400


@app.route("/api/agent/status")
@login_required
def agent_status():

    try:

        service = psutil.win_service_get(
            SERVICE_NAME
        )

        info = service.as_dict()

        return jsonify({
            "name": SERVICE_NAME,
            "display_name": info.get(
                "display_name"
            ),
            "status": info.get(
                "status"
            ),
            "start_type": info.get(
                "start_type"
            )
        })

    except Exception as error:

        return jsonify({
            "name": SERVICE_NAME,
            "status": "not_installed",
            "error": str(error)
        })


def start_api():

    current_config = load_config()

    app.run(
        host=current_config.get(
            "api_host",
            "127.0.0.1"
        ),
        port=int(
            current_config.get(
                "api_port",
                5000
            )
        ),
        debug=False,
        use_reloader=False
    )