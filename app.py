"""
AI Tier 2 Support Intelligence
==============================
A Tier 2 investigation assistant that:
  * searches YOUR troubleshooting toolkit files (the .md / .sql files next to this app.py),
  * searches the public CivicPlus Help Center (live, from https://www.civicplus.help/llms.txt),
  * searches past cases you saved in the app, and (optionally) cases pulled live from
    Zendesk, Salesforce and Slack with credentials the admin has given you,
  * ranks the closest matches with a real keyword-relevance engine (BM25),
  * tells the engineer what still has to be investigated by a human,
  * lets you save verified resolutions so future cases find them,
  * optionally asks Claude to draft a resolution using ONLY the evidence found.

Nothing here is a fake "99% accuracy" figure. Match strength is shown as measured
term overlap, and every suggestion must be verified by an engineer.
"""

import base64
import hashlib
import json
import math
import os
import re
import tempfile
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
CASES_FILE = APP_DIR / "cases.json"
HELP_INDEX_URL = "https://www.civicplus.help/llms.txt"
HELP_HOST = "https://www.civicplus.help/"
HTTP_TIMEOUT = 15
USER_AGENT = {"User-Agent": "Mozilla/5.0 (compatible; Tier2SupportIntelligence/1.0)"}
SF_API_VERSION = "v60.0"

SOURCE_ICON = {
    "Toolkit": "📘",
    "CivicPlus Help": "🏛️",
    "Saved case": "🗂️",
    "Zendesk": "🎫",
    "Salesforce": "☁️",
    "Slack": "💬",
}

HTTP_CODES = {
    400: "Bad Request – the request was invalid (missing fields, bad data or format).",
    401: "Unauthorized – authentication missing, expired or invalid.",
    403: "Forbidden – understood but refused (permissions / restricted resource).",
    404: "Not Found – wrong URL/endpoint or the resource does not exist.",
    408: "Request Timeout – the server gave up waiting for the request.",
    409: "Conflict – the request conflicts with the current state of the resource.",
    422: "Unprocessable Entity – the data was well-formed but failed validation.",
    429: "Too Many Requests – rate limit hit.",
    500: "Internal Server Error – unexpected server-side problem; may need engineering.",
    502: "Bad Gateway – an upstream/gateway server returned an invalid response.",
    503: "Service Unavailable – the service is down or overloaded.",
    504: "Gateway Timeout – an upstream server did not answer in time.",
}

CATEGORY_KEYWORDS = {
    "API / HTTP": ["api", "endpoint", "http", "payload", "json", "webhook", "rest", "request", "response",
                   "status code", "bad gateway", "timeout", "timed out"],
    "Authentication / SSO": ["login", "log in", "sign in", "sign-in", "sso", "saml", "okta", "entra", "adfs",
                             "2fa", "two-factor", "mfa", "password", "locked out", "authenticat", "token"],
    "Payments": ["payment", "transaction", "gateway", "refund", "chargeback", "card", "ach", "emv", "terminal",
                 "processor", "converge", "forte", "heartland", "authorize.net", "payflow", "braintree",
                 "tempus", "cardpointe", "deposit", "receipt"],
    "Database / Data": ["sql", "database", "query", "record", "duplicate", "deadlock", "data missing",
                        "report shows", "export"],
    "Windows / Device": ["windows", "task manager", "event viewer", "cpu", "memory", "disk", "ipconfig", "dns",
                         "vpn", "wifi", "wi-fi", "driver", "install", "tray app", "service stopped"],
    "Browser / UI": ["browser", "chrome", "cache", "cookie", "blank page", "button", "not loading", "render",
                     "safari", "firefox", "edge", "console error"],
    "Notifications / Email": ["email", "notification", "subscriber", "bounce", "sms", "alert"],
    "Integration": ["integration", "arcgis", "esri", "seeclickfix", "salesforce", "zendesk", "slack", "sync"],
}

VERIFY_BY_CATEGORY = {
    "API / HTTP": [
        "Record the exact endpoint, HTTP method, status code and timestamp.",
        "Read the response body – it usually says what was wrong.",
        "Check headers, request body and data format against what the endpoint expects.",
        "Verify authentication (missing/expired token) and permissions separately.",
        "Reproduce the request if possible and keep request + response as evidence.",
        "When escalating, never include passwords, tokens or API keys.",
    ],
    "Authentication / SSO": [
        "Is it one user or many? Compare with another user in the same organization.",
        "Check whether the account is locked, unverified or has a changed email.",
        "If an identity provider is involved (Okta / Entra / ADFS / SAML), check the IdP side and the user's group/permissions.",
        "Check two-factor settings (organization-forced 2FA, authenticator vs email).",
        "Test another browser / private window to rule out cache or cookies.",
    ],
    "Payments": [
        "Confirm which processor/gateway the organization uses and whether it is CivicPlus Payments or external.",
        "Find the transaction in the Payments Portal Activity Log; note transaction ID, time and error code.",
        "Check the processor's status page and whether the issue is card-present (EMV/device) or online.",
        "Check for duplicate-transaction, session-timeout or AVS/ZIP rules specific to that gateway.",
        "Never ask a customer for a full card number.",
    ],
    "Database / Data": [
        "Use read-only queries to collect evidence; do not change production data unless authorized and controlled.",
        "Confirm the scope: one customer, one organization, or many.",
        "Compare the record with what the UI/API shows and note timestamps.",
    ],
    "Windows / Device": [
        "Check Task Manager for a process using unusual CPU / memory / disk.",
        "Check that the dependent Windows service is running and set to start automatically.",
        "Look in Event Viewer (Application / System) around the time of the report; record Event ID and source.",
        "Test connectivity with ipconfig / ping / nslookup.",
        "Change one thing at a time and test after each change.",
    ],
    "Browser / UI": [
        "Test another browser and a private window.",
        "Disable extensions; clear cache and cookies.",
        "Open developer tools: look at Console errors and failed Network requests.",
        "Check whether another user or device has the same problem.",
    ],
    "Notifications / Email": [
        "Check subscriber status (suppressed / bounced) and the sent/pending message log.",
        "Check the send time and email-sending timeframes.",
        "Confirm the subscriber is on the correct list and verified.",
    ],
    "Integration": [
        "Confirm which side initiates the sync and check that side's sync/log first.",
        "Validate credentials/permissions for the connected application.",
        "Compare a record on both sides to find where the data diverges.",
    ],
    "General": [
        "Define expected vs actual behavior, who is affected, when it started and what changed.",
        "Reproduce the issue; if you cannot, document exactly what you tested.",
    ],
}

INFO_CHECKS = [
    ("Time of the issue / time zone",
     r"\b\d{1,2}[:.]\d{2}\b|\b20\d{2}-\d{2}-\d{2}\b|\b(today|yesterday|since|am|pm|utc|gmt|est|cst|pst)\b",
     "When exactly did it start, and in which time zone?"),
    ("Exact error message",
     r"error|exception|failed|failure|denied|\b[45]\d{2}\b|\"",
     "What is the exact error text or code (screenshot if possible)?"),
    ("Who is affected",
     r"users|everyone|all |organization|tenant|customers|only (me|one)|one user|single user|several|multiple",
     "One user, several users, one organization, or many?"),
    ("Steps to reproduce",
     r"step|click|when (i|they|he|she)|after|tried|trying|attempt|select",
     "What were they doing, step by step, when it happened?"),
    ("Environment / device",
     r"production|sandbox|chrome|edge|firefox|safari|windows|mac|ios|android|browser|device",
     "Production or sandbox? Which browser/OS/device?"),
    ("Recent changes",
     r"change|updated|update|deploy|release|upgrade|migrat|since|started after",
     "What changed recently (settings, release, credentials, users)?"),
]

STOPWORDS = set(
    "a an and are as at be been being but by can could did do does for from get got had has have how i if in into "
    "is it its just me my no not of on or our so than that the their them then there these they this to too us "
    "was we were what when where which who will with would you your am also very".split()
)
TOKEN_RE = re.compile(r"[a-z0-9]+")


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------
def stem(word):
    for suffix in ("ingly", "edly", "ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def tokenize(text):
    out = []
    for w in TOKEN_RE.findall((text or "").lower()):
        if w in STOPWORDS or len(w) < 2:
            continue
        out.append(stem(w))
    return out


def redact(text):
    """Remove obvious personal data / secrets before anything is stored."""
    text = text or ""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", text)
    text = re.sub(r"\b(?:xox[abpr]-|sk-ant-|sk-|Bearer\s+)[\w.\-]{8,}", "[secret]", text)

    def _num(m):
        s = m.group(0)
        digits = sum(ch.isdigit() for ch in s)
        if digits >= 10 and not re.match(r"\d{4}-\d{2}-\d{2}", s):
            return "[number]"
        return s

    return re.sub(r"\+?\d[\d\s().\-]{8,}\d", _num, text)


def snippet(text, query_terms, width=320):
    """Short excerpt around the first matching term."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= width:
        return text
    low = text.lower()
    pos = -1
    for t in query_terms:
        pos = low.find(t)
        if pos != -1:
            break
    start = max(0, pos - width // 3) if pos != -1 else 0
    chunk = text[start:start + width].strip()
    return ("…" if start > 0 else "") + chunk + ("…" if start + width < len(text) else "")


# ---------------------------------------------------------------------------
# Search engine (BM25) – pure Python, no extra dependencies
# ---------------------------------------------------------------------------
class Index:
    K1 = 1.5
    B = 0.75

    def __init__(self, docs):
        self.docs = docs
        self.tf = []
        self.lengths = []
        self.post = defaultdict(list)
        df = Counter()
        for i, d in enumerate(docs):
            toks = tokenize(d.get("title", "")) * 2 + tokenize(d.get("text", ""))
            c = Counter(toks)
            self.tf.append(c)
            self.lengths.append(len(toks))
            for t in c:
                df[t] += 1
                self.post[t].append(i)
        self.n = len(docs)
        self.avg = (sum(self.lengths) / self.n) if self.n else 1.0
        self.idf = {t: math.log(1 + (self.n - k + 0.5) / (k + 0.5)) for t, k in df.items()}
        self.unseen_idf = math.log(1 + (self.n + 0.5) / 0.5)

    def search(self, query, k=6):
        terms = Counter(tokenize(query))
        if not terms or not self.n:
            return []
        weighted = sorted(terms, key=lambda t: self.idf.get(t, self.unseen_idf), reverse=True)[:40]
        total_idf = sum(self.idf.get(t, self.unseen_idf) for t in weighted)
        scores = defaultdict(float)
        matched = defaultdict(float)
        for t in weighted:
            if t not in self.idf:
                continue
            idf = self.idf[t]
            for i in self.post[t]:
                f = self.tf[i][t]
                denom = f + self.K1 * (1 - self.B + self.B * self.lengths[i] / self.avg)
                scores[i] += idf * (f * (self.K1 + 1)) / denom
                matched[i] += idf
        results = []
        for i, s in scores.items():
            d = self.docs[i]
            boost = 1.0
            if d.get("kind") == "case":
                boost *= 1.15
            outcome = d.get("outcome")
            if outcome == "worked":
                boost *= 1.3
            elif outcome == "failed":
                boost *= 0.6
            coverage = matched[i] / total_idf if total_idf else 0.0
            results.append({"doc": d, "score": s * boost, "coverage": coverage})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:k]


# ---------------------------------------------------------------------------
# Knowledge sources
# ---------------------------------------------------------------------------
def _chunk_markdown(name, text):
    docs, title, buf, n = [], name, [], 0

    def flush():
        nonlocal buf, n
        body = "\n".join(buf).strip()
        if len(body) > 40:
            n += 1
            docs.append({
                "id": f"kb:{name}:{n}", "source": "Toolkit", "kind": "doc",
                "title": f"{name} › {title}", "text": f"{title}\n{body}", "url": "", "file": name,
            })
        buf = []

    for line in text.splitlines():
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            flush()
            title = m.group(2).strip()
        else:
            buf.append(line)
    flush()
    return docs


def _chunk_sql(name, text):
    docs = []
    for i, part in enumerate(re.split(r"(?m)^(?=--\s*\d+\.\s)", text), 1):
        if not re.match(r"--\s*\d+\.", part):
            continue
        head = part.splitlines()[0].lstrip("- ").strip()
        docs.append({
            "id": f"kb:{name}:{i}", "source": "Toolkit", "kind": "sql",
            "title": f"{name} › {head}", "text": part.strip(), "url": "", "file": name,
        })
    return docs


@st.cache_data(show_spinner=False)
def load_toolkit(folder, signature):
    """Reads the .md / .sql toolkit files that sit next to app.py."""
    docs = []
    for path in sorted(Path(folder).glob("*")):
        if path.suffix.lower() not in (".md", ".sql") or path.name.lower() == "readme.md":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        docs.extend(_chunk_sql(path.name, text) if path.suffix.lower() == ".sql"
                    else _chunk_markdown(path.name, text))
    return docs


def toolkit_docs():
    files = [p for p in APP_DIR.glob("*") if p.suffix.lower() in (".md", ".sql")]
    signature = "|".join(f"{p.name}:{int(p.stat().st_mtime)}" for p in sorted(files))
    return load_toolkit(str(APP_DIR), signature)


HELP_LINE = re.compile(
    r"^- \[(?P<title>.+?)\]\((?P<url>https://www\.civicplus\.help/[^)\s]+)\)(?::\s*(?P<desc>.*))?$"
)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def fetch_help_index():
    """Downloads the CivicPlus Help Center documentation index (public, no key needed)."""
    r = requests.get(HELP_INDEX_URL, headers=USER_AGENT, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    docs, section = [], ""
    for line in r.text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        m = HELP_LINE.match(line)
        if not m or not (m.group("desc") or "").strip():
            continue  # skip bare category links – they have no content to match on
        url = m.group("url")
        docs.append({
            "id": f"help:{url}", "source": "CivicPlus Help", "kind": "doc",
            "title": m.group("title").strip(),
            "text": f"{m.group('title')}. {m.group('desc')}. {section}",
            "url": url[:-3] if url.endswith(".md") else url, "md_url": url, "section": section,
        })
    return {"docs": docs, "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def fetch_article(md_url):
    """Fetches the text of one CivicPlus Help Center article (only from civicplus.help)."""
    if not md_url.startswith(HELP_HOST):
        return ""
    r = requests.get(md_url, headers=USER_AGENT, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", r.text)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t[:2200]


# ---------------------------------------------------------------------------
# Case memory (saved resolutions)
# ---------------------------------------------------------------------------
def load_cases():
    try:
        data = json.loads(CASES_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def write_cases(cases):
    fd, tmp = tempfile.mkstemp(dir=str(APP_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cases, f, indent=2, ensure_ascii=False)
        os.replace(tmp, CASES_FILE)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def new_case(title, ticket, resolution, outcome, category):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cid = "case-" + hashlib.sha1((stamp + title + ticket + resolution + uuid.uuid4().hex).encode("utf-8")).hexdigest()[:10]
    return {
        "id": cid, "created": stamp, "title": redact(title).strip() or "Untitled case",
        "ticket": redact(ticket).strip(), "resolution": redact(resolution).strip(),
        "outcome": outcome, "category": category,
    }


def case_to_doc(c):
    return {
        "id": c.get("id", ""), "source": "Saved case", "kind": "case",
        "title": c.get("title", ""), "text": f"{c.get('ticket', '')}\n{c.get('resolution', '')}",
        "resolution": c.get("resolution", ""), "outcome": c.get("outcome", ""), "url": "",
        "created": c.get("created", ""),
    }


# ---------------------------------------------------------------------------
# Live connectors (Zendesk / Salesforce / Slack) – real API calls
# ---------------------------------------------------------------------------
def http_json(method, url, **kw):
    r = requests.request(method, url, timeout=HTTP_TIMEOUT, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code} from {url.split('?')[0]}: {r.text[:160]}")
    return r.json()


def zendesk_base(subdomain):
    sub = (subdomain or "").strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    if sub.endswith(".zendesk.com"):
        sub = sub[: -len(".zendesk.com")]
    if not re.fullmatch(r"[a-z0-9-]+", sub):
        raise ValueError("Enter just the Zendesk subdomain, e.g. 'yourcompany'.")
    return f"https://{sub}.zendesk.com"


def zendesk_auth(email, token):
    return (f"{email.strip()}/token", token.strip())


def zendesk_test(sub, email, token):
    base = zendesk_base(sub)
    data = http_json("GET", f"{base}/api/v2/users/me.json", auth=zendesk_auth(email, token))
    return f"Connected to Zendesk as {data['user'].get('name', 'user')} ({data['user'].get('role', '')})."


def zendesk_sync(sub, email, token, limit):
    base = zendesk_base(sub)
    auth = zendesk_auth(email, token)
    url = f"{base}/api/v2/search.json"
    params = {"query": "type:ticket status:solved status:closed order_by:updated_at sort:desc", "per_page": 100}
    docs = []
    while url and len(docs) < limit:
        data = http_json("GET", url, auth=auth, params=params)
        params = None
        for t in data.get("results", []):
            subject = t.get("subject") or ""
            docs.append({
                "id": f"zd:{t['id']}", "source": "Zendesk", "kind": "case", "ref": str(t["id"]),
                "title": f"#{t['id']} {subject}".strip(),
                "text": f"{subject}\n{(t.get('description') or '')[:2000]}\n{' '.join(t.get('tags', []))}",
                "url": f"{base}/agent/tickets/{t['id']}", "resolution": "",
            })
        url = data.get("next_page")
    return docs[:limit]


def zendesk_notes(sub, email, token, ticket_id):
    base = zendesk_base(sub)
    data = http_json("GET", f"{base}/api/v2/tickets/{int(ticket_id)}/comments.json", auth=zendesk_auth(email, token))
    public = [c for c in data.get("comments", []) if c.get("public")]
    return "\n---\n".join((c.get("plain_body") or c.get("body") or "")[:600] for c in public[-2:])


def sf_instance(url):
    url = (url or "").strip().rstrip("/")
    if not re.fullmatch(r"https://[a-z0-9.\-]+\.(salesforce|force)\.com", url):
        raise ValueError("Instance URL must look like https://yourcompany.my.salesforce.com")
    return url


def sf_headers(token):
    return {"Authorization": f"Bearer {token.strip()}"}


def sf_test(instance, token):
    inst = sf_instance(instance)
    data = http_json("GET", f"{inst}/services/data/", headers=sf_headers(token))
    return f"Connected to Salesforce ({len(data)} API versions available)."


def sf_sync(instance, token, limit):
    inst = sf_instance(instance)
    soql = ("SELECT Id, CaseNumber, Subject, Description, Status, Priority FROM Case "
            f"WHERE IsClosed = true ORDER BY ClosedDate DESC LIMIT {int(limit)}")
    data = http_json("GET", f"{inst}/services/data/{SF_API_VERSION}/query", headers=sf_headers(token),
                     params={"q": soql})
    docs = []
    while True:
        for r in data.get("records", []):
            subject = r.get("Subject") or ""
            docs.append({
                "id": f"sf:{r['Id']}", "source": "Salesforce", "kind": "case", "ref": r["Id"],
                "title": f"Case {r.get('CaseNumber', '')} {subject}".strip(),
                "text": f"{subject}\n{(r.get('Description') or '')[:2000]}",
                "url": f"{inst}/lightning/r/Case/{r['Id']}/view", "resolution": "",
            })
        nxt = data.get("nextRecordsUrl")
        if not nxt or len(docs) >= limit:
            break
        data = http_json("GET", f"{inst}{nxt}", headers=sf_headers(token))
    return docs[:limit]


def sf_notes(instance, token, case_id):
    if not re.fullmatch(r"[A-Za-z0-9]{15,18}", case_id or ""):
        return ""
    inst = sf_instance(instance)
    soql = f"SELECT CommentBody FROM CaseComment WHERE ParentId = '{case_id}' ORDER BY CreatedDate DESC LIMIT 3"
    data = http_json("GET", f"{inst}/services/data/{SF_API_VERSION}/query", headers=sf_headers(token),
                     params={"q": soql})
    return "\n---\n".join((r.get("CommentBody") or "")[:600] for r in data.get("records", []))


def slack_test(token):
    data = http_json("POST", "https://slack.com/api/auth.test", headers={"Authorization": f"Bearer {token.strip()}"})
    if not data.get("ok"):
        raise RuntimeError(f"Slack said: {data.get('error')}")
    return f"Connected to Slack workspace '{data.get('team')}' as {data.get('user')}."


def slack_sync(token, channel, limit):
    headers = {"Authorization": f"Bearer {token.strip()}"}
    docs, cursor = [], None
    while len(docs) < limit:
        params = {"channel": channel.strip(), "limit": min(200, limit)}
        if cursor:
            params["cursor"] = cursor
        data = http_json("GET", "https://slack.com/api/conversations.history", headers=headers, params=params)
        if not data.get("ok"):
            raise RuntimeError(f"Slack said: {data.get('error')} (the bot must be invited to the channel and have "
                               "the channels:history / groups:history scope)")
        for m in data.get("messages", []):
            txt = (m.get("text") or "").strip()
            if m.get("subtype") or len(txt) < 25:
                continue
            docs.append({
                "id": f"slack:{m.get('ts')}", "source": "Slack", "kind": "case",
                "title": txt[:70].replace("\n", " "), "text": txt[:2000], "url": "", "resolution": "",
            })
        cursor = (data.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
    return docs[:limit]


# ---------------------------------------------------------------------------
# Case analysis helpers
# ---------------------------------------------------------------------------
def classify(text):
    low = text.lower()
    scores = {cat: sum(1 for k in kws if k in low) for cat, kws in CATEGORY_KEYWORDS.items()}
    ranked = [c for c, s in sorted(scores.items(), key=lambda x: -x[1]) if s > 0]
    return ranked[:2] or ["General"]


def detect_http_codes(text):
    found = []
    for m in re.finditer(r"\b([45]\d{2})\b", text):
        code = int(m.group(1))
        if code in HTTP_CODES and code not in found:
            found.append(code)
    return found


def suggest_priority(text):
    low = text.lower()
    if any(k in low for k in ["outage", "all users", "everyone", "system down", "production down", "data loss",
                              "cannot process payments", "unable to process payments", "breach", "security incident"]):
        return "P1 – Critical", "Wording suggests widespread impact or a security/data risk."
    if any(k in low for k in ["multiple users", "several users", "many users", "whole organization",
                              "entire organization", "all customers", "multiple organizations", "all staff"]):
        return "P2 – High", "Wording suggests more than one user is affected."
    return "P3 – Moderate", "No sign of wide impact in the text – confirm scope with the customer."


def missing_information(text):
    missing = []
    for label, pattern, question in INFO_CHECKS:
        if not re.search(pattern, text, flags=re.I):
            missing.append((label, question))
    return missing


def evidence_strength(hits):
    if not hits:
        return "Weak", "Nothing relevant found – treat this as a new investigation."
    best_case = next((h for h in hits if h["doc"].get("kind") == "case" and h["doc"].get("outcome") != "failed"), None)
    if best_case and best_case["coverage"] >= 0.5:
        return "Strong", "A comparable past case overlaps strongly with this ticket."
    if hits[0]["coverage"] >= 0.35:
        return "Moderate", "Related material found, but no close precedent – use it as a lead, not an answer."
    return "Weak", "Only loose keyword overlap – treat this as a new investigation."


def build_ai_prompt(ticket, categories, hits, extra_sql):
    parts = []
    for i, h in enumerate(hits, 1):
        d = h["doc"]
        body = d.get("resolution") or d.get("excerpt") or d.get("notes") or d.get("text", "")
        parts.append(f"[E{i}] ({d['source']}) {d['title']}\n{body[:900]}")
    for j, s in enumerate(extra_sql, 1):
        parts.append(f"[Q{j}] Read-only SQL example from the toolkit:\n{s['doc']['text'][:500]}")
    return (
        f"Support case (personal data removed):\n{redact(ticket)[:3000]}\n\n"
        f"Detected category: {', '.join(categories)}\n\nEvidence found:\n" + "\n\n".join(parts)
    )


AI_SYSTEM = (
    "You assist a Tier 2 technical support engineer. Use ONLY the evidence items provided. "
    "Cite evidence like [E1]. Write: 1) the most likely cause(s) as hypotheses, 2) numbered next steps, "
    "3) what the engineer must verify or find out before acting. If the evidence does not support a conclusion, "
    "say so plainly instead of guessing. Never invent product behaviour, settings, ticket numbers or links. "
    "Keep it under 250 words."
)


def call_claude(api_key, model, prompt):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key.strip(), "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model.strip(), "max_tokens": 800, "system": AI_SYSTEM,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Claude API error {r.status_code}: {r.text[:200]}")
    return "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")


def run_analysis(ticket, use_help, fetch_notes, ai_cfg):
    warnings = []
    toolkit = toolkit_docs()
    docs = list(toolkit)
    help_info = None
    if use_help:
        try:
            help_info = fetch_help_index()
            docs += help_info["docs"]
        except Exception as exc:  # network / site problems must never crash the app
            warnings.append(f"The CivicPlus Help Center could not be reached right now ({exc}). "
                            "Results below do not include it.")
    docs += [case_to_doc(c) for c in load_cases()]
    for lst in st.session_state.live_docs.values():
        docs += lst

    index = Index(docs)
    hits = index.search(ticket, k=6)
    sql_hits = Index([d for d in toolkit if d.get("kind") == "sql"]).search(ticket, k=3)

    if fetch_notes:
        creds = st.session_state.creds
        for h in hits[:3]:
            d = h["doc"]
            try:
                if d["source"] == "CivicPlus Help" and d.get("md_url"):
                    d["excerpt"] = fetch_article(d["md_url"])
                elif d["source"] == "Zendesk" and "zendesk" in creds:
                    c = creds["zendesk"]
                    d["notes"] = zendesk_notes(c["sub"], c["email"], c["token"], d["ref"])
                elif d["source"] == "Salesforce" and "salesforce" in creds:
                    c = creds["salesforce"]
                    d["notes"] = sf_notes(c["instance"], c["token"], d["ref"])
            except Exception as exc:
                warnings.append(f"Could not fetch extra detail for '{d['title'][:50]}': {exc}")

    categories = classify(ticket)
    strength, strength_note = evidence_strength(hits)
    priority, priority_note = suggest_priority(ticket)
    result = {
        "ticket": ticket, "hits": hits, "sql_hits": sql_hits, "categories": categories,
        "codes": detect_http_codes(ticket), "missing": missing_information(ticket),
        "strength": strength, "strength_note": strength_note,
        "priority": priority, "priority_note": priority_note,
        "n_docs": len(docs), "n_toolkit": len(toolkit),
        "n_help": len(help_info["docs"]) if help_info else 0,
        "warnings": warnings, "ai_text": "", "query_terms": list(dict.fromkeys(tokenize(ticket)))[:12],
    }
    if ai_cfg and ai_cfg.get("key"):
        try:
            result["ai_text"] = call_claude(ai_cfg["key"], ai_cfg["model"],
                                            build_ai_prompt(ticket, categories, hits, sql_hits))
        except Exception as exc:
            result["warnings"].append(f"Claude draft not available: {exc}")
    return result


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
LOGO_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64' width='56' height='56'>"
    "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#1d4ed8'/>"
    "<stop offset='1' stop-color='#22d3ee'/></linearGradient></defs>"
    "<path d='M32 4 56 14v16c0 15-10 26-24 30C18 56 8 45 8 30V14z' fill='url(#g)'/>"
    "<g stroke='#fff' stroke-width='2.2' stroke-linecap='round' fill='#fff'>"
    "<path d='M22 30 32 22 42 30 32 44z' fill='none'/><circle cx='22' cy='30' r='3'/>"
    "<circle cx='32' cy='22' r='3'/><circle cx='42' cy='30' r='3'/><circle cx='32' cy='44' r='3'/></g></svg>"
)

CSS = """
<style>
.block-container {padding-top: 1.6rem; max-width: 1200px;}
.hero {display:flex; align-items:center; gap:16px; margin-bottom:.4rem;}
.hero h1 {margin:0; font-size:1.8rem; letter-spacing:-.4px; line-height:1.15;}
.hero p {margin:.15rem 0 0 0; color:#9db0d0; font-size:.95rem;}
</style>
"""


def secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def wide_button(label, **kw):
    try:
        return st.button(label, width="stretch", **kw)
    except TypeError:  # older Streamlit versions
        return st.button(label, use_container_width=True, **kw)


def init_state():
    st.session_state.setdefault("live_docs", {})
    st.session_state.setdefault("creds", {})
    st.session_state.setdefault("conn_msg", {})
    st.session_state.setdefault("analysis", None)
    st.session_state.setdefault("saved_msg", "")


def header():
    logo = base64.b64encode(LOGO_SVG.encode("utf-8")).decode("ascii")
    st.markdown(
        f"<div class='hero'><img src='data:image/svg+xml;base64,{logo}' width='56' height='56'/>"
        "<div><h1>AI Tier 2 Support Intelligence</h1>"
        "<p>Evidence-based triage: your playbooks + CivicPlus Help Center + past cases, with the engineer in control.</p>"
        "</div></div>",
        unsafe_allow_html=True,
    )


def render_hit(i, h):
    d = h["doc"]
    with st.container(border=True):
        left, right = st.columns([5, 1])
        left.markdown(f"**{i}. {d['title']}**")
        left.caption(f"{SOURCE_ICON.get(d['source'], '•')} {d['source']}"
                     + (f" · {d['section']}" if d.get("section") else "")
                     + (f" · outcome: {d['outcome']}" if d.get("outcome") else ""))
        right.metric("Overlap", f"{h['coverage']:.0%}")
        st.write(snippet(d.get("text", ""), h.get("terms", [])))
        if d.get("resolution"):
            st.success(f"**Recorded resolution:** {d['resolution'][:700]}")
        if d.get("notes"):
            st.info(f"**Latest notes on that ticket (check they describe the real fix):**\n\n{d['notes']}")
        if d.get("excerpt"):
            with st.expander("Read the help article text"):
                st.text(d["excerpt"])
        if d.get("url"):
            st.markdown(f"[Open source]({d['url']})")


def render_result(res):
    for w in res["warnings"]:
        st.warning(w)
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Suggested priority", res["priority"])
    c2.metric("Evidence strength", res["strength"])
    c3.metric("Documents searched", f"{res['n_docs']:,}")
    c4.metric("Category", " + ".join(res["categories"]))
    st.caption(f"{res['priority_note']} (heuristic – confirm against your SLA.)  •  {res['strength_note']}")
    st.caption("Overlap = how much of the ticket's distinctive wording appears in a match. "
               "It measures similarity, not the probability that the answer is correct.")

    st.markdown("### 1 · Closest matches")
    if not res["hits"]:
        st.info("No matching material found. Follow the methodology below and save the outcome afterwards so the "
                "next similar case has something to find.")
    for i, h in enumerate(res["hits"], 1):
        h["terms"] = res["query_terms"]
        render_hit(i, h)

    st.markdown("### 2 · Suggested approach")
    precedent = next((h for h in res["hits"] if h["doc"].get("resolution") and h["doc"].get("outcome") != "failed"), None)
    if precedent and res["strength"] == "Strong":
        st.success(f"A similar case was resolved before: **{precedent['doc']['title']}** – "
                   f"{precedent['doc']['resolution'][:500]}")
        st.caption("Treat this as a hypothesis. Confirm the same conditions apply before repeating the fix.")
    else:
        st.info("No close precedent with a recorded resolution. Work from the checklist below and the help articles above.")
    if res["codes"]:
        st.markdown("**HTTP status codes spotted in the text**")
        for code in res["codes"]:
            st.write(f"• **{code}** – {HTTP_CODES[code]}")
    if res["ai_text"]:
        st.markdown("**Claude's draft (based only on the evidence above – verify before use)**")
        st.write(res["ai_text"])

    st.markdown("### 3 · What the engineer still has to find out")
    if res["missing"]:
        st.markdown("**Information missing from the ticket – ask the customer:**")
        for label, question in res["missing"]:
            st.write(f"• **{label}:** {question}")
    st.markdown("**Verify yourself before acting:**")
    seen = set()
    for cat in res["categories"] + ["General"]:
        for item in VERIFY_BY_CATEGORY.get(cat, []):
            if item not in seen:
                seen.add(item)
                st.write(f"• {item}")
    st.write("• Change one thing at a time, then confirm the whole workflow works – not just that the error disappeared.")
    st.write("• If you cannot resolve it, escalate with: summary, impact, exact error, timestamp, steps to reproduce, "
             "what you already tested, logs/evidence.")

    if res["sql_hits"]:
        st.markdown("### 4 · Read-only SQL starters from your toolkit")
        st.caption("Examples only. Check table and column names against the real schema and use read-only access.")
        for h in res["sql_hits"]:
            st.code(h["doc"]["text"], language="sql")

    st.markdown("### 5 · Save the outcome so future cases can find it")
    st.caption("Emails, phone numbers and keys are removed automatically. Still, do not paste customer details you "
               "are not allowed to store.")
    with st.form("save_case_form", clear_on_submit=False):
        title = st.text_input("Short title", value=res["ticket"].strip().splitlines()[0][:80] if res["ticket"].strip() else "")
        resolution = st.text_area("What actually fixed it (or what you found)", height=110)
        outcome = st.selectbox("Did it work?", ["worked", "partial", "failed"],
                               format_func=lambda x: {"worked": "Yes – confirmed fix", "partial": "Partly",
                                                      "failed": "No – this did not help"}[x])
        submitted = st.form_submit_button("Save to case memory")
    if submitted:
        if not resolution.strip():
            st.warning("Write what fixed it (or what you learned) first.")
        else:
            try:
                cases = load_cases()
                cases.insert(0, new_case(title, res["ticket"], resolution, outcome, " + ".join(res["categories"])))
                write_cases(cases)
                st.session_state.saved_msg = f"Saved. Case memory now holds {len(cases)} case(s)."
            except OSError as exc:
                st.session_state.saved_msg = f"Could not write cases.json: {exc}"
    if st.session_state.saved_msg:
        st.success(st.session_state.saved_msg)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
def tab_analyze():
    ticket = st.text_area(
        "Case", height=170, label_visibility="collapsed", key="ticket_text",
        placeholder="Paste the ticket, Slack thread or error log here. Example: Customer says card payments fail with "
                    "502 Bad Gateway since this morning, affecting several staff users…",
    )
    o1, o2, o3 = st.columns(3)
    use_help = o1.checkbox("Search CivicPlus Help Center", value=True)
    fetch_notes = o2.checkbox("Fetch article text / ticket notes for top matches", value=True)
    use_ai = o3.checkbox("Draft with Claude (needs API key)", value=False)
    ai_cfg = None
    if use_ai:
        with st.container(border=True):
            st.caption("Only the redacted ticket and the evidence found are sent to Anthropic's API.")
            key = st.text_input("Anthropic API key", type="password", value=secret("ANTHROPIC_API_KEY"))
            model = st.text_input("Model", value="claude-sonnet-5-5")
            ai_cfg = {"key": key, "model": model}

    if wide_button("🚀 Analyze case", type="primary"):
        if not ticket.strip():
            st.warning("Paste a ticket or error log first.")
        else:
            st.session_state.saved_msg = ""
            with st.spinner("Searching playbooks, help center and past cases…"):
                st.session_state.analysis = run_analysis(ticket, use_help, fetch_notes, ai_cfg)
    if st.session_state.analysis:
        render_result(st.session_state.analysis)


def tab_knowledge():
    toolkit = toolkit_docs()
    files = sorted({d["file"] for d in toolkit})
    c1, c2, c3 = st.columns(3)
    c1.metric("Toolkit sections", len(toolkit))
    cases = load_cases()
    c2.metric("Saved cases", len(cases))
    c3.metric("Live-synced items", sum(len(v) for v in st.session_state.live_docs.values()))
    if files:
        st.success("Toolkit files read from this app folder: " + ", ".join(files))
    else:
        st.warning("No .md / .sql toolkit files were found next to app.py. Keep app.py in the same repository folder "
                   "as your toolkit files so it can read them.")
    st.markdown("#### CivicPlus Help Center")
    if st.button("🔄 Refresh from civicplus.help"):
        fetch_help_index.clear()
    try:
        info = fetch_help_index()
        st.success(f"Connected – {len(info['docs']):,} articles indexed (fetched {info['fetched']}). No API key is needed "
                   "because the site is public.")
    except Exception as exc:
        info = None
        st.error(f"Could not reach {HELP_INDEX_URL}: {exc}")
    st.markdown("#### Try a search to see what the app can find")
    q = st.text_input("Search all sources", placeholder="e.g. two-factor authentication locked out")
    if q.strip():
        docs = list(toolkit) + (info["docs"] if info else []) + [case_to_doc(c) for c in cases]
        for lst in st.session_state.live_docs.values():
            docs += lst
        found = Index(docs).search(q, k=8)
        if not found:
            st.info("No matches.")
        for h in found:
            d = h["doc"]
            link = f" – [open]({d['url']})" if d.get("url") else ""
            st.write(f"{SOURCE_ICON.get(d['source'], '•')} **{d['title']}** ({d['source']}, overlap {h['coverage']:.0%}){link}")


def _status(name):
    msg = st.session_state.conn_msg.get(name)
    if msg:
        (st.success if msg[0] else st.error)(msg[1])


def _run(name, fn, *args):
    try:
        return fn(*args)
    except Exception as exc:
        st.session_state.conn_msg[name] = (False, str(exc))
        return None


def tab_connections():
    st.info("These connectors call the real Zendesk, Salesforce and Slack APIs, so they only work with credentials your "
            "admin has issued to you. Credentials stay in this browser session's memory and are never written to disk. "
            "Use them only where your organization's data policy allows it.")
    limit = st.slider("Max items to pull per source", 50, 1000, 200, step=50)

    with st.expander("🎫 Zendesk", expanded=False):
        sub = st.text_input("Subdomain", value=secret("ZENDESK_SUBDOMAIN"), placeholder="yourcompany")
        email = st.text_input("Agent email", value=secret("ZENDESK_EMAIL"))
        tok = st.text_input("API token", type="password", value=secret("ZENDESK_TOKEN"))
        a, b = st.columns(2)
        if a.button("Test Zendesk connection"):
            msg = _run("zendesk", zendesk_test, sub, email, tok)
            if msg:
                st.session_state.conn_msg["zendesk"] = (True, msg)
        if b.button("Sync solved tickets"):
            docs = _run("zendesk", zendesk_sync, sub, email, tok, limit)
            if docs is not None:
                st.session_state.live_docs["zendesk"] = docs
                st.session_state.creds["zendesk"] = {"sub": sub, "email": email, "token": tok}
                st.session_state.conn_msg["zendesk"] = (True, f"Synced {len(docs)} solved/closed tickets.")
        _status("zendesk")

    with st.expander("☁️ Salesforce", expanded=False):
        inst = st.text_input("Instance URL", value=secret("SALESFORCE_INSTANCE"),
                             placeholder="https://yourcompany.my.salesforce.com")
        stok = st.text_input("OAuth access token", type="password", value=secret("SALESFORCE_TOKEN"))
        a, b = st.columns(2)
        if a.button("Test Salesforce connection"):
            msg = _run("salesforce", sf_test, inst, stok)
            if msg:
                st.session_state.conn_msg["salesforce"] = (True, msg)
        if b.button("Sync closed cases"):
            docs = _run("salesforce", sf_sync, inst, stok, limit)
            if docs is not None:
                st.session_state.live_docs["salesforce"] = docs
                st.session_state.creds["salesforce"] = {"instance": inst, "token": stok}
                st.session_state.conn_msg["salesforce"] = (True, f"Synced {len(docs)} closed cases.")
        _status("salesforce")
        st.caption("The token comes from an OAuth flow for a Connected App your admin approved (or from `sf org display` "
                   "for a sandbox). Tokens expire – paste a fresh one when it does.")

    with st.expander("💬 Slack", expanded=False):
        stk = st.text_input("Bot token (xoxb-…)", type="password", value=secret("SLACK_BOT_TOKEN"))
        chan = st.text_input("Channel ID (e.g. C0123456789)", value=secret("SLACK_CHANNEL"))
        a, b = st.columns(2)
        if a.button("Test Slack connection"):
            msg = _run("slack", slack_test, stk)
            if msg:
                st.session_state.conn_msg["slack"] = (True, msg)
        if b.button("Sync channel messages"):
            docs = _run("slack", slack_sync, stk, chan, limit)
            if docs is not None:
                st.session_state.live_docs["slack"] = docs
                st.session_state.conn_msg["slack"] = (True, f"Synced {len(docs)} messages.")
        _status("slack")
        st.caption("The bot must be invited to the channel and have the channels:history (or groups:history) scope.")

    st.caption("Tip: on Streamlit Cloud, put these values under App settings → Secrets (e.g. ZENDESK_TOKEN = \"...\") "
               "so they pre-fill and are never in your GitHub repo.")


def tab_cases():
    cases = load_cases()
    st.caption("Saved resolutions are searched on every analysis. 'Worked' cases rank higher, 'did not help' cases rank lower. "
               "On Streamlit Cloud the app's disk can reset when the app restarts or is redeployed – download a backup regularly.")
    if cases:
        rows = [{"id": c["id"], "saved": c.get("created", "")[:16], "title": c.get("title", ""),
                 "outcome": c.get("outcome", ""), "category": c.get("category", ""),
                 "resolution": c.get("resolution", "")[:120]} for c in cases]
        st.dataframe(rows)
        st.download_button("⬇️ Download backup (JSON)", json.dumps(cases, indent=2, ensure_ascii=False),
                           file_name="cases-backup.json", mime="application/json")
        victim = st.selectbox("Delete a case", [""] + [c["id"] for c in cases])
        if victim and st.button("Delete selected case"):
            write_cases([c for c in cases if c["id"] != victim])
            st.rerun()
    else:
        st.info("No saved cases yet. Analyze a case and save the outcome, or import a file below.")

    st.markdown("#### Import past cases")
    st.caption("Export closed cases from Zendesk or Salesforce as CSV (columns: title, description, resolution) or restore "
               "a backup JSON from this app. Personal data patterns are redacted on import.")
    up = st.file_uploader("CSV or JSON", type=["csv", "json"])
    if up is not None and st.button("Import file"):
        try:
            raw = up.getvalue().decode("utf-8", errors="ignore")
            incoming = []
            if up.name.lower().endswith(".json"):
                for c in json.loads(raw):
                    incoming.append(new_case(c.get("title", ""), c.get("ticket", ""), c.get("resolution", ""),
                                             c.get("outcome", "partial"), c.get("category", "")))
            else:
                import csv
                import io
                for row in csv.DictReader(io.StringIO(raw)):
                    low = {(k or "").strip().lower(): (v or "") for k, v in row.items()}
                    incoming.append(new_case(
                        low.get("title") or low.get("subject") or "",
                        low.get("description") or low.get("ticket") or low.get("body") or "",
                        low.get("resolution") or low.get("solution") or "",
                        "partial", ""))
            existing = load_cases()
            known = {(c["title"], c["resolution"]) for c in existing}
            added = [c for c in incoming if (c["title"], c["resolution"]) not in known]
            write_cases(added + existing)
            st.success(f"Imported {len(added)} case(s).")
        except Exception as exc:
            st.error(f"Could not import that file: {exc}")


def main():
    st.set_page_config(page_title="AI Tier 2 Support Intelligence", page_icon="🛡️", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()
    header()
    t1, t2, t3, t4 = st.tabs(["🔍 Analyze case", "📚 Knowledge base", "🔌 Connections", "🗂️ Case memory"])
    with t1:
        tab_analyze()
    with t2:
        tab_knowledge()
    with t3:
        tab_connections()
    with t4:
        tab_cases()


if __name__ == "__main__":
    main()
