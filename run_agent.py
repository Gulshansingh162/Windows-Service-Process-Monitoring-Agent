import threading
import time

from app.config import load_config
from app.database import initialize_database
from app.event_logger import logger
from app.process_monitor import ProcessMonitor
from app.service_monitor import ServiceMonitor
from app.api import start_api


def main():

    print("=" * 65)

    print(
        " Windows Service & Process Monitoring Agent"
    )

    print(
        " Professional Security Monitoring Dashboard"
    )

    print("=" * 65)

    initialize_database()

    config = load_config()

    process_monitor = ProcessMonitor(
        config
    )

    service_monitor = ServiceMonitor(
        config
    )

    api_thread = threading.Thread(
        target=start_api,
        daemon=True
    )

    api_thread.start()

    interval = max(
        1,
        int(
            config.get(
                "monitor_interval",
                5
            )
        )
    )

    print()

    print(
        f"Monitoring interval: {interval} seconds"
    )

    print(
        "Dashboard: http://127.0.0.1:5000"
    )

    print(
        "Login: admin / Admin@12345"
    )

    print()

    print(
        "Press CTRL+C to stop."
    )

    print()

    try:

        while True:

            process_monitor.monitor()

            service_monitor.monitor()

            time.sleep(interval)

    except KeyboardInterrupt:

        logger.info(
            "Monitoring agent stopped by user."
        )

        print(
            "\nMonitoring agent stopped."
        )


if __name__ == "__main__":

    main()