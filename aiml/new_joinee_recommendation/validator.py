from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, date
import re

from .utils import get_logger

logger = get_logger("validator")

def parse_strict_calendar_date(val: Any) -> Tuple[Optional[date], Optional[str]]:
    """
    Strictly parses and validates calendar dates.
    Returns (date_obj, None) on success or (None, error_message) on failure.
    Accurately validates leap years (e.g. 29-02-2024 valid, 29-02-2023 invalid)
    and valid days per month (e.g. 31-04-2024 invalid).
    """
    if val is None or str(val).strip() in ("", "None", "nan", "null", "undefined"):
        return None, None

    if isinstance(val, datetime):
        return val.date(), None
    if isinstance(val, date):
        return val, None

    s = str(val).strip()
    # Normalize separators
    s_clean = re.sub(r"[/. ]", "-", s)

    # Try standard patterns
    patterns = [
        ("%Y-%m-%d", r"^\d{4}-\d{1,2}-\d{1,2}$"),
        ("%d-%m-%Y", r"^\d{1,2}-\d{1,2}-\d{4}$"),
    ]

    for fmt, regex in patterns:
        if re.match(regex, s_clean):
            try:
                dt = datetime.strptime(s_clean, fmt)
                # Verify exact component equality to prevent strptime silent rollover (e.g. 31 April -> 1 May)
                parts = [int(p) for p in s_clean.split("-")]
                if fmt == "%Y-%m-%d":
                    if dt.year != parts[0] or dt.month != parts[1] or dt.day != parts[2]:
                        return None, f"Invalid calendar date '{s}' (day/month out of range for year {parts[0]})."
                else:
                    if dt.year != parts[2] or dt.month != parts[1] or dt.day != parts[0]:
                        return None, f"Invalid calendar date '{s}' (day/month out of range for year {parts[2]})."
                return dt.date(), None
            except ValueError as ve:
                return None, f"Invalid calendar date '{s}': {str(ve)}."

    # Try ISO timestamp format
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.date(), None
    except Exception:
        pass

    return None, f"Unrecognized date format '{s}'. Please use DD-MM-YYYY or YYYY-MM-DD."


def validate_recommendation_payload(
    personnel_dict: Dict[str, Any],
    units_list: Optional[List[Dict[str, Any]]] = None,
    ref_date: Optional[date] = None
) -> Tuple[bool, List[str]]:
    """
    Comprehensive server-side validator for AI recommendation inputs.
    Validates:
    - Trade and Rank existence
    - Date of Birth, Date of Enrollment, Date of TOS, Date of TORS
    - Military service age (min 17 years at enrollment)
    - Chronology (DOB <= Enrollment <= TOS <= TORS <= Today)
    - Previous unit postings (From <= To <= Today, From >= Enrollment, no overlapping intervals)
    """
    errors = []
    if ref_date is None:
        ref_date = date.today()

    # 1. Mandatory Trade & Rank
    trade = str(personnel_dict.get("trade", "")).strip()
    rank = str(personnel_dict.get("rank", "")).strip()

    if not trade or trade.upper() in ("NONE", "NAN", "NULL", "UNKNOWN", ""):
        errors.append("Trade Specialty is required.")
    if not rank or rank.upper() in ("NONE", "NAN", "NULL", "UNKNOWN", ""):
        errors.append("Rank is required.")

    # 2. Date Parsing
    raw_dob = personnel_dict.get("date_of_birth")
    raw_enroll = personnel_dict.get("date_of_enrollment")
    raw_tos = personnel_dict.get("date_of_tos")
    raw_tors = personnel_dict.get("date_of_tors")

    dob, err_dob = parse_strict_calendar_date(raw_dob)
    if err_dob:
        errors.append(f"Date of Birth: {err_dob}")

    enroll_date, err_enroll = parse_strict_calendar_date(raw_enroll)
    if err_enroll:
        errors.append(f"Date of Enrollment: {err_enroll}")

    tos_date, err_tos = parse_strict_calendar_date(raw_tos)
    if err_tos:
        errors.append(f"Date of TOS: {err_tos}")

    tors_date, err_tors = parse_strict_calendar_date(raw_tors)
    if err_tors:
        errors.append(f"Date of TORS: {err_tors}")

    # 3. Personnel Dates Validations
    if dob and dob > ref_date:
        errors.append(f"Date of Birth ({dob.strftime('%d-%m-%Y')}) cannot be in the future.")

    if enroll_date:
        if enroll_date > ref_date:
            errors.append(f"Date of Enrollment ({enroll_date.strftime('%d-%m-%Y')}) cannot be in the future.")
        if dob:
            if enroll_date <= dob:
                errors.append(f"Date of Enrollment ({enroll_date.strftime('%d-%m-%Y')}) cannot be before or equal to Date of Birth ({dob.strftime('%d-%m-%Y')}).")
            else:
                # Minimum military enrollment age check (17 years)
                age_at_enroll = (enroll_date - dob).days / 365.25
                if age_at_enroll < 17.0:
                    errors.append(f"Invalid Date of Enrollment: Age at enrollment must be at least 17 years (calculated {age_at_enroll:.1f} years from DOB {dob.strftime('%d-%m-%Y')}).")

    if tos_date:
        if tos_date > ref_date:
            errors.append(f"Date of TOS ({tos_date.strftime('%d-%m-%Y')}) cannot be in the future.")
        if enroll_date and tos_date < enroll_date:
            errors.append(f"Date of TOS ({tos_date.strftime('%d-%m-%Y')}) cannot be before Date of Enrollment ({enroll_date.strftime('%d-%m-%Y')}).")

    if tors_date:
        if tos_date and tors_date < tos_date:
            errors.append(f"Date of TORS ({tors_date.strftime('%d-%m-%Y')}) cannot be before Date of TOS ({tos_date.strftime('%d-%m-%Y')}).")
        if enroll_date and tors_date < enroll_date:
            errors.append(f"Date of TORS ({tors_date.strftime('%d-%m-%Y')}) cannot be before Date of Enrollment ({enroll_date.strftime('%d-%m-%Y')}).")

    # 4. Previous Units History Validations
    if units_list and isinstance(units_list, list):
        parsed_intervals = []

        for idx, u_entry in enumerate(units_list, 1):
            if not isinstance(u_entry, dict):
                continue

            u_name = str(u_entry.get("unit", "")).strip()
            raw_f = u_entry.get("from_date")
            raw_t = u_entry.get("to_date")
            duty_perf = str(u_entry.get("duty_performed", "")).strip()

            # If row is partially filled, require all key fields
            if u_name or raw_f or raw_t or duty_perf:
                if not u_name:
                    errors.append(f"Unit row #{idx}: Unit Name is required.")

                if not raw_f and not raw_t:
                    errors.append(f"Unit row #{idx} ('{u_name or 'Unit'}'): Please provide both From Date and To Date.")
                    continue
                elif not raw_f or not raw_t:
                    errors.append(f"Unit row #{idx} ('{u_name or 'Unit'}'): Please provide both From Date and To Date (partial date entry not permitted).")
                    continue

                f_date, err_f = parse_strict_calendar_date(raw_f)
                t_date, err_t = parse_strict_calendar_date(raw_t)

                if err_f:
                    errors.append(f"Unit row #{idx} ('{u_name}'): From Date - {err_f}")
                if err_t:
                    errors.append(f"Unit row #{idx} ('{u_name}'): To Date - {err_t}")

                if f_date and t_date:
                    if f_date > ref_date:
                        errors.append(f"Unit '{u_name}': From Date ({f_date.strftime('%d-%m-%Y')}) cannot be in the future.")
                    if t_date > ref_date:
                        errors.append(f"Unit '{u_name}': To Date ({t_date.strftime('%d-%m-%Y')}) cannot be in the future.")

                    if f_date > t_date:
                        errors.append(f"Unit '{u_name}': To Date ({t_date.strftime('%d-%m-%Y')}) cannot be earlier than From Date ({f_date.strftime('%d-%m-%Y')}).")

                    if enroll_date and f_date < enroll_date:
                        errors.append(f"Unit '{u_name}': Previous posting From Date ({f_date.strftime('%d-%m-%Y')}) cannot begin before Date of Enrollment ({enroll_date.strftime('%d-%m-%Y')}).")

                    parsed_intervals.append({
                        "row": idx,
                        "unit": u_name,
                        "from": f_date,
                        "to": t_date
                    })

        # 5. Overlapping Postings Check
        for i in range(len(parsed_intervals)):
            for j in range(i + 1, len(parsed_intervals)):
                item_a = parsed_intervals[i]
                item_b = parsed_intervals[j]

                # Two intervals [F1, T1] and [F2, T2] overlap if max(F1, F2) < min(T1, T2)
                overlap_start = max(item_a["from"], item_b["from"])
                overlap_end = min(item_a["to"], item_b["to"])

                if overlap_start < overlap_end:
                    errors.append(
                        f"Overlapping Posting Periods: Unit '{item_a['unit']}' ({item_a['from'].strftime('%d-%m-%Y')} to {item_a['to'].strftime('%d-%m-%Y')}) "
                        f"overlaps with Unit '{item_b['unit']}' ({item_b['from'].strftime('%d-%m-%Y')} to {item_b['to'].strftime('%d-%m-%Y')})."
                    )

    is_valid = len(errors) == 0
    return is_valid, errors
