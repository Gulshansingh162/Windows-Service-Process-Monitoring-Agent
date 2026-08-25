import sys
import subprocess


def main():

    print("Starting Windows Monitoring Agent...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "service.windows_service",
            "start"
        ],
        check=True
    )

    print()
    print("Service started successfully.")
    print(
        "Dashboard: http://127.0.0.1:5000"
    )


if __name__ == "__main__":
    main()