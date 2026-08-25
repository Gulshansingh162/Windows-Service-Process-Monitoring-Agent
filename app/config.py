import json
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CONFIG_FILE = os.path.join(
    BASE_DIR,
    "config.json"
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

LOG_DIR = os.path.join(
    BASE_DIR,
    "logs"
)

DATABASE_FILE = os.path.join(
    DATA_DIR,
    "monitoring.db"
)

LOG_FILE = os.path.join(
    LOG_DIR,
    "agent.log"
)


def ensure_directories():
    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    os.makedirs(
        LOG_DIR,
        exist_ok=True
    )


def load_config():

    ensure_directories()

    if not os.path.exists(CONFIG_FILE):

        return {
            "monitor_interval": 5,
            "api_host": "127.0.0.1",
            "api_port": 5000,
            "process_cpu_threshold": 90.0,
            "process_memory_threshold": 80.0,
            "monitored_processes": [],
            "monitored_services": [],
            "dashboard_username": "admin",
            "dashboard_password": "Admin@12345",
            "session_secret": "CHANGE_ME"
        }

    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)