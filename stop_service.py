import sys
import subprocess


def main():

    print("Stopping Windows Monitoring Agent...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "service.windows_service",
            "stop"
        ],
        check=True
    )

    print()
    print("Service stopped successfully.")


if __name__ == "__main__":
    main()