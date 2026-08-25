import os
import sys
import time
import threading

import win32event
import win32service
import win32serviceutil
import servicemanager

from app.config import load_config
from app.database import initialize_database
from app.event_logger import logger
from app.process_monitor import ProcessMonitor
from app.service_monitor import ServiceMonitor
from app.api import start_api


class MonitoringAgentService(
    win32serviceutil.ServiceFramework
):

    _svc_name_ = "WindowsMonitoringAgent"

    _svc_display_name_ = (
        "Windows Service & Process Monitoring Agent"
    )

    _svc_description_ = (
        "Monitors Windows processes, "
        "system resources and Windows services."
    )

    def __init__(self, args):

        win32serviceutil.ServiceFramework.__init__(
            self,
            args
        )

        self.stop_event = win32event.CreateEvent(
            None,
            0,
            0,
            None
        )

        self.running = True

    def SvcStop(self):

        self.ReportServiceStatus(
            win32service.SERVICE_STOP_PENDING
        )

        logger.info(
            "Monitoring Agent stop requested."
        )

        self.running = False

        win32event.SetEvent(
            self.stop_event
        )

    def SvcDoRun(self):

        servicemanager.LogInfoMsg(
            "Windows Monitoring Agent started."
        )

        logger.info(
            "Windows Monitoring Agent started."
        )

        self.main()

    def main(self):

        initialize_database()

        config = load_config()

        process_monitor = ProcessMonitor(
            config
        )

        service_monitor = ServiceMonitor(
            config
        )

        # Start dashboard/API
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

        logger.info(
            f"Monitoring interval: {interval} seconds"
        )

        while self.running:

            try:

                process_monitor.monitor()

                service_monitor.monitor()

            except Exception as error:

                logger.exception(
                    f"Monitoring cycle failed: {error}"
                )

            result = win32event.WaitForSingleObject(
                self.stop_event,
                interval * 1000
            )

            if result == win32event.WAIT_OBJECT_0:

                break

        logger.info(
            "Windows Monitoring Agent stopped."
        )


if __name__ == "__main__":

    win32serviceutil.HandleCommandLine(
        MonitoringAgentService
    )