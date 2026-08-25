import psutil

from .database import (
    add_event,
    add_alert,
    add_process_snapshot
)

from .event_logger import logger


class ProcessMonitor:

    def __init__(self, config):

        self.config = config

        self.monitored_processes = set(
            name.lower()
            for name in config.get(
                "monitored_processes",
                []
            )
        )

        self.cpu_threshold = float(
            config.get(
                "process_cpu_threshold",
                90.0
            )
        )

        self.memory_threshold = float(
            config.get(
                "process_memory_threshold",
                80.0
            )
        )

        self.previous_processes = set()

    def get_processes(self):

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

                pid = info["pid"]

                name = (
                    info["name"]
                    or "Unknown"
                )

                cpu = process.cpu_percent(
                    interval=0.05
                )

                memory = (
                    info.get(
                        "memory_percent",
                        0.0
                    )
                    or 0.0
                )

                status = info.get(
                    "status",
                    "unknown"
                )

                username = (
                    info.get(
                        "username",
                        ""
                    )
                    or ""
                )

                processes.append({
                    "pid": pid,
                    "name": name,
                    "status": status,
                    "cpu_percent": round(
                        cpu,
                        2
                    ),
                    "memory_percent": round(
                        memory,
                        2
                    ),
                    "username": username
                })

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess
            ):

                continue

        return processes

    def monitor(self):

        processes = self.get_processes()

        current_processes = set()

        for process in processes:

            pid = process["pid"]

            name = process["name"]

            current_processes.add(pid)

            add_process_snapshot(
                pid,
                name,
                process["status"],
                process["cpu_percent"],
                process["memory_percent"],
                process["username"]
            )

            if (
                process["cpu_percent"]
                >= self.cpu_threshold
            ):

                message = (
                    f"Process {name} "
                    f"(PID {pid}) is using "
                    f"{process['cpu_percent']}% CPU."
                )

                logger.warning(message)

                add_event(
                    "HIGH_CPU",
                    name,
                    process["status"],
                    message,
                    process["cpu_percent"],
                    process["memory_percent"],
                    pid
                )

                add_alert(
                    "HIGH",
                    "CPU",
                    "High CPU Usage",
                    message
                )

            if (
                process["memory_percent"]
                >= self.memory_threshold
            ):

                message = (
                    f"Process {name} "
                    f"(PID {pid}) is using "
                    f"{process['memory_percent']}% memory."
                )

                logger.warning(message)

                add_event(
                    "HIGH_MEMORY",
                    name,
                    process["status"],
                    message,
                    process["cpu_percent"],
                    process["memory_percent"],
                    pid
                )

                add_alert(
                    "HIGH",
                    "MEMORY",
                    "High Memory Usage",
                    message
                )

            if (
                self.monitored_processes
                and
                name.lower()
                in self.monitored_processes
            ):

                if pid not in self.previous_processes:

                    message = (
                        f"Monitored process started: "
                        f"{name} "
                        f"(PID {pid})"
                    )

                    logger.info(message)

                    add_event(
                        "PROCESS_STARTED",
                        name,
                        process["status"],
                        message,
                        process["cpu_percent"],
                        process["memory_percent"],
                        pid
                    )

                    add_alert(
                        "INFO",
                        "PROCESS_STARTED",
                        "Monitored Process Started",
                        message
                    )

        terminated = (
            self.previous_processes
            -
            current_processes
        )

        for pid in terminated:

            message = (
                f"Process terminated: PID {pid}"
            )

            logger.info(message)

            add_event(
                "PROCESS_TERMINATED",
                str(pid),
                "terminated",
                message,
                pid=pid
            )

        self.previous_processes = (
            current_processes
        )

        return processes