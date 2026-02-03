"""
============================================================
 TOOL COPY VIDEO TỰ ĐỘNG - CHỐNG TRÙNG HASH
 Author : TRẦN ĐÌNH QUÂN
 Zalo   : 0375823061
============================================================
"""

import os
import sys
import json
import hashlib
import shutil
import time
import signal
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from colorama import init, Fore, Style

# ─── Init colorama ──────────────────────────────────────────────
init(autoreset=True, strip=not sys.platform.startswith("win"))


# ════════════════════════════════════════════════════════════════
#  BASE DIR – hoạt động cả .py lẫn .exe (PyInstaller)
# ════════════════════════════════════════════════════════════════
def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    else:
        return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
load_dotenv(dotenv_path=BASE_DIR / ".env")


# ════════════════════════════════════════════════════════════════
#  LOGGING – console (màu) + file (.log) song song
# ════════════════════════════════════════════════════════════════
_LOG_FILE_RAW = os.getenv("LOG_FILE", "").strip()
LOG_FILE_PATH = Path(_LOG_FILE_RAW) if _LOG_FILE_RAW else BASE_DIR / "video_copy.log"
if not LOG_FILE_PATH.is_absolute():
    LOG_FILE_PATH = BASE_DIR / LOG_FILE_PATH

_file_logger = logging.getLogger("videocopy")
_file_logger.setLevel(logging.DEBUG)
_file_logger.propagate = False

try:
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _fh = logging.FileHandler(str(LOG_FILE_PATH), encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)-5s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    _file_logger.addHandler(_fh)
    _LOG_FILE_OK = True
except Exception:
    _LOG_FILE_OK = False


# ── Log helpers ─────────────────────────────────────────────────
def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _log_both(level_tag: str, color: str, msg: str, log_level: int = logging.INFO):
    print(f"{color}[{_timestamp()}] [{level_tag}] {msg}{Style.RESET_ALL}")
    _file_logger.log(log_level, msg)


def log_info(msg: str):
    _log_both("INFO ", Fore.CYAN, msg, logging.INFO)


def log_success(msg: str):
    _log_both("OK   ", Fore.GREEN, msg, logging.INFO)


def log_warning(msg: str):
    _log_both("SKIP ", Fore.YELLOW, msg, logging.WARNING)


def log_error(msg: str):
    _log_both("ERR  ", Fore.RED, msg, logging.ERROR)


# ════════════════════════════════════════════════════════════════
#  BANNER
# ════════════════════════════════════════════════════════════════
def print_banner():
    w = 54
    border = "─" * w
    print(f"\n{Fore.CYAN}{border}")
    print(f"  TOOL COPY VIDEO TỰ ĐỘNG - CHỐNG TRÙNG HASH")
    print(f"  Author : TRẦN ĐÌNH QUÂN")
    print(f"  Zalo   : 0375823061")
    print(f"{border}{Style.RESET_ALL}\n")


# ════════════════════════════════════════════════════════════════
#  PRESS ANY KEY
# ════════════════════════════════════════════════════════════════
def press_any_key_to_exit():
    print()
    print(f"{Fore.YELLOW}  >>> Nhấn phím bất kỳ để thoát chương trình… <<<{Style.RESET_ALL}")
    try:
        import msvcrt
        msvcrt.getch()
    except ImportError:
        input()


# ════════════════════════════════════════════════════════════════
#  PARSE COPY_PAIRS từ .env
#  Định dạng:  [LABEL] nguồn → đích | [LABEL2] nguồn2 → đích2
#  Label tùy chọn – nếu bỏ sẽ tự sinh Pair_1, Pair_2 …
#  Hỗ trợ cả "→" (unicode) và "->" (ASCII)
# ════════════════════════════════════════════════════════════════
def parse_copy_pairs(raw: str) -> list[dict] | None:
    if not raw or not raw.strip():
        return None

    pairs   = []
    counter = 0
    segments = raw.split("|")

    for seg in segments:
        seg = seg.strip()
        if not seg or seg.startswith("#"):
            continue

        # ── Tách label [LABEL] ──────────────────────────────
        label = None
        body  = seg
        if seg.startswith("["):
            close = seg.find("]")
            if close != -1:
                label = seg[1:close].strip()
                body  = seg[close + 1:].strip()

        # ── Tách nguồn → đích ───────────────────────────────
        if "→" in body:
            parts = body.split("→", maxsplit=1)
        elif "->" in body:
            parts = body.split("->", maxsplit=1)
        else:
            log_error(f"Pair không hợp lệ (thiếu '→' hoặc '->'): '{seg}'")
            continue

        src = parts[0].strip()
        dst = parts[1].strip() if len(parts) > 1 else ""

        if not src or not dst:
            log_error(f"Pair không hợp lệ (nguồn/đích rỗng): '{seg}'")
            continue

        counter += 1
        if not label:
            label = f"Pair_{counter}"

        pairs.append({
            "label":  label,
            "source": Path(src),
            "dest":   Path(dst),
        })

    return pairs if pairs else None


# ════════════════════════════════════════════════════════════════
#  LOAD CONFIG từ .env
# ════════════════════════════════════════════════════════════════
def load_config() -> dict | None:
    # ── Biến bắt buộc (trừ COPY_PAIRS – check riêng) ──────────
    required = ["SCAN_INTERVAL", "VIDEO_EXTENSIONS", "HASH_CHUNK_MB"]
    missing  = [k for k in required if not os.getenv(k)]
    if missing:
        log_error(f"Thiếu biến trong .env: {', '.join(missing)}")
        log_error(f"Đường dẫn .env đang tìm: {BASE_DIR / '.env'}")
        return None

    # ── COPY_PAIRS ──────────────────────────────────────────────
    pairs = parse_copy_pairs(os.getenv("COPY_PAIRS", ""))
    if not pairs:
        log_error("COPY_PAIRS rỗng hoặc không có pair hợp lệ.")
        log_error("Định dạng: COPY_PAIRS=[A1] D:\\src → E:\\dst | [A2] …")
        return None

    # ── SCAN_INTERVAL ───────────────────────────────────────────
    try:
        scan_interval = int(os.getenv("SCAN_INTERVAL"))
        if scan_interval < 1:
            raise ValueError
    except (TypeError, ValueError):
        log_error("SCAN_INTERVAL phải là số nguyên >= 1")
        return None

    # ── VIDEO_EXTENSIONS ────────────────────────────────────────
    raw_ext = os.getenv("VIDEO_EXTENSIONS", "")
    extensions = {
        (e.strip().lower() if e.strip().startswith(".") else f".{e.strip().lower()}")
        for e in raw_ext.split(",") if e.strip()
    }
    if not extensions:
        log_error("VIDEO_EXTENSIONS rỗng hoặc không hợp lệ")
        return None

    # ── HASH_CHUNK_MB ───────────────────────────────────────────
    try:
        chunk_mb = float(os.getenv("HASH_CHUNK_MB"))
        if chunk_mb <= 0:
            raise ValueError
    except (TypeError, ValueError):
        log_error("HASH_CHUNK_MB phải là số dương")
        return None

    # ── HISTORY_FILE (base name – mỗi pair thêm suffix _label) ──
    history_raw  = os.getenv("HISTORY_FILE", "history.json").strip()
    history_base = Path(history_raw)
    if not history_base.is_absolute():
        history_base = BASE_DIR / history_base

    return {
        "pairs":         pairs,
        "scan_interval": scan_interval,
        "extensions":    extensions,
        "chunk_size":    int(chunk_mb * 1024 * 1024),
        "history_base":  history_base,
    }


# ════════════════════════════════════════════════════════════════
#  HISTORY – 1 file per pair:  history_<label>.json
# ════════════════════════════════════════════════════════════════
def get_history_path(history_base: Path, label: str) -> Path:
    """history.json + label 'A1'  →  history_A1.json"""
    return history_base.parent / f"{history_base.stem}_{label}{history_base.suffix}"


def load_history(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {item["hash"]: item for item in data if "hash" in item}
        return {}
    except (json.JSONDecodeError, KeyError, TypeError):
        log_warning(f"File lịch sử '{path.name}' bị hỏng → rebuild.")
        return {}


def save_history(path: Path, history: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError as e:
        log_error(f"Lưu '{path.name}' thất bại: {e}")


# ════════════════════════════════════════════════════════════════
#  FILE STABILITY
# ════════════════════════════════════════════════════════════════
STABILITY_INTERVAL = 1.0
STABILITY_CHECKS   = 2


def is_file_stable(filepath: Path) -> bool:
    try:
        size_prev = filepath.stat().st_size
        for _ in range(STABILITY_CHECKS):
            time.sleep(STABILITY_INTERVAL)
            size_now = filepath.stat().st_size
            if size_now != size_prev:
                return False
            size_prev = size_now
        return True
    except OSError:
        return False


# ════════════════════════════════════════════════════════════════
#  HASH MD5 – chunk-based
# ════════════════════════════════════════════════════════════════
def compute_md5(filepath: Path, chunk_size: int) -> str | None:
    try:
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()
    except OSError as e:
        log_error(f"Lỗi tính hash '{filepath.name}': {e}")
        return None


# ════════════════════════════════════════════════════════════════
#  QUÉT THỤ MỤC
# ════════════════════════════════════════════════════════════════
def scan_videos(source_dir: Path, extensions: set) -> list[Path]:
    try:
        return [
            p for p in source_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in extensions
        ]
    except OSError as e:
        log_error(f"Không quét được '{source_dir}': {e}")
        return []


# ════════════════════════════════════════════════════════════════
#  XỬ LÝ 1 VIDEO
# ════════════════════════════════════════════════════════════════
def process_video(
    video_path: Path,
    dest_dir:   Path,
    chunk_size: int,
    history:    dict,
    label:      str,
) -> bool:
    """Returns True nếu history đã cập nhật."""

    name = video_path.name
    tag  = f"[{label}]"

    try:
        current_size = video_path.stat().st_size
    except OSError as e:
        log_error(f"{tag} Không đọc được '{name}': {e}")
        return False

    # ── Ổn định file ────────────────────────────────────────
    if not is_file_stable(video_path):
        log_warning(f"{tag} '{name}' đang ghi dở → bỏ qua.")
        return False

    # ── Fast-path: size chưa có trong history → file mới chắc chắn ──
    #    Size đã có → vẫn cần tính hash để xác minh nội dung
    size_set = {rec.get("size") for rec in history.values()}
    if current_size not in size_set:
        pass   # chắc chắn mới – tính hash 1 lần bên dưới

    # ── Tính hash ───────────────────────────────────────────
    file_hash = compute_md5(video_path, chunk_size)
    if file_hash is None:
        return False

    # ── Chống trùng ─────────────────────────────────────────
    if file_hash in history:
        existing = history[file_hash]
        log_warning(
            f"{tag} '{name}' trùng với '{existing['filename']}' "
            f"(hash: {file_hash[:12]}…) → bỏ qua."
        )
        return False

    # ── Copy sang đích ─────────────────────────────────────
    dest_path = dest_dir / name
    if dest_path.exists():
        stem, suffix = dest_path.stem, dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        log_info(f"{tag} Tên tồn tại → đổi thành '{dest_path.name}'")

    try:
        shutil.copy2(str(video_path), str(dest_path))
    except OSError as e:
        log_error(f"{tag} Copy '{name}' thất bại: {e}")
        return False

    log_success(f"{tag} '{name}' → '{dest_path.name}' ({_human_size(current_size)})")

    # ── Ghi lịch sử ─────────────────────────────────────────
    history[file_hash] = {
        "hash":      file_hash,
        "filename":  dest_path.name,
        "size":      current_size,
        "timestamp": datetime.now().isoformat(),
        "source":    str(video_path),
    }
    return True


# ════════════════════════════════════════════════════════════════
#  UTILITY
# ════════════════════════════════════════════════════════════════
def _human_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB"):
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} GB"


# ════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ════════════════════════════════════════════════════════════════
_shutdown_flag = False


def _signal_handler(signum, frame):
    global _shutdown_flag
    _shutdown_flag = True


def main():
    global _shutdown_flag

    signal.signal(signal.SIGINT, _signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _signal_handler)

    # ── Banner ──────────────────────────────────────────────
    print_banner()

    if _LOG_FILE_OK:
        log_info(f"Log file: {LOG_FILE_PATH}")
    else:
        log_warning("Không mở được file log → chỉ log console.")

    # ── Config ──────────────────────────────────────────────
    config = load_config()
    if config is None:
        return

    pairs      = config["pairs"]
    extensions = config["extensions"]
    chunk_size = config["chunk_size"]
    interval   = config["scan_interval"]

    # ── Validate + init history cho từng pair ───────────────
    histories  = {}          # { label: dict }
    hist_paths = {}          # { label: Path }
    valid_pairs = []

    log_info(f"Tổng pair đọc được: {len(pairs)}\n")

    for pair in pairs:
        label  = pair["label"]
        source = pair["source"]
        dest   = pair["dest"]

        if not source.is_dir():
            log_error(f"[{label}] Nguồn không tồn tại: {source} → BỏQUA.")
            continue

        dest.mkdir(parents=True, exist_ok=True)

        h_path = get_history_path(config["history_base"], label)
        hist_paths[label] = h_path
        histories[label]  = load_history(h_path)
        valid_pairs.append(pair)

        log_info(f"[{label}] {source}")
        log_info(f"         → {dest}")
        log_info(f"         Lịch sử: {h_path.name} ({len(histories[label])} record)\n")

    if not valid_pairs:
        log_error("Không có pair hợp lệ nào. Kiểm tra COPY_PAIRS trong .env.")
        return

    log_info(f"Extensions : {', '.join(sorted(extensions))}")
    log_info(f"Chunk hash : {_human_size(chunk_size)}")
    log_info(f"Chu kỳ quét: {interval}s")
    log_info("Nhấn Ctrl+C để dừng.\n")

    # ── Main loop ───────────────────────────────────────────
    cycle = 0
    while not _shutdown_flag:
        cycle += 1

        print(f"{Fore.CYAN}{'═' * 54}{Style.RESET_ALL}")
        log_info(f"  Chu kỳ quét #{cycle}  |  {len(valid_pairs)} pair")
        print(f"{Fore.CYAN}{'═' * 54}\n{Style.RESET_ALL}")

        for pair in valid_pairs:
            if _shutdown_flag:
                break

            label   = pair["label"]
            source  = pair["source"]
            dest    = pair["dest"]
            history = histories[label]

            log_info(f"[{label}] Quét: {source}")
            videos = scan_videos(source, extensions)
            log_info(f"[{label}] Tìm thấy {len(videos)} video.")

            dirty = False
            for vid in videos:
                if _shutdown_flag:
                    break
                if process_video(vid, dest, chunk_size, history, label):
                    dirty = True

            if dirty:
                save_history(hist_paths[label], history)
                log_info(f"[{label}] Đã lưu lịch sử.")

            print()   # spacing giữa pair

        # ── Chờ ─────────────────────────────────────────────
        log_info(f"Chờ {interval}s cho chu kỳ tiếp theo…\n")
        deadline = time.time() + interval
        while time.time() < deadline and not _shutdown_flag:
            time.sleep(0.25)

    # ── Shutdown ────────────────────────────────────────────
    print()
    log_info("Đã nhận tín hiệu dừng. Thoát chương trình.")


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(f"Lỗi không lường đoán: {e}")
        _file_logger.exception("Lỗi không lường đoán")
    finally:
        press_any_key_to_exit()