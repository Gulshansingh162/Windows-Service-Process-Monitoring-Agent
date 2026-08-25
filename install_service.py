import sys
import subprocess


def main():

    print("Installing Windows Monitoring Agent...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "service.windows_service",
            "install"
        ],
        check=True
    )

    print()
    print("Service installed successfully.")
    print()
    print(
        "Start it with: python start_service.py"
    )


if __name__ == "__main__":
    main()