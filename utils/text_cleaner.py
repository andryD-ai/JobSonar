"""Text cleaning, salary parsing, and hashing utilities."""
import re
import hashlib
import unicodedata
from typing import Tuple, Optional
from bs4 import BeautifulSoup


def strip_accents(text: str) -> str:
    """Removes Vietnamese accents for normalized search/comparison."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")


REMOTE_KEYWORDS = [
    "remote", "tu xa", "từ xa", "work from home", "wfh", "online",
    "telecommute", "truc tuyen", "trực tuyến", "lam tai nha", "làm tại nhà", "anywhere"
]


def is_remote_job(title: Optional[str], location: Optional[str], description: Optional[str] = None) -> bool:
    """
    Determines if a job posting is a remote/online position.
    Checks location, title, and optionally description for remote indicators.
    """
    corpus = f"{title or ''} {location or ''}"
    norm = strip_accents(corpus.lower())
    for kw in REMOTE_KEYWORDS:
        clean_kw = strip_accents(kw)
        if clean_kw in norm:
            return True

    if description:
        norm_desc = strip_accents(description.lower()[:1000])
        for kw in ["100% remote", "fully remote", "remote toan thoi gian", "lam viec tu xa", "work from anywhere"]:
            if strip_accents(kw) in norm_desc:
                return True

    return False


def get_job_type(title: Optional[str], description: Optional[str] = None, benefits: Optional[str] = None) -> str:
    """
    Infers job employment type: 'Intern / Fresher', 'Part-time', 'Contract / Freelance', or 'Full-time'.
    """
    text = strip_accents(f"{title or ''} {description or ''} {benefits or ''}").lower()
    if any(k in text for k in ["intern", "thuc tap", "trainee", "fresher"]):
        return "Intern / Fresher"
    if any(k in text for k in ["part-time", "parttime", "ban thoi gian", "ban thoi vu"]):
        return "Part-time"
    if any(k in text for k in ["contract", "freelance", "hop dong", "thoi vu", "contractor", "1099"]):
        return "Contract / Freelance"
    return "Full-time"


def get_workplace_mode(title: Optional[str], location: Optional[str], description: Optional[str] = None) -> str:
    """
    Infers workplace model: 'Remote', 'Hybrid', or 'On-site'.
    """
    if is_remote_job(title, location, description):
        return "Remote"
    loc_text = strip_accents(f"{title or ''} {location or ''}").lower()
    if "hybrid" in loc_text or (description and "hybrid" in strip_accents(description).lower()[:300]):
        return "Hybrid"
    return "On-site"


def get_deployment_region(location: Optional[str], title: Optional[str] = None) -> str:
    """
    Normalizes deployment region:
    'Hà Nội & Miền Bắc', 'TP. HCM & Miền Nam', 'Đà Nẵng & Miền Trung', 'Quốc tế / Toàn cầu', or 'Toàn quốc / Khác'.
    """
    text = strip_accents(f"{location or ''} {title or ''}").lower()
    if any(k in text for k in ["ha noi", "hanoi", "bac ninh", "hai phong", "vinh phuc", "hung yen"]):
        return "Hà Nội & Miền Bắc"
    if any(k in text for k in ["ho chi minh", "hcm", "sai gon", "binh duong", "dong nai", "cu chi", "can tho"]):
        return "TP. HCM & Miền Nam"
    if any(k in text for k in ["da nang", "hue", "quang nam"]):
        return "Đà Nẵng & Miền Trung"
    if any(k in text for k in ["worldwide", "global", "usa", "europe", "latam", "apac", "canada", "australia", ", va", ", tx", ", ca", ", oh", ", mn", ", md", ", pa", ", ny"]):
        return "Quốc tế / Toàn cầu"
    if "remote" in text or "tu xa" in text:
        return "Làm từ xa (Remote)"
    return "Toàn quốc / Chưa rõ"


def match_location(job_location: Optional[str], requested_location: Optional[str], job_title: Optional[str] = None) -> bool:
    """
    Checks if job_location matches any of the requested locations.
    Handles 'Ha Noi', 'Hà Nội', 'Hanoi', 'Da Nang', 'Đà Nẵng', 'Remote', etc.
    """
    if not requested_location or not requested_location.strip():
        return True

    norm_req = strip_accents(requested_location.lower())

    # If specifically searching for Remote/Online
    if any(r in norm_req for r in ["remote", "tu xa", "online", "wfh"]):
        if is_remote_job(job_title or "", job_location or ""):
            return True
        # If user ONLY requested remote, don't match onsite jobs
        if norm_req in ["remote", "tu xa", "online", "wfh"]:
            return False

    if not job_location:
        return False

    norm_job_loc = strip_accents(job_location.lower())
    terms = [strip_accents(t.strip().lower()) for t in requested_location.replace(";", ",").split(",") if t.strip()]

    for term in terms:
        if term in norm_job_loc:
            return True
        # Without spaces e.g. "hanoi" in "ha noi" or "ha noi" in "hanoi"
        no_space_term = term.replace(" ", "")
        no_space_job = norm_job_loc.replace(" ", "")
        if no_space_term in no_space_job or no_space_job in no_space_term:
            return True
    return False


BLACKLIST_PROFESSIONS = [
    "thu hoi no", "bat dong san", "nha hang", "khach san", "f&b", "phuc vu",
    "bao ve", "tap vu", "thu ngan", "giao hang", "shipper", "le tan", "spa",
    "tho may", "cong nhan", "giam sat cua hang", "ban le", "telesale", "telesales",
    "cham soc khach hang", "tong dai", "tu van vien", "tuyen sinh", "xuat nhap khau",
    "ke toan", "kinh doanh", "ban hang", "sales", "nhan vien ky thuat", "video editor",
    "quan ly hoc vu"
]

ROLE_STOPWORDS = {
    "engineer", "developer", "chuyen", "vien", "ky", "su", "lap", "trinh", "nhan",
    "can", "bo", "lead", "senior", "junior", "intern", "fresher", "trainee", "head",
    "manager", "director", "expert", "chuyen gia", "staff", "specialist", "officer",
    "executive", "associate", "nganh", "cong", "nghe", "thong", "tin"
}

DOMAIN_SYNONYMS = {
    "ai": ["tri tue nhan tao", "machine learning", "ml", "deep learning", "computer vision", "nlp", "llm", "genai", "generative ai"],
    "ml": ["machine learning", "deep learning", "ai"],
    "data": ["du lieu", "big data", "etl", "analytics", "data warehouse"],
    "python": ["django", "fastapi", "flask"],
    "frontend": ["front-end", "front end", "react", "vue", "angular"],
    "backend": ["back-end", "back end"],
    "devops": ["cloud", "sre", "infrastructure", "kubernetes", "ci/cd"],
}


def is_keyword_relevant(title: Optional[str], description: Optional[str], keyword: Optional[str]) -> bool:
    """
    Checks if a job posting is genuinely relevant to the searched keyword.
    Strictly filters out irrelevant jobs (Sales, F&B, Thu hồi nợ, Bất động sản...)
    and ensures keyword domain tokens match as whole words, not partial substrings.
    """
    if not keyword or not keyword.strip():
        return True
    if not title:
        return False

    norm_title = strip_accents(title.lower())
    norm_kw = strip_accents(keyword.lower().strip())

    # 1. Blacklist check (excludes non-tech / irrelevant professions unless user explicitly searched for them)
    active_blacklist = [b for b in BLACKLIST_PROFESSIONS if b not in norm_kw]
    if any(b in norm_title for b in active_blacklist):
        return False

    # 2. Exact phrase match in title
    if norm_kw in norm_title:
        return True

    # 3. Domain token whole-word matching
    kw_words = [w for w in re.findall(r"\b\w+\b", norm_kw) if len(w) >= 2]
    domain_tokens = [w for w in kw_words if w not in ROLE_STOPWORDS]
    if not domain_tokens:
        domain_tokens = kw_words

    title_words = set(re.findall(r"\b\w+\b", norm_title))

    matched_all = True
    for dt in domain_tokens:
        if dt in title_words:
            continue
        syns = DOMAIN_SYNONYMS.get(dt, [])
        if any(syn in norm_title for syn in syns):
            continue
        matched_all = False
        break

    if matched_all:
        return True

    # 4. Fallback description check (only allowed for technical job titles)
    TECH_ROLES = {"engineer", "developer", "ky su", "lap trinh", "architect", "scientist", "chuyen gia", "tech"}
    if any(r in norm_title for r in TECH_ROLES) and description:
        norm_desc = strip_accents(description.lower())
        if norm_kw in norm_desc:
            return True
        if all(dt in norm_desc for dt in domain_tokens):
            return True

    return False


def clean_html(text: Optional[str]) -> str:
    """Strips HTML tags and normalizes whitespace."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    # Remove script and style elements
    for element in soup(["script", "style", "noscript"]):
        element.extract()
    cleaned = soup.get_text(separator=" ")
    # Normalize multiple whitespace and newlines
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    return cleaned.strip()


def generate_job_hash(source: str, url: Optional[str], title: str, company: Optional[str]) -> str:
    """
    Generates a deterministic unique hash for a job posting.
    Prefers URL if valid, falls back to normalized source + title + company.
    """
    if url and url.startswith("http"):
        clean_url = url.split("?")[0].strip().lower()
        key = f"{source}:{clean_url}"
    else:
        norm_title = re.sub(r"\W+", "", (title or "").lower())
        norm_company = re.sub(r"\W+", "", (company or "").lower())
        key = f"{source}:{norm_company}:{norm_title}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def parse_salary(salary_text: Optional[str]) -> Tuple[Optional[float], Optional[float], str]:
    """
    Parses Vietnamese salary strings to extract min, max and currency.
    """
    if not salary_text:
        return None, None, "Unknown"

    text = salary_text.strip().lower()

    if any(k in text for k in ["thỏa thuận", "thoa thuan", "negotiable", "cạnh tranh", "hấp dẫn"]):
        return None, None, "Negotiable"

    # Check for USD
    if "$" in text or "usd" in text:
        nums = [float(n.replace(",", "")) for n in re.findall(r"\d+(?:,\d+)?", text)]
        if len(nums) >= 2:
            return min(nums), max(nums), "USD"
        elif len(nums) == 1:
            if "tới" in text or "lên tới" in text or "up to" in text:
                return None, nums[0], "USD"
            elif "từ" in text or "from" in text:
                return nums[0], None, "USD"
            return nums[0], nums[0], "USD"

    # Check for triệu VND
    if "triệu" in text or "tr" in text or "vnd" in text or "đ" in text:
        nums = [float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", text)]
        if len(nums) >= 2:
            return nums[0] * 1_000_000, nums[1] * 1_000_000, "VND"
        elif len(nums) == 1:
            val = nums[0] * 1_000_000
            if "tới" in text or "lên tới" in text or "dưới" in text:
                return None, val, "VND"
            elif "từ" in text or "trên" in text:
                return val, None, "VND"
            return val, val, "VND"

    return None, None, "Other"
