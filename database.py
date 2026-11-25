import sqlite3
from config import DATABASE_NAME


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_column(conn, table_name, column_name, column_def):
    existing = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in existing:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL,
                glucose REAL NOT NULL,
                haemoglobin REAL NOT NULL,
                cholesterol REAL NOT NULL,
                remarks TEXT DEFAULT '',
                record_source TEXT DEFAULT 'Manual',
                validation_status TEXT DEFAULT 'Valid',
                validation_errors TEXT DEFAULT '',
                ai_analyzed_at TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Safe schema upgrades for existing databases
        _ensure_column(conn, "patients", "record_source", "TEXT DEFAULT 'Manual'")
        _ensure_column(conn, "patients", "validation_status", "TEXT DEFAULT 'Valid'")
        _ensure_column(conn, "patients", "validation_errors", "TEXT DEFAULT ''")
        _ensure_column(conn, "patients", "ai_analyzed_at", "TEXT DEFAULT ''")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                remarks TEXT NOT NULL,
                model_name TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        """)


def create_patient(data):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO patients (
                full_name,
                dob,
                email,
                glucose,
                haemoglobin,
                cholesterol,
                remarks,
                record_source,
                validation_status,
                validation_errors,
                ai_analyzed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["full_name"],
            data["dob"],
            data["email"],
            float(data["glucose"]),
            float(data["haemoglobin"]),
            float(data["cholesterol"]),
            data.get("remarks", ""),
            data.get("record_source", "Manual"),
            data.get("validation_status", "Valid"),
            data.get("validation_errors", ""),
            data.get("ai_analyzed_at", ""),
        ))

        return cursor.lastrowid


def get_all_patients():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM patients
            ORDER BY id DESC
        """)

        return [dict(row) for row in cursor.fetchall()]


def get_patient_by_id(patient_id):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM patients
            WHERE id = ?
        """, (patient_id,))

        row = cursor.fetchone()
        return dict(row) if row else None


def update_patient(patient_id, data):
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE patients
            SET
                full_name = ?,
                dob = ?,
                email = ?,
                glucose = ?,
                haemoglobin = ?,
                cholesterol = ?,
                remarks = ?,
                validation_status = COALESCE(?, validation_status),
                validation_errors = COALESCE(?, validation_errors),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data["full_name"],
            data["dob"],
            data["email"],
            float(data["glucose"]),
            float(data["haemoglobin"]),
            float(data["cholesterol"]),
            data.get("remarks", ""),
            data.get("validation_status"),
            data.get("validation_errors"),
            patient_id,
        ))

        return cursor.rowcount > 0


def update_patient_validation(patient_id, status, errors_text):
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE patients
            SET
                validation_status = ?,
                validation_errors = ?
            WHERE id = ?
        """, (status, errors_text, patient_id))
        return cursor.rowcount > 0


def delete_patient(patient_id):
    with get_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM patients
            WHERE id = ?
        """, (patient_id,))

        return cursor.rowcount > 0


def get_patient_count():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM patients
        """)

        return cursor.fetchone()[0]


def save_ai_analysis(patient_id, remarks, model_name=""):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO ai_analyses (patient_id, remarks, model_name)
            VALUES (?, ?, ?)
        """, (patient_id, remarks, model_name))

        conn.execute("""
            UPDATE patients
            SET
                remarks = ?,
                ai_analyzed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (remarks, patient_id))


def get_ai_analyses_for_patient(patient_id):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM ai_analyses
            WHERE patient_id = ?
            ORDER BY id DESC
        """, (patient_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_total_ai_analyses_count():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM ai_analyses
        """)
        history_count = cursor.fetchone()[0]
        if history_count > 0:
            return history_count

        # Fallback for records that have remarks without history rows
        cursor = conn.execute("""
            SELECT COUNT(*) FROM patients
            WHERE TRIM(COALESCE(remarks, '')) != ''
        """)
        return cursor.fetchone()[0]


def has_assignment_dataset():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM patients
            WHERE record_source = 'Assignment Import'
        """)
        return cursor.fetchone()[0] > 0


def delete_assignment_dataset():
    with get_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM patients
            WHERE record_source = 'Assignment Import'
        """)
        return cursor.rowcount


def import_assignment_records(records, replace_existing=False):
    """Import assignment records unchanged into SQLite."""
    with get_connection() as conn:
        if replace_existing:
            conn.execute("""
                DELETE FROM patients
                WHERE record_source = 'Assignment Import'
            """)

        inserted_ids = []
        for rec in records:
            cursor = conn.execute("""
                INSERT INTO patients (
                    full_name,
                    dob,
                    email,
                    glucose,
                    haemoglobin,
                    cholesterol,
                    remarks,
                    record_source,
                    validation_status,
                    validation_errors
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Assignment Import', ?, ?)
            """, (
                rec["full_name"],
                rec["dob"],
                rec["email"],
                float(rec["glucose"]),
                float(rec["haemoglobin"]),
                float(rec["cholesterol"]),
                rec.get("remarks", ""),
                rec.get("validation_status", "Valid"),
                rec.get("validation_errors", ""),
            ))
            inserted_ids.append(cursor.lastrowid)

        return inserted_ids
