"""Excel/CSV -> listing dicts for Nuru.

Accepted formats
1. Hub format (same as hub_repo.xlsx):  path | title | url | details
     path    = "Jobs/<Category>" or "Scholarships/<Open now|Opens soon>"
     title   = "Company - Role"  (jobs)  or "Name (Org, Country)" (scholarships)
     details = free text; location + "Closes 16 Oct 2026" are auto-extracted
2. Rich format - any of these optional columns are used when present:
     type, title, company, category, job_type, work_mode, location,
     salary_min, salary_max, currency, deadline, description, url, apply_email
"""
import re
from datetime import datetime
import pandas as pd

DATE_RE = re.compile(r"(?:closes|deadline)\s+(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})", re.I)
MONTH_ONLY_RE = re.compile(r"(?:closes|deadline)\s+([A-Za-z]{3,9}\s+\d{4})", re.I)
JOB_TYPES = ["Full-time", "Part-time", "Internship", "Contract"]
WORK_MODES = ["On-site", "Remote", "Hybrid"]


def _s(v):
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()


def _num(v):
    try:
        return None if v is None or pd.isna(v) or str(v).strip() == "" else float(str(v).replace(",", ""))
    except ValueError:
        return None


def parse_date(text):
    text = _s(text)
    if not text:
        return None
    m = DATE_RE.search(text)
    candidate = m.group(1) if m else text
    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(candidate, fmt).date().isoformat()
        except ValueError:
            pass
    try:
        ts = pd.to_datetime(candidate, dayfirst=True)
        return None if pd.isna(ts) else ts.date().isoformat()
    except Exception:
        return None


def _infer_job_type(path_cat, title, details):
    blob = f"{title} {details}".lower()
    if "intern" in path_cat.lower() or "trainee" in blob or "internship" in blob:
        return "Internship"
    if "part-time" in blob or "part time" in blob or "50% time" in blob:
        return "Part-time"
    if "contract" in blob or "consultan" in blob:
        return "Contract"
    return "Full-time"


def _infer_mode(details):
    d = details.lower()
    if "remote" in d:
        return "Remote"
    if "hybrid" in d:
        return "Hybrid"
    return "On-site"


def _job_location(details):
    first = re.split(r"\.\s", details, maxsplit=1)[0].strip().rstrip(".")
    low = first.lower()
    if not first or "closes" in low or "no closing" in low or len(first) > 70 \
            or re.search(r"\b(post|role|apply|degree|diploma|bachelor)\b", low):
        return "Uganda"
    parts = [p.strip() for p in first.split(",")]
    parts = [p for p in parts if not re.search(r"full-time|part-time|on-site|remote|ugx|\d", p, re.I)]
    return ", ".join(parts) or "Uganda"


def _from_hub_row(row):
    path = _s(row.get("path"))
    title = _s(row.get("title"))
    url = _s(row.get("url"))
    details = _s(row.get("details"))
    top, _, cat = path.partition("/")
    kind = "Scholarship" if top.lower().startswith("schol") else "Job"
    company, location = "", ""
    if kind == "Job":
        if " - " in title:
            company, title = [x.strip() for x in title.split(" - ", 1)]
        location = _job_location(details)
        job_type = _infer_job_type(cat, title, details)
        work_mode = _infer_mode(details)
    else:
        m = re.search(r"\(([^()]*)\)\s*$", title)
        if m:
            inner = m.group(1)
            title = title[: m.start()].strip()
            if re.search(r"\bvia\b", inner) and "," in inner:
                location, company = [x.strip() for x in inner.split(",", 1)]
            elif "," in inner:
                company, location = [x.strip() for x in inner.rsplit(",", 1)]
            elif re.match(r"(university|government|ministry|college)", inner, re.I):
                company = inner.strip()
            else:
                location = inner.strip()
        if " - " in title:
            title, company = [x.strip() for x in title.split(" - ", 1)]
        job_type, work_mode = "Scholarship", "n/a"
    return dict(kind=kind, title=title, company=company, category=cat or "General",
                job_type=job_type, work_mode=work_mode, location=location,
                salary_min=None, salary_max=None, currency="UGX",
                deadline=parse_date(details), description=details, url=url, apply_email="")


def _from_rich_row(row):
    kind = _s(row.get("type")).title() or "Job"
    kind = "Scholarship" if kind.lower().startswith("schol") else "Job"
    jt = _s(row.get("job_type")).title().replace("Full Time", "Full-time").replace("Part Time", "Part-time")
    jt = {"Full-Time": "Full-time", "Part-Time": "Part-time"}.get(jt, jt) or ("Scholarship" if kind == "Scholarship" else "Full-time")
    wm = _s(row.get("work_mode")).title().replace("Onsite", "On-site") or "On-site"
    return dict(kind=kind, title=_s(row.get("title")), company=_s(row.get("company")),
                category=_s(row.get("category")) or "General", job_type=jt, work_mode=wm,
                location=_s(row.get("location")) or "Uganda",
                salary_min=_num(row.get("salary_min")), salary_max=_num(row.get("salary_max")),
                currency=_s(row.get("currency")) or "UGX", deadline=parse_date(row.get("deadline")),
                description=_s(row.get("description")) or _s(row.get("details")),
                url=_s(row.get("url")), apply_email=_s(row.get("apply_email")))


def parse_dataframe(df: pd.DataFrame):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    if "title" not in df.columns:
        raise ValueError("Sheet needs at least a 'title' column. Expected: path, title, url, details.")
    hub = "path" in df.columns and "details" in df.columns
    out = []
    for _, row in df.iterrows():
        if not _s(row.get("title")):
            continue
        out.append(_from_hub_row(row) if hub else _from_rich_row(row))
    return out


def read_file(file) -> pd.DataFrame:
    name = getattr(file, "name", str(file)).lower()
    return pd.read_csv(file) if name.endswith(".csv") else pd.read_excel(file)


def to_hub_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Listings -> the hub_repo.xlsx layout (path, title, url, details), so the sheet can be re-uploaded anywhere."""
    rows = []
    for _, r in df.iterrows():
        school = r["kind"] == "Scholarship"
        cat = r["category"] or ("Open now" if school else "General")
        path = f"{'Scholarships' if school else 'Jobs'}/{cat}"
        org, loc = _s(r["company"]), _s(r["location"])
        if school:
            tail = ", ".join(x for x in [org, loc] if x)
            title = f"{r['title']} ({tail})" if tail else r["title"]
        else:
            title = f"{org} - {r['title']}" if org else r["title"]
        details = _s(r["description"])
        if r["source"] == "form":          # form posts: add the location / closing-date lead-in the sheet uses
            lead = f"{loc or 'Uganda'}."
            if _s(r["deadline"]):
                lead += f" Closes {datetime.strptime(r['deadline'], '%Y-%m-%d').strftime('%d %b %Y')}."
            details = f"{lead} {details}".strip()
        rows.append({"path": path, "title": title, "url": _s(r["url"]), "details": details})
    return pd.DataFrame(rows, columns=["path", "title", "url", "details"])
