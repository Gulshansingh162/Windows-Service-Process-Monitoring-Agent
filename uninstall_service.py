import sys
import subprocess


def main():

    print("Removing Windows Monitoring Agent...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "service.windows_service",
            "remove"
        ],
        check=True
    )

    print()
    print("Service removed successfully.")


if __name__ == "__main__":
    main()