---
applyTo: '**'
description: 'description'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.
# Tổng quan chức năng
## Core Functionality
- Chương trình sẽ có một vài core microservice chính để xử lý các chức năng cơ bản như:
  - BinanceMicroservice: quản lý position và earn ở binance: Mục tiêu là duy trì position short ở binance đồng thời vay mua spotdđể hedge, đem đi simple earn và vay usdt để tiếp tục
  - OKXMicorservice: quản lý position và earn ở okx: Mục tiêu là duy trì position short ở okx đồng thời mua coin để đi stake và launchpool
  - BitgetMicroservice: quản lý position và earn ở bitget: Mục tiêu là duy trì position short ở bitget đồng thời mua coin để đi stake và launchpool
  - DiscordMicroservice: quản lý việc gửi thông báo qua discord

## Chi tiet chức năng
### BinanceMicroservice
- Ở file coonfig có thông tin:
  - List các coin để trade
  - Số lượng short duy trì mỗi coin
- Dùng định kỳ ( 10 giây ) kiểm tra tài sản ở future và earn, loan, cân bằng để future không bị cháy và earn không bị thanh lý
- Dùng websocket để lắng nghe giá và tự động điều chỉnh position future, nếu có xảy ra ADL thì mua lại vị thế short

### OKXMicroservice
- Ở file coonfig có thông tin:
- List các coin để trade
- Số lượng short duy trì mỗi coin
- Dùng định kỳ ( 10 giây ) kiểm tra tài sản ở future và stake , launchpool, cân bằng để future không bị cháy và stake không bị thanh lý
- Dùng websocket để lắng nghe giá và tự động điều chỉnh position future, nếu có xảy ra ADL thì mua lại vị thế short

### Bitget
- Ở file coonfig có thông tin:
- List các coin để trade
- Số lượng short duy trì mỗi coin
- Dùng định kỳ ( 10 giây ) kiểm tra tài sản ở future và stake
- Dùng websocket để lắng nghe giá và tự động điều chỉnh position future, nếu có xảy ra ADL thì mua lại vị thế short

### DiscordMicroservice
Đọc nội dung mới nhất từ file share_log, nếu có nội dung mới thì gửi lên discord

### server
- chạy flask server để điều khiển
- server quản lý các microservice bật tắt và kiểm tra trạng thái
- các microserivec sẽ chạy trên docker bên trong máy cùng với server
- Có màn hình đ xem tài sản hện tại, report tài sản định kỳ vào 10h, 18h, 2h

---
## Docker hoá microservices
Các microservice Binance / OKX / Bitget đã được docker hoá với cấu trúc:
- `Dockerfile`: build image chuẩn
- `docker-compose.yml`: định nghĩa 3 service `binance`, `okx`, `bitget`
- `run_microservice.py`: entrypoint chung, chọn service qua biến môi trường `SERVICE`
- Thư mục mount:
  - `./_settings` (read-only) chứa `hedge.json` (API keys + strategy)
  - `./logs` chứa file `shared.log` để Discord đọc

### Chuẩn bị cấu hình
File `_settings/hedge.json` (ví dụ tối giản – tự điền key thực tế):
```
{
  "binance": {"api_key": "...", "api_secret": "..."},
  "okx": {"api_key": "...", "api_secret": "...", "passphrase": "..."},
  "bitget": {"api_key": "...", "api_secret": "...", "password": "..."},
  "strategy": {
    "binance": {"enabled": true, "coins": [{"symbol": "SXP/USDT", "perp_symbol": "SXP/USDT:USDT", "short_size": 15000, "step": 10}]},
    "okx": {"enabled": false, "coins": []},
    "bitget": {"enabled": true, "coins": [{"symbol": "BGB/USDT", "perp_symbol": "BGB/USDT:USDT", "short_size": 5000, "step": 10}]}
  }
}
```

### Build & chạy (Linux / WSL)
```
docker compose up -d --build
# Hoặc script:
./rebuild_docker.sh
```

### Build & chạy (Windows CMD / PowerShell)
```
rebuild_docker.bat
```

### Kiểm tra log
```
docker logs -f earn_binance_ms
```
File log chung: `logs/shared.log`

### Thay đổi tham số nhanh khi chạy
Dùng biến môi trường để override limit USDT:
```
docker run --rm -e SERVICE=binance -e FUTURES_BAL_LOWER=80 -e FUTURES_BAL_UPPER=160 earn_bot_image
```
(Trong compose có thể thêm vào mục `environment:`)

### Dừng toàn bộ
```
docker compose down
```

### Nâng cấp code
```
git pull
./rebuild_docker.sh
```

### Ghi chú
- `ccxtpro` dùng websocket => cần license hợp lệ (nếu môi trường sản xuất) hoặc bản free giới hạn.
- Nếu chưa cài `ccxtpro` local, cảnh báo IDE có thể hiện nhưng container sẽ cài theo `requirements.txt`.
- Discord microservice chưa docker hoá ở bước này; có thể thêm riêng nếu cần.
