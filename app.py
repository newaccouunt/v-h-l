#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚗 ALL-IN-ONE Vehicle Info Server (Render.com Ready)
Endpoints:
  /rc=MH46BV8300      -> SAB sources combined (scrapers + APIs) => one merged list
  /rc-api=MH46BV8300  -> SIRF bronx.duckdns.org APIs ka combined result
  /                -> status
"""

import os
import re
import json
import time
import base64
import hashlib
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from datetime import datetime, timezone

app = Flask(__name__)

# ==================== CONFIG ====================
UA = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36")

# ---------- Bronx APIs ----------
BRONX_APIS = {
    "bronx_fastag":       "https://leakapi.duckdns.org/api/fastag?vehicle={v}",
    "bronx_vinfo":        "https://leakapi.duckdns.org/vinfo/vehicle?reg={v}",
    "bronx_vehicle_info": "https://leakapi.duckdns.org/vehicle-info?registration_number={v}",
    "bronx_api_vehicle":  "https://leakapi.duckdns.org/api/vehicle?vehicle={v}",
}

# ---------- Park+ ----------
PARKPLUS_URL = "https://insurance-v2.parkplus.io/api/v2/vehicle"
PARKPLUS_TOKEN_FILE = "parkplus_token.json"
PARKPLUS_DEFAULT_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6InYxIn0.eyJleHAiOjE3OTM0MjgxODAsInN1YiI6IjM3NDg3MDQwIiwidW5pcXVlX2lkIjoiZ3V3a3RhUUtQRFBMY2pWUGVFUFpmUFJYSEJPUVVkand5VFZsUW9Xb1NpSUdtS0VoakpCY09YZ2xRU1l5ek1FeCIsImh0dHBzOi8vcGFya3doZWVscy5jby5pbi8iOnsidXNlcl9pZCI6Mzc0ODcwNDAsIm5hbWUiOiIgIiwiZW1haWwiOiIiLCJwaG9uZV9udW1iZXIiOiI4MDk5NDg1MTEwIiwicm9sZSI6ImNsaWVudCIsImRldmljZV9pZCI6bnVsbCwidmVyc2lvbiI6NCwidGVzdF91c2VyIjpmYWxzZX19.0gJhqB1rycVLsuXo9y71kB4wZ4m0SgtQPLANE0R_MFLkBCuO8qrz-Y6BDz2uVEezSvDzUmQ-bVhIAVNUMf0uTA"

# ---------- Cars24 ----------
CARS24_BASE = "https://vehicle.cars24.team/v1/2025-09/vehicle-number"

# ---------- PBWheels ----------
PBWHEELS_URL = "https://carinfo.pbwheels.com/api/Vahan/getdetails"
PBWHEELS_SID_FILE = "pbwheels_sid.txt"
PBWHEELS_DEFAULT_SID = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJFbnF1aXJ5SWQiOiIxNDkxNDI4IiwiQ2F0ZWdvcnlJZCI6IlZBSEFOIiwiTGVhZElkIjoiODM5MDI2IiwiVmlzaXRJZCI6IjE1NzI0NTEiLCJSZWdOdW1iZXIiOiJNSDAyRlowNTU1IiwiQ3VzdG9tZXJJZCI6IjY4NDM3NjUiLCJuYmYiOjE3OTA4MzczNTksImV4cCI6MjUzNDAyMzAwODAwLCJpYXQiOjE3OTA4MzczNTl9.mQQzzv28a1udz6OCg5S_tP-aFVGDurOIzdDthBCwSgI"
PBWHEELS_COOKIE = "PbwVisitId=1572451; VisitProfileCookie=%7B%22visitId%22%3A1572451%2C%22UtmSource%22%3A%22%22%2C%22UtmMedium%22%3A%22vehicle-state%22%2C%22UtmTerm%22%3A%22maharashtra%22%2C%22UtmCampaign%22%3A%22%22%7D; CustomerAccessToken=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJDdXN0b21lcklkIjoiNjg0Mzc2NSIsIlR5cGUiOiJGcmVzaCIsIlNlc3Npb25JZCI6IjE5MWIzNzM1ZGIzZjQ0MTRhNTcxMTA4NzI2OWZhZjUwIiwiQ2F0ZWdvcnkiOiJSZWd1bGFyIiwibmJmIjoxNzkwODM3MzU4LCJleHAiOjE3OTM0MjkzNTgsImlhdCI6MTc5MDgzNzM1OH0.E0PC3xb6YVCgUnc45D37FSrSjDAvrLELT19UoCxU7NWbaO7rcCJJ5aRaHbHtyobbFPrW6TnWPlouDdtqflLYHY1hK968BKnxSAuxzhgJycgKAdvXIvFzGlJQjcSP0o-qmEa-jUPH5QX6QvtCnrFl294Iiq1RpIYSa9W--6OAGmBiUpgqTqNV3HgQJi2TU9oUBIOoDCi84TSFp8xcYDAe57aQCPmm6KbnsPkv09sMs3EFofylMwP8Krp8KN-gVLjb0aFDhtgCchMtqTapgjst12yWuyZ5wsHs346BcADrlp6nw_B6BELnSYBHGf6fLGpQZJQl0jChidv6-rCOs38lDA"

# ---------- VahanDetails (PoW) ----------
VD_BASE = "https://restapi.vahandetails.com"
VD_POW_URL = f"{VD_BASE}/api/auth/pow-challenge"
VD_TOKEN_URL = f"{VD_BASE}/api/auth/session-token"
VD_SEARCH_URL = f"{VD_BASE}/api/vehicles/search"
VD_COMMON_HEADERS = {
    'User-Agent': UA,
    'Accept-Encoding': "gzip, deflate",
    'Content-Type': "application/json",
    'sec-ch-ua-platform': '"Android"',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Brave";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': "?1",
    'Sec-GPC': "1",
    'Origin': "https://vahandetails.com",
    'Sec-Fetch-Site': "same-site",
    'Sec-Fetch-Mode': "cors",
    'Sec-Fetch-Dest': "empty",
    'Referer': "https://vahandetails.com/",
    'Accept-Language': "en-US,en;q=0.9",
}

# ---------- VahanX ----------
VX_BASE = "https://vahanx.in"
VX_HOME = f"{VX_BASE}/rc-search"
VX_SEARCH = f"{VX_BASE}/rc-search/{{rc}}"
VX_HEADERS = {
    'User-Agent': UA,
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    'Accept-Encoding': "gzip, deflate",
    'Accept-Language': "en-US,en;q=0.9",
    'Upgrade-Insecure-Requests': "1",
    'Sec-Fetch-Site': "same-origin",
    'Sec-Fetch-Mode': "navigate",
    'Sec-Fetch-User': "?1",
    'Sec-Fetch-Dest': "document",
}


# ==================== HELPERS ====================
def load_token(path, default):
    try:
        if path.endswith(".json") and os.path.exists(path):
            return json.loads(open(path).read()).get("token", default)
        if os.path.exists(path):
            return open(path).read().strip() or default
    except Exception:
        pass
    return default


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        try:
            return {"raw": resp.content.decode("utf-8", errors="replace")[:1500]}
        except Exception:
            return {"raw": "<unreadable>"}


# ==================== PARK+ ====================
def fetch_parkplus(vnum):
    token = load_token(PARKPLUS_TOKEN_FILE, PARKPLUS_DEFAULT_TOKEN)
    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "authorization": token,
        "app-name": "Park+ PWA",
        "package-name": "web.pwa",
        "client-id": "8186c1be-660f-428c-93a7-6480c2d8af66",
        "client-secret": "hjjh0uw8c3j7vw5jgba8",
        "device-id": "75112be82bf6deb427e4a5e26b6cf58b",
        "new-device-id": "75112be82bf6deb427e4a5e26b6cf58b",
        "content-type": "application/json;charset=UTF-8",
        "platform": "web",
        "origin": "https://parkplus.io",
        "referer": "https://parkplus.io/",
        "accept-language": "en-US,en;q=0.8",
    }
    try:
        r = requests.post(PARKPLUS_URL,
                          json={"source": "existing-car", "vehicle_number": vnum.upper()},
                          headers=headers, timeout=20)
        return {"source": "parkplus", "status": r.status_code, "data": safe_json(r)}
    except Exception as e:
        return {"source": "parkplus", "status": 500, "error": str(e)}


# ==================== CARS24 ====================
def fetch_cars24(vnum):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "authorization": "Basic YzJiX2Zyb250ZW5kOko1SXRmQTk2bTJfY3lRVk00dEtOSnBYaFJ0c0NtY1h1",
        "device_category": "mSite",
        "origin_source": "c2b-website",
        "platform": "rto",
        "origin": "https://www.cars24.com",
        "referer": "https://www.cars24.com/",
        "accept-language": "en-US,en;q=0.8",
    }
    try:
        r = requests.get(f"{CARS24_BASE}/{vnum.upper()}", headers=headers, timeout=20)
        return {"source": "cars24", "status": r.status_code, "data": safe_json(r)}
    except Exception as e:
        return {"source": "cars24", "status": 500, "error": str(e)}


# ==================== PBWHEELS ====================
def fetch_pbwheels(vnum):
    sid = load_token(PBWHEELS_SID_FILE, PBWHEELS_DEFAULT_SID)
    try:
        p = sid.split('.')[1]
        p += '=' * (-len(p) % 4)
        payload = json.loads(base64.urlsafe_b64decode(p))
        token_reg = (payload.get("RegNumber") or "").upper()
        if token_reg and token_reg != vnum.upper():
            return {"source": "pbwheels", "status": 400,
                    "error": f"Token only valid for {token_reg} (not {vnum.upper()})"}
    except Exception:
        pass

    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "origin": "https://carinfo.pbwheels.com",
        "referer": f"https://carinfo.pbwheels.com/vahan?sid={sid}",
        "accept-language": "en-US,en;q=0.8",
        "Cookie": PBWHEELS_COOKIE,
    }
    try:
        r = requests.post(PBWHEELS_URL, json={"sid": sid}, headers=headers, timeout=30)
        return {"source": "pbwheels", "status": r.status_code, "data": safe_json(r)}
    except Exception as e:
        return {"source": "pbwheels", "status": 500, "error": str(e)}


# ==================== VAHANDETAILS (PoW) ====================
_vd_pool = []
_vd_lock = threading.Lock()


def _vd_solve_pow(challenge, difficulty):
    prefix = "0" * int(difficulty)
    for nonce in range(10_000_000):
        if hashlib.sha256(f"{challenge}{nonce}".encode()).hexdigest().startswith(prefix):
            return str(nonce)
    raise Exception("PoW unsolvable")


def _vd_generate_token():
    for _ in range(4):
        try:
            r = requests.get(VD_POW_URL, headers=VD_COMMON_HEADERS, timeout=12)
            if r.status_code != 200:
                time.sleep(1); continue
            d = r.json()
            ch, diff = d.get("challenge"), d.get("difficulty", 4)
            if not ch:
                time.sleep(1); continue
            nonce = _vd_solve_pow(ch, diff)
            r2 = requests.post(VD_TOKEN_URL, json={"challenge": ch, "solution": nonce},
                               headers=VD_COMMON_HEADERS, timeout=12)
            if r2.status_code == 200:
                t = r2.json().get("token")
                if t:
                    return t
        except Exception:
            time.sleep(1)
    return None


def _vd_get_token():
    with _vd_lock:
        if _vd_pool:
            t = _vd_pool.pop(0); _vd_pool.append(t); return t
    t = _vd_generate_token()
    if t:
        with _vd_lock:
            _vd_pool.append(t)
    return t


def fetch_vahandetails(vnum):
    try:
        token = _vd_get_token()
        if not token:
            return {"source": "vahandetails", "status": 503, "error": "No token"}
        headers = VD_COMMON_HEADERS.copy()
        headers["X-Session-Token"] = token
        r = requests.post(VD_SEARCH_URL, json={"rc_regn_no": vnum.upper()},
                          headers=headers, timeout=20)
        return {"source": "vahandetails", "status": r.status_code, "data": safe_json(r)}
    except Exception as e:
        return {"source": "vahandetails", "status": 500, "error": str(e)}


# ==================== VAHANX (scrape) ====================
_vx_state = {"session": None, "token": None, "last_refresh": 0}
_vx_lock = threading.Lock()


def _vx_refresh():
    s = requests.Session()
    s.headers.update(VX_HEADERS)
    try:
        r = s.get(VX_HOME, timeout=20, allow_redirects=True)
        if r.status_code != 200:
            return False
        m = re.search(r'window\.VX_ST\s*=\s*\{([^}]+)\}', r.text, re.S)
        if not m:
            return False
        tok = re.search(r'rc\s*:\s*"([^"]+)"', m.group(1))
        if not tok:
            return False
        _vx_state["session"] = s
        _vx_state["token"] = tok.group(1)
        _vx_state["last_refresh"] = time.time()
        return True
    except Exception:
        return False


def fetch_vahanx(vnum):
    with _vx_lock:
        if (not _vx_state["token"] or
                (time.time() - _vx_state["last_refresh"]) > 900):
            if not _vx_refresh():
                return {"source": "vahanx", "status": 503,
                        "error": "Session refresh failed"}
        s = _vx_state["session"]
        tok = _vx_state["token"]

    try:
        url = VX_SEARCH.format(rc=vnum.upper())
        r = s.get(url, params={"t": tok}, timeout=25, allow_redirects=True)
        if r.status_code in (401, 403, 419):
            with _vx_lock:
                _vx_refresh()
            return {"source": "vahanx", "status": r.status_code,
                    "error": "Token rejected"}
        if r.status_code != 200:
            return {"source": "vahanx", "status": r.status_code,
                    "error": f"HTTP {r.status_code}"}

        data = _parse_vx(r.text, vnum)
        if not (data.get("owner_name") or data.get("model_name")):
            return {"source": "vahanx", "status": 404,
                    "error": "No data (invalid RC?)", "data": data}
        return {"source": "vahanx", "status": 200, "data": data}
    except Exception as e:
        return {"source": "vahanx", "status": 500, "error": str(e)}


def _parse_vx(html, rc_number):
    soup = BeautifulSoup(html, "html.parser")
    out = {"rc_number": rc_number}
    hero = soup.find("section", class_="hero-rc-details")
    if hero:
        h1 = hero.find("h1")
        if h1:
            out["rc_number"] = h1.get_text(strip=True)
        for card in hero.find_all("div", class_="hrcd-cardbody"):
            lab, val = card.find("span"), card.find("p")
            if not lab or not val:
                continue
            k = lab.get_text(strip=True).lower()
            v = val.get_text(" ", strip=True)
            if "owner name" in k: out["owner_name"] = v
            elif "modal name" in k or "model name" in k: out["model_name"] = v
            elif "phone" in k: out["rto_phone"] = v
            elif "website" in k: out["rto_website"] = v
            elif "address" in k: out["rto_address"] = v
    mapping = {
        "owner name": "owner_name", "owner serial": "owner_serial",
        "registration number": "rc_number", "registered rto": "registered_rto",
        "model name": "model_name", "maker model": "maker_model",
        "vehicle class": "vehicle_class", "fuel type": "fuel_type",
        "fuel norms": "fuel_norms", "chassis number": "chassis_number",
        "engine number": "engine_number", "insurance no": "insurance_no",
        "insurance company": "insurance_company", "registration date": "registration_date",
        "fitness upto": "fitness_upto", "tax upto": "tax_upto",
        "puc no": "puc_no", "puc upto": "puc_upto",
    }
    for card in soup.find_all("div", class_="hrc-details-card"):
        for item in card.find_all("div", class_=re.compile(r"col-sm-6|col-12")):
            lab = item.find("span", class_="text-muted")
            val = item.find("p", class_="fw-semibold")
            if not lab or not val:
                continue
            k = lab.get_text(strip=True).lower()
            v = val.get_text(" ", strip=True)
            if not v or v.upper() in ("NA", "N/A"):
                continue
            for mk, field in mapping.items():
                if mk in k:
                    out[field] = v
                    break
            else:
                if "insurance expiry" in k and " in" not in k:
                    out["insurance_upto"] = v
    return out


# ==================== BRONX APIs ====================
def fetch_bronx(name, url_template, vnum):
    url = url_template.format(v=vnum.upper())
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept": "application/json"}, timeout=25)
        return {"source": name, "status": r.status_code, "data": safe_json(r)}
    except Exception as e:
        return {"source": name, "status": 500, "error": str(e)}


# ==================== PARALLEL FETCHER ====================
def run_all_sources(vnum, include_scrapers=True):
    tasks = []

    for name, tpl in BRONX_APIS.items():
        tasks.append((name, lambda n=name, t=tpl: fetch_bronx(n, t, vnum)))

    if include_scrapers:
        tasks.append(("parkplus",     lambda: fetch_parkplus(vnum)))
        tasks.append(("cars24",       lambda: fetch_cars24(vnum)))
        tasks.append(("pbwheels",     lambda: fetch_pbwheels(vnum)))
        tasks.append(("vahandetails", lambda: fetch_vahandetails(vnum)))
        tasks.append(("vahanx",       lambda: fetch_vahanx(vnum)))

    results = [None] * len(tasks)

    def worker(i, fn):
        try:
            results[i] = fn()
        except Exception as e:
            results[i] = {"source": f"task_{i}", "status": 500, "error": str(e)}

    threads = [threading.Thread(target=worker, args=(i, fn), daemon=True)
               for i, (_, fn) in enumerate(tasks)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=45)

    out = []
    for i, (name, _) in enumerate(tasks):
        r = results[i] or {"source": name, "status": 504, "error": "timeout"}
        r.setdefault("source", name)
        out.append(r)
    return out


# ==================== ROUTES ====================
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "server": "All-in-One Vehicle Info",
        "time": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "/rc=<number>":     "SAB sources combined (bronx + scrapers)",
            "/rc-api=<number>": "SIRF bronx.duckdns.org APIs",
        },
        "examples": [
            "/rc=MH46BV8300",
            "/rc-api=MH46BV8300",
        ],
    })


@app.route("/rc-api=<path:vnum>")
def rc_api(vnum):
    vnum = vnum.upper().strip()
    if len(vnum) < 8:
        return jsonify({"error": "Invalid RC"}), 400
    results = run_all_sources(vnum, include_scrapers=False)
    return jsonify({
        "vehicle_number": vnum,
        "total_sources": len(results),
        "ok_sources": sum(1 for r in results if r.get("status") == 200),
        "results": results,
    })


@app.route("/rc=<path:vnum>")
def rc_full(vnum):
    vnum = vnum.upper().strip()
    if len(vnum) < 8:
        return jsonify({"error": "Invalid RC"}), 400
    results = run_all_sources(vnum, include_scrapers=True)
    return jsonify({
        "vehicle_number": vnum,
        "total_sources": len(results),
        "ok_sources": sum(1 for r in results if r.get("status") == 200),
        "results": results,
    })


# ==================== MAIN ====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("  🚗 ALL-IN-ONE Vehicle Info Server")
    print("=" * 60)
    print(f"  ➜ Listening on port {port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
