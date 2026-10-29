#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║        PEGASUS NICEHASH MINER v19.0 — CLI TOOLS VERSION         ║
║   ✅ XMRig (CPU) + lolMiner (GPU) — SUPPORT NICEHASH            ║
║   ✅ Real-time Mining Detection (Hashrate, Shares, Diff)        ║
║   ✅ Auto-detect GPU/CPU                                        ║
║   ✅ Auto download binary     ✅ Wallet langsung ke NiceHash    ║
║   ✅ HISTORY LOG MINING       ✅ EXPORT CSV / JSON              ║
║   ✅ SESSION TRACKING         ✅ BTC BALANCE PERSISTENT         ║
║   ✅ BTC BOOSTER SYSTEM       ✅ AUTO-SAVE WALLET               ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, re, sys, json, time, shutil, zipfile, tarfile, csv, hashlib
import platform, tempfile, subprocess, threading, traceback, socket, argparse
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

for mod, pkg in [("requests","requests"),("psutil","psutil")]:
    if not _can(mod):
        print(f"[*] Install {pkg}...")
        _pip(pkg)

import requests, psutil

# ══════════════════════════════════════════════════════════════════
#  PEGASUSMETASEC BRANDING
# ══════════════════════════════════════════════════════════════════
PEGASUS_BRAND = "PegasusMetaSec"
PEGASUS_URL   = "https://pegasusmetasec.com"
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
#  WARNA TERMINAL
# ══════════════════════════════════════════════════════════════════
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    GREEN   = "\033[92m"
    GREEN_D = "\033[32m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    ORANGE  = "\033[33m"
    CYAN    = "\033[96m"
    CYAN_D  = "\033[36m"
    MAGENTA = "\033[95m"
    PURPLE  = "\033[35m"
    GOLD    = "\033[33m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"

    @staticmethod
    def disable():
        for k in list(vars(C).keys()):
            if k.isupper():
                setattr(C, k, "")

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
            "wallet": WALLET, "worker": WORKER, "balance_btc": 0.0,
            "total_earned_btc": 0.0, "total_earned_usd": 0.0, "total_earned_idr": 0.0,
            "total_withdrawn_btc": 0.0, "booster_active": True, "booster_multiplier": 1.0,
            "created": datetime.now().isoformat(), "last_updated": datetime.now().isoformat(),
            "total_shares": 0, "total_mining_seconds": 0, "sessions_count": 0,
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
        if btc_amount <= 0:
            return
        if self.wallet.get("booster_active", True):
            boosted = btc_amount * self.wallet.get("booster_multiplier", 1.0)
        else:
            boosted = btc_amount
        self.wallet["balance_btc"] += boosted
        self.wallet["total_earned_btc"] += boosted
        self.session_btc += boosted
        price = get_btc_price()
        if price.get("usd"):
            self.wallet["total_earned_usd"] += boosted * price["usd"]
        if price.get("idr"):
            self.wallet["total_earned_idr"] += boosted * price["idr"]
        if time.time() - self._last_save > 30:
            self._last_save = time.time()
            self._save()

    def record_snapshot(self):
        self.balance_history["snapshots"].append({
            "ts": datetime.now().isoformat(),
            "balance_btc": self.wallet["balance_btc"],
            "total_earned_btc": self.wallet["total_earned_btc"],
        })
        if len(self.balance_history["snapshots"]) > 5000:
            self.balance_history["snapshots"] = self.balance_history["snapshots"][-3000:]
        self._save()

    def set_booster(self, active, multiplier=1.0):
        self.wallet["booster_active"] = active
        self.wallet["booster_multiplier"] = max(1.0, multiplier)
        self._save()

    def get_balance(self):
        return self.wallet["balance_btc"]

    def get_balance_usd(self):
        return self.wallet["balance_btc"] * get_btc_price().get("usd", 0)

    def get_balance_idr(self):
        return self.wallet["balance_btc"] * get_btc_price().get("idr", 0)

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
    def __init__(self):
        self.levels = [
            {"name": "NONE",      "mult": 1.0,  "color": C.GRAY,    "req_shares": 0},
            {"name": "BRONZE",    "mult": 1.15, "color": "\033[38;5;173m", "req_shares": 10},
            {"name": "SILVER",    "mult": 1.30, "color": "\033[37m", "req_shares": 50},
            {"name": "GOLD",      "mult": 1.50, "color": C.GOLD,    "req_shares": 200},
            {"name": "PLATINUM",  "mult": 1.75, "color": "\033[97m", "req_shares": 500},
            {"name": "DIAMOND",   "mult": 2.00, "color": C.CYAN,    "req_shares": 1000},
            {"name": "LEGENDARY", "mult": 2.50, "color": C.MAGENTA, "req_shares": 5000},
            {"name": "MYTHIC",    "mult": 3.00, "color": C.PURPLE,  "req_shares": 10000},
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
        lvl = self.get_current_level()
        base_mult = lvl["mult"]
        if btc_wallet.wallet.get("booster_active", True):
            return base_btc * base_mult
        return base_btc

booster = BTCBooster()

# ══════════════════════════════════════════════════════════════════
#  REAL-TIME MINING DETECTOR
# ══════════════════════════════════════════════════════════════════
class MiningDetector:
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
        return booster.apply_boost(base)

    def format_hashrate(self, hr):
        if hr >= 1e9: return f"{hr/1e9:.3f} GH/s"
        if hr >= 1e6: return f"{hr/1e6:.3f} MH/s"
        if hr >= 1e3: return f"{hr/1e3:.3f} KH/s"
        return f"{hr:.2f} H/s"

    def update_btc_earnings(self, paying_rate):
        if time.time() - self._last_btc_add < 10:
            return
        self._last_btc_add = time.time()
        daily = self.get_estimated_earnings(paying_rate)
        per_10s = daily * (10 / 86400)
        if per_10s > 0:
            btc_wallet.add_earnings(per_10s)

detector = MiningDetector()

# ══════════════════════════════════════════════════════════════════
#  HISTORY MANAGER
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
            "algo": algo, "region": region, "mode": mode,
            "start": datetime.now().isoformat(), "end": None,
            "duration": 0, "accepted": 0, "rejected": 0,
            "hashrate_avg": 0.0, "hashrate_max": 0.0, "btc_earned": 0.0, "shares": [],
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
            "total_sessions": len(s), "total_time": self.db["total_mining_time"],
            "total_accepted": self.db["total_accepted"],
            "total_rejected": self.db["total_rejected"], "sessions": s,
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
            str(exe), "-o", pool,
            "-u", f"{WALLET}.{WORKER}",
            "-p", "x",
            "-a", "rx/0" if algo == "RANDOMXMONERO" else algo.lower(),
            "-k", "--no-color",
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
            str(exe), "--algo", lol_algo,
            "--pool", pool,
            "--user", f"{WALLET}.{WORKER}",
            "--pass", "x",
            "--apiport", "0", "--nocolor",
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
                if time.time() - self._last_history_update > 30:
                    self._last_history_update = time.time()
                    history.update_session(detector.accepted, detector.rejected,
                                            detector.hashrate_60s)

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
#  CLI TOOLS FUNCTIONS
# ══════════════════════════════════════════════════════════════════
def clear_screen():
    os.system("cls" if IS_WIN else "clear")

def print_banner():
    clear_screen()
    print(f"{C.GREEN}{PEGASUS_ASCII.format(url=PEGASUS_URL)}{C.RESET}")
    print(f"{C.YELLOW}{C.BOLD}  [ {PEGASUS_BRAND} — NICEHASH MINER v19.0 CLI TOOLS ]{C.RESET}")
    print(f"{C.CYAN}  Visit: {PEGASUS_URL}{C.RESET}")
    print(f"{C.GREEN}  {'=' * 64}{C.RESET}")

def print_log(msg, tag="info"):
    colors = {
        "ok":   C.GREEN, "err": C.RED, "warn": C.YELLOW,
        "info": C.WHITE, "cyan": C.CYAN, "mag": C.MAGENTA, "gold": C.GOLD,
    }
    ts = datetime.now().strftime("%H:%M:%S")
    color = colors.get(tag, C.WHITE)
    print(f"{C.GRAY}[{ts}]{C.RESET} {color}{msg}{C.RESET}")

def status_bar():
    running = miner.is_running()
    bal = btc_wallet.get_balance()
    lvl = booster.get_current_level()
    s = history.get_stats()
    tt = s["total_time"]
    h, r = divmod(tt, 3600); m, sec = divmod(r, 60)
    status = f"{C.GREEN}● MINING{C.RESET}" if running else f"{C.RED}○ OFFLINE{C.RESET}"
    hr = detector.format_hashrate(detector.hashrate_60s)
    print(f"\n{C.GRAY}{'─' * 64}{C.RESET}")
    print(f"  Status : {status}   Uptime: {C.YELLOW}{miner.uptime()}{C.RESET}   "
          f"Hashrate: {C.GREEN}{hr}{C.RESET}")
    print(f"  BTC    : {C.GOLD}{bal:.10f}{C.RESET}   "
          f"Booster: {lvl['color']}{lvl['name']} x{lvl['mult']:.2f}{C.RESET}   "
          f"Shares: {C.CYAN}{btc_wallet.wallet.get('total_shares',0)}{C.RESET}")
    print(f"  Session: {C.MAGENTA}{s['total_sessions']}{C.RESET}  "
          f"Time: {C.YELLOW}{h:02d}h {m:02d}m {sec:02d}s{C.RESET}  "
          f"Accepted: {C.GREEN}{detector.accepted}{C.RESET}  "
          f"Rejected: {C.RED}{detector.rejected}{C.RESET}")
    print(f"{C.GRAY}{'─' * 64}{C.RESET}\n")

def print_stats():
    status_bar()
    print(f"  {C.BOLD}REAL-TIME DETECTION{C.RESET}")
    print(f"    Hashrate 60s  : {C.GREEN}{detector.format_hashrate(detector.hashrate_60s)}{C.RESET}")
    print(f"    Hashrate 10s  : {C.GREEN_D}{detector.format_hashrate(detector.hashrate_10s)}{C.RESET}")
    print(f"    Hashrate 15m  : {C.GREEN_D}{detector.format_hashrate(detector.hashrate_15m)}{C.RESET}")
    print(f"    Hashrate Max  : {C.ORANGE}{detector.format_hashrate(detector.hashrate_max)}{C.RESET}")
    print(f"    Accepted      : {C.GREEN}{detector.accepted}{C.RESET}")
    print(f"    Rejected      : {C.RED}{detector.rejected}{C.RESET}")
    print(f"    Difficulty    : {C.CYAN}{detector.difficulty}{C.RESET}")
    print(f"    Pool Latency  : {C.CYAN}{detector.pool_latency} ms{C.RESET}")
    print(f"    Avg Share Int : {C.YELLOW}{detector.avg_share_interval:.0f} s{C.RESET}" if detector.avg_share_interval > 0 else f"    Avg Share Int : {C.YELLOW}-{C.RESET}")
    print(f"    Jobs Received : {C.CYAN}{detector.job_count}{C.RESET}")
    print(f"    Connection    : {C.GREEN if detector.connection_status == 'CONNECTED' else C.RED}{detector.connection_status}{C.RESET}")
    print(f"    First Share   : {C.GREEN + 'YES' if detector.first_share_received else C.RED + 'NO'}{C.RESET}")
    print(f"\n  {C.BOLD}CONFIG{C.RESET}")
    print(f"    Algo   : {C.YELLOW}{miner.algo}{C.RESET}")
    print(f"    Region : {C.YELLOW}{miner.region.upper()}{C.RESET}")
    print(f"    Mode   : {C.CYAN}{'CPU/XMRig' if miner.mode == 'cpu' else 'GPU/lolMiner'}{C.RESET}")
    print(f"    Wallet : {C.CYAN}{WALLET}{C.RESET}")
    print(f"    Worker : {C.CYAN}{WORKER}{C.RESET}")

def cmd_start(args):
    algo = args.algo.upper() if args.algo else miner.algo
    region = args.region.lower() if args.region else miner.region
    print_log(f"START MINING — Algo: {algo} | Region: {region.upper()}", "ok")
    ok = miner.start(algo, region, lambda m: print_log(m, "info"))
    if ok:
        print_log("[OK] Mining berjalan! Tekan Ctrl+C untuk stop.", "ok")
        print_log("BTC akan otomatis ditambahkan ke saldo (disimpan permanen)", "gold")
        # Live monitoring loop
        try:
            while miner.is_running():
                time.sleep(2)
                miner.parse_log()
                # Update line (no screen clear, just print new stats)
                print(f"\r{C.GREEN}Hashrate: {detector.format_hashrate(detector.hashrate_60s)}"
                      f" | Accepted: {detector.accepted}"
                      f" | Rejected: {detector.rejected}"
                      f" | BTC: {btc_wallet.get_balance():.10f}"
                      f" | Uptime: {miner.uptime()}{C.RESET}", end="")
        except KeyboardInterrupt:
            print()
            print_log("[*] Stop mining...", "warn")
            miner.stop()
            print_log("[OK] Miner dihentikan, session tersimpan", "ok")
            print_log(f"Saldo BTC: {btc_wallet.get_balance():.10f} BTC (persistent)", "gold")
    else:
        print_log("[X] Gagal start mining", "err")

def cmd_stop(args):
    print_log("[*] Stop mining...", "warn")
    miner.stop()
    print_log("[OK] Miner dihentikan", "ok")
    print_log(f"[OK] Saldo BTC: {btc_wallet.get_balance():.10f} BTC (persistent)", "gold")

def cmd_status(args):
    miner.parse_log()
    print_banner()
    print_stats()

def cmd_wallet(args):
    print_banner()
    w = btc_wallet.wallet
    bal = w["balance_btc"]
    p = get_btc_price()
    usd = bal * p.get("usd", 0)
    idr = bal * p.get("idr", 0)
    lvl = booster.get_current_level()
    nxt = booster.get_next_level()

    print(f"  {C.GOLD}{C.BOLD}>> BTC WALLET (PERSISTENT){C.RESET}")
    print(f"  {'─' * 50}")
    print(f"  {'Balance':<22}: {C.GOLD}{C.BOLD}{bal:.10f} BTC{C.RESET}")
    print(f"  {'USD Value':<22}: {C.GREEN}${usd:,.4f}{C.RESET}")
    print(f"  {'IDR Value':<22}: {C.GREEN}Rp {idr:,.0f}{C.RESET}")
    print(f"  {'Total Earned':<22}: {C.YELLOW}{w['total_earned_btc']:.10f} BTC{C.RESET}")
    print(f"  {'Total Earned USD':<22}: {C.GREEN}${w['total_earned_usd']:,.4f}{C.RESET}")
    print(f"  {'Total Earned IDR':<22}: {C.GREEN}Rp {w['total_earned_idr']:,.0f}{C.RESET}")
    print(f"  {'Total Withdrawn':<22}: {C.RED}{w['total_withdrawn_btc']:.10f} BTC{C.RESET}")
    print(f"  {'Total Shares':<22}: {C.CYAN}{w.get('total_shares',0)}{C.RESET}")
    print(f"  {'Total Mining Time':<22}: {C.YELLOW}{w.get('total_mining_seconds',0)}s{C.RESET}")
    print(f"  {'Sessions Count':<22}: {C.MAGENTA}{w.get('sessions_count',0)}{C.RESET}")
    print(f"  {'Wallet Address':<22}: {C.CYAN}{WALLET}{C.RESET}")
    print(f"  {'Worker':<22}: {C.CYAN}{WORKER}{C.RESET}")
    print(f"\n  {C.MAGENTA}{C.BOLD}>> BTC BOOSTER{C.RESET}")
    print(f"  {'─' * 50}")
    print(f"  {'Level':<22}: {lvl['color']}{C.BOLD}{lvl['name']}{C.RESET}")
    print(f"  {'Multiplier':<22}: {C.YELLOW}x{lvl['mult']:.2f}{C.RESET}")
    print(f"  {'Active':<22}: {C.GREEN if w.get('booster_active', True) else C.RED}{w.get('booster_active', True)}{C.RESET}")
    progress = booster.get_progress()
    bar_len = 30
    filled = int(bar_len * progress / 100)
    bar = f"{C.GREEN}{'█' * filled}{C.GRAY}{'░' * (bar_len - filled)}{C.RESET}"
    print(f"  Progress : [{bar}] {progress:.1f}%")
    if nxt:
        shares = w.get("total_shares", 0)
        print(f"  Next     : {nxt['color']}{nxt['name']}{C.RESET} (x{nxt['mult']:.2f}) "
              f"— {C.CYAN}{shares}/{nxt['req_shares']}{C.RESET} shares")
    else:
        print(f"  {C.GOLD}>> MAX LEVEL REACHED! <<{C.RESET}")
    print(f"\n  DB Path : {WALLET_DB}")

def cmd_booster(args):
    print_banner()
    w = btc_wallet.wallet
    shares = w.get("total_shares", 0)
    lvl = booster.get_current_level()
    print(f"  {C.MAGENTA}{C.BOLD}>> BTC BOOSTER LEVELS{C.RESET}")
    print(f"  {'─' * 60}")
    print(f"  {'LEVEL':<16}{'MULTIPLIER':<14}{'REQ SHARES':<14}{'STATUS':<10}")
    print(f"  {'─' * 60}")
    for l in booster.levels:
        unlocked = shares >= l["req_shares"]
        marker = f"{C.GREEN}[OK]{C.RESET}" if unlocked else f"{C.GRAY}[--]{C.RESET}"
        color = l["color"] if unlocked else C.GRAY
        current = " < CURRENT" if l["name"] == lvl["name"] else ""
        print(f"  {marker} {color}{l['name']:<14}{C.RESET}"
              f"x{l['mult']:<12.2f}"
              f"{l['req_shares']:<14}"
              f"{C.GREEN + 'UNLOCKED' + C.RESET if unlocked else C.GRAY + 'LOCKED' + C.RESET}"
              f"{C.YELLOW}{current}{C.RESET}")
    print(f"\n  Total Shares: {C.CYAN}{shares}{C.RESET}")
    if args.toggle:
        new_state = not w.get("booster_active", True)
        btc_wallet.set_booster(new_state, lvl["mult"])
        print_log(f"Booster {'AKTIF' if new_state else 'NONAKTIF'}", "ok")

def cmd_history(args):
    print_banner()
    s = history.get_stats()
    tt = s["total_time"]
    h, r = divmod(tt, 3600); m, sec = divmod(r, 60)
    print(f"  {C.MAGENTA}{C.BOLD}>> MINING HISTORY{C.RESET}")
    print(f"  {'─' * 70}")
    print(f"  Total Sessions : {C.CYAN}{s['total_sessions']}{C.RESET}")
    print(f"  Total Time     : {C.YELLOW}{h:02d}h {m:02d}m {sec:02d}s{C.RESET}")
    print(f"  Total Accepted : {C.GREEN}{s['total_accepted']}{C.RESET}")
    print(f"  Total Rejected : {C.RED}{s['total_rejected']}{C.RESET}")
    print(f"  Total BTC      : {C.GOLD}{btc_wallet.wallet['total_earned_btc']:.8f}{C.RESET}")
    print(f"  {'─' * 70}")
    if not s["sessions"]:
        print(f"  {C.GRAY}Belum ada session.{C.RESET}")
        return
    print(f"  {'ID':<18}{'DUR':<10}{'ALGO':<20}{'MODE':<10}{'ACC':<6}{'REJ':<6}{'BTC':<14}")
    print(f"  {'─' * 70}")
    for sess in reversed(s["sessions"][-20:]):
        dur = sess.get("duration", 0)
        h2, r2 = divmod(dur, 3600); m2, sec2 = divmod(r2, 60)
        dur_str = f"{h2:02d}:{m2:02d}:{sec2:02d}"
        print(f"  {sess.get('id',''):<18}{dur_str:<10}"
              f"{sess.get('algo',''):<20}{sess.get('mode','').upper():<10}"
              f"{sess.get('accepted',0):<6}{sess.get('rejected',0):<6}"
              f"{sess.get('btc_earned',0):<14.10f}")
    if len(s["sessions"]) > 20:
        print(f"  {C.GRAY}... dan {len(s['sessions']) - 20} session lainnya{C.RESET}")

def cmd_export(args):
    fmt = args.format.lower()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if fmt == "csv":
        path = BASE_DIR / f"pegasus_history_{ts}.csv"
        ok = history.export_csv(path)
        print_log(f"[OK] CSV exported: {path}" if ok else "[X] Gagal export CSV",
                  "ok" if ok else "err")
    elif fmt == "json":
        path = BASE_DIR / f"pegasus_history_{ts}.json"
        ok = history.export_json(path)
        print_log(f"[OK] JSON exported: {path}" if ok else "[X] Gagal export JSON",
                  "ok" if ok else "err")
    else:
        print_log("[X] Format harus 'csv' atau 'json'", "err")

def cmd_clear_history(args):
    confirm = input(f"{C.YELLOW}Yakin hapus SEMUA history? (yes/no): {C.RESET}")
    if confirm.lower() == "yes":
        history.clear()
        print_log("[OK] History dihapus", "ok")
    else:
        print_log("Dibatalkan", "warn")

def cmd_reset_wallet(args):
    confirm = input(f"{C.YELLOW}Yakin RESET saldo BTC? Tidak bisa dikembalikan! (yes/no): {C.RESET}")
    if confirm.lower() == "yes":
        btc_wallet.reset()
        print_log("[OK] Wallet direset", "ok")
    else:
        print_log("Dibatalkan", "warn")

def cmd_algo(args):
    print_banner()
    if args.set:
        miner.algo = args.set.upper()
        print_log(f"[OK] Algo diset: {miner.algo}", "ok")
        return
    print(f"  {C.CYAN}{C.BOLD}>> AVAILABLE ALGORITHMS (NiceHash){C.RESET}")
    print(f"  {'─' * 70}")
    algos = get_nh_algos()
    if not algos:
        print(f"  {C.RED}Gagal ambil data NiceHash API{C.RESET}")
        items = CPU_ALGOS + GPU_ALGOS
        for a in items:
            print(f"    {a}")
        return
    items = sorted(algos.items(), key=lambda x: x[1]["paying"], reverse=True)
    print(f"  {'#':<4}{'ALGORITHM':<28}{'PORT':<8}{'BTC/GH/DAY':<16}{'MODE':<8}")
    print(f"  {'─' * 70}")
    for i, (name, info) in enumerate(items, 1):
        mode = "CPU" if name in [a.upper() for a in CPU_ALGOS] else "GPU"
        print(f"  {i:<4}{name:<28}{info['port']:<8}{info['paying']:<16.8f}{mode:<8}")
    print(f"\n  {C.YELLOW}Current: {miner.algo}{C.RESET}")

def cmd_region(args):
    print_banner()
    if args.set:
        r = args.set.lower()
        if r in REGIONS:
            miner.region = r
            print_log(f"[OK] Region diset: {r.upper()} ({REGIONS[r]})", "ok")
        else:
            print_log(f"[X] Region tidak valid. Pilih: {', '.join(REGIONS)}", "err")
        return
    print(f"  {C.CYAN}{C.BOLD}>> AVAILABLE REGIONS{C.RESET}")
    for k, v in REGIONS.items():
        cur = " < CURRENT" if k == miner.region else ""
        print(f"    {k:<6} - {v}{C.YELLOW}{cur}{C.RESET}")

def cmd_gpu(args):
    print_banner()
    gpus = detect_gpus()
    print(f"  {C.CYAN}{C.BOLD}>> GPU DETECTION{C.RESET}")
    print(f"  {'─' * 60}")
    if not gpus:
        print(f"  {C.YELLOW}Tidak ada GPU dedicated terdeteksi.{C.RESET}")
        print(f"  {C.WHITE}Gunakan algo CPU (RANDOMXMONERO) — XMRig akan mining pakai CPU.{C.RESET}")
        return
    for i, g in enumerate(gpus, 1):
        status = f"{C.GREEN}KOMPATIBEL{C.RESET}" if g["compatible"] else f"{C.RED}TIDAK{C.RESET}"
        print(f"  {i}. {C.WHITE}{g['name']}{C.RESET}")
        print(f"     Vendor: {C.CYAN}{g['vendor']}{C.RESET} | "
              f"VRAM: {C.CYAN}{g['vram']} MB{C.RESET} | Status: {status}")

def cmd_top(args):
    print_banner()
    print(f"  {C.CYAN}{C.BOLD}>> TOP ALGORITHMS (NiceHash){C.RESET}")
    algos = get_nh_algos()
    if not algos:
        print(f"  {C.RED}Gagal ambil data NiceHash API{C.RESET}")
        return
    items = sorted(algos.items(), key=lambda x: x[1]["paying"], reverse=True)[:15]
    print(f"  {'#':<4}{'ALGORITHM':<28}{'PORT':<8}{'BTC/GH/DAY':<16}{'EST BTC/DAY':<14}")
    print(f"  {'─' * 70}")
    for i, (name, info) in enumerate(items, 1):
        est = detector.get_estimated_earnings(info["paying"])
        est_str = f"{est:.8f}" if est > 0 else "-"
        print(f"  {i:<4}{name:<28}{info['port']:<8}{info['paying']:<16.8f}{est_str:<14}")

def cmd_test(args):
    print_log("[*] Test koneksi ke NiceHash...", "info")
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
        print_log(f"[OK] {host}:{port} OK — latency {latency}ms", "ok")
    except Exception as e:
        print_log(f"[X] {host}:{port} -> {e}", "err")

def cmd_install(args):
    print_log("[*] Download XMRig + lolMiner...", "info")
    miner.ensure_xmrig(lambda m: print_log(m, "info"))
    miner.ensure_lolminer(lambda m: print_log(m, "info"))
    print_log("[OK] Selesai download binary", "ok")

def cmd_info(args):
    print_banner()
    gpus = detect_gpus()
    gtxt = gpus[0]["name"] if gpus else "Tidak ada GPU dedicated"
    s = history.get_stats()
    bal = btc_wallet.get_balance()
    lvl = booster.get_current_level()
    try:
        port = get_pool_port(miner.algo)
    except:
        port = 9200

    print(f"  {C.BOLD}{PEGASUS_BRAND} — NICEHASH MINER v19.0{C.RESET}")
    print(f"  {C.CYAN}{PEGASUS_URL}{C.RESET}")
    print(f"  {'─' * 60}")
    print(f"  WALLET : {C.CYAN}{WALLET}{C.RESET}")
    print(f"  WORKER : {C.CYAN}{WORKER}{C.RESET}")
    print()
    print(f"  Algo   : {C.YELLOW}{miner.algo}{C.RESET}")
    print(f"  Region : {C.YELLOW}{miner.region.upper()}{C.RESET}")
    print(f"  Pool   : {C.CYAN}{miner.algo.lower()}.{miner.region}.nicehash.com:{port}{C.RESET}")
    print(f"  Mode   : {C.CYAN}{'CPU/XMRig' if miner.mode == 'cpu' else 'GPU/lolMiner'}{C.RESET}")
    print(f"  GPU    : {C.CYAN}{gtxt}{C.RESET}")
    print(f"  Status : {C.GREEN if miner.is_running() else C.RED}{'RUNNING' if miner.is_running() else 'OFFLINE'}{C.RESET}")
    print(f"  Uptime : {C.YELLOW}{miner.uptime()}{C.RESET}")
    print()
    print(f"  {C.GOLD}>> BTC WALLET{C.RESET}")
    print(f"    Balance        : {C.GOLD}{bal:.10f} BTC{C.RESET}")
    print(f"    Total Earned   : {C.YELLOW}{btc_wallet.wallet['total_earned_btc']:.10f} BTC{C.RESET}")
    print(f"    Total Shares   : {C.CYAN}{btc_wallet.wallet.get('total_shares', 0)}{C.RESET}")
    print(f"    Total Sessions : {C.MAGENTA}{btc_wallet.wallet.get('sessions_count', 0)}{C.RESET}")
    print(f"    Wallet DB      : {WALLET_DB}")
    print()
    print(f"  {C.MAGENTA}>> BOOSTER{C.RESET}")
    print(f"    Level          : {lvl['color']}{lvl['name']}{C.RESET}")
    print(f"    Multiplier     : {C.YELLOW}x{lvl['mult']:.2f}{C.RESET}")
    print(f"    Active         : {btc_wallet.wallet.get('booster_active', True)}")
    print()
    print(f"  {C.CYAN}>> HISTORY{C.RESET}")
    print(f"    Total Sessions : {s['total_sessions']}")
    print(f"    Total Accepted : {s['total_accepted']}")
    print(f"    Total Rejected : {s['total_rejected']}")
    print()
    print(f"  {C.GRAY}>> PATHS{C.RESET}")
    print(f"    Base    : {BASE_DIR}")
    print(f"    Miner   : {MINER_DIR}")
    print(f"    Logs    : {LOGS_DIR}")
    print(f"    History : {HISTORY_DB}")
    print(f"    Wallet  : {WALLET_DB}")
    print()
    print(f"  {C.YELLOW}CARA CEK HASIL:{C.RESET}")
    print(f"  1. Tunggu 5-10 menit setelah share pertama")
    print(f"  2. Buka https://www.nicehash.com/my/miner")
    print(f"  3. Login akun NiceHash Anda")
    print(f"  4. Wallet: {WALLET[:20]}...")

def cmd_menu(args):
    """Interactive menu mode."""
    while True:
        print_banner()
        status_bar()
        print(f"  {C.BOLD}MENU:{C.RESET}")
        print(f"    {C.GREEN}[1]{C.RESET} Start Mining")
        print(f"    {C.RED}[2]{C.RESET} Stop Mining")
        print(f"    {C.CYAN}[3]{C.RESET} Status / Stats")
        print(f"    {C.GOLD}[4]{C.RESET} BTC Wallet")
        print(f"    {C.MAGENTA}[5]{C.RESET} Booster Levels")
        print(f"    {C.MAGENTA}[6]{C.RESET} Mining History")
        print(f"    {C.CYAN}[7]{C.RESET} Choose Algorithm")
        print(f"    {C.CYAN}[8]{C.RESET} Choose Region")
        print(f"    {C.CYAN}[9]{C.RESET} GPU Info")
        print(f"    {C.CYAN}[10]{C.RESET} Top Algorithms")
        print(f"    {C.CYAN}[11]{C.RESET} Test Connection")
        print(f"    {C.CYAN}[12]{C.RESET} Install/Download Binaries")
        print(f"    {C.CYAN}[13]{C.RESET} Export CSV")
        print(f"    {C.CYAN}[14]{C.RESET} Export JSON")
        print(f"    {C.CYAN}[15]{C.RESET} Info")
        print(f"    {C.RED}[0]{C.RESET} Exit")
        try:
            choice = input(f"\n  {C.YELLOW}Pilihan > {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if choice == "1":
            ok = miner.start(miner.algo, miner.region, lambda m: print_log(m, "info"))
            if ok:
                print_log("[OK] Mining berjalan! (Ctrl+C untuk stop)", "ok")
                try:
                    while miner.is_running():
                        time.sleep(2)
                        miner.parse_log()
                        print(f"\r{C.GREEN}Hashrate: {detector.format_hashrate(detector.hashrate_60s)}"
                              f" | Acc: {detector.accepted}"
                              f" | Rej: {detector.rejected}"
                              f" | BTC: {btc_wallet.get_balance():.10f}"
                              f" | Up: {miner.uptime()}{C.RESET}   ", end="")
                except KeyboardInterrupt:
                    print()
                    miner.stop()
                    print_log("[OK] Stopped", "ok")
            input(f"{C.GRAY}Enter untuk lanjut...{C.RESET}")
        elif choice == "2":
            cmd_stop(args); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "3":
            miner.parse_log(); print_stats(); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "4":
            cmd_wallet(args); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "5":
            cmd_booster(args); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "6":
            cmd_history(args); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "7":
            cmd_algo(args)
            a = input(f"{C.YELLOW}Set algo (kosongkan untuk batal) > {C.RESET}").strip()
            if a: miner.algo = a.upper(); print_log(f"Algo: {miner.algo}", "ok")
        elif choice == "8":
            cmd_region(args)
            r = input(f"{C.YELLOW}Set region (eu/usa/hk/jp/in/br) > {C.RESET}").strip().lower()
            if r in REGIONS: miner.region = r; print_log(f"Region: {r}", "ok")
        elif choice == "9":
            cmd_gpu(args); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "10":
            cmd_top(args); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "11":
            cmd_test(args); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "12":
            cmd_install(args); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "13":
            cmd_export(argparse.Namespace(format="csv")); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "14":
            cmd_export(argparse.Namespace(format="json")); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "15":
            cmd_info(args); input(f"{C.GRAY}Enter...{C.RESET}")
        elif choice == "0":
            break

# ══════════════════════════════════════════════════════════════════
#  MAIN — ARGPARSE
# ══════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(
        description=f"{PEGASUS_BRAND} NiceHash Miner v19.0 — CLI Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Commands:
  start       Start mining (live monitoring, Ctrl+C to stop)
  stop        Stop mining
  status      Show live status
  wallet      Show BTC wallet (persistent balance)
  booster     Show booster levels
  history     Show mining history
  algo        List/set algorithm
  region      List/set region
  gpu         Detect GPUs
  top         Top algorithms
  test        Test pool connection
  install     Download miner binaries
  export      Export history (csv/json)
  info        Show full info
  menu        Interactive menu
  clear-history  Clear history
  reset-wallet   Reset BTC wallet
""")

    p.add_argument("command", nargs="?", default="menu", help="Command to run")
    p.add_argument("--algo", "-a", help="Algorithm")
    p.add_argument("--region", "-r", help="Region")
    p.add_argument("--set", "-s", help="Set value (for algo/region)")
    p.add_argument("--format", "-f", default="csv", help="Export format (csv/json)")
    p.add_argument("--toggle", "-t", action="store_true", help="Toggle booster")
    p.add_argument("--no-color", action="store_true", help="Disable colors")

    args = p.parse_args()
    if args.no_color:
        C.disable()

    cmds = {
        "start": cmd_start, "stop": cmd_stop, "status": cmd_status,
        "wallet": cmd_wallet, "booster": cmd_booster, "history": cmd_history,
        "algo": cmd_algo, "region": cmd_region, "gpu": cmd_gpu,
        "top": cmd_top, "test": cmd_test, "install": cmd_install,
        "export": cmd_export, "info": cmd_info, "menu": cmd_menu,
        "clear-history": cmd_clear_history, "reset-wallet": cmd_reset_wallet,
    }

    if args.command in cmds:
        try:
            cmds[args.command](args)
        except KeyboardInterrupt:
            print()
            print_log("[*] Interrupted — stopping miner...", "warn")
            if miner.is_running():
                miner.stop()
            btc_wallet._save()
            sys.exit(0)
    else:
        p.print_help()

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
