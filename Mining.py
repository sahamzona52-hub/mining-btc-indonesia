#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PEGASUS NICEHASH MINER v20.0 - open source (MIT License)

Fitur (semua berbasis DATA ASLI, tidak ada angka "booster" palsu):
  * XMRig (CPU) + lolMiner (GPU) untuk pool NiceHash, unduh binary otomatis
  * Real-time via API lokal miner (hashrate, share, difficulty, latency)
  * Suhu / daya GPU NVIDIA (nvidia-smi), CPU load & suhu (psutil, opsional)
  * Kalkulator profit: pendapatan - biaya listrik (harga algoritma NiceHash live)
  * Benchmark hashrate per algoritma + auto-switch ke algoritma paling untung
  * Saldo & unpaid ASLI dari NiceHash API (API key read-only milik Anda)
  * Riwayat sesi, snapshot saldo, export CSV / JSON
  * Stop aman: hanya mematikan proses miner milik script ini

Pakai:  python pegasus_nicehash_miner.py --help
Install dependensi:  pip install requests psutil

Copyright (c) 2026 - dilisensikan di bawah MIT License. Bebas dipakai,
diubah, dan disebarkan dengan menyertakan pemberitahuan lisensi ini.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import traceback
import uuid
import zipfile
from collections import deque
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Modul 'requests' belum terpasang. Jalankan: pip install requests psutil")
try:
    import psutil
except ImportError:
    psutil = None

# ══════════════════════════════════════════════════════════════════
#  KONSTANTA & PATH
# ══════════════════════════════════════════════════════════════════
VERSION = "20.0"
BRAND = "PegasusMetaSec"
UA = {"User-Agent": f"{BRAND}/{VERSION}"}
OS_NAME = platform.system().lower()
IS_WIN = OS_NAME == "windows"
IS_LINUX = OS_NAME == "linux"

BASE_DIR = Path(os.environ.get("PEGASUS_HOME") or (Path.home() / "PegasusNiceHash"))
MINER_DIR = BASE_DIR / "miners"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "config.json"
HISTORY_DB = DATA_DIR / "history.json"
BENCH_DB = DATA_DIR / "benchmarks.json"
BALANCE_LOG = DATA_DIR / "balance_log.json"
PID_FILE = BASE_DIR / "miner.pid.json"
for _d in (BASE_DIR, MINER_DIR, LOGS_DIR, DATA_DIR):
    _d.mkdir(parents=True, exist_ok=True)

XMRIG_API = 18080
LOL_API = 18081
NH_HOST = "https://api2.nicehash.com"

REGIONS = {
    "auto": "Otomatis (terdekat)", "eu-north": "Eropa Utara", "eu-west": "Eropa Barat",
    "usa-east": "AS Timur", "usa-west": "AS Barat", "hk": "Hong Kong",
    "jp": "Jepang", "in": "India", "br": "Brasil",
}
# nama algoritma NiceHash -> nama algoritma di miner
CPU_ALGOS = {"RANDOMXMONERO": "rx/0", "GHOSTRIDER": "gr"}
GPU_ALGOS = {"ETCHASH": "ETCHASH", "AUTOLYKOS": "AUTOLYKOS2", "BEAMV3": "BEAM-III",
             "KHEAVYHASH": "KASPA", "FISHHASH": "FISHHASH"}

SOURCES = {
    "xmrig": {
        "windows": ("https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-gcc-win64.zip", ["xmrig.exe"]),
        "linux": ("https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-linux-static-x64.tar.gz", ["xmrig"]),
    },
    "lolminer": {
        "windows": ("https://github.com/Lolliedieb/lolMiner-releases/releases/download/1.88/lolMiner_v1.88_Win64.zip", ["lolMiner.exe"]),
        "linux": ("https://github.com/Lolliedieb/lolMiner-releases/releases/download/1.88/lolMiner_v1.88_Lin64.tar.gz", ["lolMiner"]),
    },
}

DEFAULTS = {
    "wallet": "NHbRMmowbz9DvKMeegGHTndbHb3GSKRMsAxw",  # ganti dengan alamat Anda
    "worker": "PegasusRig",
    "algo": "RANDOMXMONERO",
    "region": "auto",
    "port": 9200,
    "electricity_usd_kwh": 0.10,
    "power_watts_cpu": 65.0,    # konsumsi CPU saat mining (ukur dengan watt-meter)
    "power_watts_gpu": 0.0,     # 0 = baca otomatis dari nvidia-smi
    "cpu_threads_pct": 100,
    "cpu_priority": 2,
    "autoswitch": False,
    "autoswitch_minutes": 30,
    "autoswitch_margin": 0.10,
    "nh_api_key": "", "nh_api_secret": "", "nh_org_id": "",
    "sha256_xmrig": "", "sha256_lolminer": "",   # opsional: verifikasi unduhan
}
ENV_MAP = {"NICEHASH_API_KEY": "nh_api_key", "NICEHASH_API_SECRET": "nh_api_secret",
           "NICEHASH_ORG_ID": "nh_org_id"}
SECRET_KEYS = ("nh_api_key", "nh_api_secret", "nh_org_id")


# ══════════════════════════════════════════════════════════════════
#  WARNA
# ══════════════════════════════════════════════════════════════════
class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; GREEN = "\033[92m"; RED = "\033[91m"
    YELLOW = "\033[93m"; CYAN = "\033[96m"; MAGENTA = "\033[95m"
    WHITE = "\033[97m"; GRAY = "\033[90m"

    @classmethod
    def disable(cls):
        for k in dir(cls):
            if k.isupper():
                setattr(cls, k, "")


if IS_WIN:
    os.system("")  # aktifkan ANSI di terminal Windows
if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.disable()


# ══════════════════════════════════════════════════════════════════
#  UTILITAS
# ══════════════════════════════════════════════════════════════════
def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)


def fmt_hr(h):
    for div, unit in ((1e12, "TH/s"), (1e9, "GH/s"), (1e6, "MH/s"), (1e3, "kH/s")):
        if h >= div:
            return f"{h / div:.3f} {unit}"
    return f"{h:.2f} H/s"


def fmt_dur(sec):
    sec = int(max(0, sec))
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def spark(values, width=40):
    bars = "▁▂▃▄▅▆▇█"
    vals = list(values)[-width:]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        return bars[0] * len(vals)
    return "".join(bars[int((v - lo) / (hi - lo) * (len(bars) - 1))] for v in vals)


def log(msg, tag="info"):
    colors = {"ok": C.GREEN, "err": C.RED, "warn": C.YELLOW, "info": C.WHITE, "gold": C.YELLOW}
    print(f"{C.GRAY}[{datetime.now():%H:%M:%S}]{C.RESET} {colors.get(tag, C.WHITE)}{msg}{C.RESET}")


def http_json(url, timeout=3):
    try:
        r = requests.get(url, timeout=timeout, headers=UA)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


_cache: dict = {}


def cached(key, ttl, fn):
    e = _cache.get(key)
    if e and time.time() - e[0] < ttl:
        return e[1]
    try:
        v = fn()
    except Exception:
        v = None
    if v is not None:
        _cache[key] = (time.time(), v)
        return v
    return e[1] if e else None


# ══════════════════════════════════════════════════════════════════
#  KONFIGURASI
# ══════════════════════════════════════════════════════════════════
class Config:
    def __init__(self):
        self.data = dict(DEFAULTS)
        self.data.update({k: v for k, v in load_json(CONFIG_FILE, {}).items() if k in DEFAULTS})

    def __getitem__(self, key):
        for env, k in ENV_MAP.items():  # environment variable menimpa file
            if k == key and os.environ.get(env):
                return os.environ[env]
        return self.data[key]

    def save(self):
        save_json(CONFIG_FILE, self.data)
        try:
            CONFIG_FILE.chmod(0o600)
        except Exception:
            pass

    def set(self, key, value):
        if key not in DEFAULTS:
            raise KeyError(f"Kunci tidak dikenal: {key}")
        t = type(DEFAULTS[key])
        if t is bool:
            value = str(value).lower() in ("1", "true", "yes", "on", "ya")
        else:
            value = t(value)
        self.data[key] = value
        self.save()


cfg = Config()


# ══════════════════════════════════════════════════════════════════
#  DATA PASAR (NiceHash publik + CoinGecko)
# ══════════════════════════════════════════════════════════════════
def _fetch_algos():
    r = requests.get(NH_HOST + "/main/api/v2/public/simplemultialgo/info/", timeout=15, headers=UA)
    r.raise_for_status()
    out = {}
    for a in r.json().get("miningAlgorithms", []):
        try:
            factor = float(a.get("marketFactor") or 0)
            paying = float(a.get("paying") or a.get("payingRate") or 0)
        except (TypeError, ValueError):
            continue
        if factor <= 0:
            continue
        out[str(a.get("algorithm", "")).upper()] = {
            "paying": paying,  # BTC per unit (marketFactor H/s) per hari
            "factor": factor,
            "unit": a.get("displayMarketFactor", ""),
            "port": int(a.get("port") or 9200),
        }
    return out or None


def get_algos():
    return cached("algos", 120, _fetch_algos) or {}


def _fetch_prices():
    r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                     params={"ids": "bitcoin", "vs_currencies": "usd,idr"}, timeout=10, headers=UA)
    r.raise_for_status()
    return r.json().get("bitcoin") or None


def get_prices():
    return cached("prices", 120, _fetch_prices) or {}


def profit_estimate(algo, hashrate, watts):
    """Estimasi per hari. Belum termasuk fee NiceHash dan fluktuasi harga."""
    a = get_algos().get(str(algo).upper())
    if not a or hashrate <= 0:
        return None
    rev_btc = hashrate / a["factor"] * a["paying"]
    rev_usd = rev_btc * get_prices().get("usd", 0)
    cost = watts / 1000.0 * 24 * float(cfg["electricity_usd_kwh"])
    return {"rev_btc_day": rev_btc, "rev_usd_day": rev_usd,
            "cost_usd_day": cost, "net_usd_day": rev_usd - cost}


# ══════════════════════════════════════════════════════════════════
#  NICEHASH PRIVATE API (read-only) - saldo & unpaid ASLI
# ══════════════════════════════════════════════════════════════════
class NiceHashAPI:
    def configured(self):
        return all(cfg[k] for k in SECRET_KEYS)

    def request(self, method, path, query=""):
        key, secret, org = cfg["nh_api_key"], cfg["nh_api_secret"], cfg["nh_org_id"]
        xtime, nonce = str(int(time.time() * 1000)), str(uuid.uuid4())
        msg = f"{key}\x00{xtime}\x00{nonce}\x00\x00{org}\x00\x00{method}\x00{path}\x00{query}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        headers = dict(UA)
        headers.update({"X-Time": xtime, "X-Nonce": nonce, "X-Auth": f"{key}:{sig}",
                        "X-Organization-Id": org, "X-Request-Id": str(uuid.uuid4())})
        url = NH_HOST + path + (("?" + query) if query else "")
        try:
            r = requests.request(method, url, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.json(), None
            return None, f"HTTP {r.status_code}: {r.text[:120]}"
        except Exception as e:
            return None, str(e)

    def btc_balance(self):
        data, err = self.request("GET", "/main/api/v2/accounting/account2/BTC")
        return data, err

    def rigs(self):
        return self.request("GET", "/main/api/v2/mining/rigs2")


nh = NiceHashAPI()


def snapshot_balance():
    if not nh.configured():
        return None
    data, _ = nh.btc_balance()
    if not data:
        return None
    try:
        snap = {"ts": datetime.now().isoformat(timespec="seconds"),
                "available": float(data.get("available", 0)),
                "total": float(data.get("totalBalance", 0))}
    except (TypeError, ValueError):
        return None
    db = load_json(BALANCE_LOG, {"snapshots": []})
    db["snapshots"].append(snap)
    db["snapshots"] = db["snapshots"][-3000:]
    save_json(BALANCE_LOG, db)
    return snap


# ══════════════════════════════════════════════════════════════════
#  TELEMETRI (GPU NVIDIA, CPU) & DETEKSI GPU
# ══════════════════════════════════════════════════════════════════
def _run(cmd, timeout=10):
    kw = {"creationflags": 0x08000000} if IS_WIN else {}
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kw)


def _num(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def nvidia_stats():
    def fetch():
        out = _run(["nvidia-smi", "--query-gpu=name,temperature.gpu,power.draw,utilization.gpu,memory.total",
                    "--format=csv,noheader,nounits"], 6)
        gpus = []
        for line in out.stdout.strip().splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) >= 5:
                gpus.append({"name": p[0], "temp": _num(p[1]), "power": _num(p[2]),
                             "util": _num(p[3]), "vram": int(_num(p[4]))})
        return gpus or None
    return cached("nvsmi", 3, fetch) or []


def cpu_stats():
    if not psutil:
        return {"load": None, "temp": None}
    temp = None
    try:
        for entries in (psutil.sensors_temperatures() or {}).values():
            for e in entries:
                if e.current and (temp is None or e.current > temp):
                    temp = e.current
    except Exception:
        pass
    return {"load": psutil.cpu_percent(interval=None), "temp": temp}


def detect_gpus():
    gpus = [{"name": g["name"], "vendor": "NVIDIA", "vram": g["vram"], "compatible": True}
            for g in nvidia_stats()]
    if gpus:
        return gpus
    try:
        if IS_WIN:
            out = _run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json"], 20)
            data = json.loads(out.stdout or "[]")
            data = data if isinstance(data, list) else [data]
            names = [(d.get("Name", ""), int((d.get("AdapterRAM") or 0) / 1048576)) for d in data]
        elif IS_LINUX:
            out = _run(["lspci"])
            names = [(ln.split(":", 2)[-1].strip(), 0) for ln in out.stdout.splitlines()
                     if any(k in ln.lower() for k in ("vga", "3d", "display"))]
        else:
            names = []
    except Exception:
        names = []
    for name, vram in names:
        nl = name.lower()
        vendor = ("NVIDIA" if "nvidia" in nl else
                  "AMD" if ("amd" in nl or "radeon" in nl) else
                  "Intel" if "intel" in nl else "Unknown")
        gpus.append({"name": name, "vendor": vendor, "vram": vram,
                     "compatible": vendor in ("NVIDIA", "AMD")})
    return gpus


def has_gpu():
    return any(g["compatible"] for g in detect_gpus())


def current_watts(mode):
    if mode == "gpu":
        w = sum(g["power"] for g in nvidia_stats())
        return w if w > 0 else float(cfg["power_watts_gpu"])
    return float(cfg["power_watts_cpu"])


# ══════════════════════════════════════════════════════════════════
#  DOWNLOAD & EKSTRAK (aman)
# ══════════════════════════════════════════════════════════════════
def download(url, dest, progress=None):
    try:
        r = requests.get(url, stream=True, timeout=300, allow_redirects=True, headers=UA)
        if r.status_code != 200:
            return None
        total = int(r.headers.get("content-length", 0))
        done, last, h = 0, -10, hashlib.sha256()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(65536):
                if chunk:
                    f.write(chunk); h.update(chunk); done += len(chunk)
                    if progress and total:
                        pct = int(done * 100 / total)
                        if pct - last >= 10:
                            last = pct; progress(pct)
        return h.hexdigest() if dest.stat().st_size > 1000 else None
    except Exception as e:
        log(f"Download error: {e}", "err")
        return None


def safe_extract(archive, dest):
    dest = Path(dest).resolve()
    s = str(archive).lower()
    if s.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            for n in z.namelist():
                if not (dest / n).resolve().is_relative_to(dest):
                    raise ValueError("Arsip berisi path berbahaya")
            z.extractall(dest)
    elif s.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive, "r:gz") as t:
            for m in t.getmembers():
                if not (dest / m.name).resolve().is_relative_to(dest) or m.issym() or m.islnk():
                    raise ValueError("Arsip berisi entri berbahaya")
            t.extractall(dest)
    else:
        raise ValueError("Format arsip tidak didukung")


def ensure_binary(kind):
    """Kembalikan Path executable miner; unduh jika belum ada."""
    src = SOURCES[kind].get("windows" if IS_WIN else "linux") if (IS_WIN or IS_LINUX) else None
    if not src:
        log(f"{kind} tidak didukung di OS ini", "err")
        return None
    url, names = src
    target_dir = MINER_DIR / kind
    for n in names:
        if (target_dir / n).exists():
            return target_dir / n
    log(f"Mengunduh {kind}...")
    arc = BASE_DIR / (kind + (".zip" if url.endswith(".zip") else ".tar.gz"))
    digest = download(url, arc, lambda p: log(f"    {p}%"))
    if not digest:
        log(f"Download {kind} gagal", "err")
        return None
    log(f"SHA256 unduhan: {digest}")
    expected = cfg["sha256_" + kind].lower().strip()
    if expected and expected != digest:
        log("SHA256 TIDAK COCOK - dibatalkan!", "err")
        arc.unlink(missing_ok=True)
        return None
    tmp = Path(tempfile.mkdtemp(prefix="pegasus_"))
    try:
        safe_extract(arc, tmp)
        found = next((Path(r) / f for r, _, fs in os.walk(tmp) for f in fs
                      if f.lower() in [n.lower() for n in names]), None)
        if not found:
            log("Binary tidak ditemukan di arsip", "err")
            return None
        shutil.copytree(found.parent, target_dir, dirs_exist_ok=True)
        exe = target_dir / found.name
        if not IS_WIN:
            exe.chmod(0o755)
        log(f"{kind} siap: {exe}", "ok")
        return exe
    except Exception as e:
        log(f"Ekstrak gagal: {e}", "err")
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        arc.unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════
#  STATISTIK REAL-TIME
# ══════════════════════════════════════════════════════════════════
class Stats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.accepted = self.rejected = 0
        self.hr10 = self.hr60 = self.hr15m = self.hr_max = 0.0
        self.diff = 0
        self.latency = 0
        self.uptime = 0
        self.pool = ""
        self.connection = "OFFLINE"
        self.source = "-"
        self.hr_hist = deque(maxlen=120)

    def best_hr(self):
        return self.hr60 or self.hr10 or self.hr15m


stats = Stats()
_HR_UNITS = {"h/s": 1, "kh/s": 1e3, "mh/s": 1e6, "gh/s": 1e9, "th/s": 1e12}


def poll_xmrig():
    d = http_json(f"http://127.0.0.1:{XMRIG_API}/2/summary")
    if not d:
        return False
    tot = ((d.get("hashrate") or {}).get("total") or []) + [0, 0, 0]
    stats.hr10, stats.hr60, stats.hr15m = (float(x or 0) for x in tot[:3])
    stats.hr_max = max(stats.hr_max, float((d.get("hashrate") or {}).get("highest") or 0), stats.hr10)
    res, conn = d.get("results") or {}, d.get("connection") or {}
    stats.accepted = int(res.get("shares_good", 0) or 0)
    stats.rejected = max(0, int(res.get("shares_total", 0) or 0) - stats.accepted)
    stats.diff = int(res.get("diff_current", 0) or 0)
    stats.latency = int(conn.get("ping", 0) or 0)
    stats.pool = str(conn.get("pool", ""))
    stats.connection = "CONNECTED" if (conn.get("uptime") or 0) > 0 else "CONNECTING"
    stats.uptime = int(d.get("uptime", 0) or 0)
    stats.source = "xmrig-api"
    return True


def poll_lolminer():
    d = http_json(f"http://127.0.0.1:{LOL_API}/")
    if not d:
        return False
    alg = (d.get("Algorithms") or [{}])[0]
    mult = _HR_UNITS.get(str(alg.get("Performance_Unit", "mh/s")).lower(), 1e6)
    hr = _num(alg.get("Total_Performance")) * mult
    stats.hr10 = stats.hr60 = stats.hr15m = hr
    stats.hr_max = max(stats.hr_max, hr)
    sess = d.get("Session") or {}
    stats.accepted = int(_num(alg.get("Total_Accepted", sess.get("Accepted", 0))))
    stats.rejected = int(_num(alg.get("Total_Rejected", 0)))
    stats.uptime = int(_num(sess.get("Uptime", 0)))
    stats.pool = str((d.get("Stratum") or {}).get("Current_Pool", ""))
    stats.latency = int(_num((d.get("Stratum") or {}).get("Average_Latency", 0)))
    stats.connection = "CONNECTED" if hr > 0 else "CONNECTING"
    stats.source = "lolminer-api"
    return True


_RE_SPEED = re.compile(r"speed\s+10s/60s/15m\s+([\d.]+|n/a)\s+([\d.]+|n/a)\s+([\d.]+|n/a)\s+(\w+)/s", re.I)
_RE_ACC = re.compile(r"accepted\s*\((\d+)/(\d+)\)", re.I)


def poll_logfile(path):
    """Cadangan jika API lokal tidak tersedia: baca ekor log XMRig."""
    try:
        lines = Path(path).read_text(errors="ignore").splitlines()[-60:]
    except Exception:
        return False
    ok = False
    for ln in lines:
        m = _RE_SPEED.search(ln)
        if m:
            mult = {"h": 1, "kh": 1e3, "mh": 1e6, "gh": 1e9}.get(m.group(4).lower(), 1)
            v = [_num(x) * mult for x in m.groups()[:3]]
            stats.hr10, stats.hr60, stats.hr15m = v
            stats.hr_max = max(stats.hr_max, v[0])
            ok = True
        m = _RE_ACC.search(ln)
        if m:
            stats.accepted, stats.rejected = int(m.group(1)), int(m.group(2))
            ok = True
    if ok:
        stats.source = "log"
        stats.connection = "CONNECTED"
    return ok


# ══════════════════════════════════════════════════════════════════
#  RIWAYAT & BENCHMARK
# ══════════════════════════════════════════════════════════════════
class History:
    def __init__(self):
        self.db = load_json(HISTORY_DB, {"sessions": []})
        self.cur = None

    def start(self, algo, region, mode, watts):
        self.cur = {"id": datetime.now().strftime("%Y%m%d_%H%M%S"), "algo": algo, "region": region,
                    "mode": mode, "start": datetime.now().isoformat(timespec="seconds"), "end": None,
                    "duration": 0, "accepted": 0, "rejected": 0, "hashrate_avg": 0.0,
                    "hashrate_max": 0.0, "est_btc": 0.0, "est_usd": 0.0, "energy_kwh": 0.0,
                    "cost_usd": 0.0, "_n": 0}

    def update(self):
        c = self.cur
        if not c:
            return
        c["accepted"], c["rejected"] = stats.accepted, stats.rejected
        hr = stats.best_hr()
        if hr > 0:
            c["hashrate_avg"] = (c["hashrate_avg"] * c["_n"] + hr) / (c["_n"] + 1)
            c["_n"] += 1
            c["hashrate_max"] = max(c["hashrate_max"], hr)

    def accrue(self, btc, usd, kwh, cost):
        if self.cur:
            self.cur["est_btc"] += btc; self.cur["est_usd"] += usd
            self.cur["energy_kwh"] += kwh; self.cur["cost_usd"] += cost

    def end(self):
        c = self.cur
        if not c:
            return
        self.update()
        c["end"] = datetime.now().isoformat(timespec="seconds")
        c["duration"] = int((datetime.now() - datetime.fromisoformat(c["start"])).total_seconds())
        self.db["sessions"].append({k: v for k, v in c.items() if not k.startswith("_")})
        save_json(HISTORY_DB, self.db)
        self.cur = None

    def totals(self):
        s = self.db["sessions"]
        return {"sessions": len(s), "time": sum(x.get("duration", 0) for x in s),
                "accepted": sum(x.get("accepted", 0) for x in s),
                "rejected": sum(x.get("rejected", 0) for x in s),
                "est_btc": sum(x.get("est_btc", 0) for x in s),
                "est_usd": sum(x.get("est_usd", 0) for x in s),
                "cost_usd": sum(x.get("cost_usd", 0) for x in s)}

    def export_csv(self, path):
        cols = ["id", "start", "end", "duration", "algo", "region", "mode", "accepted", "rejected",
                "hashrate_avg", "hashrate_max", "est_btc", "est_usd", "energy_kwh", "cost_usd"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for s in self.db["sessions"]:
                w.writerow([s.get(c, "") for c in cols])

    def export_json(self, path):
        save_json(path, self.db)

    def clear(self):
        self.db = {"sessions": []}
        save_json(HISTORY_DB, self.db)


history = History()


def record_benchmark(algo, hashrate, watts, mode, force=False):
    if hashrate <= 0:
        return
    db = load_json(BENCH_DB, {})
    old = db.get(algo)
    hr = hashrate if (force or not old) else old["hashrate"] * 0.7 + hashrate * 0.3
    db[algo] = {"hashrate": hr, "watts": watts, "mode": mode, "ts": datetime.now().isoformat(timespec="seconds")}
    save_json(BENCH_DB, db)


# ══════════════════════════════════════════════════════════════════
#  MINER MANAGER
# ══════════════════════════════════════════════════════════════════
def pid_alive(pid):
    try:
        if psutil:
            return psutil.pid_exists(pid) and psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def read_pidfile():
    d = load_json(PID_FILE, None)
    if d and pid_alive(int(d.get("pid", 0))):
        return d
    return None


class MinerManager:
    def __init__(self):
        self.proc = None
        self.owned = False
        self.start_t = None
        self.log_file = None
        self.log_handle = None
        self.algo = cfg["algo"].upper()
        self.region = cfg["region"]
        self.mode = "cpu"
        self.watchdog = False
        self._wd = None
        self._stopping = False
        self._last_tick = time.time()
        self._last_hist = 0.0
        self._last_bench = 0.0
        self._restarts = 0

    # ---- status ----
    def is_running(self):
        if self.proc is not None:
            return self.proc.poll() is None
        ext = read_pidfile()
        if ext:  # miner dijalankan oleh proses lain: mode attach
            self.algo, self.mode = ext.get("algo", self.algo), ext.get("mode", self.mode)
            return True
        return False

    def uptime(self):
        return fmt_dur(time.time() - self.start_t) if self.start_t else fmt_dur(stats.uptime)

    # ---- command builder ----
    def _host(self, algo, region):
        return f"{algo.lower()}.{region}.nicehash.com"

    def _cmd_xmrig(self, exe, algo, region):
        cmd = [str(exe), "-o", f"{self._host(algo, region)}:{cfg['port']}",
               "-u", f"{cfg['wallet']}.{cfg['worker']}", "-p", "x", "-a", CPU_ALGOS[algo],
               "-k", "--nicehash", "--no-color", "--print-time", "10", "--donate-level", "1",
               "--retries", "5", "--retry-pause", "5",
               "--http-host", "127.0.0.1", "--http-port", str(XMRIG_API),
               "--cpu-priority", str(cfg["cpu_priority"])]
        if int(cfg["cpu_threads_pct"]) < 100:
            cmd.append(f"--cpu-max-threads-hint={int(cfg['cpu_threads_pct'])}")
        return cmd

    def _cmd_lol(self, exe, algo, region):
        lol = GPU_ALGOS[algo]
        cmd = [str(exe), "--algo", lol, "--pool", f"{self._host(algo, region)}:{cfg['port']}",
               "--user", f"{cfg['wallet']}.{cfg['worker']}", "--pass", "x", "--tls", "0",
               "--apiport", str(LOL_API), "--nocolor"]
        if lol == "ETCHASH":
            cmd += ["--ethstratum", "ETHV1"]
        return cmd

    # ---- start / stop ----
    def start(self, algo=None, region=None, say=log):
        algo = (algo or self.algo).upper()
        region = region or self.region
        if self.is_running():
            say("Miner sudah berjalan", "warn")
            return True
        if not cfg["wallet"]:
            say("Wallet belum diatur: python ... config wallet <alamat>", "err")
            return False
        if region not in REGIONS:
            say(f"Region tidak valid: {', '.join(REGIONS)}", "err")
            return False
        if algo in CPU_ALGOS:
            mode = "cpu"
        elif algo in GPU_ALGOS:
            mode = "gpu"
            if not has_gpu():
                say("Tidak ada GPU NVIDIA/AMD yang kompatibel. Pakai algoritma CPU.", "err")
                return False
        else:
            say(f"Algoritma tidak didukung: {algo}", "err")
            return False
        exe = ensure_binary("xmrig" if mode == "cpu" else "lolminer")
        if not exe:
            return False
        cmd = (self._cmd_xmrig if mode == "cpu" else self._cmd_lol)(exe, algo, region)
        say(f"Mode {mode.upper()} | {algo} | {self._host(algo, region)}:{cfg['port']}")

        self.log_file = LOGS_DIR / f"miner_{datetime.now():%Y%m%d_%H%M%S}.log"
        kw = ({"creationflags": 0x00000200 | 0x08000000} if IS_WIN else {"start_new_session": True})
        try:
            self.log_handle = open(self.log_file, "w", encoding="utf-8", errors="ignore")
            self.proc = subprocess.Popen(cmd, stdout=self.log_handle, stderr=subprocess.STDOUT,
                                         cwd=str(exe.parent), **kw)
        except Exception as e:
            say(f"Gagal start: {e}", "err")
            return False
        self.owned, self._stopping = True, False
        self.algo, self.region, self.mode = algo, region, mode
        self.start_t = time.time()
        self._last_tick = time.time()
        stats.reset()
        stats.connection = "CONNECTING"
        save_json(PID_FILE, {"pid": self.proc.pid, "algo": algo, "mode": mode, "region": region,
                             "started": datetime.now().isoformat(timespec="seconds")})
        history.start(algo, region, mode, current_watts(mode))
        time.sleep(6)
        if self.proc.poll() is not None:
            say("Miner langsung berhenti. Log terakhir:", "err")
            for ln in self._tail(8):
                say("    " + ln, "err")
            self._cleanup()
            return False
        say(f"MINER BERJALAN - PID {self.proc.pid}", "ok")
        self.watchdog = True
        if not (self._wd and self._wd.is_alive()):
            self._wd = threading.Thread(target=self._watch, daemon=True)
            self._wd.start()
        return True

    def _tail(self, n=20):
        try:
            return Path(self.log_file).read_text(errors="ignore").splitlines()[-n:]
        except Exception:
            return []

    def _cleanup(self):
        try:
            if self.log_handle:
                self.log_handle.close()
        except Exception:
            pass
        self.log_handle = None
        PID_FILE.unlink(missing_ok=True)
        stats.connection = "OFFLINE"
        history.end()
        self.proc, self.start_t = None, None

    def stop(self):
        self._stopping, self.watchdog = True, False
        p = self.proc
        if p is not None and p.poll() is None:
            try:
                if IS_WIN:
                    import signal
                    p.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    p.terminate()
                p.wait(timeout=8)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        elif p is None:
            return stop_external()
        self._cleanup()
        return True

    def _watch(self):
        while self.watchdog:
            time.sleep(10)
            if not self.watchdog or self._stopping:
                break
            if self.proc is not None and self.proc.poll() is not None:
                if self.start_t and time.time() - self.start_t > 600:
                    self._restarts = 0
                if self._restarts >= 5:
                    log("Miner mati terus - watchdog berhenti", "err")
                    self._cleanup()
                    break
                self._restarts += 1
                algo, region = self.algo, self.region
                log(f"Miner mati, restart #{self._restarts}...", "warn")
                self._cleanup()
                time.sleep(min(60, 5 * self._restarts))
                if not self.start(algo, region, lambda m, t="info": None):
                    continue

    # ---- siklus real-time ----
    def poll(self):
        ok = poll_xmrig() if self.mode == "cpu" else poll_lolminer()
        if not ok and self.log_file and self.mode == "cpu":
            poll_logfile(self.log_file)
        stats.hr_hist.append(stats.best_hr())

    def tick(self):
        self.poll()
        now = time.time()
        dt, self._last_tick = now - self._last_tick, now
        if not self.is_running() or dt > 60:
            return
        hr, w = stats.best_hr(), current_watts(self.mode)
        est = profit_estimate(self.algo, hr, w)
        if est:
            history.accrue(est["rev_btc_day"] * dt / 86400, est["rev_usd_day"] * dt / 86400,
                           w / 1000 * dt / 3600, est["cost_usd_day"] * dt / 86400)
        if now - self._last_hist > 30:
            self._last_hist = now
            history.update()
        if self.start_t and now - self.start_t > 180 and now - self._last_bench > 60 and hr > 0:
            self._last_bench = now
            record_benchmark(self.algo, hr, w, self.mode)

    def autoswitch(self):
        bench = load_json(BENCH_DB, {})
        best, best_net = None, None
        for algo, b in bench.items():
            if (b["mode"] == "gpu" and not has_gpu()) or algo not in {**CPU_ALGOS, **GPU_ALGOS}:
                continue
            e = profit_estimate(algo, b["hashrate"], b["watts"])
            if e and (best_net is None or e["net_usd_day"] > best_net):
                best, best_net = algo, e["net_usd_day"]
        cur = bench.get(self.algo)
        cur_est = profit_estimate(self.algo, cur["hashrate"], cur["watts"]) if cur else None
        cur_net = cur_est["net_usd_day"] if cur_est else float("-inf")
        margin = float(cfg["autoswitch_margin"])
        if best and best != self.algo and best_net > cur_net + abs(cur_net if cur_net != float("-inf") else 0) * margin:
            log(f"Auto-switch {self.algo} -> {best} (net ${best_net:.4f}/hari)", "gold")
            region = self.region
            self.stop()
            time.sleep(2)
            self.start(best, region)


miner = MinerManager()


def stop_external():
    d = read_pidfile()
    if not d:
        return False
    pid = int(d["pid"])
    try:
        if psutil:
            pr = psutil.Process(pid)
            if not any(k in pr.name().lower() for k in ("xmrig", "lolminer")):
                log("PID bukan proses miner - tidak dihentikan", "err")
                return False
            pr.terminate()
            try:
                pr.wait(8)
            except Exception:
                pr.kill()
        else:
            os.kill(pid, 15)
    except Exception as e:
        log(f"Gagal menghentikan: {e}", "err")
        return False
    PID_FILE.unlink(missing_ok=True)
    return True


# ══════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════
def render_dashboard():
    s, hr = stats, stats.best_hr()
    w = current_watts(miner.mode)
    est = profit_estimate(miner.algo, hr, w)
    price = get_prices().get("usd", 0)
    run = miner.is_running()
    L = []
    add = L.append
    bar = "─" * 66
    add(f"{C.BOLD}{C.CYAN}PEGASUS NICEHASH MINER v{VERSION}{C.RESET}   {C.GRAY}{datetime.now():%Y-%m-%d %H:%M:%S}{C.RESET}")
    add(bar)
    status = f"{C.GREEN}● MINING{C.RESET}" if run else f"{C.RED}○ OFFLINE{C.RESET}"
    add(f" Status   {status}   Uptime {C.YELLOW}{miner.uptime()}{C.RESET}   Sumber data: {s.source}")
    add(f" Algo     {C.YELLOW}{miner.algo}{C.RESET} ({miner.mode.upper()})   Region {miner.region}   Pool {s.pool or '-'}")
    add(bar)
    add(f" Hashrate  60s {C.GREEN}{fmt_hr(s.hr60)}{C.RESET} | 10s {fmt_hr(s.hr10)} | 15m {fmt_hr(s.hr15m)} | max {fmt_hr(s.hr_max)}")
    add(f" Tren      {C.GREEN}{spark(s.hr_hist)}{C.RESET}")
    add(f" Share     diterima {C.GREEN}{s.accepted}{C.RESET} | ditolak {C.RED}{s.rejected}{C.RESET} | diff {s.diff} | latency {s.latency} ms")
    add(f" Koneksi   {C.GREEN if s.connection == 'CONNECTED' else C.YELLOW}{s.connection}{C.RESET}")
    add(bar)
    if miner.mode == "gpu":
        for i, g in enumerate(nvidia_stats()):
            add(f" GPU{i}     {g['name'][:28]} | {g['temp']:.0f}°C | {g['power']:.0f} W | util {g['util']:.0f}%")
    c = cpu_stats()
    add(f" CPU       load {c['load'] if c['load'] is not None else '-'}% | suhu {('%.0f°C' % c['temp']) if c['temp'] else '-'} | daya (config) {w:.0f} W")
    add(bar)
    if est:
        col = C.GREEN if est["net_usd_day"] > 0 else C.RED
        add(f" ESTIMASI/HARI  pendapatan ${est['rev_usd_day']:.4f} ({est['rev_btc_day']:.8f} BTC)")
        add(f"                listrik   ${est['cost_usd_day']:.4f}   NET {col}${est['net_usd_day']:.4f}{C.RESET}")
    else:
        add(f" ESTIMASI/HARI  menunggu hashrate / data harga NiceHash...")
    cur = history.cur
    if cur:
        add(f" SESI INI (est) {cur['est_btc']:.10f} BTC (${cur['est_usd']:.5f}) | listrik ${cur['cost_usd']:.5f} | {cur['energy_kwh']:.4f} kWh")
    if nh.configured():
        bal = cached("balance", 60, lambda: nh.btc_balance()[0])
        if bal:
            add(f" SALDO ASLI NiceHash  tersedia {C.YELLOW}{_num(bal.get('available')):.8f}{C.RESET} BTC "
                f"(${_num(bal.get('available')) * price:.2f})")
    else:
        add(f" {C.GRAY}Saldo asli: isi API key read-only (config nh_api_key / nh_api_secret / nh_org_id){C.RESET}")
    add(bar)
    add(f" {C.GRAY}Estimasi belum termasuk fee NiceHash. Ctrl+C untuk keluar.{C.RESET}")
    return L


def draw(lines):
    sys.stdout.write("\033[H" + "".join(ln + "\033[K\n" for ln in lines) + "\033[J")
    sys.stdout.flush()


def live_loop():
    sys.stdout.write("\033[2J")
    last_switch = last_snap = time.time()
    try:
        while miner.is_running():
            miner.tick()
            draw(render_dashboard())
            now = time.time()
            if now - last_snap > 300:
                last_snap = now
                snapshot_balance()
            if miner.owned and cfg["autoswitch"] and now - last_switch > float(cfg["autoswitch_minutes"]) * 60:
                last_switch = now
                miner.autoswitch()
            time.sleep(2)
        print()
        log("Miner berhenti.", "warn")
    except KeyboardInterrupt:
        print()
        if miner.owned:
            log("Menghentikan miner...", "warn")
            miner.stop()
            log("Miner dihentikan, sesi tersimpan.", "ok")
        else:
            log("Dashboard ditutup (miner tetap berjalan).", "info")


# ══════════════════════════════════════════════════════════════════
#  PERINTAH CLI
# ══════════════════════════════════════════════════════════════════
def banner():
    print(f"{C.BOLD}{C.CYAN}=== {BRAND} - NICEHASH MINER v{VERSION} (open source, MIT) ==={C.RESET}\n")


def cmd_start(args):
    algo = args.algo.upper() if args.algo else cfg["algo"].upper()
    region = args.region.lower() if args.region else cfg["region"]
    if miner.start(algo, region):
        live_loop()


def cmd_stop(args):
    if miner.proc is None:
        ok = stop_external()
    else:
        ok = miner.stop()
    log("Miner dihentikan." if ok else "Tidak ada miner yang berjalan.", "ok" if ok else "warn")


def cmd_dashboard(args):
    if not miner.is_running():
        log("Tidak ada miner yang berjalan. Jalankan: start", "warn")
        return
    live_loop()


def cmd_status(args):
    if miner.is_running():
        miner.poll()
    draw_lines = render_dashboard()
    print("\n".join(draw_lines))


def cmd_wallet(args):
    banner()
    price = get_prices()
    print(f"Harga BTC: ${price.get('usd', 0):,.2f} | Rp {price.get('idr', 0):,.0f}\n")
    if nh.configured():
        data, err = nh.btc_balance()
        if data:
            av, tot = _num(data.get("available")), _num(data.get("totalBalance"))
            print(f"{C.BOLD}SALDO ASLI NICEHASH{C.RESET}")
            print(f"  Tersedia : {av:.8f} BTC (${av * price.get('usd', 0):,.2f})")
            print(f"  Total    : {tot:.8f} BTC (${tot * price.get('usd', 0):,.2f})")
            snapshot_balance()
        else:
            log(f"Gagal ambil saldo: {err}", "err")
        rigs, err = nh.rigs()
        if rigs:
            print(f"  Unpaid   : {rigs.get('unpaidAmount', '-')} BTC")
            for r in (rigs.get("miningRigs") or [])[:10]:
                print(f"  Rig      : {r.get('name', '?')} - {r.get('minerStatus', '?')}")
    else:
        print("Saldo asli belum aktif. Buat API key di nicehash.com (Settings > API Keys)")
        print("dengan izin READ-ONLY (view wallet + view mining), lalu atur lewat env var")
        print("NICEHASH_API_KEY / NICEHASH_API_SECRET / NICEHASH_ORG_ID atau perintah 'config'.")
    t = history.totals()
    print(f"\n{C.BOLD}ESTIMASI DARI RIWAYAT (bukan saldo){C.RESET}")
    print(f"  Pendapatan est. : {t['est_btc']:.10f} BTC (${t['est_usd']:.4f})")
    print(f"  Biaya listrik   : ${t['cost_usd']:.4f}   NET ${t['est_usd'] - t['cost_usd']:.4f}")
    print(f"  Wallet tujuan   : {cfg['wallet']}")


def cmd_profit(args):
    banner()
    algos, bench = get_algos(), load_json(BENCH_DB, {})
    if not algos:
        log("Gagal ambil data NiceHash", "err")
        return
    print(f"{C.BOLD}{'ALGO':<16}{'MODE':<6}{'HASHRATE':<14}{'WATT':<7}{'REV $/hari':<12}{'NET $/hari':<12}{C.RESET}")
    rows = []
    for algo, b in bench.items():
        e = profit_estimate(algo, b["hashrate"], b["watts"])
        if e:
            rows.append((e["net_usd_day"], algo, b, e))
    for net, algo, b, e in sorted(rows, reverse=True):
        col = C.GREEN if net > 0 else C.RED
        print(f"{algo:<16}{b['mode'].upper():<6}{fmt_hr(b['hashrate']):<14}{b['watts']:<7.0f}"
              f"{e['rev_usd_day']:<12.4f}{col}{net:<12.4f}{C.RESET}")
    if not rows:
        print("Belum ada benchmark. Jalankan: benchmark --seconds 180")
    print(f"\nListrik: ${cfg['electricity_usd_kwh']}/kWh. Net negatif = mining merugi.")


def cmd_algos(args):
    banner()
    algos = get_algos()
    if not algos:
        log("Gagal ambil data NiceHash", "err")
        return
    print(f"{C.BOLD}{'ALGORITMA':<24}{'BTC/unit/hari':<18}{'UNIT':<6}{'DIDUKUNG':<10}{C.RESET}")
    for name, a in sorted(algos.items(), key=lambda x: x[0]):
        sup = "CPU" if name in CPU_ALGOS else "GPU" if name in GPU_ALGOS else "-"
        print(f"{name:<24}{a['paying']:<18.10f}{a['unit']:<6}{sup:<10}")


def cmd_benchmark(args):
    banner()
    algos = [a.upper() for a in args.algos] if args.algos else \
        list(CPU_ALGOS) + (list(GPU_ALGOS) if has_gpu() else [])
    for algo in algos:
        log(f"Benchmark {algo} selama {args.seconds} detik...")
        if not miner.start(algo, None):
            continue
        t0 = time.time()
        try:
            while time.time() - t0 < args.seconds and miner.is_running():
                miner.tick()
                time.sleep(3)
            hr = stats.hr15m or stats.best_hr()
            if hr > 0:
                record_benchmark(algo, hr, current_watts(miner.mode), miner.mode, force=True)
                log(f"{algo}: {fmt_hr(hr)}", "ok")
            else:
                log(f"{algo}: tidak ada hashrate", "warn")
        except KeyboardInterrupt:
            miner.stop()
            return
        miner.stop()
        time.sleep(2)
    cmd_profit(args)


def cmd_gpu(args):
    banner()
    gpus = detect_gpus()
    if not gpus:
        print("Tidak ada GPU terdeteksi. Gunakan algoritma CPU (RANDOMXMONERO).")
        return
    for i, g in enumerate(gpus, 1):
        st = f"{C.GREEN}kompatibel{C.RESET}" if g["compatible"] else f"{C.RED}tidak{C.RESET}"
        print(f"{i}. {g['name']} | {g['vendor']} | VRAM {g['vram']} MB | {st}")


def cmd_history(args):
    banner()
    t = history.totals()
    print(f"Sesi {t['sessions']} | waktu {fmt_dur(t['time'])} | diterima {t['accepted']} | ditolak {t['rejected']}")
    print(f"Estimasi pendapatan ${t['est_usd']:.4f} | listrik ${t['cost_usd']:.4f}\n")
    print(f"{C.BOLD}{'ID':<17}{'DURASI':<10}{'ALGO':<16}{'ACC':<6}{'REJ':<6}{'EST BTC':<14}{C.RESET}")
    for s in reversed(history.db["sessions"][-20:]):
        print(f"{s.get('id', ''):<17}{fmt_dur(s.get('duration', 0)):<10}{s.get('algo', ''):<16}"
              f"{s.get('accepted', 0):<6}{s.get('rejected', 0):<6}{s.get('est_btc', 0):<14.10f}")


def cmd_export(args):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fmt = args.format.lower()
    if fmt not in ("csv", "json"):
        log("Format harus csv atau json", "err")
        return
    path = BASE_DIR / f"pegasus_history_{ts}.{fmt}"
    (history.export_csv if fmt == "csv" else history.export_json)(path)
    log(f"Diekspor: {path}", "ok")


def cmd_clear_history(args):
    if input("Hapus SEMUA riwayat? (yes/no): ").strip().lower() == "yes":
        history.clear()
        log("Riwayat dihapus", "ok")


def cmd_config(args):
    if args.key and args.value is not None:
        try:
            cfg.set(args.key, args.value)
            log(f"{args.key} diatur.", "ok")
        except Exception as e:
            log(str(e), "err")
        return
    banner()
    for k in DEFAULTS:
        v = cfg.data[k]
        if k in SECRET_KEYS and v:
            v = v[:4] + "****"
        print(f"  {k:<22}= {v}")
    print(f"\nUbah: config <kunci> <nilai>   File: {CONFIG_FILE}")


def cmd_test(args):
    algo, region = cfg["algo"].lower(), cfg["region"]
    host, port = f"{algo}.{region}.nicehash.com", int(cfg["port"])
    try:
        t0 = time.time()
        socket.create_connection((host, port), timeout=8).close()
        log(f"{host}:{port} OK - latency {int((time.time() - t0) * 1000)} ms", "ok")
    except Exception as e:
        log(f"{host}:{port} gagal: {e}", "err")


def cmd_install(args):
    ensure_binary("xmrig")
    ensure_binary("lolminer")


def cmd_tune(args):
    banner()
    print("""Cara NYATA menaikkan hashrate (bukan angka palsu):
 CPU (RandomX)
  - Aktifkan huge pages (Linux: sudo sysctl -w vm.nr_hugepages=1280; Windows: jalankan
    sebagai Administrator agar XMRig bisa memakai large pages).
  - Jalankan sebagai root/admin agar XMRig memasang MSR mod (naik 10-15% di banyak CPU).
  - RAM dual-channel + XMP/EXPO; RandomX sangat bergantung pada cache L3 dan RAM.
  - Hindari 100% thread jika PC dipakai kerja: config cpu_threads_pct 75.
 GPU
  - Undervolt + naikkan memory clock (MSI Afterburner / nvidia-smi -pl) untuk efisiensi.
  - Pastikan suhu < 70C; kipas dan airflow menentukan stabilitas.
 Profit
  - Ukur watt dengan watt-meter lalu isi power_watts_cpu / power_watts_gpu.
  - Isi electricity_usd_kwh sesuai tarif Anda, lalu jalankan: benchmark, profit, atau
    aktifkan auto-switch (config autoswitch true).""")


def cmd_menu(args):
    items = [("1", "Start mining", lambda: cmd_start(argparse.Namespace(algo=None, region=None))),
             ("2", "Stop mining", lambda: cmd_stop(None)),
             ("3", "Dashboard real-time", lambda: cmd_dashboard(None)),
             ("4", "Saldo & wallet", lambda: cmd_wallet(None)),
             ("5", "Profit per algoritma", lambda: cmd_profit(None)),
             ("6", "Benchmark", lambda: cmd_benchmark(argparse.Namespace(algos=None, seconds=180))),
             ("7", "Riwayat", lambda: cmd_history(None)),
             ("8", "Daftar algoritma NiceHash", lambda: cmd_algos(None)),
             ("9", "GPU", lambda: cmd_gpu(None)),
             ("10", "Config", lambda: cmd_config(argparse.Namespace(key=None, value=None))),
             ("11", "Test koneksi pool", lambda: cmd_test(None)),
             ("12", "Install binary", lambda: cmd_install(None)),
             ("13", "Export CSV", lambda: cmd_export(argparse.Namespace(format="csv"))),
             ("14", "Tips tuning", lambda: cmd_tune(None)),
             ("0", "Keluar", None)]
    while True:
        banner()
        for k, name, _ in items:
            print(f"  [{k}] {name}")
        try:
            ch = input("\nPilihan > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if ch == "0":
            break
        fn = next((f for k, _, f in items if k == ch), None)
        if fn:
            fn()
            try:
                input("\nEnter untuk lanjut...")
            except (EOFError, KeyboardInterrupt):
                break


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
def build_parser():
    p = argparse.ArgumentParser(description=f"{BRAND} NiceHash Miner v{VERSION}")
    p.add_argument("--no-color", action="store_true", help="matikan warna")
    sub = p.add_subparsers(dest="command")
    s = sub.add_parser("start", help="mulai mining + dashboard"); s.add_argument("-a", "--algo"); s.add_argument("-r", "--region")
    sub.add_parser("stop", help="hentikan miner")
    sub.add_parser("dashboard", help="dashboard real-time (attach)")
    sub.add_parser("status", help="ringkasan sekali tampil")
    sub.add_parser("wallet", help="saldo asli NiceHash + estimasi")
    sub.add_parser("profit", help="profit per algoritma (dari benchmark)")
    sub.add_parser("algos", help="daftar algoritma NiceHash live")
    b = sub.add_parser("benchmark", help="ukur hashrate tiap algoritma")
    b.add_argument("--algos", nargs="*"); b.add_argument("--seconds", type=int, default=180)
    sub.add_parser("gpu", help="deteksi GPU")
    sub.add_parser("history", help="riwayat sesi")
    e = sub.add_parser("export", help="export riwayat"); e.add_argument("-f", "--format", default="csv")
    sub.add_parser("clear-history", help="hapus riwayat")
    c = sub.add_parser("config", help="lihat/ubah konfigurasi"); c.add_argument("key", nargs="?"); c.add_argument("value", nargs="?")
    sub.add_parser("test", help="tes koneksi pool")
    sub.add_parser("install", help="unduh XMRig & lolMiner")
    sub.add_parser("tune", help="tips menaikkan hashrate")
    sub.add_parser("menu", help="menu interaktif")
    return p


def main():
    args = build_parser().parse_args()
    if args.no_color:
        C.disable()
    cmds = {"start": cmd_start, "stop": cmd_stop, "dashboard": cmd_dashboard, "status": cmd_status,
            "wallet": cmd_wallet, "profit": cmd_profit, "algos": cmd_algos, "benchmark": cmd_benchmark,
            "gpu": cmd_gpu, "history": cmd_history, "export": cmd_export, "clear-history": cmd_clear_history,
            "config": cmd_config, "test": cmd_test, "install": cmd_install, "tune": cmd_tune,
            "menu": cmd_menu}
    try:
        cmds[args.command or "menu"](args)
    except KeyboardInterrupt:
        print()
        if miner.owned and miner.is_running():
            miner.stop()
    except Exception as e:
        print(f"Fatal: {e}")
        traceback.print_exc()
        if miner.owned and miner.is_running():
            miner.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
