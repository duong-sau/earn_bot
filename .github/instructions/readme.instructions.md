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