import psutil

from .database import (
    add_event,
    add_alert,
    add_service_snapshot
)

from .event_logger import logger


class ServiceMonitor:

    def __init__(self, config):

        self.monitored_services = [
            service.lower()
            for service in config.get(
                "monitored_services",
                []
            )
        ]

        self.previous_status = {}

    def get_services(self):

        services = []

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
                        name
                    )

                    status = info.get(
                        "status",
                        "unknown"
                    )

                    start_type = info.get(
                        "start_type",
                        "unknown"
                    )

                    if (
                        self.monitored_services
                        and
                        name.lower()
                        not in self.monitored_services
                        and
                        display_name.lower()
                        not in self.monitored_services
                    ):

                        continue

                    services.append({
                        "name": name,
                        "display_name": display_name,
                        "status": status,
                        "start_type": start_type
                    })

                except Exception as error:

                    logger.warning(
                        f"Service inspection failed: {error}"
                    )

        except Exception as error:

            logger.error(
                f"Service enumeration failed: {error}"
            )

        return services

    def monitor(self):

        services = self.get_services()

        for service in services:

            name = service["name"]

            status = service["status"]

            previous = self.previous_status.get(
                name
            )

            add_service_snapshot(
                name,
                service["display_name"],
                status,
                service["start_type"]
            )

            if previous is not None:

                if previous != status:

                    message = (
                        f"Service "
                        f"{service['display_name']} "
                        f"changed from "
                        f"{previous} to {status}."
                    )

                    logger.warning(message)

                    add_event(
                        "SERVICE_STATE_CHANGED",
                        name,
                        status,
                        message
                    )

                    severity = (
                        "HIGH"
                        if status != "running"
                        else "INFO"
                    )

                    add_alert(
                        severity,
                        "SERVICE",
                        "Windows Service State Changed",
                        message
                    )

            self.previous_status[name] = status

        return services