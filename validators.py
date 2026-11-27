from collections import Counter
from datetime import datetime, date
import math
from email_validator import validate_email, EmailNotValidError


DATE_FORMAT = "%d/%m/%Y"
SUPPORTED_DATE_FORMATS = ("%d/%m/%Y", "%d.%m.%Y")

ASSIGNMENT_DATASET = [
    {
        "full_name": "Robyn Pears",
        "dob": "28.01.1960",
        "email": "robyn@gmail.com",
        "glucose": 232,
        "haemoglobin": 13.5,
        "cholesterol": 180,
    },
    {
        "full_name": "John Hunter",
        "dob": "10.12.1990",
        "email": "hunter@gmail",
        "glucose": 94,
        "haemoglobin": 15,
        "cholesterol": 200,
    },
    {
        "full_name": "Darryl Tim",
        "dob": "12.11.1993",
        "email": "timd@smh.com.au",
        "glucose": 240,
        "haemoglobin": 18.6,
        "cholesterol": 326,
    },
    {
        "full_name": "Peter Larry",
        "dob": "31.11.2001",
        "email": "Larry@hotmail.com",
        "glucose": 88,
        "haemoglobin": 11.5,
        "cholesterol": 165,
    },
    {
        "full_name": "Sam Kerr",
        "dob": "09.12.2006",
        "email": "sam@news.com.au",
        "glucose": 198,
        "haemoglobin": 8.9,
        "cholesterol": 192,
    },
    {
        "full_name": "Robyn Pears",
        "dob": "28.01.1960",
        "email": "robyn@gmail.com",
        "glucose": 232,
        "haemoglobin": 13.5,
        "cholesterol": 180,
    },
    {
        "full_name": "Madison XI",
        "dob": "12.09.1998",
        "email": "madison@hotmail.com",
        "glucose": 85,
        "haemoglobin": 7.6,
        "cholesterol": 163,
    },
    {
        "full_name": "Kris Wu",
        "dob": "19.10.2030",
        "email": "Kris.wu.gmail.com",
        "glucose": 79,
        "haemoglobin": 16.5,
        "cholesterol": 197,
    },
    {
        "full_name": "Tenille Singh",
        "dob": "30.11.1991",
        "email": "Tenille@yahoo.com",
        "glucose": 101,
        "haemoglobin": 15,
        "cholesterol": 310,
    },
    {
        "full_name": "Prem Kumar",
        "dob": "28.04.1990",
        "email": "prem@telstra.com",
        "glucose": 155,
        "haemoglobin": 12.5,
        "cholesterol": 265,
    },
]


def validate_name(name):
    if not name or not str(name).strip():
        return False, "Full name is required."

    if len(str(name).strip()) < 2:
        return False, "Name must contain at least 2 characters."

    return True, ""


def validate_email_address(email):
    if not email or not str(email).strip():
        return False, "Email address is required."

    try:
        validate_email(str(email).strip(), check_deliverability=False)
        return True, ""
    except EmailNotValidError:
        return False, "Invalid email format."


def validate_dob(dob, allow_dot_format=False):
    if not dob or not str(dob).strip():
        return False, "Date of birth is required."

    dob_str = str(dob).strip()
    formats = SUPPORTED_DATE_FORMATS if allow_dot_format else (DATE_FORMAT,)

    for fmt in formats:
        try:
            parsed_date = datetime.strptime(dob_str, fmt).date()
            if parsed_date.strftime(fmt) != dob_str:
                continue
            if parsed_date > date.today():
                return False, "DOB is in the future."
            return True, ""
        except ValueError:
            continue

    if allow_dot_format:
        return False, "Date is not valid."
    return False, "Enter a valid date in DD/MM/YYYY format."


def validate_blood_values(glucose, haemoglobin, cholesterol):
    values = {
        "Glucose": glucose,
        "Haemoglobin": haemoglobin,
        "Cholesterol": cholesterol,
    }

    for field, value in values.items():
        try:
            numeric_value = float(value)

            if numeric_value <= 0:
                return False, f"{field} must be greater than zero."

        except (ValueError, TypeError):
            return False, f"{field} must be a numeric value."

    return True, ""


def validate_patient(data):
    checks = [
        validate_name(data.get("full_name", "")),
        validate_email_address(data.get("email", "")),
        validate_dob(data.get("dob", ""), allow_dot_format=False),
        validate_blood_values(
            data.get("glucose"),
            data.get("haemoglobin"),
            data.get("cholesterol"),
        ),
    ]

    for is_valid, error in checks:
        if not is_valid:
            return False, error

    return True, ""


def record_identity_key(record):
    return (
        str(record.get("full_name", "")).strip().lower(),
        str(record.get("dob", "")).strip(),
        str(record.get("email", "")).strip().lower(),
    )


def compute_duplicate_keys(records):
    counts = Counter(record_identity_key(rec) for rec in records)
    return {key for key, count in counts.items() if count > 1}


def evaluate_record_quality(record, duplicate_keys=None):
    """Evaluate a record's data quality without mutating it. Returns (status, reasons_list)."""
    reasons = []
    has_hard_error = False

    checks = [
        validate_name(record.get("full_name", "")),
        validate_email_address(record.get("email", "")),
        validate_dob(record.get("dob", ""), allow_dot_format=True),
        validate_blood_values(
            record.get("glucose"),
            record.get("haemoglobin"),
            record.get("cholesterol"),
        ),
    ]

    for is_valid, err in checks:
        if not is_valid:
            has_hard_error = True
            reasons.append(err)

    is_duplicate = duplicate_keys is not None and record_identity_key(record) in duplicate_keys
    if is_duplicate:
        reasons.append("Duplicate patient record detected.")

    if has_hard_error:
        return "Invalid", reasons
    if is_duplicate:
        return "Needs Review", reasons
    return "Valid", []


def parse_dob_for_editor(dob_str):
    """Parse DD/MM/YYYY or DD.MM.YYYY into a date object if valid, else None."""
    if not dob_str:
        return None
    text = str(dob_str).strip()
    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def analyze_name_and_email_duplicates(records):
    """
    Detect records with duplicate full_name or duplicate email (case-insensitive).
    Returns a dict with counts and annotated duplicate records.
    """
    name_counts = Counter(str(r.get("full_name", "")).strip().lower() for r in records if str(r.get("full_name", "")).strip())
    email_counts = Counter(str(r.get("email", "")).strip().lower() for r in records if str(r.get("email", "")).strip())

    dup_names = {k for k, v in name_counts.items() if v > 1}
    dup_emails = {k for k, v in email_counts.items() if v > 1}

    flagged = []
    for r in records:
        n_key = str(r.get("full_name", "")).strip().lower()
        e_key = str(r.get("email", "")).strip().lower()
        is_dup_name = n_key in dup_names
        is_dup_email = e_key in dup_emails
        if is_dup_name or is_dup_email:
            if is_dup_name and is_dup_email:
                reason = "Duplicate Name & Email"
            elif is_dup_name:
                reason = "Duplicate Name"
            else:
                reason = "Duplicate Email"
            item = dict(r)
            item["duplicate_reason"] = reason
            flagged.append(item)

    return {
        "duplicate_name_groups": len(dup_names),
        "duplicate_email_groups": len(dup_emails),
        "duplicate_name_records": sum(1 for r in records if str(r.get("full_name", "")).strip().lower() in dup_names),
        "duplicate_email_records": sum(1 for r in records if str(r.get("email", "")).strip().lower() in dup_emails),
        "flagged_records": flagged,
    }


BULK_FIELD_SPECS = [
    ("full_name", "Full Name", "Patient full name (min. 2 characters)"),
    ("dob", "DOB", "Date of birth (DD/MM/YYYY or DD.MM.YYYY, not in future)"),
    ("email", "Email", "Valid email address (e.g. patient@example.com)"),
    ("glucose", "Glucose", "Numeric value > 0"),
    ("haemoglobin", "Haemoglobin", "Numeric value > 0"),
    ("cholesterol", "Cholesterol", "Numeric value > 0"),
]

_COLUMN_ALIASES = {
    "full_name": {"full name", "fullname", "name", "patient name", "patient", "full_name"},
    "dob": {"dob", "date of birth", "dateofbirth", "birth date", "birthdate", "date_of_birth"},
    "email": {"email", "email address", "email id", "e-mail", "mail", "email_address"},
    "glucose": {"glucose", "blood glucose", "sugar", "fasting glucose", "glucose level"},
    "haemoglobin": {"haemoglobin", "hemoglobin", "hb", "hgb", "hb level"},
    "cholesterol": {"cholesterol", "total cholesterol", "chol", "cholesterol level"},
}


def auto_map_columns(uploaded_columns):
    """Best-effort mapping from uploaded file headers to HealthSync AI patient fields."""
    normalized = {str(col).strip().lower().replace("_", " "): str(col) for col in uploaded_columns}
    mapping = {}
    used_cols = set()

    for field_key, _, _ in BULK_FIELD_SPECS:
        aliases = _COLUMN_ALIASES[field_key]
        matched = None
        for norm_col, orig_col in normalized.items():
            if norm_col in aliases and orig_col not in used_cols:
                matched = orig_col
                break
        mapping[field_key] = matched
        if matched:
            used_cols.add(matched)

    return mapping


def _is_missing(val):
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    text = str(val).strip()
    return text == "" or text.lower() in ("nan", "none", "nat")


def _format_cell_text(val):
    if _is_missing(val):
        return ""
    return str(val).strip()


def _format_dob_cell(val):
    if _is_missing(val):
        return ""
    if isinstance(val, (datetime, date)):
        return val.strftime("%d/%m/%Y")
    return str(val).strip()


def validate_bulk_dataframe(df, column_mapping, existing_records):
    """
    Validate all rows of an uploaded DataFrame using column_mapping without mutating original values.
    Returns (valid_rows, invalid_rows, preview_rows).
    """
    existing_emails = {
        str(r.get("email", "")).strip().lower()
        for r in existing_records
        if str(r.get("email", "")).strip()
    }
    existing_names = {
        str(r.get("full_name", "")).strip().lower()
        for r in existing_records
        if str(r.get("full_name", "")).strip()
    }

    seen_file_emails = set()
    seen_file_names = set()

    valid_rows = []
    invalid_rows = []
    preview_rows = []

    for idx, row in df.iterrows():
        row_num = idx + 1
        raw_name = _format_cell_text(row[column_mapping["full_name"]]) if column_mapping.get("full_name") else ""
        raw_dob = _format_dob_cell(row[column_mapping["dob"]]) if column_mapping.get("dob") else ""
        raw_email = _format_cell_text(row[column_mapping["email"]]) if column_mapping.get("email") else ""
        raw_glucose = row[column_mapping["glucose"]] if column_mapping.get("glucose") else None
        raw_hb = row[column_mapping["haemoglobin"]] if column_mapping.get("haemoglobin") else None
        raw_chol = row[column_mapping["cholesterol"]] if column_mapping.get("cholesterol") else None

        errors = []

        ok_name, err_name = validate_name(raw_name)
        if not ok_name:
            errors.append(err_name)

        ok_email, err_email = validate_email_address(raw_email)
        if not ok_email:
            errors.append(err_email)

        ok_dob, err_dob = validate_dob(raw_dob, allow_dot_format=True)
        if not ok_dob:
            errors.append(err_dob)

        g_val = None if _is_missing(raw_glucose) else raw_glucose
        h_val = None if _is_missing(raw_hb) else raw_hb
        c_val = None if _is_missing(raw_chol) else raw_chol
        ok_blood, err_blood = validate_blood_values(g_val, h_val, c_val)
        if not ok_blood:
            errors.append(err_blood)

        name_key = raw_name.lower()
        email_key = raw_email.lower()

        if email_key and (email_key in existing_emails or email_key in seen_file_emails):
            errors.append(
                "Duplicate email detected (already exists in database or earlier in this file)."
            )
        if name_key and (name_key in existing_names or name_key in seen_file_names):
            errors.append(
                "Duplicate name detected (already exists in database or earlier in this file)."
            )

        status = "Valid" if not errors else "Invalid"
        record_payload = {
            "row_num": row_num,
            "full_name": raw_name,
            "dob": raw_dob,
            "email": raw_email,
            "glucose": "" if _is_missing(raw_glucose) else raw_glucose,
            "haemoglobin": "" if _is_missing(raw_hb) else raw_hb,
            "cholesterol": "" if _is_missing(raw_chol) else raw_chol,
            "status": status,
            "errors": "; ".join(errors),
        }

        preview_rows.append(record_payload)
        if not errors:
            seen_file_emails.add(email_key)
            seen_file_names.add(name_key)
            valid_rows.append(
                {
                    "full_name": raw_name,
                    "dob": raw_dob,
                    "email": raw_email,
                    "glucose": float(raw_glucose),
                    "haemoglobin": float(raw_hb),
                    "cholesterol": float(raw_chol),
                    "remarks": "",
                    "record_source": "Bulk Import",
                    "validation_status": "Valid",
                    "validation_errors": "",
                }
            )
        else:
            invalid_rows.append(record_payload)

    return valid_rows, invalid_rows, preview_rows


def suggest_correction_for_errors(errors_text):
    """Return human-readable suggested corrections for validation error strings."""
    text = (errors_text or "").lower()
    suggestions = []
    if "email" in text:
        suggestions.append("Update to a valid email format (e.g. name@domain.com).")
    if "future" in text:
        suggestions.append("Correct the birth year so DOB is not in the future.")
    if "date" in text:
        suggestions.append("Use a valid calendar date in DD/MM/YYYY format.")
    if "greater than zero" in text or "numeric" in text:
        suggestions.append("Enter positive numeric lab values (> 0).")
    if "duplicate" in text:
        suggestions.append("Review in Duplicate Review and remove or merge redundant entries.")
    if not suggestions:
        suggestions.append("Verify all required fields are complete and properly formatted.")
    return " ".join(suggestions)
