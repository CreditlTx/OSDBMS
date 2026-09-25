import sqlite3
import os
import threading
from datetime import datetime


DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "database.db")


_thread_local = threading.local()


def get_connection():
    """
    Get a database connection for the current thread.
    
    WHY THREAD-LOCAL:
        SQLite in Python's default mode does not allow a connection created
        in one thread to be used in another. We use threading.local() to give
        each thread its own connection. This is a common pattern in
        multi-threaded database applications.
    
    Returns:
        sqlite3.Connection: A connection specific to the calling thread.
    """
    if not hasattr(_thread_local, "connection") or _thread_local.connection is None:
        _thread_local.connection = sqlite3.connect(DATABASE_PATH, timeout=10)
        _thread_local.connection.row_factory = sqlite3.Row
        _thread_local.connection.execute("PRAGMA foreign_keys = ON")
    return _thread_local.connection


def close_connection():
    """Close the database connection for the current thread."""
    if hasattr(_thread_local, "connection") and _thread_local.connection is not None:
        _thread_local.connection.close()
        _thread_local.connection = None