import os
import logging
from logging.handlers import RotatingFileHandler
from enum import Enum
import importlib

# Safe resolve of log paths from Define with fallbacks
try:
    DefineModule = importlib.import_module("Define")
    _DEF_LOG_DIR = getattr(DefineModule, "log_path", None)
    _DEF_SHARED = getattr(DefineModule, "shared_log_path", None)
except Exception:
    DefineModule = None
    _DEF_LOG_DIR = None
    _DEF_SHARED = None
    _DEF_DISCORD = None

if os.name == "nt":
    _ROOT_DEFAULT = "C\\job\\dim\\fr_bot"
else:
    _ROOT_DEFAULT = "/home/ubuntu/fr_bot"

log_path = _DEF_LOG_DIR or os.path.join(_ROOT_DEFAULT, "logs")
shared_log_path = _DEF_SHARED or os.path.join(log_path, "shared.log")


class LogService(Enum):
    SERVER = "server"
    ADL = "adl"
    ASSET = "asset"
    TUNEL = "tunel"
    TP_SL = "tp_sl"

class LogTarget(Enum):
    SHARED = "shared"
    DISCORD = "discord"
    SERVICE = "service"
    ALL = "all"

_initialized = {}

DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5MB
DEFAULT_BACKUP_COUNT = 3


def _ensure_parent(file_path: str):
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _ensure_dir(dir_path: str):
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)


def _level_from_env() -> int:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level, logging.INFO)


def _discord_level_from_env() -> int:
    # Bắt buộc tối thiểu INFO để không bao giờ ghi DEBUG vào file Discord
    level = os.getenv("DISCORD_LOG_LEVEL", "INFO").upper()
    lvl = getattr(logging, level, logging.INFO)
    return lvl if lvl >= logging.INFO else logging.INFO


class DiscordFilter(logging.Filter):
    """
    Đơn giản hoá log cho Discord:
    - Loại bỏ mọi record dưới INFO.
    - Loại stack/exception để nội dung gọn gàng.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < logging.INFO:
            return False
        record.exc_info = None
        record.stack_info = None
        return True


class TargetFilter(logging.Filter):
    """Chỉ cho phép message có target phù hợp đi vào handler này.
    Nếu target là 'all' hoặc không set, cho phép tất cả handler nhận.
    """
    def __init__(self, allowed_targets: set[str]):
        super().__init__()
        self.allowed_targets = allowed_targets

    def filter(self, record: logging.LogRecord) -> bool:
        target = getattr(record, "target", LogTarget.ALL.value)
        if isinstance(target, Enum):
            target = target.value
        return target == LogTarget.ALL.value or target in self.allowed_targets


def get_logger(service: LogService) -> logging.Logger:
    """
    Trả về logger cho service. Logger này sẽ ghi:
    - shared_log_path (đầy đủ level theo LOG_LEVEL)
    - discord_simple_log_path (đơn giản, chỉ INFO+; có filter Discord + filter theo target) — BỎ QUA với service TUNEL
    - file log riêng của service (syslog.log)
    """
    name = f"frbot.{service.value}"
    if name in _initialized:
        return logging.getLogger(name)

    logger = logging.getLogger(name)
    logger.setLevel(_level_from_env())
    logger.propagate = False  # tránh ghi trùng lên root

    # Formatter chi tiết (cho shared và service)
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Formatter đơn giản (cho Discord)
    simple_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler shared log
    _ensure_parent(shared_log_path)
    shared_handler = RotatingFileHandler(shared_log_path, maxBytes=DEFAULT_MAX_BYTES, backupCount=DEFAULT_BACKUP_COUNT, encoding='utf-8')
    shared_handler.setFormatter(detailed_formatter)
    shared_handler.setLevel(_level_from_env())
    shared_handler.addFilter(TargetFilter({LogTarget.SHARED.value}))
    logger.addHandler(shared_handler)

    # Handler simple dành cho Discord - BỎ QUA với service TUNEL
    if service != LogService.TUNEL:
        _ensure_parent(discord_simple_log_path)
        discord_handler = RotatingFileHandler(discord_simple_log_path, maxBytes=DEFAULT_MAX_BYTES, backupCount=DEFAULT_BACKUP_COUNT, encoding='utf-8')
        discord_handler.setFormatter(simple_formatter)
        discord_handler.setLevel(_discord_level_from_env())
        discord_handler.addFilter(DiscordFilter())
        discord_handler.addFilter(TargetFilter({LogTarget.DISCORD.value}))
        logger.addHandler(discord_handler)

    # Handler theo service -> logs/{service}/syslog.log
    service_dir = os.path.join(log_path, service.value)
    _ensure_dir(service_dir)
    service_file = os.path.join(service_dir, 'syslog.log')
    _ensure_parent(service_file)
    service_handler = RotatingFileHandler(service_file, maxBytes=DEFAULT_MAX_BYTES, backupCount=DEFAULT_BACKUP_COUNT, encoding='utf-8')
    service_handler.setFormatter(detailed_formatter)
    service_handler.setLevel(_level_from_env())
    service_handler.addFilter(TargetFilter({LogTarget.SERVICE.value}))
    logger.addHandler(service_handler)

    _initialized[name] = True
    return logger


# Các helper cho caller; có tham số target để chỉ định log file nhận bản ghi.
# target có thể là LogTarget hoặc string: 'shared' | 'discord' | 'service' | 'all'

def _normalize_target(target):
    if target is None:
        return LogTarget.ALL.value
    if isinstance(target, LogTarget):
        return target.value
    if isinstance(target, str):
        t = target.lower()
        if t in {e.value for e in LogTarget}:
            return t
    # fallback
    return LogTarget.ALL.value


def log_info(service: LogService, message: str, target: LogTarget | str | None = None):
    get_logger(service).info(message, extra={"target": _normalize_target(target)})


def log_warning(service: LogService, message: str, target: LogTarget | str | None = None):
    get_logger(service).warning(message, extra={"target": _normalize_target(target)})


def log_error(service: LogService, message: str, target: LogTarget | str | None = None):
    get_logger(service).error(message, extra={"target": _normalize_target(target)})


def log_debug(service: LogService, message: str, target: LogTarget | str | None = None):
    get_logger(service).debug(message, extra={"target": _normalize_target(target)})