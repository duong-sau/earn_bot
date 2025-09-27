import os
import sys
from enum import Enum
from Core.Define import convert_exchange_name_to_exchange

print(f"argv: {sys.argv}")

# Xác định root_path động dựa trên vị trí file hiện tại
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

LEGACY_LINUX = "/home/ubuntu/earn_bot"
LEGACY_WIN = "C:\\job\\dim\\earn_bot\\"

if os.path.exists(LEGACY_LINUX):
    root_path = LEGACY_LINUX
elif os.path.exists(LEGACY_WIN):
    root_path = LEGACY_WIN
else:
    raise EnvironmentError("Không tìm thấy đường dẫn root mặc định.")
# Helper chọn file tồn tại đầu tiên

def _first_exists(*candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]

# Chuẩn mới: _settings nằm trực tiếp ở root repo
new_settings_dir = os.path.join(root_path, "_settings")
legacy_settings_dir = os.path.join(root_path, "code", "_settings")
selected_settings_dir = new_settings_dir if os.path.exists(new_settings_dir) else legacy_settings_dir

log_path = os.path.join(root_path, "logs")

discord_config_path = _first_exists(
    os.path.join(selected_settings_dir, "config.json"),
    os.path.join(legacy_settings_dir, "config.json"),
)

shared_log_path = os.path.join(log_path, "shared.log")
discord_simple_log_path = os.path.join(log_path, "discord_simple.log")
