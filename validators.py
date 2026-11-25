from collections import Counter
from datetime import datetime, date
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
