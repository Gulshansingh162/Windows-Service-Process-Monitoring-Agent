import sqlite3

from datetime import datetime

from .config import (
    DATABASE_FILE,
    ensure_directories
)


def get_connection():

    ensure_directories()

    connection = sqlite3.connect(
        DATABASE_FILE,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            name TEXT,
            status TEXT,
            cpu_percent REAL,
            memory_percent REAL,
            pid INTEGER,
            message TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS process_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            pid INTEGER,
            name TEXT,
            status TEXT,
            cpu_percent REAL,
            memory_percent REAL,
            username TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            name TEXT,
            display_name TEXT,
            status TEXT,
            start_type TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            severity TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            acknowledged INTEGER DEFAULT 0
        )
    """)

    connection.commit()

    connection.close()


def add_event(
    event_type,
    name,
    status,
    message,
    cpu_percent=None,
    memory_percent=None,
    pid=None
):

    connection = get_connection()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection.execute("""
        INSERT INTO events (
            timestamp,
            event_type,
            name,
            status,
            cpu_percent,
            memory_percent,
            pid,
            message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        event_type,
        name,
        status,
        cpu_percent,
        memory_percent,
        pid,
        message
    ))

    connection.commit()

    connection.close()


def add_alert(
    severity,
    alert_type,
    title,
    message
):

    connection = get_connection()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection.execute("""
        INSERT INTO alerts (
            timestamp,
            severity,
            alert_type,
            title,
            message,
            acknowledged
        )
        VALUES (?, ?, ?, ?, ?, 0)
    """, (
        timestamp,
        severity,
        alert_type,
        title,
        message
    ))

    connection.commit()

    connection.close()


def acknowledge_alert(alert_id):

    connection = get_connection()

    connection.execute("""
        UPDATE alerts
        SET acknowledged = 1
        WHERE id = ?
    """, (alert_id,))

    connection.commit()

    connection.close()


def add_process_snapshot(
    pid,
    name,
    status,
    cpu_percent,
    memory_percent,
    username
):

    connection = get_connection()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection.execute("""
        INSERT INTO process_snapshots (
            timestamp,
            pid,
            name,
            status,
            cpu_percent,
            memory_percent,
            username
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        pid,
        name,
        status,
        cpu_percent,
        memory_percent,
        username
    ))

    connection.commit()

    connection.close()


def add_service_snapshot(
    name,
    display_name,
    status,
    start_type
):

    connection = get_connection()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection.execute("""
        INSERT INTO service_snapshots (
            timestamp,
            name,
            display_name,
            status,
            start_type
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        timestamp,
        name,
        display_name,
        status,
        start_type
    ))

    connection.commit()

    connection.close()


def get_recent_events(limit=100):

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM events
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_recent_alerts(limit=50):

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM alerts
        WHERE acknowledged = 0
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_alert_count():

    connection = get_connection()

    row = connection.execute("""
        SELECT COUNT(*) AS count
        FROM alerts
        WHERE acknowledged = 0
    """).fetchone()

    connection.close()

    return row["count"]


def get_recent_processes(limit=100):

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM process_snapshots
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_recent_services(limit=100):

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM service_snapshots
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]