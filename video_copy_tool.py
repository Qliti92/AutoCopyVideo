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
    """
    - Chạy từ .exe (PyInstaller --onefile): trả về thư mục chứa .exe
    - Chạy từ .py bằng python:            trả về thư mục chứa .py
    """
    if getattr(sys, "frozen", False):
        # PyInstaller đóng gói → sys.executable là đường dẫn .exe
        return Path(sys.executable).resolve().parent
    else:
        return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()

# ─── Load .env từ BASE_DIR (cạnh .exe hoặc .py) ─────────────────
load_dotenv(dotenv_path=BASE_DIR / ".env")


# ════════════════════════════════════════════════════════════════
#  LOGGING – console (màu) + file (.log) song song
# ════════════════════════════════════════════════════════════════
# File log path – đọc từ .env, fallback về BASE_DIR nếu rỗng
_LOG_FILE_RAW = os.getenv("LOG_FILE", "").strip()
LOG_FILE_PATH = Path(_LOG_FILE_RAW) if _LOG_FILE_RAW else BASE_DIR / "video_copy.log"

# Nếu LOG_FILE là relative path → gắn vào BASE_DIR
if not LOG_FILE_PATH.is_absolute():
    LOG_FILE_PATH = BASE_DIR / LOG_FILE_PATH

# Setup file logger (plain text, không màu)
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
    """In console có màu + ghi file log cùng lúc."""
    print(f"{color}[{_timestamp()}] [{level_tag}] {msg}{Style.RESET_ALL}")
    _file_logger.log(log_level, msg)


def log_info(msg: str):
    """Cyan – thông tin hệ thống."""
    _log_both("INFO ", Fore.CYAN, msg, logging.INFO)


def log_success(msg: str):
    """Xanh lá – copy thành công."""
    _log_both("OK   ", Fore.GREEN, msg, logging.INFO)


def log_warning(msg: str):
    """Vàng – bỏ qua (trùng nội dung / ghi dở)."""
    _log_both("SKIP ", Fore.YELLOW, msg, logging.WARNING)


def log_error(msg: str):
    """Đỏ – lỗi."""
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
#  PRESS ANY KEY TO EXIT (Windows)
# ════════════════════════════════════════════════════════════════
def press_any_key_to_exit():
    """Hiển thị 'Nhấn phím bất kỳ để thoát…' và đợi."""
    print()
    print(f"{Fore.YELLOW}  >>> Nhấn phím bất kỳ để thoát chương trình… <<<{Style.RESET_ALL}")
    try:
        # Windows: msvcrt có thể đọc 1 phím không cần Enter
        import msvcrt
        msvcrt.getch()
    except ImportError:
        # Linux / macOS fallback: dùng input()
        input()


# ════════════════════════════════════════════════════════════════
#  CẤU HÌNH – đọc 100% từ .env
# ════════════════════════════════════════════════════════════════
def load_config() -> dict:
    """Load và validate toàn bộ config từ .env.
    Ném SystemExit nếu thiếu biến bắt buộc."""

    required = [
        "SOURCE_DIR",
        "DEST_DIR",
        "SCAN_INTERVAL",
        "HISTORY_FILE",
        "VIDEO_EXTENSIONS",
        "HASH_CHUNK_MB",
    ]

    missing = [k for k in required if not os.getenv(k)]
    if missing:
        log_error(f"Thiếu biến trong file .env: {', '.join(missing)}")
        log_error(f"Đường dẫn .env đang tìm: {BASE_DIR / '.env'}")
        log_error("Vui lòng kiểm tra file .env đặt cạnh chương trình và thử lại.")
        return None  # báo lỗi, không exit ở đây để press_any_key vẫn chạy

    try:
        scan_interval = int(os.getenv("SCAN_INTERVAL"))
        if scan_interval < 1:
            raise ValueError
    except (TypeError, ValueError):
        log_error("SCAN_INTERVAL phải là số nguyên >= 1")
        return None

    try:
        chunk_mb = float(os.getenv("HASH_CHUNK_MB"))
        if chunk_mb <= 0:
            raise ValueError
    except (TypeError, ValueError):
        log_error("HASH_CHUNK_MB phải là số dương")
        return None

    # Parse extension → set {'.mp4', '.avi', …}
    raw_ext = os.getenv("VIDEO_EXTENSIONS", "")
    extensions = {
        (ext.strip().lower() if ext.strip().startswith(".") else f".{ext.strip().lower()}")
        for ext in raw_ext.split(",") if ext.strip()
    }
    if not extensions:
        log_error("VIDEO_EXTENSIONS rỗng hoặc không hợp lệ")
        return None

    # HISTORY_FILE: nếu relative → gắn BASE_DIR
    history_raw = Path(os.getenv("HISTORY_FILE"))
    history_path = history_raw if history_raw.is_absolute() else BASE_DIR / history_raw

    return {
        "source_dir":    Path(os.getenv("SOURCE_DIR")),
        "dest_dir":      Path(os.getenv("DEST_DIR")),
        "scan_interval": scan_interval,
        "history_file":  history_path,
        "extensions":    extensions,
        "chunk_size":    int(chunk_mb * 1024 * 1024),
    }


# ════════════════════════════════════════════════════════════════
#  LỊCH SỬ – JSON
# ════════════════════════════════════════════════════════════════
def load_history(history_path: Path) -> dict:
    if not history_path.is_file():
        return {}
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {item["hash"]: item for item in data if "hash" in item}
        return {}
    except (json.JSONDecodeError, KeyError, TypeError):
        log_warning("File lịch sử bị hỏng → rebuild từ đầu.")
        return {}


def save_history(history_path: Path, history: dict):
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError as e:
        log_error(f"Không thể lưu file lịch sử: {e}")


# ════════════════════════════════════════════════════════════════
#  FILE STABILITY
# ════════════════════════════════════════════════════════════════
STABILITY_INTERVAL = 1.0   # giây
STABILITY_CHECKS   = 2     # lần


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
        log_error(f"Không thể quét thư mục nguồn: {e}")
        return []


# ════════════════════════════════════════════════════════════════
#  XỬ LÝ 1 VIDEO
# ════════════════════════════════════════════════════════════════
def process_video(video_path: Path, config: dict, history: dict) -> bool:
    """Returns True nếu history đã được cập nhật."""
    name = video_path.name

    try:
        current_size = video_path.stat().st_size
    except OSError as e:
        log_error(f"Không đọc được '{name}': {e}")
        return False

    # ── Ổn định file ────────────────────────────────────────
    if not is_file_stable(video_path):
        log_warning(f"'{name}' đang được ghi dở → bỏ qua lần này.")
        return False

    # ── Fast-path: so sánh size trước ──────────────────────
    # Nếu không có record nào trong history có cùng size → file mới chắc chắn
    # → tính hash 1 lần.  Nếu có size trùng → vẫn cần tính hash để xác minh.
    size_exists_in_history = any(
        rec.get("size") == current_size for rec in history.values()
    )
    # (Dù size có trùng hay không, đều cần tính hash vì nội dung có thể khác)

    # ── Tính hash ───────────────────────────────────────────
    file_hash = compute_md5(video_path, config["chunk_size"])
    if file_hash is None:
        return False

    # ── Chống trùng ─────────────────────────────────────────
    if file_hash in history:
        existing = history[file_hash]
        log_warning(
            f"'{name}' trùng nội dung với '{existing['filename']}' "
            f"(hash: {file_hash[:12]}…) → bỏ qua."
        )
        return False

    # ── Copy sang đích ─────────────────────────────────────
    dest_path = config["dest_dir"] / name

    # Tên đã tồn tại nhưng hash khác → đổi tên _1, _2…
    if dest_path.exists():
        stem, suffix = dest_path.stem, dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = config["dest_dir"] / f"{stem}_{counter}{suffix}"
            counter += 1
        log_info(f"Tên đã tồn tại → đổi thành '{dest_path.name}'")

    try:
        shutil.copy2(str(video_path), str(dest_path))
    except OSError as e:
        log_error(f"Copy '{name}' thất bại: {e}")
        return False

    log_success(f"Copy '{name}' → '{dest_path.name}' ({_human_size(current_size)})")

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

    # Bắt Ctrl+C / SIGTERM
    signal.signal(signal.SIGINT, _signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _signal_handler)

    # ── Banner ──────────────────────────────────────────────
    print_banner()

    # ── Báo log file ────────────────────────────────────────
    if _LOG_FILE_OK:
        log_info(f"Log file: {LOG_FILE_PATH}")
    else:
        log_warning("Không thể mở file log → chỉ log console.")

    # ── Load config ─────────────────────────────────────────
    config = load_config()
    if config is None:
        # Lỗi config → dừng nhưng vẫn cho press any key
        return

    # ── Validate thư mục nguồn ──────────────────────────────
    if not config["source_dir"].is_dir():
        log_error(f"Thư mục nguồn không tồn tại: {config['source_dir']}")
        return

    # Tạo thư mục đích nếu chưa có
    config["dest_dir"].mkdir(parents=True, exist_ok=True)

    # ── In cấu hình ─────────────────────────────────────────
    log_info("Cấu hình đã nạp:")
    log_info(f"  Thư mục nguồn   : {config['source_dir']}")
    log_info(f"  Thư mục đích    : {config['dest_dir']}")
    log_info(f"  Chu kỳ quét     : {config['scan_interval']}s")
    log_info(f"  File lịch sử    : {config['history_file']}")
    log_info(f"  Extensions      : {', '.join(sorted(config['extensions']))}")
    log_info(f"  Chunk hash      : {_human_size(config['chunk_size'])}")
    log_info("Nhấn Ctrl+C để dừng.\n")

    # ── Load history ────────────────────────────────────────
    history = load_history(config["history_file"])
    log_info(f"Đã load {len(history)} record lịch sử.\n")

    # ── Main loop ───────────────────────────────────────────
    cycle = 0
    while not _shutdown_flag:
        cycle += 1
        log_info(f"═══ Chu kỳ quét #{cycle} ═══")

        videos = scan_videos(config["source_dir"], config["extensions"])
        log_info(f"Tìm thấy {len(videos)} file video.")

        history_dirty = False
        for vid in videos:
            if _shutdown_flag:
                break
            if process_video(vid, config, history):
                history_dirty = True

        if history_dirty:
            save_history(config["history_file"], history)
            log_info("Đã lưu lịch sử.")

        log_info(f"Chờ {config['scan_interval']}s cho chu kỳ tiếp theo…\n")

        # Sleep có thể interrupt bởi Ctrl+C
        deadline = time.time() + config["scan_interval"]
        while time.time() < deadline and not _shutdown_flag:
            time.sleep(0.25)

    # ── Shutdown ────────────────────────────────────────────
    print()
    log_info("Đã nhận tín hiệu dừng. Thoát chương trình.")


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT – wrap try/except → luôn press any key cuối cùng
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Unexpected crash → vẫn log được
        log_error(f"Lỗi không lường đoán được: {e}")
        _file_logger.exception("Lỗi không lường đoán được")
    finally:
        press_any_key_to_exit()
