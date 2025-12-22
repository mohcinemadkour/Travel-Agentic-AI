import os
import singlestoredb as s2
from dotenv import load_dotenv

load_dotenv()


def get_conn():
    """
    Create and return a SingleStore database connection using
    S2_HOST, S2_USER, S2_PASSWORD, S2_DB from .env.
    """
    host = os.getenv("S2_HOST")
    user = os.getenv("S2_USER")
    password = os.getenv("S2_PASSWORD")
    db = os.getenv("S2_DB")

    if not all([host, user, password, db]):
        # Missing DB credentials — treat as unavailable in deployed environments
        # (platforms like Render will provide env vars via their dashboard)
        print("[singlestore_client] Missing one of S2_HOST, S2_USER, S2_PASSWORD, S2_DB; SingleStore disabled.")
        return None

    # Allow S2_HOST to include an explicit port (e.g. host:3306).
    port = 3306
    hostname = host
    if host and ("://" in host):
        # strip any scheme like tcp:// or mysql://
        hostname = host.split("://", 1)[1]

    if hostname and ":" in hostname:
        # split on the last ':' to support potential IPv6 addresses
        h, sep, p = hostname.rpartition(":")
        if p.isdigit():
            hostname = h or p  # if rpartition returned empty left-side, keep p
            try:
                port = int(p)
            except ValueError:
                port = 3306

    try:
        conn = s2.connect(
            host=hostname,
            user=user,
            password=password,
            database=db,
            port=port,
        )
        return conn
    except Exception as e:
        # Don't raise in deployed apps; return None to allow graceful degradation.
        # Log a clear message for diagnostics.
        print(f"[singlestore_client] Failed to connect to SingleStore (host={hostname!r}, port={port}): {e}")
        return None