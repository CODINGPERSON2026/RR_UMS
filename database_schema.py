import builtins
def _log(*args, **kwargs):
    kwargs['flush'] = True
    builtins.print(*args, **kwargs)

"""
UMS Database Schema & Auto-Migration System
==========================================
Automatically ensures that the MySQL database and all required tables exist
whenever anyone runs the project.

Key Features:
1. Auto-creation at runtime:
   Whenever the app starts, any tables that do not exist in the database are
   automatically created with 'CREATE TABLE IF NOT EXISTS'.
2. Team collaboration:
   - If a developer creates a new table, they can add its SQL to `database_tables/<table_name>.sql`
     or register it in this file.
   - When any other developer pulls the code and runs the project, the new table
     is automatically detected and created in their database.
3. Developer CLI:
   - Run `python database_schema.py` to check and create missing tables.
   - Run `python database_schema.py --export` to export any tables created directly
     in MySQL Workbench into `database_tables/*.sql` files.
"""

import os
import sys
import re
import mysql.connector
from mysql.connector import Error

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TABLES_DIR = os.path.join(BASE_DIR, 'database_tables')

# Lazy import db_config to avoid circular dependencies
def _get_db_config():
    sys.path.insert(0, BASE_DIR)
    from db_config import get_db_config
    return get_db_config()

# Programmatically registered tables (runtime registry)
_REGISTERED_TABLES = {}

def register_table(table_name: str, create_sql: str):
    """
    Register a table definition programmatically.
    Can be called from blueprints or modules to declare custom tables.
    """
    clean_name = table_name.strip('`').strip().lower()
    _REGISTERED_TABLES[clean_name] = create_sql.strip()


def load_sql_files():
    """
    Loads all .sql files from the `database_tables` directory.
    Returns a dictionary of {table_name: create_table_sql}.
    """
    tables = {}
    if not os.path.exists(TABLES_DIR):
        return tables

    for filename in sorted(os.listdir(TABLES_DIR)):
        if filename.endswith('.sql'):
            table_name = filename[:-4].lower()
            file_path = os.path.join(TABLES_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sql = f.read().strip()
                # Remove leading comments
                clean_sql = re.sub(r'^--.*?\n', '', sql, flags=re.MULTILINE).strip()
                if clean_sql:
                    tables[table_name] = clean_sql
            except Exception as e:
                _log(f"[Database Schema Warning] Failed to read {filename}: {e}")

    return tables


def get_all_table_schemas():
    """
    Combines SQL files from `database_tables/` and any programmatically
    registered tables via `register_table()`.
    """
    schemas = load_sql_files()
    # Programmatic registrations take precedence / add new tables
    for name, sql in _REGISTERED_TABLES.items():
        schemas[name] = sql
    return schemas


def ensure_database_exists():
    """
    Connects to MySQL server (without selecting a database) and creates the
    target database if it does not already exist.
    """
    config = _get_db_config()
    db_name = config.get('database') or 'hrms'

    # Connection params without database
    server_config = {
        'host': config.get('host', 'localhost'),
        'user': config.get('user', 'root'),
        'password': config.get('password', ''),
        'port': config.get('port', 3306)
    }

    try:
        conn = mysql.connector.connect(**server_config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        cursor.close()
        conn.close()
        try:
            from db_config import _init_pool
            _init_pool()
        except Exception:
            pass
        return True
    except Error as e:
        _log(f"[Database Init Warning] Could not ensure database '{db_name}' exists: {e}")
        return False


def ensure_all_tables(conn=None, verbose=True):
    """
    Checks all defined tables against the current MySQL database.
    Creates any missing tables at runtime.
    Safe to call repeatedly on every application startup.
    """
    # 1. Ensure the database itself exists
    ensure_database_exists()

    should_close_conn = False
    if conn is None:
        try:
            sys.path.insert(0, BASE_DIR)
            from db_config import get_db_connection
            conn = get_db_connection()
            should_close_conn = True
        except Exception as e:
            _log(f"[Database Init Error] Could not connect to database: {e}")
            return False

    if not conn:
        _log("[Database Init Error] Database connection is unavailable.")
        return False

    cursor = None
    try:
        cursor = conn.cursor()

        # 2. Query currently existing tables in the database
        cursor.execute("SHOW TABLES")
        existing_tables = set(row[0].lower() for row in cursor.fetchall())

        # 3. Load all defined tables
        defined_tables = get_all_table_schemas()

        missing_tables = [t for t in defined_tables if t not in existing_tables]

        if not missing_tables:
            if verbose:
                _log(f"[Database Init] All {len(defined_tables)} tables verified (all exist).")
            return True

        if verbose:
            _log(f"[Database Init] Found {len(missing_tables)} missing table(s): {', '.join(missing_tables)}")
            _log("[Database Init] Creating missing tables...")

        # 4. Disable foreign key checks to allow creating tables in any order
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        created_count = 0
        error_count = 0

        for table_name in missing_tables:
            create_sql = defined_tables[table_name]
            # Ensure CREATE TABLE IF NOT EXISTS
            if not re.search(r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS', create_sql, re.IGNORECASE):
                create_sql = re.sub(r'CREATE\s+TABLE\s+', 'CREATE TABLE IF NOT EXISTS ', create_sql, count=1, flags=re.IGNORECASE)

            # Strip trailing semicolon for mysql-connector execution
            exec_sql = create_sql.strip()
            if exec_sql.endswith(';'):
                exec_sql = exec_sql[:-1]

            try:
                cursor.execute(exec_sql)
                created_count += 1
                if verbose:
                    _log(f"  [+] Created table: `{table_name}`")
            except Error as e:
                error_count += 1
                _log(f"  [-] Failed to create table `{table_name}`: {e}")

        # 5. Re-enable foreign key checks and commit
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()

        # 6. Post-create hooks (e.g. seed pending_cases default rows if pending_cases was created)
        if 'pending_cases' in missing_tables:
            try:
                from blueprints.pending_cases import ensure_default_cases
                ensure_default_cases(cursor, conn)
                if verbose:
                    _log("  [+] Seeded default case types for `pending_cases`")
            except Exception as seed_err:
                pass

        if verbose:
            _log(f"[Database Init] Finished: {created_count} table(s) created, {error_count} error(s).")

        return error_count == 0

    except Exception as e:
        _log(f"[Database Init Error] Error during table verification: {e}")
        return False

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if should_close_conn and conn:
            try:
                conn.close()
            except Exception:
                pass


def export_tables_from_db():
    """
    Developer helper: Inspects the connected MySQL database,
    retrieves 'SHOW CREATE TABLE' for all tables, and writes/updates
    their .sql files into the `database_tables/` directory.
    Useful when a developer creates or modifies tables in MySQL Workbench
    and wants to commit the updated schemas to git.
    """
    sys.path.insert(0, BASE_DIR)
    from db_config import get_db_connection

    conn = get_db_connection()
    if not conn:
        _log("Failed to connect to database for export.")
        return

    os.makedirs(TABLES_DIR, exist_ok=True)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]

    _log(f"Exporting {len(tables)} tables from MySQL into `{TABLES_DIR}`...")

    count = 0
    for t in tables:
        try:
            cursor.execute(f"SHOW CREATE TABLE `{t}`")
            sql = cursor.fetchone()[1]

            # Make idempotent
            sql = re.sub(r'^CREATE TABLE\s+', 'CREATE TABLE IF NOT EXISTS ', sql, flags=re.IGNORECASE)
            sql = re.sub(r'\s+AUTO_INCREMENT=\d+', '', sql).strip()
            if not sql.endswith(';'):
                sql += ';'

            file_path = os.path.join(TABLES_DIR, f"{t.lower()}.sql")
            header = f"-- Table schema for `{t}`\n-- Auto-created if not exists at runtime\n\n"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(header + sql + "\n")
            count += 1
        except Exception as e:
            _log(f"Failed to export `{t}`: {e}")

    cursor.close()
    conn.close()
    _log(f"Export completed: {count} table schema file(s) written to `{TABLES_DIR}`.")


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--export' in args:
        export_tables_from_db()
    else:
        _log("==================================================")
        _log("UMS DATABASE SCHEMA & AUTO-MIGRATION RUNNER")
        _log("==================================================")
        schemas = get_all_table_schemas()
        _log(f"Total defined table files: {len(schemas)}")
        ensure_all_tables(verbose=True)
        _log("==================================================")
