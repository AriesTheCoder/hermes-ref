"""Lazy profile-local journal with non-destructive legacy migration."""
from __future__ import annotations

import hashlib
import sqlite3
import threading
from contextlib import contextmanager



class WorkspaceStore:
    def __init__(self):
        self.lock = threading.RLock()
        self.ready = set()

    @staticmethod
    def session_key(session_id):
        return hashlib.sha256(str(session_id).encode()).hexdigest()

    @contextmanager
    def connect(self):
        # These are documented public helpers. Resolve the active profile on
        # every call rather than retaining a home from plugin registration.
        from plugins.plugin_storage import plugin_data_dir, plugin_db

        root = plugin_data_dir('hermes-ref')
        path = root / 'workspace.sqlite3'
        with self.lock:
            db = plugin_db('hermes-ref', 'workspace.sqlite3')
            try:
                db.execute('PRAGMA busy_timeout=10000')
                # Initialise once per journal file; a deleted or replaced file
                # has a new inode and is initialised again.
                identity = (str(path), path.stat().st_ino)
                if identity not in self.ready:
                    self.initialise(db, root, path)
                    self.ready.add(identity)
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                db.close()

    @staticmethod
    def initialise(db, root, path):
        # The 0700 directory is the access boundary: SQLite recreates -wal/-shm
        # sidecars with the process umask whenever the last connection closes.
        root.chmod(0o700)
        legacy = root.parent.parent / 'plugin-state' / 'hermes-ref' / 'workspace.sqlite3'
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS sessions (session TEXT PRIMARY KEY, plan TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS attempts (key TEXT PRIMARY KEY, status TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        version = db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        if version and version[0] != '1':
            raise RuntimeError('Unsupported workspace journal schema; preserve the database and use a compatible plugin')
        migrated = db.execute("SELECT value FROM metadata WHERE key='legacy_imported'").fetchone()
        if not migrated:
            if legacy.exists():
                # Read-only source; existing destination rows win. Import
                # bindings and attempt claims in the same transaction.
                source = sqlite3.connect(legacy.resolve().as_uri() + '?mode=ro', uri=True)
                try:
                    db.executemany('INSERT OR IGNORE INTO sessions VALUES (?, ?)', source.execute('SELECT session, plan FROM sessions'))
                    db.executemany('INSERT OR IGNORE INTO attempts VALUES (?, ?)', source.execute('SELECT key, status FROM attempts'))
                finally:
                    source.close()
            db.execute("INSERT INTO metadata VALUES ('legacy_imported', '1')")
        db.execute("INSERT OR IGNORE INTO metadata VALUES ('schema_version', '1')")
        db.commit()
        path.chmod(0o600)

    def current(self, session_id):
        with self.connect() as db:
            row = db.execute('SELECT plan FROM sessions WHERE session=?', (self.session_key(session_id),)).fetchone()
        return row[0] if row else None

    def bind(self, session_id, plan):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO sessions VALUES (?, ?)', (self.session_key(session_id), plan))

    def claim(self, key, legacy_key=None):
        with self.connect() as db:
            if legacy_key and legacy_key != key and db.execute('SELECT 1 FROM attempts WHERE key=?', (legacy_key,)).fetchone():
                return False
            return bool(db.execute("INSERT OR IGNORE INTO attempts VALUES (?, 'creating')", (key,)).rowcount)

    def verified(self, key):
        with self.connect() as db:
            db.execute("UPDATE attempts SET status='verified' WHERE key=?", (key,))
