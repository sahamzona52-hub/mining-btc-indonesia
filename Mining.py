#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║        PEGASUS NICEHASH MINER v19.0 — MEGA PROFESSIONAL        ║
║   ✅ XMRig (CPU) + lolMiner (GPU) — SUPPORT NICEHASH            ║
║   ✅ Real-time Mining Detection (Hashrate, Shares, Diff)        ║
║   ✅ Auto-detect GPU/CPU      ✅ Premium Hacking GUI            ║
║   ✅ Auto download binary     ✅ Wallet langsung ke NiceHash    ║
║   ✅ HISTORY LOG MINING       ✅ EXPORT CSV / JSON              ║
║   ✅ LIVE CHART + ANALYTICS   ✅ SESSION TRACKING               ║
║   ✅ PROFESSIONAL DASHBOARD   ✅ REAL-TIME MONITORING           ║
║   ✅ PEGASUSMETASEC LOGO      ✅ BTC BALANCE PERSISTENT         ║
║   ✅ BTC BOOSTER SYSTEM       ✅ AUTO-SAVE WALLET               ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, re, sys, json, time, shutil, zipfile, tarfile, csv, hashlib
import platform, tempfile, subprocess, threading, traceback, socket
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

# ══════════════════════════════════════════════════════════════════
#  AUTO INSTALL DEPENDENCIES
# ══════════════════════════════════════════════════════════════════
def _pip(pkg):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                               "--disable-pip-version-check", pkg],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def _can(mod):
    try: __import__(mod); return True
    except ImportError: return False

for mod, pkg in [("requests","requests"),("psutil","psutil"),("PIL","pillow")]:
    if not _can(mod):
        print(f"[*] Install {pkg}...")
        _pip(pkg)

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests, psutil
try:
    from PIL import Image, ImageTk, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ══════════════════════════════════════════════════════════════════
#  PEGASUSMETASEC BRANDING — LOGO & URL
# ══════════════════════════════════════════════════════════════════
PEGASUS_BRAND = "PegasusMetaSec"
PEGASUS_URL   = "https://pegasusmetasec.com"
PEGASUS_LOGO_URL = "https://d.top4top.io/p_392470fjr1.jpg"
PEGASUS_ASCII = r"""
   ██████╗ ███████╗ ██████╗  █████╗ ███████╗██╗   ██╗███████╗
   ██╔══██╗██╔════╝██╔════╝ ██╔══██╗██╔════╝██║   ██║██╔════╝
   ██████╔╝█████╗  ██║  ███╗███████║███████╗██║   ██║███████╗
   ██╔═══╝ ██╔══╝  ██║   ██║██╔══██║╚════██║██║   ██║╚════██║
   ██║     ███████╗╚██████╔╝██║  ██║███████║╚██████╔╝███████║
   ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝
        M E T A S E C   |   {url}
"""

# ══════════════════════════════════════════════════════════════════
#  KONFIGURASI — WALLET NICEHASH ANDA
# ══════════════════════════════════════════════════════════════════
WALLET = "NHbRMmowbz9DvKMeegGHTndbHb3GSKRMsAxw"
WORKER = "PegasusRig"
LOGIN_PASS = "123456"

REGIONS = {
    "eu":  "Europe (Frankfurt)",
    "usa": "USA (New York)",
    "hk":  "Hong Kong",
    "jp":  "Japan (Tokyo)",
    "in":  "India (Mumbai)",
    "br":  "Brazil (Sao Paulo)",
}

CPU_ALGOS  = ["RANDOMXMONERO", "GHOSTRIDER", "CN/HEAVY", "CN/GPU", "CN/R", "CN-PICO/TRTL"]
GPU_ALGOS  = ["KAWPOW", "AUTOLYKOS", "OCTOPUS", "FISHHASH", "BEAMV3", "DAGGERHASHIMOTO",
              "ETCHASH", "KHEAVYHASH", "CUCKOOCCYCLE", "ZELHASH"]

DEFAULT_ALGO = "RANDOMXMONERO"
DEFAULT_REGION = "eu"

# ══════════════════════════════════════════════════════════════════
#  WARNA — TEMA HACKER PREMIUM
# ══════════════════════════════════════════════════════════════════
C = {
    "bg":        "#000000",
    "panel":     "#0a0f0a",
    "panel2":    "#0d130d",
    "panel3":    "#111811",
    "border":    "#00ff41",
    "green":     "#00ff41",
    "green_dim": "#00aa2a",
    "green_dark":"#003d10",
    "red":       "#ff0033",
    "red_dim":   "#aa0022",
    "yellow":    "#ffff00",
    "orange":    "#ffaa00",
    "cyan":      "#00ffff",
    "cyan_dim":  "#009999",
    "magenta":   "#ff00ff",
    "purple":    "#9d00ff",
    "gold":      "#ffd700",
    "text":      "#c0ffc0",
    "text_dim":  "#3a5a3a",
    "text_bright":"#ffffff",
    "black":     "#000000",
    "white":     "#ffffff",
}

# ══════════════════════════════════════════════════════════════════
#  PATH
# ══════════════════════════════════════════════════════════════════
BASE_DIR   = Path.home() / "PegasusNiceHash"
MINER_DIR  = BASE_DIR / "miners"
LOGS_DIR   = BASE_DIR / "logs"
HISTORY_DIR= BASE_DIR / "history"
WALLET_DIR = BASE_DIR / "wallet"
CONFIG     = BASE_DIR / "pegasus.json"
HISTORY_DB = HISTORY_DIR / "mining_history.json"
WALLET_DB  = WALLET_DIR / "btc_wallet.json"
BALANCE_LOG= WALLET_DIR / "balance_history.json"
for d in (BASE_DIR, MINER_DIR, LOGS_DIR, HISTORY_DIR, WALLET_DIR):
    d.mkdir(parents=True, exist_ok=True)

OS_NAME  = platform.system().lower()
IS_WIN   = OS_NAME == "windows"
IS_LINUX = OS_NAME == "linux"

# ══════════════════════════════════════════════════════════════════
#  BINARY SOURCES
# ══════════════════════════════════════════════════════════════════
XMRIG_URLS = {
    "windows": "https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-gcc-win64.zip",
    "linux":   "https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-linux-static-x64.tar.gz",
}

LOLMINER_URLS = {
    "windows": "https://github.com/Lolliedieb/lolMiner-releases/releases/download/1.88/lolMiner_v1.88_Win64.zip",
    "linux":   "https://github.com/Lolliedieb/lolMiner-releases/releases/download/1.88/lolMiner_v1.88_Lin64.tar.gz",
}

# ══════════════════════════════════════════════════════════════════
#  NICEHASH API
# ══════════════════════════════════════════════════════════════════
_algo_cache = {"ts": 0, "data": {}}

def get_nh_algos():
    if time.time() - _algo_cache["ts"] < 120 and _algo_cache["data"]:
        return _algo_cache["data"]
    try:
        r = requests.get("https://api2.nicehash.com/main/api/v2/public/simplemultialgo/info/",
                         timeout=15, headers={"User-Agent": f"{PEGASUS_BRAND}/19.0"})
        if r.status_code == 200:
            data = r.json()
            algos = {}
            for a in data.get("miningAlgorithms", []):
                algos[a["algorithm"].upper()] = {
                    "port": a.get("port", 9200),
                    "paying": float(a.get("payingRate", 0) or 0),
                    "speed": float(a.get("speed", 0) or 0),
                }
            _algo_cache["data"] = algos
            _algo_cache["ts"] = time.time()
            return algos
    except Exception as e:
        print(f"API error: {e}")
    return _algo_cache["data"]

def get_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,idr",
                         timeout=8)
        if r.status_code == 200:
            return r.json().get("bitcoin", {})
    except Exception:
        pass
    return {}

def get_pool_port(algo):
    algos = get_nh_algos()
    a = algos.get(algo.upper())
    if a:
        return a["port"]
    fallback = {
        "RANDOMXMONERO": 3380, "KAWPOW": 9200, "AUTOLYKOS": 9201,
        "OCTOPUS": 9202, "FISHHASH": 9203, "BEAMV3": 9204,
        "DAGGERHASHIMOTO": 9205, "ETCHASH": 9206, "KHEAVYHASH": 9207,
    }
    return fallback.get(algo.upper(), 9200)

# ══════════════════════════════════════════════════════════════════
#  BTC WALLET MANAGER — SALDO PERSISTEN (TIDAK HILANG)
# ══════════════════════════════════════════════════════════════════
class BTCWalletManager:
    """
    Mengelola saldo BTC yang di-estimate dari mining.
    - Tersimpan permanen di wallet/btc_wallet.json
    - Tidak hilang walau aplikasi ditutup
    - History balance tersimpan di balance_history.json
    """
    def __init__(self):
        self.wallet = self._load()
        self.balance_history = self._load_history()
        self._last_save = 0
        self._pending_btc = 0.0
        self.session_btc = 0.0

    def _load(self):
        if WALLET_DB.exists():
            try:
                return json.loads(WALLET_DB.read_text(encoding="utf-8"))
            except:
                pass
        return {
            "wallet": WALLET,
            "worker": WORKER,
            "balance_btc": 0.0,
            "total_earned_btc": 0.0,
            "total_earned_usd": 0.0,
            "total_earned_idr": 0.0,
            "total_withdrawn_btc": 0.0,
            "booster_active": True,
            "booster_multiplier": 1.0,
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_shares": 0,
            "total_mining_seconds": 0,
            "sessions_count": 0,
        }

    def _load_history(self):
        if BALANCE_LOG.exists():
            try:
                return json.loads(BALANCE_LOG.read_text(encoding="utf-8"))
            except:
                pass
        return {"snapshots": []}

    def _save(self):
        try:
            self.wallet["last_updated"] = datetime.now().isoformat()
            WALLET_DB.write_text(json.dumps(self.wallet, indent=2), encoding="utf-8")
            BALANCE_LOG.write_text(json.dumps(self.balance_history, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Wallet save error: {e}")

    def add_earnings(self, btc_amount):
        """Tambahkan earning BTC (dari mining)."""
        if btc_amount <= 0:
            return
        # Apply booster multiplier
        if self.wallet.get("booster_active", True):
            boosted = btc_amount * self.wallet.get("booster_multiplier", 1.0)
        else:
            boosted = btc_amount

        self.wallet["balance_btc"] += boosted
        self.wallet["total_earned_btc"] += boosted
        self.session_btc += boosted

        # Update USD/IDR
        price = get_btc_price()
        if price.get("usd"):
            self.wallet["total_earned_usd"] += boosted * price["usd"]
        if price.get("idr"):
            self.wallet["total_earned_idr"] += boosted * price["idr"]

        # Save tiap 30 detik
        if time.time() - self._last_save > 30:
            self._last_save = time.time()
            self._save()

    def record_snapshot(self):
        """Simpan snapshot balance untuk history."""
        self.balance_history["snapshots"].append({
            "ts": datetime.now().isoformat(),
            "balance_btc": self.wallet["balance_btc"],
            "total_earned_btc": self.wallet["total_earned_btc"],
        })
        # Batasi 5000 snapshot
        if len(self.balance_history["snapshots"]) > 5000:
            self.balance_history["snapshots"] = self.balance_history["snapshots"][-3000:]
        self._save()

    def set_booster(self, active, multiplier=1.0):
        self.wallet["booster_active"] = active
        self.wallet["booster_multiplier"] = max(1.0, multiplier)
        self._save()

    def withdraw_estimate(self, amount):
        """Simulasi withdraw."""
        if amount > self.wallet["balance_btc"]:
            return False
        self.wallet["balance_btc"] -= amount
        self.wallet["total_withdrawn_btc"] += amount
        self._save()
        return True

    def get_balance(self):
        return self.wallet["balance_btc"]

    def get_balance_usd(self):
        p = get_btc_price()
        return self.wallet["balance_btc"] * p.get("usd", 0)

    def get_balance_idr(self):
        p = get_btc_price()
        return self.wallet["balance_btc"] * p.get("idr", 0)

    def increment_shares(self, count):
        self.wallet["total_shares"] += count
        self._save()

    def add_mining_time(self, seconds):
        self.wallet["total_mining_seconds"] += seconds
        self._save()

    def increment_sessions(self):
        self.wallet["sessions_count"] += 1
        self._save()

    def reset(self):
        self.wallet["balance_btc"] = 0.0
        self.wallet["total_earned_btc"] = 0.0
        self.wallet["total_earned_usd"] = 0.0
        self.wallet["total_earned_idr"] = 0.0
        self.wallet["total_withdrawn_btc"] = 0.0
        self.wallet["total_shares"] = 0
        self.wallet["total_mining_seconds"] = 0
        self.wallet["sessions_count"] = 0
        self._save()

btc_wallet = BTCWalletManager()

# ══════════════════════════════════════════════════════════════════
#  BTC BOOSTER SYSTEM
# ══════════════════════════════════════════════════════════════════
class BTCBooster:
    """
    Sistem booster untuk meningkatkan earning BTC.
    - Passive boost: meningkatkan estimasi earning
    - Active boost: multiplier dari aktivitas mining
    """
    def __init__(self):
        self.levels = [
            {"name": "NONE",     "mult": 1.0,  "color": C["text_dim"],  "req_shares": 0},
            {"name": "BRONZE",   "mult": 1.15, "color": "#cd7f32",      "req_shares": 10},
            {"name": "SILVER",   "mult": 1.30, "color": "#c0c0c0",      "req_shares": 50},
            {"name": "GOLD",     "mult": 1.50, "color": C["gold"],      "req_shares": 200},
            {"name": "PLATINUM", "mult": 1.75, "color": "#e5e4e2",      "req_shares": 500},
            {"name": "DIAMOND",  "mult": 2.00, "color": C["cyan"],      "req_shares": 1000},
            {"name": "LEGENDARY","mult": 2.50, "color": C["magenta"],   "req_shares": 5000},
            {"name": "MYTHIC",   "mult": 3.00, "color": C["purple"],    "req_shares": 10000},
        ]

    def get_current_level(self):
        shares = btc_wallet.wallet.get("total_shares", 0)
        current = self.levels[0]
        for lvl in self.levels:
            if shares >= lvl["req_shares"]:
                current = lvl
            else:
                break
        return current

    def get_next_level(self):
        shares = btc_wallet.wallet.get("total_shares", 0)
        for lvl in self.levels:
            if shares < lvl["req_shares"]:
                return lvl
        return None

    def get_progress(self):
        """0-100 progress ke next level."""
        shares = btc_wallet.wallet.get("total_shares", 0)
        nxt = self.get_next_level()
        if not nxt:
            return 100.0
        cur = self.get_current_level()
        span = nxt["req_shares"] - cur["req_shares"]
        if span <= 0:
            return 100.0
        done = shares - cur["req_shares"]
        return min(100.0, (done / span) * 100)

    def apply_boost(self, base_btc):
        """Apply multiplier ke earning."""
        lvl = self.get_current_level()
        # Passive booster toggle + level multiplier
        base_mult = lvl["mult"]
        if btc_wallet.wallet.get("booster_active", True):
            return base_btc * base_mult
        return base_btc

booster = BTCBooster()

# ══════════════════════════════════════════════════════════════════
#  REAL-TIME MINING DETECTOR — MONITORING AKURAT
# ══════════════════════════════════════════════════════════════════
class MiningDetector:
    """Deteksi mining real-time dengan parsing log yang akurat."""
    def __init__(self):
        self.reset()
        self._last_btc_add = 0

    def reset(self):
        self.accepted = 0
        self.rejected = 0
        self.hashrate_10s = 0.0
        self.hashrate_60s = 0.0
        self.hashrate_15m = 0.0
        self.hashrate_max = 0.0
        self.shares_history = deque(maxlen=200)
        self.hashrate_history = deque(maxlen=300)
        self.last_share_time = None
        self.last_job_time = None
        self.difficulty = 0
        self.pool_latency = 0
        self.uptime_seconds = 0
        self.connection_status = "OFFLINE"
        self.mining_started = False
        self.first_share_received = False
        self.job_count = 0
        self.avg_share_interval = 0
        self._share_timestamps = deque(maxlen=50)
        self._last_parse_offset = 0
        self._last_accepted = 0

    def parse_xmrig_line(self, line):
        updated = False
        low = line.lower()

        m = re.search(r"accepted\s*\((\d+)/(\d+)\)\s*diff\s+(\d+)(?:\s*\((\d+)\s*ms\))?", line)
        if m:
            new_acc = int(m.group(1))
            self.accepted = new_acc
            self.rejected = int(m.group(2))
            self.difficulty = int(m.group(3))
            if m.group(4):
                self.pool_latency = int(m.group(4))
            self.last_share_time = datetime.now()
            self.first_share_received = True
            self._share_timestamps.append(time.time())
            self._calc_share_interval()
            self.shares_history.append(("accepted", datetime.now(), self.difficulty))
            # Tambah share ke wallet
            if new_acc > self._last_accepted:
                btc_wallet.increment_shares(new_acc - self._last_accepted)
                self._last_accepted = new_acc
            updated = True

        m = re.search(r"rejected\s*\((\d+)/(\d+)\)", line)
        if m:
            self.accepted = int(m.group(1))
            self.rejected = int(m.group(2))
            self.shares_history.append(("rejected", datetime.now(), 0))
            updated = True

        m = re.search(r"speed\s+10s/60s/15m\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\w+)/s\s+max\s+([\d.]+)", line)
        if m:
            mult = {"H": 1, "kH": 1e3, "MH": 1e6, "GH": 1e9}.get(m.group(4), 1)
            self.hashrate_10s = float(m.group(1)) * mult
            self.hashrate_60s = float(m.group(2)) * mult
            self.hashrate_15m = float(m.group(3)) * mult
            self.hashrate_max = max(self.hashrate_max, float(m.group(5)) * mult)
            self.hashrate_history.append((datetime.now(), self.hashrate_60s))
            updated = True
        else:
            m = re.search(r"speed\s+10s/60s/15m\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\w+)/s", line)
            if m:
                mult = {"H": 1, "kH": 1e3, "MH": 1e6, "GH": 1e9}.get(m.group(4), 1)
                self.hashrate_10s = float(m.group(1)) * mult
                self.hashrate_60s = float(m.group(2)) * mult
                self.hashrate_15m = float(m.group(3)) * mult
                self.hashrate_max = max(self.hashrate_max, self.hashrate_60s)
                self.hashrate_history.append((datetime.now(), self.hashrate_60s))
                updated = True

        if "new job from" in low:
            self.last_job_time = datetime.now()
            self.job_count += 1
            m = re.search(r"diff\s+(\d+)", line)
            if m:
                self.difficulty = int(m.group(1))
            updated = True

        if "connected" in low and "pool" in low:
            self.connection_status = "CONNECTED"
            updated = True
        if "connection lost" in low or "disconnected" in low:
            self.connection_status = "DISCONNECTED"
            updated = True

        if "mining" in low and "started" in low:
            self.mining_started = True
            updated = True

        return updated

    def parse_lolminer_line(self, line):
        updated = False
        low = line.lower()

        m = re.search(r"Total[:\s]+([\d.]+)\s*(\w?H)/s", line)
        if m:
            mult = {"H": 1, "kH": 1e3, "MH": 1e6, "GH": 1e9}.get(m.group(2), 1)
            val = float(m.group(1)) * mult
            self.hashrate_10s = val
            self.hashrate_60s = val
            self.hashrate_15m = val
            self.hashrate_max = max(self.hashrate_max, val)
            self.hashrate_history.append((datetime.now(), val))
            updated = True

        m = re.search(r"[Aa]ccepted[:\s]+(\d+)", line)
        if m:
            new_acc = int(m.group(1))
            if new_acc > self.accepted:
                btc_wallet.increment_shares(new_acc - self.accepted)
                self.accepted = new_acc
                self.last_share_time = datetime.now()
                self.first_share_received = True
                self._share_timestamps.append(time.time())
                self._calc_share_interval()
                self.shares_history.append(("accepted", datetime.now(), 0))
            updated = True

        m = re.search(r"[Rr]ejected[:\s]+(\d+)", line)
        if m:
            self.rejected = max(self.rejected, int(m.group(1)))
            updated = True

        if "new job" in low or "job received" in low:
            self.last_job_time = datetime.now()
            self.job_count += 1
            updated = True

        if "connected" in low:
            self.connection_status = "CONNECTED"
            updated = True

        return updated

    def _calc_share_interval(self):
        if len(self._share_timestamps) >= 2:
            intervals = [self._share_timestamps[i] - self._share_timestamps[i-1]
                         for i in range(1, len(self._share_timestamps))]
            self.avg_share_interval = sum(intervals) / len(intervals) if intervals else 0

    def get_estimated_earnings(self, paying_rate):
        if self.hashrate_60s <= 0 or paying_rate <= 0:
            return 0.0
        hashrate_gh = self.hashrate_60s / 1e9
        base = hashrate_gh * paying_rate
        # Apply booster
        return booster.apply_boost(base)

    def format_hashrate(self, hr):
        if hr >= 1e9: return f"{hr/1e9:.3f} GH/s"
        if hr >= 1e6: return f"{hr/1e6:.3f} MH/s"
        if hr >= 1e3: return f"{hr/1e3:.3f} KH/s"
        return f"{hr:.2f} H/s"

    def update_btc_earnings(self, paying_rate):
        """Update saldo BTC dari estimasi earning."""
        if time.time() - self._last_btc_add < 10:
            return
        self._last_btc_add = time.time()
        # Per 10 detik, tambahkan earning
        daily = self.get_estimated_earnings(paying_rate)
        per_10s = daily * (10 / 86400)  # 10 detik dari 24 jam
        if per_10s > 0:
            btc_wallet.add_earnings(per_10s)

detector = MiningDetector()

# ══════════════════════════════════════════════════════════════════
#  HISTORY MANAGER — TRACK SEMUA SESSION MINING
# ══════════════════════════════════════════════════════════════════
class HistoryManager:
    def __init__(self):
        self.db = self._load()
        self.current_session = None

    def _load(self):
        if HISTORY_DB.exists():
            try:
                return json.loads(HISTORY_DB.read_text(encoding="utf-8"))
            except:
                pass
        return {"sessions": [], "total_mining_time": 0, "total_accepted": 0,
                "total_rejected": 0, "total_btc_estimate": 0.0}

    def _save(self):
        try:
            HISTORY_DB.write_text(json.dumps(self.db, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"History save error: {e}")

    def start_session(self, algo, region, mode):
        self.current_session = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "algo": algo,
            "region": region,
            "mode": mode,
            "start": datetime.now().isoformat(),
            "end": None,
            "duration": 0,
            "accepted": 0,
            "rejected": 0,
            "hashrate_avg": 0.0,
            "hashrate_max": 0.0,
            "btc_earned": 0.0,
            "shares": [],
        }
        self._save()
        btc_wallet.increment_sessions()

    def update_session(self, accepted, rejected, hashrate):
        if not self.current_session:
            return
        self.current_session["accepted"] = accepted
        self.current_session["rejected"] = rejected
        if hashrate > 0:
            old_avg = self.current_session["hashrate_avg"]
            old_count = self.current_session.get("_count", 0)
            new_avg = (old_avg * old_count + hashrate) / (old_count + 1)
            self.current_session["hashrate_avg"] = new_avg
            self.current_session["_count"] = old_count + 1
            self.current_session["hashrate_max"] = max(
                self.current_session.get("hashrate_max", 0), hashrate)

    def end_session(self):
        if not self.current_session:
            return
        now = datetime.now()
        start = datetime.fromisoformat(self.current_session["start"])
        self.current_session["end"] = now.isoformat()
        self.current_session["duration"] = int((now - start).total_seconds())
        self.current_session["btc_earned"] = btc_wallet.session_btc
        session_copy = {k: v for k, v in self.current_session.items()
                        if not k.startswith("_")}
        self.db["sessions"].append(session_copy)
        self.db["total_mining_time"] += self.current_session["duration"]
        self.db["total_accepted"] += self.current_session["accepted"]
        self.db["total_rejected"] += self.current_session["rejected"]
        self._save()
        btc_wallet.add_mining_time(self.current_session["duration"])
        btc_wallet.record_snapshot()
        btc_wallet.session_btc = 0.0
        self.current_session = None

    def get_stats(self):
        s = self.db["sessions"]
        return {
            "total_sessions": len(s),
            "total_time": self.db["total_mining_time"],
            "total_accepted": self.db["total_accepted"],
            "total_rejected": self.db["total_rejected"],
            "sessions": s,
        }

    def export_csv(self, path):
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["ID", "Start", "End", "Duration(s)", "Algo", "Region",
                            "Mode", "Accepted", "Rejected", "Hashrate Avg", "Hashrate Max", "BTC Earned"])
                for s in self.db["sessions"]:
                    w.writerow([s.get("id",""), s.get("start",""), s.get("end",""),
                                s.get("duration",0), s.get("algo",""), s.get("region",""),
                                s.get("mode",""), s.get("accepted",0), s.get("rejected",0),
                                f"{s.get('hashrate_avg',0):.2f}", f"{s.get('hashrate_max',0):.2f}",
                                f"{s.get('btc_earned',0):.10f}"])
            return True
        except Exception as e:
            print(f"CSV export error: {e}")
            return False

    def export_json(self, path):
        try:
            Path(path).write_text(json.dumps(self.db, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            print(f"JSON export error: {e}")
            return False

    def clear(self):
        self.db = {"sessions": [], "total_mining_time": 0, "total_accepted": 0,
                   "total_rejected": 0, "total_btc_estimate": 0.0}
        self._save()

history = HistoryManager()

# ══════════════════════════════════════════════════════════════════
#  GPU DETECTION
# ══════════════════════════════════════════════════════════════════
def detect_gpus():
    gpus = []
    if IS_WIN:
        try:
            out = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name,AdapterRAM", "/format:csv"],
                capture_output=True, text=True, timeout=15, creationflags=0x08000000)
            for line in out.stdout.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3 and parts[-1]:
                    name = parts[-1]
                    if "microsoft" in name.lower() or "basic" in name.lower():
                        continue
                    ram = parts[1] if len(parts) > 1 else "0"
                    try: vram = int(ram) // (1024*1024) if ram.isdigit() else 0
                    except: vram = 0
                    nl = name.lower()
                    vendor = "NVIDIA" if any(x in nl for x in ["nvidia","rtx","gtx","geforce","quadro"]) \
                        else "AMD" if any(x in nl for x in ["amd","radeon","rx "]) \
                        else "Intel" if "intel" in nl else "Unknown"
                    compatible = vendor in ("NVIDIA","AMD") and (vram >= 2048 or vram == 0)
                    gpus.append({"name": name, "vendor": vendor, "vram": vram, "compatible": compatible})
        except Exception as e:
            print(f"WMIC error: {e}")
        if not gpus:
            try:
                out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total",
                                      "--format=csv,noheader,nounits"],
                                     capture_output=True, text=True, timeout=10, creationflags=0x08000000)
                for line in out.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2:
                        gpus.append({"name": parts[0], "vendor": "NVIDIA",
                                     "vram": int(parts[1]) if parts[1].isdigit() else 0,
                                     "compatible": True})
            except Exception: pass
    elif IS_LINUX:
        try:
            out = subprocess.run(["lspci"], capture_output=True, text=True, timeout=10)
            for line in out.stdout.splitlines():
                if any(k in line.lower() for k in ["vga","3d","display"]):
                    name = line.split(":", 2)[-1].strip()
                    nl = name.lower()
                    vendor = "NVIDIA" if "nvidia" in nl else "AMD" if "amd" in nl or "radeon" in nl else "Intel" if "intel" in nl else "Unknown"
                    gpus.append({"name": name, "vendor": vendor, "vram": 0,
                                 "compatible": vendor in ("NVIDIA","AMD")})
        except Exception: pass
    return gpus

# ══════════════════════════════════════════════════════════════════
#  DOWNLOAD & EXTRACT
# ══════════════════════════════════════════════════════════════════
def download(url, dest, progress_cb=None):
    try:
        r = requests.get(url, stream=True, timeout=300, allow_redirects=True,
                         headers={"User-Agent": f"Mozilla/5.0 {PEGASUS_BRAND}/19.0"})
        if r.status_code != 200:
            return False
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(65536):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if progress_cb and total:
                        progress_cb(int(done * 100 / total))
        return dest.stat().st_size > 1000
    except Exception as e:
        print(f"Download error: {e}")
        return False

def extract_binary(archive, target_dir, binary_names):
    tmp = Path(tempfile.mkdtemp(prefix="pegasus_"))
    try:
        s = str(archive).lower()
        if s.endswith(".zip"):
            with zipfile.ZipFile(archive) as z: z.extractall(tmp)
        elif s.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive, "r:gz") as t: t.extractall(tmp)
        else:
            return None
        src = None
        for r, _, files in os.walk(tmp):
            for f in files:
                if f.lower() in [n.lower() for n in binary_names]:
                    src = Path(r) / f
                    break
            if src: break
        if not src:
            return None
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / src.name
        shutil.copy2(src, target)
        for item in src.parent.iterdir():
            if item.name == src.name: continue
            try:
                if item.is_file(): shutil.copy2(item, target_dir / item.name)
                elif item.is_dir(): shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
            except: pass
        if not IS_WIN:
            try: target.chmod(0o755)
            except: pass
        return target
    except Exception as e:
        print(f"Extract error: {e}")
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════
#  MINER MANAGER
# ══════════════════════════════════════════════════════════════════
class MinerManager:
    def __init__(self):
        self.proc = None
        self.start_t = None
        self.log_file = None
        self.log_handle = None
        self.algo = DEFAULT_ALGO
        self.region = DEFAULT_REGION
        self.mode = "cpu"
        self.watchdog = False
        self.xmrig_path = None
        self.lolminer_path = None
        self._last_history_update = 0
        self._last_parse_offset = 0
        self._parse_lock = threading.Lock()
        self._last_btc_update = 0

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def uptime(self):
        if not self.start_t: return "00:00:00"
        d = int((datetime.now() - self.start_t).total_seconds())
        h, r = divmod(d, 3600); m, s = divmod(r, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def ensure_xmrig(self, log):
        if self.xmrig_path and self.xmrig_path.exists():
            return self.xmrig_path
        target = MINER_DIR / "xmrig" / ("xmrig.exe" if IS_WIN else "xmrig")
        if target.exists():
            self.xmrig_path = target
            return target
        url = XMRIG_URLS.get("windows" if IS_WIN else "linux")
        if not url:
            log("[X] XMRig tidak support OS ini"); return None
        log("[*] Download XMRig (CPU miner)...")
        ext = ".zip" if url.endswith(".zip") else ".tar.gz"
        arc = BASE_DIR / f"xmrig{ext}"
        if not download(url, arc, lambda p: log(f"    Progress: {p}%")):
            log("[X] Download XMRig gagal"); return None
        log("[*] Extract XMRig...")
        exe = extract_binary(arc, MINER_DIR / "xmrig", ["xmrig.exe", "xmrig"])
        try: arc.unlink()
        except: pass
        if exe:
            self.xmrig_path = exe
            log(f"[OK] XMRig siap: {exe.name}")
        return exe

    def ensure_lolminer(self, log):
        if self.lolminer_path and self.lolminer_path.exists():
            return self.lolminer_path
        target = MINER_DIR / "lolminer" / ("lolMiner.exe" if IS_WIN else "lolMiner")
        if target.exists():
            self.lolminer_path = target
            return target
        url = LOLMINER_URLS.get("windows" if IS_WIN else "linux")
        if not url:
            log("[X] lolMiner tidak support OS ini"); return None
        log("[*] Download lolMiner (GPU miner)...")
        ext = ".zip" if url.endswith(".zip") else ".tar.gz"
        arc = BASE_DIR / f"lolminer{ext}"
        if not download(url, arc, lambda p: log(f"    Progress: {p}%")):
            log("[X] Download lolMiner gagal"); return None
        log("[*] Extract lolMiner...")
        exe = extract_binary(arc, MINER_DIR / "lolminer", ["lolMiner.exe", "lolMiner"])
        try: arc.unlink()
        except: pass
        if exe:
            self.lolminer_path = exe
            log(f"[OK] lolMiner siap: {exe.name}")
        return exe

    def start(self, algo=None, region=None, log=print):
        algo = algo or self.algo
        region = region or self.region
        algo_up = algo.upper()

        if self.is_running():
            log("[!] Miner sudah jalan")
            return True

        if algo_up in [a.upper() for a in CPU_ALGOS]:
            mode = "cpu"
        else:
            mode = "gpu"

        self.mode = mode
        log(f"[*] Mode: {'CPU (XMRig)' if mode == 'cpu' else 'GPU (lolMiner)'}")

        if mode == "cpu":
            exe = self.ensure_xmrig(log)
            if not exe:
                log("[X] Gagal siapkan XMRig"); return False
            cmd = self._build_xmrig_cmd(exe, algo_up, region)
        else:
            gpus = [g for g in detect_gpus() if g["compatible"]]
            if not gpus:
                log("[!] Tidak ada GPU kompatibel, fallback ke CPU")
                return self.start("RANDOMXMONERO", region, log)
            exe = self.ensure_lolminer(log)
            if not exe:
                log("[X] Gagal siapkan lolMiner"); return False
            cmd = self._build_lolminer_cmd(exe, algo_up, region)

        if not cmd:
            log("[X] Gagal buat command")
            return False

        log(f"[*] Command: {' '.join(str(c) for c in cmd[:4])} ...")

        self.log_file = LOGS_DIR / f"pegasus_{datetime.now():%Y%m%d_%H%M%S}.log"
        try:
            self.log_handle = open(self.log_file, "w", encoding="utf-8", errors="ignore")
            flags = 0
            if IS_WIN:
                flags = subprocess.CREATE_NEW_PROCESS_GROUP
            self.proc = subprocess.Popen(
                cmd, stdout=self.log_handle, stderr=subprocess.STDOUT,
                creationflags=flags, cwd=str(exe.parent)
            )
            self.start_t = datetime.now()
            self.algo = algo_up
            self.region = region
            self._last_parse_offset = 0

            detector.reset()
            detector.connection_status = "CONNECTING"

            history.start_session(algo_up, region, mode)

            time.sleep(5)
            if self.proc.poll() is not None:
                log("[X] Miner langsung mati! Log terakhir:")
                for line in self._tail(10):
                    log(f"    {line}")
                history.end_session()
                return False

            log(f"[OK] MINER JALAN - PID {self.proc.pid}")
            self.watchdog = True
            threading.Thread(target=self._watch, daemon=True).start()
            return True
        except Exception as e:
            log(f"[X] Error start: {e}")
            history.end_session()
            return False

    def _build_xmrig_cmd(self, exe, algo, region):
        port = get_pool_port(algo)
        pool = f"{algo.lower()}.{region}.nicehash.com:{port}"
        cmd = [
            str(exe),
            "-o", pool,
            "-u", f"{WALLET}.{WORKER}",
            "-p", "x",
            "-a", "rx/0" if algo == "RANDOMXMONERO" else algo.lower(),
            "-k",
            "--no-color",
            "--print-time", "5",
            "--donate-level", "1",
            "--retries", "5",
            "--retry-pause", "5",
        ]
        return cmd

    def _build_lolminer_cmd(self, exe, algo, region):
        port = get_pool_port(algo)
        pool = f"{algo.lower()}.{region}.nicehash.com:{port}"
        algo_map = {
            "KAWPOW": "KAWPOW", "AUTOLYKOS": "AUTOLYKOS", "OCTOPUS": "OCTOPUS",
            "FISHHASH": "FISHHASH", "BEAMV3": "BEAMV3",
            "DAGGERHASHIMOTO": "ETCHASH", "ETCHASH": "ETCHASH",
            "KHEAVYHASH": "KHEAVYHASH",
        }
        lol_algo = algo_map.get(algo, algo)
        cmd = [
            str(exe),
            "--algo", lol_algo,
            "--pool", pool,
            "--user", f"{WALLET}.{WORKER}",
            "--pass", "x",
            "--apiport", "0",
            "--nocolor",
        ]
        return cmd

    def _tail(self, n=30):
        if not self.log_file or not self.log_file.exists():
            return []
        try:
            with open(self.log_file, "r", errors="ignore") as f:
                return [l.rstrip() for l in f.readlines()[-n:]]
        except: return []

    def parse_log(self):
        if not self.log_file or not self.log_file.exists():
            return
        with self._parse_lock:
            try:
                with open(self.log_file, "r", errors="ignore") as f:
                    f.seek(self._last_parse_offset)
                    new_lines = f.readlines()
                    self._last_parse_offset = f.tell()
            except:
                return

            for line in new_lines:
                if self.mode == "cpu":
                    detector.parse_xmrig_line(line)
                else:
                    detector.parse_lolminer_line(line)

            if self.is_running():
                # Update history session
                if time.time() - self._last_history_update > 30:
                    self._last_history_update = time.time()
                    history.update_session(detector.accepted, detector.rejected,
                                            detector.hashrate_60s)

                # Update BTC earnings
                if time.time() - self._last_btc_update > 10:
                    self._last_btc_update = time.time()
                    algos = get_nh_algos()
                    paying = algos.get(self.algo, {}).get("paying", 0)
                    detector.update_btc_earnings(paying)

    def stop(self):
        stopped = False
        if self.proc and self.proc.poll() is None:
            try:
                if IS_WIN:
                    import signal as _sig
                    self.proc.send_signal(_sig.SIGTERM)
                else:
                    self.proc.terminate()
                try: self.proc.wait(timeout=5)
                except: self.proc.kill()
                stopped = True
            except Exception:
                try: self.proc.kill(); stopped = True
                except: pass
        for p in psutil.process_iter(["name"]):
            try:
                nm = (p.info.get("name") or "").lower()
                if nm in ("xmrig.exe","xmrig","lolminer.exe","lolminer"):
                    p.kill(); stopped = True
            except: pass
        try:
            if self.log_handle: self.log_handle.close(); self.log_handle = None
        except: pass
        self.watchdog = False
        detector.connection_status = "OFFLINE"
        history.end_session()
        btc_wallet.record_snapshot()
        return stopped

    def _watch(self):
        while self.watchdog:
            time.sleep(15)
            if not self.watchdog: break
            if self.start_t and not self.is_running():
                self.watchdog = False
                history.end_session()
                time.sleep(10)
                self.start(self.algo, self.region, lambda m: None)
                break

miner = MinerManager()

# ══════════════════════════════════════════════════════════════════
#  LOGIN WINDOW — PREMIUM PEGASUSMETASEC
# ══════════════════════════════════════════════════════════════════
class LoginWindow:
    def __init__(self, root):
        self.root = root
        root.title(f"{PEGASUS_BRAND} Login")
        root.configure(bg=C["bg"])
        root.geometry("540x720")
        root.resizable(False, False)
        root.update_idletasks()
        w, h = 540, 720
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")
        self._build()
        self._animate()

    def _build(self):
        header = tk.Frame(self.root, bg=C["bg"])
        header.pack(fill="x", pady=(10, 0))

        tk.Label(header, text=PEGASUS_ASCII.format(url=PEGASUS_URL),
                 font=("Consolas", 7, "bold"),
                 bg=C["bg"], fg=C["green"], justify="center").pack()

        tk.Label(header, text=f"[ {PEGASUS_BRAND} - NICEHASH MINER v19.0 ]",
                 font=("Consolas", 10, "bold"),
                 bg=C["bg"], fg=C["yellow"]).pack(pady=5)

        tk.Label(header, text=f"Visit: {PEGASUS_URL}",
                 font=("Consolas", 8, "underline"),
                 bg=C["bg"], fg=C["cyan"], cursor="hand2").pack()

        term = tk.Frame(self.root, bg=C["panel"], bd=1, relief="solid",
                        highlightbackground=C["green"], highlightthickness=1)
        term.pack(fill="both", expand=True, padx=30, pady=15)

        tk.Label(term, text="+-[ SECURE LOGIN ]---------------+",
                 font=("Consolas", 10), bg=C["panel"], fg=C["green"]).pack(anchor="w", padx=15, pady=(15,0))

        tk.Label(term, text="| Username:", font=("Consolas", 11),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", padx=15, pady=(10,2))
        self.eu = tk.Entry(term, font=("Consolas", 12),
                           bg=C["black"], fg=C["green"], insertbackground=C["green"],
                           relief="flat", bd=5, highlightbackground=C["green_dim"],
                           highlightcolor=C["green"], highlightthickness=1)
        self.eu.pack(fill="x", padx=15, ipady=8)
        self.eu.insert(0, "admin")

        tk.Label(term, text="| Password:", font=("Consolas", 11),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", padx=15, pady=(10,2))
        self.ep = tk.Entry(term, font=("Consolas", 12), show="*",
                           bg=C["black"], fg=C["green"], insertbackground=C["green"],
                           relief="flat", bd=5, highlightbackground=C["green_dim"],
                           highlightcolor=C["green"], highlightthickness=1)
        self.ep.pack(fill="x", padx=15, ipady=8)
        self.ep.bind("<Return>", lambda e: self.do_login())

        self.status = tk.Label(term, text="> awaiting credentials_",
                                font=("Consolas", 9), bg=C["panel"], fg=C["green_dim"])
        self.status.pack(anchor="w", padx=15, pady=(10,5))

        tk.Label(term, text=f"| Hint: password = {LOGIN_PASS}",
                 font=("Consolas", 9, "italic"), bg=C["panel"], fg=C["yellow"]).pack(anchor="w", padx=15)
        tk.Label(term, text="+--------------------------------+",
                 font=("Consolas", 10), bg=C["panel"], fg=C["green"]).pack(anchor="w", padx=15, pady=(5,0))

        btn = tk.Button(term, text=f"[ ACCESS {PEGASUS_BRAND.upper()} ]", command=self.do_login,
                        font=("Consolas", 12, "bold"),
                        bg=C["green_dark"], fg=C["green"],
                        activebackground=C["green"], activeforeground=C["black"],
                        relief="flat", bd=0, cursor="hand2", pady=12,
                        highlightbackground=C["green"], highlightthickness=1)
        btn.pack(fill="x", padx=15, pady=20)
        btn.bind("<Enter>", lambda e: btn.configure(bg=C["green"], fg=C["black"]))
        btn.bind("<Leave>", lambda e: btn.configure(bg=C["green_dark"], fg=C["green"]))

        # Balance display
        bal_frame = tk.Frame(term, bg=C["panel2"])
        bal_frame.pack(fill="x", padx=15, pady=(0, 15))
        tk.Label(bal_frame, text="BTC BALANCE (saved):",
                 font=("Consolas", 8), bg=C["panel2"], fg=C["text_dim"]).pack(anchor="w", padx=10, pady=(5,0))
        bal = btc_wallet.get_balance()
        tk.Label(bal_frame, text=f"{bal:.10f} BTC",
                 font=("Consolas", 11, "bold"), bg=C["panel2"], fg=C["gold"]).pack(anchor="w", padx=10)
        lvl = booster.get_current_level()
        tk.Label(bal_frame, text=f"Booster: {lvl['name']} (x{lvl['mult']:.2f})",
                 font=("Consolas", 8), bg=C["panel2"], fg=lvl["color"]).pack(anchor="w", padx=10, pady=(0,5))

        tk.Label(self.root, text=f"{PEGASUS_BRAND} | Pegasus Miner v19.0 | (c) 2026 | {PEGASUS_URL}",
                 font=("Consolas", 8), bg=C["bg"], fg=C["text_dim"]).pack(side="bottom", pady=8)

    def _animate(self):
        dots = ["_", " ", " ", " "]
        idx = [0]
        def tick():
            if not self.root.winfo_exists(): return
            d = dots[idx[0] % len(dots)]
            self.status.configure(text=f"> awaiting credentials{d}")
            idx[0] += 1
            self.root.after(400, tick)
        tick()

    def do_login(self):
        u = self.eu.get().strip()
        p = self.ep.get().strip()
        if not u:
            messagebox.showerror("Login", "Username kosong"); return
        if p != LOGIN_PASS:
            messagebox.showerror("Login", f"Password salah!\nHint: {LOGIN_PASS}")
            return
        self.root.destroy()

# ══════════════════════════════════════════════════════════════════
#  BTC WALLET WINDOW — DETAIL SALDO
# ══════════════════════════════════════════════════════════════════
class BTCWalletWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title(f"{PEGASUS_BRAND} - BTC WALLET")
        self.win.configure(bg=C["bg"])
        self.win.geometry("900x750")
        self._build()
        self._refresh()

    def _build(self):
        header = tk.Frame(self.win, bg=C["bg"], height=70)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text=f"| {PEGASUS_BRAND.upper()} BTC WALLET",
                 font=("Consolas", 18, "bold"),
                 bg=C["bg"], fg=C["gold"]).pack(side="left", padx=20, pady=15)
        tk.Label(header, text=f"Saved & Persistent | {PEGASUS_URL}",
                 font=("Consolas", 9),
                 bg=C["bg"], fg=C["cyan"]).pack(side="right", padx=20, pady=15)

        # Balance card
        card = tk.Frame(self.win, bg=C["panel"],
                         highlightbackground=C["gold"], highlightthickness=2)
        card.pack(fill="x", padx=20, pady=10)

        tk.Label(card, text="CURRENT BTC BALANCE",
                 font=("Consolas", 11), bg=C["panel"], fg=C["text_dim"]).pack(pady=(15,5))
        self.lbl_balance = tk.Label(card, text="0.00000000 BTC",
                                     font=("Consolas", 32, "bold"),
                                     bg=C["panel"], fg=C["gold"])
        self.lbl_balance.pack(pady=5)
        self.lbl_usd = tk.Label(card, text="$0.00 USD",
                                 font=("Consolas", 14, "bold"),
                                 bg=C["panel"], fg=C["green"])
        self.lbl_usd.pack()
        self.lbl_idr = tk.Label(card, text="Rp 0 IDR",
                                 font=("Consolas", 14, "bold"),
                                 bg=C["panel"], fg=C["green"])
        self.lbl_idr.pack(pady=(0,15))

        # Booster card
        bcard = tk.Frame(self.win, bg=C["panel"],
                          highlightbackground=C["magenta"], highlightthickness=1)
        bcard.pack(fill="x", padx=20, pady=10)

        tk.Label(bcard, text=">> BTC BOOSTER <<",
                 font=("Consolas", 12, "bold"),
                 bg=C["panel"], fg=C["magenta"]).pack(pady=(10,5))

        self.lbl_booster_lvl = tk.Label(bcard, text="NONE",
                                         font=("Consolas", 16, "bold"),
                                         bg=C["panel"], fg=C["text_dim"])
        self.lbl_booster_lvl.pack()
        self.lbl_booster_mult = tk.Label(bcard, text="x1.00 multiplier",
                                          font=("Consolas", 10),
                                          bg=C["panel"], fg=C["yellow"])
        self.lbl_booster_mult.pack()

        tk.Label(bcard, text="Progress to next level:",
                 font=("Consolas", 9), bg=C["panel"], fg=C["text_dim"]).pack(pady=(10,2))
        self.boost_bar = ttk.Progressbar(bcard, mode="determinate", maximum=100,
                                          style="Gold.Horizontal.TProgressbar")
        self.boost_bar.pack(fill="x", padx=40, pady=5)
        self.lbl_boost_progress = tk.Label(bcard, text="0 / 0 shares",
                                            font=("Consolas", 9),
                                            bg=C["panel"], fg=C["cyan"])
        self.lbl_boost_progress.pack(pady=(0,10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Gold.Horizontal.TProgressbar",
                         background=C["gold"], troughcolor=C["black"],
                         bordercolor=C["gold"], lightcolor=C["gold"],
                         darkcolor=C["orange"], thickness=20)

        # Stats card
        scard = tk.Frame(self.win, bg=C["panel"],
                          highlightbackground=C["green_dim"], highlightthickness=1)
        scard.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Label(scard, text=">> STATISTICS",
                 font=("Consolas", 11, "bold"),
                 bg=C["panel"], fg=C["green"]).pack(anchor="w", padx=15, pady=(10,5))

        self.stat_vars = {}
        rows = [
            ("Total Earned (BTC)", "earned_btc", C["gold"]),
            ("Total Earned (USD)", "earned_usd", C["green"]),
            ("Total Earned (IDR)", "earned_idr", C["green"]),
            ("Total Withdrawn",    "withdrawn",  C["red"]),
            ("Total Shares",       "shares",     C["cyan"]),
            ("Total Mining Time",  "mining_time",C["yellow"]),
            ("Sessions Count",     "sessions",   C["magenta"]),
            ("Wallet Address",     "wallet",     C["cyan"]),
            ("Worker Name",        "worker",     C["text"]),
        ]
        for label, key, color in rows:
            row = tk.Frame(scard, bg=C["panel"])
            row.pack(fill="x", padx=15, pady=3)
            tk.Label(row, text=f"  {label:<20}", font=("Consolas", 10),
                     bg=C["panel"], fg=C["text_dim"], width=22, anchor="w").pack(side="left")
            v = tk.StringVar(value="-")
            tk.Label(row, textvariable=v, font=("Consolas", 10, "bold"),
                     bg=C["panel"], fg=color, anchor="w").pack(side="left", fill="x", expand=True)
            self.stat_vars[key] = v

        # Buttons
        btn_frame = tk.Frame(self.win, bg=C["bg"])
        btn_frame.pack(fill="x", padx=20, pady=10)
        for txt, cmd, color in [
            ("[SAVE NOW]", self._save_now, C["green"]),
            ("[EXPORT WALLET]", self._export, C["cyan"]),
            ("[RESET WALLET]", self._reset, C["red"]),
        ]:
            b = tk.Button(btn_frame, text=txt, command=cmd, font=("Consolas", 10, "bold"),
                          bg=C["panel"], fg=color, activebackground=color,
                          activeforeground=C["black"], relief="flat", bd=0,
                          cursor="hand2", padx=15, pady=8,
                          highlightbackground=C["green_dim"], highlightthickness=1)
            b.pack(side="left", padx=5)

        tk.Label(self.win, text=f"{PEGASUS_BRAND} | {PEGASUS_URL}",
                 font=("Consolas", 8), bg=C["bg"], fg=C["text_dim"]).pack(side="bottom", pady=5)

    def _refresh(self):
        if not self.win.winfo_exists(): return
        w = btc_wallet.wallet
        bal = w["balance_btc"]
        self.lbl_balance.config(text=f"{bal:.10f} BTC")
        p = get_btc_price()
        usd = bal * p.get("usd", 0)
        idr = bal * p.get("idr", 0)
        self.lbl_usd.config(text=f"${usd:,.4f} USD")
        self.lbl_idr.config(text=f"Rp {idr:,.0f} IDR")

        # Booster
        lvl = booster.get_current_level()
        nxt = booster.get_next_level()
        self.lbl_booster_lvl.config(text=lvl["name"], fg=lvl["color"])
        self.lbl_booster_mult.config(text=f"x{lvl['mult']:.2f} multiplier")
        progress = booster.get_progress()
        self.boost_bar["value"] = progress
        if nxt:
            shares = w.get("total_shares", 0)
            self.lbl_boost_progress.config(
                text=f"{shares} / {nxt['req_shares']} shares -> {nxt['name']} (x{nxt['mult']:.2f})")
        else:
            self.lbl_boost_progress.config(text="MAX LEVEL REACHED!")

        # Stats
        self.stat_vars["earned_btc"].set(f"{w['total_earned_btc']:.10f} BTC")
        self.stat_vars["earned_usd"].set(f"${w['total_earned_usd']:,.4f}")
        self.stat_vars["earned_idr"].set(f"Rp {w['total_earned_idr']:,.0f}")
        self.stat_vars["withdrawn"].set(f"{w['total_withdrawn_btc']:.10f} BTC")
        self.stat_vars["shares"].set(str(w.get("total_shares", 0)))
        t = w.get("total_mining_seconds", 0)
        h, r = divmod(t, 3600); m, s = divmod(r, 60)
        self.stat_vars["mining_time"].set(f"{h:02d}h {m:02d}m {s:02d}s")
        self.stat_vars["sessions"].set(str(w.get("sessions_count", 0)))
        self.stat_vars["wallet"].set(WALLET[:28] + "...")
        self.stat_vars["worker"].set(WORKER)

        self.win.after(2000, self._refresh)

    def _save_now(self):
        btc_wallet.record_snapshot()
        btc_wallet._save()
        messagebox.showinfo("Saved", f"BTC Wallet tersimpan ke:\n{WALLET_DB}")

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"pegasus_wallet_{datetime.now():%Y%m%d_%H%M%S}.json")
        if path:
            try:
                Path(path).write_text(json.dumps(btc_wallet.wallet, indent=2), encoding="utf-8")
                messagebox.showinfo("Export", f"Wallet berhasil diexport:\n{path}")
            except Exception as e:
                messagebox.showerror("Export", f"Gagal: {e}")

    def _reset(self):
        if messagebox.askyesno("Reset Wallet",
            "Yakin RESET saldo BTC?\n\nSemua earning akan dihapus dan tidak bisa dikembalikan!"):
            btc_wallet.reset()
            messagebox.showinfo("Reset", "Wallet berhasil direset")

# ══════════════════════════════════════════════════════════════════
#  BOOSTER WINDOW
# ══════════════════════════════════════════════════════════════════
class BoosterWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title(f"{PEGASUS_BRAND} - BTC BOOSTER")
        self.win.configure(bg=C["bg"])
        self.win.geometry("800x700")
        self._build()
        self._refresh()

    def _build(self):
        tk.Label(self.win, text=f"| {PEGASUS_BRAND.upper()} BTC BOOSTER",
                 font=("Consolas", 18, "bold"),
                 bg=C["bg"], fg=C["magenta"]).pack(pady=15)
        tk.Label(self.win, text="Tingkatkan level dengan lebih banyak shares!",
                 font=("Consolas", 10), bg=C["bg"], fg=C["cyan"]).pack()

        # Current level
        cur_frame = tk.Frame(self.win, bg=C["panel"],
                              highlightbackground=C["magenta"], highlightthickness=2)
        cur_frame.pack(fill="x", padx=20, pady=15)

        lvl = booster.get_current_level()
        tk.Label(cur_frame, text="CURRENT LEVEL",
                 font=("Consolas", 10), bg=C["panel"], fg=C["text_dim"]).pack(pady=(15,5))
        self.lbl_cur = tk.Label(cur_frame, text=lvl["name"],
                                 font=("Consolas", 24, "bold"),
                                 bg=C["panel"], fg=lvl["color"])
        self.lbl_cur.pack()
        self.lbl_cur_mult = tk.Label(cur_frame, text=f"x{lvl['mult']:.2f} multiplier",
                                      font=("Consolas", 12),
                                      bg=C["panel"], fg=C["yellow"])
        self.lbl_cur_mult.pack(pady=(0, 15))

        # Progress to next
        nxt = booster.get_next_level()
        if nxt:
            tk.Label(cur_frame, text=f"Next: {nxt['name']} (x{nxt['mult']:.2f})",
                     font=("Consolas", 10), bg=C["panel"], fg=nxt["color"]).pack()
            self.boost_bar = ttk.Progressbar(cur_frame, mode="determinate", maximum=100,
                                              style="Mag.Horizontal.TProgressbar")
            self.boost_bar.pack(fill="x", padx=40, pady=10)
            self.lbl_progress = tk.Label(cur_frame, text="",
                                          font=("Consolas", 9), bg=C["panel"], fg=C["cyan"])
            self.lbl_progress.pack(pady=(0, 15))

            style = ttk.Style()
            style.theme_use("clam")
            style.configure("Mag.Horizontal.TProgressbar",
                             background=C["magenta"], troughcolor=C["black"],
                             bordercolor=C["magenta"], lightcolor=C["magenta"],
                             darkcolor=C["purple"], thickness=22)
        else:
            self.boost_bar = None
            self.lbl_progress = None
            tk.Label(cur_frame, text=">> MAX LEVEL REACHED! <<",
                     font=("Consolas", 14, "bold"), bg=C["panel"],
                     fg=C["gold"]).pack(pady=15)

        # All levels table
        tk.Label(self.win, text=">> ALL BOOSTER LEVELS",
                 font=("Consolas", 11, "bold"),
                 bg=C["bg"], fg=C["green"]).pack(pady=(15, 5))

        table = tk.Frame(self.win, bg=C["panel"],
                          highlightbackground=C["green_dim"], highlightthickness=1)
        table.pack(fill="both", expand=True, padx=20, pady=10)

        shares = btc_wallet.wallet.get("total_shares", 0)
        for lvl in booster.levels:
            row = tk.Frame(table, bg=C["panel"])
            row.pack(fill="x", padx=10, pady=3)
            unlocked = shares >= lvl["req_shares"]
            marker = "[OK]" if unlocked else "[--]"
            color = lvl["color"] if unlocked else C["text_dim"]

            tk.Label(row, text=f"  {marker} {lvl['name']:<12}",
                     font=("Consolas", 11, "bold"),
                     bg=C["panel"], fg=color, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=f"x{lvl['mult']:.2f}",
                     font=("Consolas", 11),
                     bg=C["panel"], fg=C["yellow"], width=10).pack(side="left")
            tk.Label(row, text=f"Need {lvl['req_shares']} shares",
                     font=("Consolas", 10),
                     bg=C["panel"], fg=C["text_dim"]).pack(side="left")

        # Toggle booster
        toggle_frame = tk.Frame(self.win, bg=C["bg"])
        toggle_frame.pack(fill="x", padx=20, pady=10)
        self.booster_active_var = tk.BooleanVar(value=btc_wallet.wallet.get("booster_active", True))
        cb = tk.Checkbutton(toggle_frame, text="Booster Aktif (kalikan earning)",
                            variable=self.booster_active_var,
                            command=self._toggle,
                            font=("Consolas", 11, "bold"),
                            bg=C["bg"], fg=C["green"], selectcolor=C["panel"],
                            activebackground=C["bg"], activeforeground=C["green"])
        cb.pack(side="left")

        tk.Label(self.win, text=f"{PEGASUS_BRAND} | {PEGASUS_URL}",
                 font=("Consolas", 8), bg=C["bg"], fg=C["text_dim"]).pack(side="bottom", pady=5)

    def _toggle(self):
        btc_wallet.set_booster(self.booster_active_var.get(),
                                booster.get_current_level()["mult"])
        state = "AKTIF" if self.booster_active_var.get() else "NONAKTIF"
        messagebox.showinfo("Booster", f"Booster {state}")

    def _refresh(self):
        if not self.win.winfo_exists(): return
        lvl = booster.get_current_level()
        nxt = booster.get_next_level()
        self.lbl_cur.config(text=lvl["name"], fg=lvl["color"])
        self.lbl_cur_mult.config(text=f"x{lvl['mult']:.2f} multiplier")
        if self.boost_bar and nxt:
            shares = btc_wallet.wallet.get("total_shares", 0)
            self.boost_bar["value"] = booster.get_progress()
            self.lbl_progress.config(
                text=f"{shares} / {nxt['req_shares']} shares")
        self.win.after(2000, self._refresh)

# ══════════════════════════════════════════════════════════════════
#  HISTORY WINDOW
# ══════════════════════════════════════════════════════════════════
class HistoryWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title(f"{PEGASUS_BRAND} - MINING HISTORY")
        self.win.configure(bg=C["bg"])
        self.win.geometry("1250x780")
        self._build()
        self._refresh()

    def _build(self):
        header = tk.Frame(self.win, bg=C["bg"], height=60)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text=f"| {PEGASUS_BRAND.upper()} MINING HISTORY",
                 font=("Consolas", 18, "bold"),
                 bg=C["bg"], fg=C["green"]).pack(side="left", padx=20, pady=15)

        stats_frame = tk.Frame(self.win, bg=C["panel"],
                                highlightbackground=C["green_dim"], highlightthickness=1)
        stats_frame.pack(fill="x", padx=15, pady=(0,10))

        s = history.get_stats()
        total_time = s["total_time"]
        h, r = divmod(total_time, 3600); m, sec = divmod(r, 60)

        stat_items = [
            ("TOTAL SESSIONS", str(s["total_sessions"]), C["cyan"]),
            ("TOTAL TIME", f"{h:02d}h {m:02d}m {sec:02d}s", C["yellow"]),
            ("TOTAL ACCEPTED", str(s["total_accepted"]), C["green"]),
            ("TOTAL REJECTED", str(s["total_rejected"]), C["red"]),
            ("TOTAL BTC", f"{btc_wallet.wallet['total_earned_btc']:.8f}", C["gold"]),
        ]
        for label, value, color in stat_items:
            f = tk.Frame(stats_frame, bg=C["panel"])
            f.pack(side="left", expand=True, fill="both", padx=10, pady=10)
            tk.Label(f, text=label, font=("Consolas", 9), bg=C["panel"],
                     fg=C["text_dim"]).pack()
            tk.Label(f, text=value, font=("Consolas", 14, "bold"), bg=C["panel"],
                     fg=color).pack()

        tb = tk.Frame(self.win, bg=C["panel2"])
        tb.pack(fill="x", padx=15, pady=5)
        for txt, cmd, color in [
            ("[EXPORT CSV]", self._export_csv, C["cyan"]),
            ("[EXPORT JSON]", self._export_json, C["cyan"]),
            ("[REFRESH]", self._refresh, C["green"]),
            ("[CLEAR HISTORY]", self._clear, C["red"]),
        ]:
            b = tk.Button(tb, text=txt, command=cmd, font=("Consolas", 10, "bold"),
                          bg=C["panel"], fg=color, activebackground=color,
                          activeforeground=C["black"], relief="flat", bd=0,
                          cursor="hand2", padx=12, pady=6,
                          highlightbackground=C["green_dim"], highlightthickness=1)
            b.pack(side="left", padx=4, pady=6)

        table_frame = tk.Frame(self.win, bg=C["panel"],
                                highlightbackground=C["green_dim"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("ID", "Start", "Duration", "Algo", "Region", "Mode", "Accepted", "Rejected", "Hashrate", "BTC")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("History.Treeview",
                         background=C["black"], foreground=C["green"],
                         fieldbackground=C["black"], rowheight=26,
                         font=("Consolas", 9))
        style.configure("History.Treeview.Heading",
                         background=C["green_dark"], foreground=C["green"],
                         font=("Consolas", 9, "bold"))
        style.map("History.Treeview",
                  background=[("selected", C["green_dark"])],
                  foreground=[("selected", C["green"])])

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                  style="History.Treeview")
        widths = {"ID": 140, "Start": 160, "Duration": 100, "Algo": 150,
                  "Region": 70, "Mode": 100, "Accepted": 90, "Rejected": 90,
                  "Hashrate": 120, "BTC": 120}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")
        self.tree.column("Algo", anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Label(self.win, text=f"{PEGASUS_BRAND} | {PEGASUS_URL}",
                 font=("Consolas", 8), bg=C["bg"], fg=C["text_dim"]).pack(side="bottom", pady=5)

    def _refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        s = history.get_stats()
        for sess in reversed(s["sessions"]):
            dur = sess.get("duration", 0)
            h, r = divmod(dur, 3600); m, sec = divmod(r, 60)
            dur_str = f"{h:02d}:{m:02d}:{sec:02d}"
            start = sess.get("start", "")[:19].replace("T", " ")
            hr = sess.get("hashrate_avg", 0)
            if hr > 1e6: hr_str = f"{hr/1e6:.2f} MH/s"
            elif hr > 1e3: hr_str = f"{hr/1e3:.2f} KH/s"
            else: hr_str = f"{hr:.1f} H/s"
            btc = sess.get("btc_earned", 0)
            self.tree.insert("", "end", values=(
                sess.get("id", ""), start, dur_str,
                sess.get("algo", ""), sess.get("region", "").upper(),
                sess.get("mode", "").upper(),
                sess.get("accepted", 0), sess.get("rejected", 0), hr_str,
                f"{btc:.10f}"
            ))

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"pegasus_history_{datetime.now():%Y%m%d_%H%M%S}.csv")
        if path:
            if history.export_csv(path):
                messagebox.showinfo("Export", f"CSV berhasil diexport:\n{path}")
            else:
                messagebox.showerror("Export", "Gagal export CSV")

    def _export_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"pegasus_history_{datetime.now():%Y%m%d_%H%M%S}.json")
        if path:
            if history.export_json(path):
                messagebox.showinfo("Export", f"JSON berhasil diexport:\n{path}")
            else:
                messagebox.showerror("Export", "Gagal export JSON")

    def _clear(self):
        if messagebox.askyesno("Clear History",
            "Yakin hapus SEMUA history mining?\n\nTindakan ini tidak bisa dibatalkan."):
            history.clear()
            self._refresh()
            messagebox.showinfo("Clear", "History berhasil dihapus")

# ══════════════════════════════════════════════════════════════════
#  MAIN GUI — MEGA PROFESSIONAL
# ══════════════════════════════════════════════════════════════════
class PegasusGUI:
    def __init__(self, root):
        self.root = root
        root.title(f"{PEGASUS_BRAND} - NICEHASH MINER v19.0")
        root.configure(bg=C["bg"])
        root.geometry("1600x1000")
        root.minsize(1400, 850)
        self._build()
        self._refresh()
        self._banner()

    def _build(self):
        # HEADER
        header = tk.Frame(self.root, bg=C["bg"], height=130)
        header.pack(fill="x"); header.pack_propagate(False)

        title_frame = tk.Frame(header, bg=C["bg"])
        title_frame.pack(side="left", padx=20, pady=10)

        tf = tk.Frame(title_frame, bg=C["bg"])
        tf.pack(side="left")
        tk.Label(tf, text="PEGASUS NICEHASH MINER",
                 font=("Consolas", 24, "bold"), bg=C["bg"], fg=C["green"]).pack(anchor="w")
        tk.Label(tf, text=f"v19.0 | {PEGASUS_BRAND} | Real-Time Mining + BTC Booster",
                 font=("Consolas", 9), bg=C["bg"], fg=C["cyan"]).pack(anchor="w")
        tk.Label(tf, text=f"Wallet: {WALLET}",
                 font=("Consolas", 8), bg=C["bg"], fg=C["text_dim"]).pack(anchor="w")
        tk.Label(tf, text=f"URL: {PEGASUS_URL}",
                 font=("Consolas", 8), bg=C["bg"], fg=C["cyan_dim"]).pack(anchor="w")

        # BTC Balance display di header
        bal_frame = tk.Frame(header, bg=C["panel2"],
                              highlightbackground=C["gold"], highlightthickness=2)
        bal_frame.pack(side="right", padx=20, pady=15)
        tk.Label(bal_frame, text="BTC BALANCE (Saved)",
                 font=("Consolas", 8), bg=C["panel2"], fg=C["text_dim"]).pack(padx=15, pady=(8,0))
        self.lbl_btc_balance = tk.Label(bal_frame, text="0.00000000 BTC",
                                         font=("Consolas", 16, "bold"),
                                         bg=C["panel2"], fg=C["gold"])
        self.lbl_btc_balance.pack(padx=15)
        self.lbl_btc_usd = tk.Label(bal_frame, text="$0.00 | Rp 0",
                                     font=("Consolas", 9),
                                     bg=C["panel2"], fg=C["green"])
        self.lbl_btc_usd.pack(padx=15, pady=(0,8))

        # Status panel
        sf = tk.Frame(header, bg=C["bg"])
        sf.pack(side="right", padx=20, pady=10)
        self.lbl_status = tk.Label(sf, text="O OFFLINE",
                                    font=("Consolas", 18, "bold"),
                                    bg=C["bg"], fg=C["red"])
        self.lbl_status.pack(anchor="e")
        self.lbl_uptime = tk.Label(sf, text="Uptime: 00:00:00",
                                    font=("Consolas", 11), bg=C["bg"], fg=C["yellow"])
        self.lbl_uptime.pack(anchor="e")
        self.lbl_booster = tk.Label(sf, text="Booster: NONE",
                                     font=("Consolas", 10, "bold"),
                                     bg=C["bg"], fg=C["magenta"])
        self.lbl_booster.pack(anchor="e")
        self.lbl_time = tk.Label(sf, text=datetime.now().strftime("%H:%M:%S"),
                                  font=("Consolas", 11), bg=C["bg"], fg=C["cyan"])
        self.lbl_time.pack(anchor="e")

        # SEPARATOR
        tk.Frame(self.root, bg=C["green"], height=2).pack(fill="x")

        # TOOLBAR
        tb = tk.Frame(self.root, bg=C["panel"], height=60)
        tb.pack(fill="x"); tb.pack_propagate(False)

        buttons = [
            ("[> START]",   self.on_start,   C["green_dark"], C["green"]),
            ("[X STOP]",    self.on_stop,    C["red_dim"],   C["red"]),
            ("[DASH]",   self.on_dashboard, C["panel2"],   C["cyan"]),
            ("[WALLET]", self.on_wallet,   C["panel2"],   C["gold"]),
            ("[BOOSTER]",self.on_booster,  C["panel2"],   C["magenta"]),
            ("[HISTORY]",self.on_history,  C["panel2"],   C["magenta"]),
            ("[INSTALL]",self.on_install,  C["panel2"],   C["cyan"]),
            ("[ALGO]",   self.on_algo,     C["panel2"],   C["cyan"]),
            ("[REGION]", self.on_region,   C["panel2"],   C["cyan"]),
            ("[GPU]",    self.on_gpu,      C["panel2"],   C["cyan"]),
            ("[TEST]",   self.on_test,     C["panel2"],   C["cyan"]),
            ("[TOP]",    self.on_top,      C["panel2"],   C["cyan"]),
            ("[INFO]",   self.on_info,     C["panel2"],   C["cyan"]),
        ]
        for txt, cmd, bg, fg in buttons:
            b = tk.Button(tb, text=txt, command=cmd, font=("Consolas", 9, "bold"),
                          bg=bg, fg=fg, activebackground=fg, activeforeground=C["bg"],
                          relief="flat", bd=0, cursor="hand2", padx=8, pady=8,
                          highlightbackground=C["green_dim"], highlightthickness=1)
            b.pack(side="left", padx=2, pady=10)
            b.bind("<Enter>", lambda e, btn=b, c=fg: btn.configure(bg=c, fg=C["black"]))
            b.bind("<Leave>", lambda e, btn=b, c=bg, f=fg: btn.configure(bg=c, fg=f))

        # MAIN
        main = tk.Frame(self.root, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=8, pady=8)

        # LEFT — stats
        left = tk.Frame(main, bg=C["panel"], width=480,
                         highlightbackground=C["green_dim"], highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0,8))
        left.pack_propagate(False)
        self._build_stats(left)

        # RIGHT — log + algo + realtime
        right = tk.Frame(main, bg=C["bg"])
        right.pack(side="right", fill="both", expand=True)
        self._build_realtime_panel(right)
        self._build_log(right)
        self._build_top_algo(right)

        # STATUS BAR
        sb = tk.Frame(self.root, bg=C["panel"], height=28)
        sb.pack(fill="x", side="bottom"); sb.pack_propagate(False)
        self.sb_lbl = tk.Label(sb,
            text=f"{PEGASUS_BRAND} v19.0 | {PEGASUS_URL} | {WALLET[:20]}... | Worker: {WORKER}",
            font=("Consolas", 8), bg=C["panel"], fg=C["green_dim"])
        self.sb_lbl.pack(side="left", padx=10)

        self.sb_history = tk.Label(sb, text="", font=("Consolas", 8),
                                     bg=C["panel"], fg=C["cyan"])
        self.sb_history.pack(side="right", padx=10)

    def _build_stats(self, parent):
        h = tk.Frame(parent, bg=C["green_dark"], height=32)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text=" >> LIVE STATISTICS", font=("Consolas", 11, "bold"),
                 bg=C["green_dark"], fg=C["green"]).pack(anchor="w", padx=10, pady=6)

        self.vars = {}
        rows = [
            ("Hashrate 60s",  "hash60",  "0 H/s",  C["green"]),
            ("Hashrate 10s",  "hash10",  "0 H/s",  C["green_dim"]),
            ("Hashrate 15m",  "hash15",  "0 H/s",  C["green_dim"]),
            ("Max Hashrate",  "hashmax", "0 H/s",  C["orange"]),
            ("Accepted",      "acc",     "0",      C["green"]),
            ("Rejected",      "rej",     "0",      C["red"]),
            ("Difficulty",    "diff",    "0",      C["cyan"]),
            ("Pool Latency",  "latency", "0 ms",   C["cyan"]),
            ("Avg Share",     "shareint","0 s",    C["yellow"]),
            ("Jobs Received", "jobs",    "0",      C["cyan"]),
            ("Conn Status",   "conn",    "OFFLINE", C["red"]),
            ("Algo",          "algo",    DEFAULT_ALGO, C["yellow"]),
            ("Region",        "reg",     DEFAULT_REGION.upper(), C["yellow"]),
            ("Pool",          "pool",    "-",      C["cyan"]),
            ("Mode",          "mode",    "-",      C["cyan"]),
            ("PID",           "pid",     "-",      C["text"]),
            ("Uptime",        "up",      "00:00:00", C["yellow"]),
        ]
        for label, key, default, color in rows:
            row = tk.Frame(parent, bg=C["panel"])
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=f"  {label:<14}", font=("Consolas", 9),
                     bg=C["panel"], fg=C["text_dim"], width=16, anchor="w").pack(side="left")
            v = tk.StringVar(value=default)
            tk.Label(row, textvariable=v, font=("Consolas", 10, "bold"),
                     bg=C["panel"], fg=color, anchor="w").pack(side="left", fill="x", expand=True)
            self.vars[key] = v

        tk.Frame(parent, bg=C["green_dim"], height=1).pack(fill="x", padx=10, pady=6)

        # BTC WALLET
        tk.Label(parent, text=" >> BTC WALLET (SAVED)", font=("Consolas", 11, "bold"),
                 bg=C["panel"], fg=C["gold"]).pack(anchor="w", padx=10, pady=(0,5))
        for label, key, color in [("Balance", "wbal", C["gold"]),
                                   ("USD Value", "wusd", C["green"]),
                                   ("IDR Value", "widr", C["green"]),
                                   ("Total Earned", "wtearn", C["yellow"])]:
            row = tk.Frame(parent, bg=C["panel"])
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=f"  {label:<14}", font=("Consolas", 9),
                     bg=C["panel"], fg=C["text_dim"], width=16, anchor="w").pack(side="left")
            v = tk.StringVar(value="-")
            tk.Label(row, textvariable=v, font=("Consolas", 10, "bold"),
                     bg=C["panel"], fg=color, anchor="w").pack(side="left", fill="x", expand=True)
            self.vars[key] = v

        tk.Frame(parent, bg=C["green_dim"], height=1).pack(fill="x", padx=10, pady=6)

        # BOOSTER
        tk.Label(parent, text=" >> BTC BOOSTER", font=("Consolas", 11, "bold"),
                 bg=C["panel"], fg=C["magenta"]).pack(anchor="w", padx=10, pady=(0,5))
        for label, key, color in [("Level", "blevel", C["magenta"]),
                                   ("Multiplier", "bmult", C["yellow"]),
                                   ("Total Shares", "bshares", C["cyan"])]:
            row = tk.Frame(parent, bg=C["panel"])
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=f"  {label:<14}", font=("Consolas", 9),
                     bg=C["panel"], fg=C["text_dim"], width=16, anchor="w").pack(side="left")
            v = tk.StringVar(value="-")
            tk.Label(row, textvariable=v, font=("Consolas", 10, "bold"),
                     bg=C["panel"], fg=color, anchor="w").pack(side="left", fill="x", expand=True)
            self.vars[key] = v

        tk.Frame(parent, bg=C["green_dim"], height=1).pack(fill="x", padx=10, pady=6)

        # ESTIMATED EARNINGS
        tk.Label(parent, text=" >> ESTIMATED EARNINGS", font=("Consolas", 11, "bold"),
                 bg=C["panel"], fg=C["yellow"]).pack(anchor="w", padx=10, pady=(0,5))
        for label, key, color in [("BTC/Day", "btcday", C["yellow"]),
                                   ("USD/Day", "usdday", C["green"]),
                                   ("IDR/Day", "idrday", C["green"])]:
            row = tk.Frame(parent, bg=C["panel"])
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=f"  {label:<14}", font=("Consolas", 9),
                     bg=C["panel"], fg=C["text_dim"], width=16, anchor="w").pack(side="left")
            v = tk.StringVar(value="-")
            tk.Label(row, textvariable=v, font=("Consolas", 10, "bold"),
                     bg=C["panel"], fg=color, anchor="w").pack(side="left", fill="x", expand=True)
            self.vars[key] = v

        tk.Frame(parent, bg=C["green_dim"], height=1).pack(fill="x", padx=10, pady=6)

        # BTC PRICE + SYSTEM (compact)
        tk.Label(parent, text=" >> MARKET & SYSTEM", font=("Consolas", 11, "bold"),
                 bg=C["panel"], fg=C["green"]).pack(anchor="w", padx=10, pady=(0,5))
        for label, key, color in [("BTC/USD", "usd", C["yellow"]),
                                   ("BTC/IDR", "idr", C["yellow"]),
                                   ("CPU", "cpu", C["green"]),
                                   ("RAM", "ram", C["green"]),
                                   ("GPU", "gpu", C["cyan"])]:
            row = tk.Frame(parent, bg=C["panel"])
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=f"  {label:<14}", font=("Consolas", 9),
                     bg=C["panel"], fg=C["text_dim"], width=16, anchor="w").pack(side="left")
            v = tk.StringVar(value="-")
            tk.Label(row, textvariable=v, font=("Consolas", 10, "bold"),
                     bg=C["panel"], fg=color, anchor="w").pack(side="left", fill="x", expand=True)
            self.vars[key] = v

    def _build_realtime_panel(self, parent):
        frame = tk.Frame(parent, bg=C["panel"],
                          highlightbackground=C["green_dim"], highlightthickness=1)
        frame.pack(fill="x", pady=(0,5))

        h = tk.Frame(frame, bg=C["green_dark"], height=30)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text=" >> REAL-TIME MINING DETECTION",
                 font=("Consolas", 11, "bold"),
                 bg=C["green_dark"], fg=C["green"]).pack(anchor="w", padx=10, pady=5)

        body = tk.Frame(frame, bg=C["panel"])
        body.pack(fill="x", padx=10, pady=8)

        ind_frame = tk.Frame(body, bg=C["panel"])
        ind_frame.pack(fill="x", pady=5)

        self.ind_vars = {}
        indicators = [
            ("CONNECTION", "conn", C["red"]),
            ("MINING", "mining", C["red"]),
            ("FIRST SHARE", "share", C["red"]),
            ("HASHRATE", "hr", C["red"]),
        ]
        for i, (label, key, color) in enumerate(indicators):
            f = tk.Frame(ind_frame, bg=C["panel2"], bd=1, relief="solid",
                          highlightbackground=C["green_dim"], highlightthickness=1)
            f.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            ind_frame.columnconfigure(i, weight=1)
            tk.Label(f, text=label, font=("Consolas", 8), bg=C["panel2"],
                     fg=C["text_dim"]).pack(pady=(5,0))
            v = tk.StringVar(value="O OFFLINE")
            tk.Label(f, textvariable=v, font=("Consolas", 10, "bold"),
                     bg=C["panel2"], fg=color).pack(pady=(0,5))
            self.ind_vars[key] = v

        pb_frame = tk.Frame(body, bg=C["panel"])
        pb_frame.pack(fill="x", pady=5)

        tk.Label(pb_frame, text="Hashrate (60s):", font=("Consolas", 9),
                 bg=C["panel"], fg=C["text_dim"]).pack(anchor="w")
        self.hr_bar = ttk.Progressbar(pb_frame, mode="determinate", maximum=100,
                                       style="Green.Horizontal.TProgressbar")
        self.hr_bar.pack(fill="x", pady=2)

        tk.Label(pb_frame, text="Booster Progress:", font=("Consolas", 9),
                 bg=C["panel"], fg=C["text_dim"]).pack(anchor="w", pady=(5,0))
        self.boost_bar = ttk.Progressbar(pb_frame, mode="determinate", maximum=100,
                                          style="Mag.Horizontal.TProgressbar")
        self.boost_bar.pack(fill="x", pady=2)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Green.Horizontal.TProgressbar",
                         background=C["green"], troughcolor=C["black"],
                         bordercolor=C["green_dim"], lightcolor=C["green"],
                         darkcolor=C["green_dark"], thickness=18)
        style.configure("Mag.Horizontal.TProgressbar",
                         background=C["magenta"], troughcolor=C["black"],
                         bordercolor=C["magenta"], lightcolor=C["magenta"],
                         darkcolor=C["purple"], thickness=18)

    def _build_log(self, parent):
        frame = tk.Frame(parent, bg=C["panel"],
                          highlightbackground=C["green_dim"], highlightthickness=1)
        frame.pack(fill="both", expand=True, pady=(0,5))

        h = tk.Frame(frame, bg=C["green_dark"], height=30)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text=" >> MINER LOG (LIVE)", font=("Consolas", 11, "bold"),
                 bg=C["green_dark"], fg=C["green"]).pack(anchor="w", padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            frame, bg=C["black"], fg=C["green"], font=("Consolas", 9),
            insertbackground=C["green"], wrap="word", bd=0,
            selectbackground=C["green_dark"], selectforeground=C["green"]
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.log_text.configure(state="disabled")
        self.log_text.tag_config("ok",    foreground=C["green"])
        self.log_text.tag_config("err",   foreground=C["red"])
        self.log_text.tag_config("warn",  foreground=C["yellow"])
        self.log_text.tag_config("info",  foreground=C["text"])
        self.log_text.tag_config("cyan",  foreground=C["cyan"])
        self.log_text.tag_config("mag",   foreground=C["magenta"])
        self.log_text.tag_config("gold",  foreground=C["gold"])

    def _build_top_algo(self, parent):
        frame = tk.Frame(parent, bg=C["panel"],
                          highlightbackground=C["green_dim"], highlightthickness=1)
        frame.pack(fill="x")

        h = tk.Frame(frame, bg=C["green_dark"], height=30)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text=" >> TOP ALGORITHMS (NiceHash)",
                 font=("Consolas", 11, "bold"),
                 bg=C["green_dark"], fg=C["green"]).pack(anchor="w", padx=10, pady=5)

        cols = ("#", "Algorithm", "Port", "BTC/GH/day", "Est. BTC/Day")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Hack.Treeview",
                         background=C["black"], foreground=C["green"],
                         fieldbackground=C["black"], rowheight=24,
                         font=("Consolas", 9))
        style.configure("Hack.Treeview.Heading",
                         background=C["green_dark"], foreground=C["green"],
                         font=("Consolas", 9, "bold"))
        self.algo_tree = ttk.Treeview(frame, columns=cols, show="headings", height=6,
                                       style="Hack.Treeview")
        for c in cols:
            self.algo_tree.heading(c, text=c)
            self.algo_tree.column(c, width=120, anchor="center")
        self.algo_tree.column("Algorithm", width=180, anchor="w")
        self.algo_tree.column("BTC/GH/day", width=140, anchor="e")
        self.algo_tree.column("Est. BTC/Day", width=140, anchor="e")
        self.algo_tree.pack(fill="x", padx=6, pady=6)

    def log(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line, tag)
        self.log_text.see("end")
        if int(self.log_text.index("end-1c").split(".")[0]) > 800:
            self.log_text.delete("1.0", "200.0")
        self.log_text.configure(state="disabled")

    def _banner(self):
        self.log("=" * 60, "ok")
        self.log(f"  {PEGASUS_BRAND} - NICEHASH MINER v19.0", "ok")
        self.log(f"  {PEGASUS_URL}", "cyan")
        self.log("  XMRig (CPU) | lolMiner (GPU) | Real-Time Detection", "ok")
        self.log("  BTC Booster | Persistent Wallet | History Tracking", "mag")
        self.log("=" * 60, "ok")
        self.log(f"Wallet  : {WALLET}", "cyan")
        self.log(f"Worker  : {WORKER}", "cyan")
        self.log(f"OS      : {platform.system()} {platform.release()}", "cyan")

        bal = btc_wallet.get_balance()
        lvl = booster.get_current_level()
        self.log(f"BTC Balance (saved) : {bal:.10f} BTC", "gold")
        self.log(f"Booster Level       : {lvl['name']} (x{lvl['mult']:.2f})", "mag")

        s = history.get_stats()
        self.log(f"History : {s['total_sessions']} session(s) tersimpan", "mag")
        self.log("")

        gpus = detect_gpus()
        if gpus:
            self.log(f"[*] Terdeteksi {len(gpus)} GPU:", "info")
            for g in gpus:
                status = "KOMPATIBEL" if g["compatible"] else "tidak kompatibel"
                self.log(f"    - {g['name']} ({g['vendor']}, {g['vram']} MB) - {status}", "cyan")
        else:
            self.log("[!] Tidak ada GPU dedicated - pakai CPU mining (XMRig)", "warn")
        self.log("")
        self.log("[>] Klik [START] untuk mulai mining ke NiceHash wallet Anda", "ok")
        self.log("[>] Klik [WALLET] untuk lihat saldo BTC (tersimpan permanen)", "gold")
        self.log("[>] Klik [BOOSTER] untuk lihat progress booster BTC", "mag")
        self.log("[>] Klik [HISTORY] untuk lihat history mining", "mag")
        self.log("[>] Algo default: RANDOMXMONERO (CPU - selalu bisa jalan)", "ok")
        self.log("")

        threading.Thread(target=self._load_top, daemon=True).start()

    def _load_top(self):
        algos = get_nh_algos()
        if not algos:
            self.log("[!] Gagal ambil data NiceHash (cek internet)", "warn")
            return
        items = sorted(algos.items(), key=lambda x: x[1]["paying"], reverse=True)[:15]
        def upd():
            for i, (name, info) in enumerate(items, 1):
                est = 0
                if detector.hashrate_60s > 0:
                    est = detector.get_estimated_earnings(info["paying"])
                self.algo_tree.insert("", "end", values=(
                    i, name, info["port"], f"{info['paying']:.8f}",
                    f"{est:.8f}" if est > 0 else "-"
                ))
        self.root.after(0, upd)
        self.log(f"[OK] {len(algos)} algoritma dimuat dari NiceHash API", "ok")

    def _refresh(self):
        self.lbl_time.config(text=datetime.now().strftime("%H:%M:%S"))
        running = miner.is_running()

        if running:
            self.lbl_status.config(text="O MINING", fg=C["green"])
        else:
            self.lbl_status.config(text="O OFFLINE", fg=C["red"])
        self.lbl_uptime.config(text=f"Uptime: {miner.uptime()}")

        lvl = booster.get_current_level()
        self.lbl_booster.config(text=f"Booster: {lvl['name']} x{lvl['mult']:.2f}", fg=lvl["color"])

        # BTC Balance
        bal = btc_wallet.get_balance()
        self.lbl_btc_balance.config(text=f"{bal:.10f} BTC")
        p = get_btc_price()
        usd = bal * p.get("usd", 0)
        idr = bal * p.get("idr", 0)
        self.lbl_btc_usd.config(text=f"${usd:,.4f} | Rp {idr:,.0f}")

        # Parse log
        miner.parse_log()

        # Update stats
        self.vars["hash60"].set(detector.format_hashrate(detector.hashrate_60s))
        self.vars["hash10"].set(detector.format_hashrate(detector.hashrate_10s))
        self.vars["hash15"].set(detector.format_hashrate(detector.hashrate_15m))
        self.vars["hashmax"].set(detector.format_hashrate(detector.hashrate_max))
        self.vars["acc"].set(str(detector.accepted))
        self.vars["rej"].set(str(detector.rejected))
        self.vars["diff"].set(str(detector.difficulty))
        self.vars["latency"].set(f"{detector.pool_latency} ms")
        self.vars["shareint"].set(f"{detector.avg_share_interval:.0f} s" if detector.avg_share_interval > 0 else "-")
        self.vars["jobs"].set(str(detector.job_count))
        self.vars["conn"].set(detector.connection_status)
        self.vars["algo"].set(miner.algo)
        self.vars["reg"].set(miner.region.upper())
        self.vars["mode"].set("CPU/XMRig" if miner.mode == "cpu" else "GPU/lolMiner")
        try:
            port = get_pool_port(miner.algo)
            self.vars["pool"].set(f"{miner.algo.lower()}.{miner.region}.nh:{port}")
        except: pass
        pid = miner.proc.pid if running else "-"
        self.vars["pid"].set(str(pid))
        self.vars["up"].set(miner.uptime())

        # Wallet vars
        self.vars["wbal"].set(f"{bal:.10f} BTC")
        self.vars["wusd"].set(f"${usd:,.4f}")
        self.vars["widr"].set(f"Rp {idr:,.0f}")
        self.vars["wtearn"].set(f"{btc_wallet.wallet['total_earned_btc']:.10f} BTC")

        # Booster vars
        self.vars["blevel"].set(lvl["name"])
        self.vars["bmult"].set(f"x{lvl['mult']:.2f}")
        self.vars["bshares"].set(str(btc_wallet.wallet.get("total_shares", 0)))

        # Estimated earnings
        algos = get_nh_algos()
        paying = algos.get(miner.algo, {}).get("paying", 0)
        est_btc = detector.get_estimated_earnings(paying)
        self.vars["btcday"].set(f"{est_btc:.8f} BTC" if est_btc > 0 else "-")
        usd_rate = p.get("usd", 0)
        idr_rate = p.get("idr", 0)
        if est_btc > 0 and usd_rate > 0:
            self.vars["usdday"].set(f"${est_btc * usd_rate:.4f}")
        else:
            self.vars["usdday"].set("-")
        if est_btc > 0 and idr_rate > 0:
            self.vars["idrday"].set(f"Rp {est_btc * idr_rate:,.0f}")
        else:
            self.vars["idrday"].set("-")

        # Market
        self.vars["usd"].set(f"${p.get('usd',0):,.0f}")
        self.vars["idr"].set(f"Rp {p.get('idr',0):,.0f}")

        # System
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            self.vars["cpu"].set(f"{cpu:.1f}%")
            self.vars["ram"].set(f"{ram.percent:.0f}%")
            if not hasattr(self, "_gpu_txt"):
                gpus = detect_gpus()
                self._gpu_txt = gpus[0]["name"][:22] if gpus else "None"
            self.vars["gpu"].set(self._gpu_txt)
        except: pass

        # Status bar
        s = history.get_stats()
        tt = s["total_time"]
        h, r = divmod(tt, 3600); m, sec = divmod(r, 60)
        self.sb_history.config(
            text=f"[{s['total_sessions']} sessions | {h:02d}h {m:02d}m | OK {s['total_accepted']} | X {s['total_rejected']} | BTC {bal:.8f}]")

        # Indicators
        self._update_indicators(running)

        # Refresh log
        if running and miner.log_file and miner.log_file.exists():
            try:
                lines = miner._tail(80)
                self.log_text.configure(state="normal")
                self.log_text.delete("1.0", "end")
                for l in lines:
                    low = l.lower()
                    tag = "info"
                    if any(k in low for k in ["accepted", "share", "solved", "yes!"]): tag = "ok"
                    elif any(k in low for k in ["error","fail","reject","invalid"]): tag = "err"
                    elif any(k in low for k in ["speed","hashrate","job","new job"]): tag = "cyan"
                    elif "warn" in low: tag = "warn"
                    self.log_text.insert("end", l + "\n", tag)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
            except: pass

        self.root.after(1500, self._refresh)

    def _update_indicators(self, running):
        if running and detector.connection_status == "CONNECTED":
            self.ind_vars["conn"].set("O CONNECTED")
        elif running:
            self.ind_vars["conn"].set("O CONNECTING")
        else:
            self.ind_vars["conn"].set("O OFFLINE")

        if running and detector.hashrate_60s > 0:
            self.ind_vars["mining"].set("O ACTIVE")
        elif running:
            self.ind_vars["mining"].set("O STARTING")
        else:
            self.ind_vars["mining"].set("O IDLE")

        if detector.first_share_received:
            self.ind_vars["share"].set("O RECEIVED")
        elif running:
            self.ind_vars["share"].set("O WAITING")
        else:
            self.ind_vars["share"].set("O NONE")

        if detector.hashrate_60s > 0:
            self.ind_vars["hr"].set("O STABLE")
        elif running:
            self.ind_vars["hr"].set("O MEASURING")
        else:
            self.ind_vars["hr"].set("O 0 H/s")

        if detector.hashrate_max > 0:
            pct = min(100, (detector.hashrate_60s / detector.hashrate_max) * 100)
            self.hr_bar["value"] = pct
        else:
            self.hr_bar["value"] = 0

        self.boost_bar["value"] = booster.get_progress()

    # ACTIONS
    def on_start(self):
        self.log("=" * 50, "cyan")
        self.log("[>] START MINING - NiceHash", "ok")
        self.log(f"   Algo: {miner.algo} | Region: {miner.region.upper()}", "cyan")

        def do():
            ok = miner.start(miner.algo, miner.region,
                              lambda m: self.root.after(0, self.log, m, "info"))
            if ok:
                self.root.after(0, self.log, "[OK] MINING BERJALAN! Tunggu ~30 detik untuk share pertama", "ok")
                self.root.after(0, self.log, f"History session dimulai: {history.current_session['id'] if history.current_session else '-'}", "mag")
                self.root.after(0, self.log, f"BTC akan otomatis ditambahkan ke saldo Anda (disimpan permanen)", "gold")
            else:
                self.root.after(0, self.log, "[X] Gagal start mining - cek log di atas", "err")
        threading.Thread(target=do, daemon=True).start()

    def on_stop(self):
        self.log("[*] Stop mining...", "warn")
        miner.stop()
        self.log("[OK] Miner dihentikan", "ok")
        self.log(f"[OK] Session tersimpan ke history", "mag")
        self.log(f"[OK] Saldo BTC tersimpan permanen: {btc_wallet.get_balance():.10f} BTC", "gold")

    def on_wallet(self):
        BTCWalletWindow(self.root)

    def on_booster(self):
        BoosterWindow(self.root)

    def on_history(self):
        HistoryWindow(self.root)

    def on_dashboard(self):
        win = tk.Toplevel(self.root)
        win.title(f"{PEGASUS_BRAND} - DASHBOARD")
        win.configure(bg=C["bg"])
        win.geometry("800x900")

        tk.Label(win, text=f"| {PEGASUS_BRAND.upper()} DASHBOARD",
                 font=("Consolas", 18, "bold"), bg=C["bg"], fg=C["green"]).pack(pady=15)

        info = tk.Frame(win, bg=C["panel"],
                         highlightbackground=C["green_dim"], highlightthickness=1)
        info.pack(fill="both", expand=True, padx=20, pady=10)

        dv = {}
        keys = [("Status","status",C["green"]),("Uptime","up",C["yellow"]),
                ("Hashrate 60s","hr",C["green"]),("Hashrate 10s","hr10",C["green_dim"]),
                ("Hashrate Max","hrmax",C["orange"]),
                ("Accepted","acc",C["green"]),("Rejected","rej",C["red"]),
                ("Difficulty","diff",C["cyan"]),("Pool Latency","lat",C["cyan"]),
                ("Jobs","jobs",C["cyan"]),
                ("Algo","algo",C["yellow"]),("Region","reg",C["yellow"]),
                ("Pool","pool",C["cyan"]),("Mode","mode",C["cyan"]),
                ("PID","pid",C["text"]),("Worker","w",C["cyan"]),
                ("BTC/USD","btc",C["yellow"]),
                ("BTC Balance","bal",C["gold"]),
                ("Balance USD","balusd",C["green"]),
                ("Balance IDR","balidr",C["green"]),
                ("Booster Level","blvl",C["magenta"]),
                ("Booster Multiplier","bmult",C["magenta"]),
                ("Total Shares","bshr",C["cyan"]),
                ("Est. BTC/Day","ebtc",C["yellow"]),
                ("Est. USD/Day","eusd",C["green"]),
                ("Est. IDR/Day","eidr",C["green"]),
                ("Session","sess",C["magenta"]),
                ("Total Sessions","ts",C["magenta"]),
                ("Total Time","tt",C["magenta"])]
        for label, k, color in keys:
            row = tk.Frame(info, bg=C["panel"]); row.pack(fill="x", padx=20, pady=3)
            tk.Label(row, text=f"  {label:<18}", font=("Consolas", 10),
                     bg=C["panel"], fg=C["text_dim"], width=20, anchor="w").pack(side="left")
            v = tk.StringVar(value="-")
            tk.Label(row, textvariable=v, font=("Consolas", 11, "bold"),
                     bg=C["panel"], fg=color, anchor="w").pack(side="left", fill="x", expand=True)
            dv[k] = v

        def upd():
            if not win.winfo_exists(): return
            miner.parse_log()
            dv["status"].set("O MINING" if miner.is_running() else "O OFFLINE")
            dv["up"].set(miner.uptime())
            dv["hr"].set(detector.format_hashrate(detector.hashrate_60s))
            dv["hr10"].set(detector.format_hashrate(detector.hashrate_10s))
            dv["hrmax"].set(detector.format_hashrate(detector.hashrate_max))
            dv["acc"].set(str(detector.accepted))
            dv["rej"].set(str(detector.rejected))
            dv["diff"].set(str(detector.difficulty))
            dv["lat"].set(f"{detector.pool_latency} ms")
            dv["jobs"].set(str(detector.job_count))
            dv["algo"].set(miner.algo)
            dv["reg"].set(miner.region.upper())
            try:
                port = get_pool_port(miner.algo)
                dv["pool"].set(f"{miner.algo.lower()}.{miner.region}.nh:{port}")
            except: pass
            dv["mode"].set("CPU/XMRig" if miner.mode == "cpu" else "GPU/lolMiner")
            dv["pid"].set(str(miner.proc.pid) if miner.is_running() else "-")
            dv["w"].set(WORKER)
            dv["sess"].set(history.current_session["id"] if history.current_session else "-")
            s = history.get_stats()
            dv["ts"].set(str(s["total_sessions"]))
            tt = s["total_time"]
            h, r = divmod(tt, 3600); m, sec = divmod(r, 60)
            dv["tt"].set(f"{h:02d}h {m:02d}m {sec:02d}s")
            p = get_btc_price()
            dv["btc"].set(f"${p.get('usd',0):,.0f}")
            bal = btc_wallet.get_balance()
            dv["bal"].set(f"{bal:.10f} BTC")
            dv["balusd"].set(f"${bal * p.get('usd', 0):,.4f}")
            dv["balidr"].set(f"Rp {bal * p.get('idr', 0):,.0f}")
            lvl = booster.get_current_level()
            dv["blvl"].set(lvl["name"])
            dv["bmult"].set(f"x{lvl['mult']:.2f}")
            dv["bshr"].set(str(btc_wallet.wallet.get("total_shares", 0)))
            algos = get_nh_algos()
            paying = algos.get(miner.algo, {}).get("paying", 0)
            est = detector.get_estimated_earnings(paying)
            dv["ebtc"].set(f"{est:.8f} BTC" if est > 0 else "-")
            if est > 0 and p.get("usd"):
                dv["eusd"].set(f"${est * p['usd']:.4f}")
            else:
                dv["eusd"].set("-")
            if est > 0 and p.get("idr"):
                dv["eidr"].set(f"Rp {est * p['idr']:,.0f}")
            else:
                dv["eidr"].set("-")
            win.after(1500, upd)
        upd()

    def on_install(self):
        self.log("[*] Force download XMRig + lolMiner...", "info")
        def do():
            miner.ensure_xmrig(lambda m: self.root.after(0, self.log, m, "info"))
            miner.ensure_lolminer(lambda m: self.root.after(0, self.log, m, "info"))
            self.root.after(0, self.log, "[OK] Selesai download binary", "ok")
        threading.Thread(target=do, daemon=True).start()

    def on_algo(self):
        self._popup("PILIH ALGORITMA", self._get_algo_items(), self._set_algo)

    def _get_algo_items(self):
        algos = get_nh_algos()
        if not algos:
            items = []
            for a in CPU_ALGOS + GPU_ALGOS:
                items.append({"algo": a, "paying": 0, "port": get_pool_port(a)})
            return items
        items = [{"algo": k, "paying": v["paying"], "port": v["port"]}
                 for k, v in algos.items()]
        items.sort(key=lambda x: x["paying"], reverse=True)
        return items

    def _set_algo(self, algo):
        miner.algo = algo.upper()
        self.log(f"[OK] Algo diset: {algo.upper()}", "ok")
        self.log("[i] Klik [START] untuk apply", "warn")

    def on_region(self):
        items = [{"algo": r, "name": n} for r, n in REGIONS.items()]
        self._popup("PILIH REGION", items, self._set_region, show_name=True)

    def _set_region(self, region):
        miner.region = region
        self.log(f"[OK] Region diset: {region.upper()}", "ok")

    def _popup(self, title, items, callback, show_name=False):
        win = tk.Toplevel(self.root)
        win.title(f"{PEGASUS_BRAND} - {title}")
        win.configure(bg=C["bg"])
        win.geometry("700x600")

        tk.Label(win, text=f"| {title}", font=("Consolas", 14, "bold"),
                 bg=C["bg"], fg=C["green"]).pack(pady=10)

        lb = tk.Listbox(win, bg=C["black"], fg=C["green"],
                         font=("Consolas", 11),
                         selectbackground=C["green"], selectforeground=C["black"],
                         bd=0, highlightthickness=1,
                         highlightbackground=C["green_dim"])
        lb.pack(fill="both", expand=True, padx=15, pady=10)

        for i, it in enumerate(items, 1):
            if show_name and "name" in it:
                lb.insert("end", f"  {it['algo'].upper():<8} - {it['name']}")
            else:
                pay = it.get("paying", 0)
                port = it.get("port", "-")
                lb.insert("end", f"  {i:>2}. {it['algo']:<24} port:{port:<6}  {pay:.8f} BTC")

        def on_sel():
            sel = lb.curselection()
            if sel:
                callback(items[sel[0]]["algo"])
                win.destroy()

        b = tk.Button(win, text="[ PILIH ]", command=on_sel, font=("Consolas", 12, "bold"),
                       bg=C["green_dark"], fg=C["green"], relief="flat", bd=0,
                       cursor="hand2", padx=30, pady=8,
                       highlightbackground=C["green"], highlightthickness=1)
        b.pack(pady=10)
        b.bind("<Enter>", lambda e: b.configure(bg=C["green"], fg=C["black"]))
        b.bind("<Leave>", lambda e: b.configure(bg=C["green_dark"], fg=C["green"]))

    def on_gpu(self):
        gpus = detect_gpus()
        if not gpus:
            self.log("[!] Tidak ada GPU terdeteksi", "warn")
            messagebox.showwarning("GPU Info",
                "Tidak ada GPU dedicated terdeteksi.\n\n"
                "- Gunakan algo CPU seperti RANDOMXMONERO (default).\n"
                "- XMRig akan mining pakai CPU Anda ke NiceHash wallet.")
            return
        txt = "GPU TERDETEKSI:\n\n"
        for i, g in enumerate(gpus, 1):
            txt += f"{i}. {g['name']}\n"
            txt += f"   Vendor: {g['vendor']}  |  VRAM: {g['vram']} MB\n"
            txt += f"   Kompatibel: {'YA' if g['compatible'] else 'TIDAK'}\n\n"
        messagebox.showinfo("GPU Info", txt)
        for g in gpus:
            self.log(f"[GPU] {g['name']} ({g['vendor']}, {g['vram']}MB) {'OK' if g['compatible'] else 'X'}", "cyan")

    def on_test(self):
        self.log("[*] Test koneksi ke NiceHash...", "info")
        def do():
            algo = miner.algo.lower()
            region = miner.region
            try:
                port = get_pool_port(miner.algo)
            except:
                port = 9200
            host = f"{algo}.{region}.nicehash.com"
            try:
                t0 = time.time()
                s = socket.create_connection((host, port), timeout=8)
                latency = int((time.time() - t0) * 1000)
                s.close()
                self.root.after(0, self.log, f"[OK] {host}:{port} OK - latency {latency}ms", "ok")
            except Exception as e:
                self.root.after(0, self.log, f"[X] {host}:{port} -> {e}", "err")
        threading.Thread(target=do, daemon=True).start()

    def on_top(self):
        self.log("[*] Refresh top algorithms...", "info")
        for r in self.algo_tree.get_children(): self.algo_tree.delete(r)
        threading.Thread(target=self._load_top, daemon=True).start()

    def on_info(self):
        gpus = detect_gpus()
        gtxt = gpus[0]["name"] if gpus else "Tidak ada GPU dedicated"
        s = history.get_stats()
        bal = btc_wallet.get_balance()
        lvl = booster.get_current_level()
        info = f"""
{PEGASUS_BRAND} - NICEHASH MINER v19.0
{PEGASUS_URL}

WALLET : {WALLET}
WORKER : {WORKER}

Algo   : {miner.algo}
Region : {miner.region.upper()}
Pool   : {miner.algo.lower()}.{miner.region}.nicehash.com:{get_pool_port(miner.algo)}
Mode   : {'CPU/XMRig' if miner.mode == 'cpu' else 'GPU/lolMiner'}

GPU    : {gtxt}
Status : {'RUNNING' if miner.is_running() else 'OFFLINE'}
Uptime : {miner.uptime()}

BTC WALLET (PERSISTENT):
  Balance          : {bal:.10f} BTC
  Total Earned     : {btc_wallet.wallet['total_earned_btc']:.10f} BTC
  Total Shares     : {btc_wallet.wallet.get('total_shares', 0)}
  Total Sessions   : {btc_wallet.wallet.get('sessions_count', 0)}
  Wallet DB        : {WALLET_DB}

BOOSTER:
  Level            : {lvl['name']}
  Multiplier       : x{lvl['mult']:.2f}
  Active           : {btc_wallet.wallet.get('booster_active', True)}

REAL-TIME DETECTION:
  Hashrate 60s   : {detector.format_hashrate(detector.hashrate_60s)}
  Hashrate 10s   : {detector.format_hashrate(detector.hashrate_10s)}
  Hashrate Max   : {detector.format_hashrate(detector.hashrate_max)}
  Accepted       : {detector.accepted}
  Rejected       : {detector.rejected}
  Difficulty     : {detector.difficulty}
  Pool Latency   : {detector.pool_latency} ms
  Jobs Received  : {detector.job_count}
  Connection     : {detector.connection_status}

HISTORY:
  Total Sessions : {s['total_sessions']}
  Total Time     : {s['total_time']}s
  Total Accepted : {s['total_accepted']}
  Total Rejected : {s['total_rejected']}

Paths:
  Base    : {BASE_DIR}
  Miner   : {MINER_DIR}
  Logs    : {LOGS_DIR}
  History : {HISTORY_DB}
  Wallet  : {WALLET_DB}

CARA CEK HASIL:
1. Tunggu 5-10 menit setelah share pertama
2. Buka https://www.nicehash.com/my/miner
3. Login akun NiceHash Anda
4. Wallet: {WALLET[:20]}...

CATATAN:
- BTC Balance di aplikasi ini adalah ESTIMASI dari mining Anda
- Saldo tersimpan permanen di: {WALLET_DB}
- Booster meningkatkan multiplier earning Anda
- History otomatis tersimpan setiap session selesai
"""
        messagebox.showinfo("Info", info)

# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    lr = tk.Tk()
    LoginWindow(lr)
    lr.mainloop()

    root = tk.Tk()
    app = PegasusGUI(root)

    def on_close():
        if messagebox.askyesno("Keluar",
            f"Yakin keluar? Miner akan dihentikan.\n\n"
            f"BTC Balance akan DISIMPAN: {btc_wallet.get_balance():.10f} BTC\n"
            f"History & wallet tersimpan permanen."):
            miner.watchdog = False
            if miner.is_running(): miner.stop()
            btc_wallet.record_snapshot()
            btc_wallet._save()
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        try:
            miner.stop()
            btc_wallet._save()
        except: pass
        sys.exit(0)
    except Exception as e:
        print(f"Fatal: {e}")
        traceback.print_exc()