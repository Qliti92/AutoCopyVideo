# 🎬 Video Copy Tool - Chống Trùng Hash

Tool tự động copy video từ thư mục nguồn sang thư mục đích, chống trùng nội dung bằng MD5 Hash.

---

## ✨ Tính năng

- Quét thư mục nguồn liên tục theo chu kỳ tự cấu hình
- Chống trùng dựa trên **nội dung file (MD5 Hash)**, không phụ thuộc tên file
- Tính hash theo từng chunk → không tốn RAM dù file lớn
- Bỏ qua file đang được ghi dở (chưa ổn định)
- Log màu sắc trên console + ghi log ra file `.log`
- Toàn bộ cấu hình đọc từ file `.env`

---

## 📁 Cấu trúc Project

```
├── video_copy_tool.py      # Source chính
├── build.spec              # PyInstaller build script
├── .env                    # Cấu hình (chỉnh sửa trước khi chạy)
├── requirements.txt        # Dependencies
└── README.md               # File này
```

---

## ⚙️ Cấu hình `.env`

Mở file `.env` và chỉnh sửa các giá trị:

| Biến                | Mô tả                                          | Ví dụ                        |
|---------------------|-------------------------------------------------|------------------------------|
| `SOURCE_DIR`        | Thư mục nguồn (quét tìm video)                 | `C:\Videos\Source`           |
| `DEST_DIR`          | Thư mục đích (video copy sang)                 | `C:\Videos\Destination`      |
| `SCAN_INTERVAL`     | Chu kỳ quét (giây)                             | `10`                         |
| `HISTORY_FILE`      | File lịch sử copy (JSON)                       | `history.json`               |
| `LOG_FILE`          | File log output                                | `video_copy.log`             |
| `VIDEO_EXTENSIONS`  | Danh sách đuôi video, cách nhau bằng dấu phẩy  | `.mp4,.avi,.mkv,.mov`        |
| `HASH_CHUNK_MB`     | Dung lượng chunk tính hash (MB)                | `8`                          |

---

## 🚀 Chạy từ Source

**Bước 1 — Install dependencies:**

```bash
pip install -r requirements.txt
```

**Bước 2 — Chỉnh sửa `.env`** theo thực tế máy bạn.

**Bước 3 — Run:**

```bash
python video_copy_tool.py
```

Dừng chương trình: nhấn `Ctrl + C`.

---

## 📦 Đóng gói thành `.exe`

**Bước 1 — Install PyInstaller:**

```bash
pip install pyinstaller
```

**Bước 2 — Build** (chạy từ thư mục chứa `build.spec`):

```bash
pyinstaller build.spec
```

**Bước 3 — Thêm icon** (tùy chọn):

Đặt file `icon.ico` cạnh `build.spec`, mở `build.spec` và uncomment dòng:

```python
icon=os.path.join(HERE, 'icon.ico'),
```

Rồi build lại.

**Bước 4 — Deploy:**

Sau khi build, cấu trúc cần có:

```
dist/
 ├── VideoCopyTool.exe
 └── .env                 ← đặt file .env cạnh .exe
```

> ⚠️ `.env` **không được bundle** vào `.exe`. Phải đặt tay cạnh `.exe` sau khi build.

---

## ▶️ Chạy từ file `.exe` (đã có sẵn)

Dành cho người chỉ được share file `.exe`, không cần cài Python.

---

### Lần đầu chạy

**Bước 1 — Tạo thư mục mới**, đặt `.exe` và `.env` vào cùng 1 chỗ:

```
📂 VideoCopyTool\
 ├── VideoCopyTool.exe
 └── .env
```

> ⚠️ `.exe` và `.env` **phải cùng thư mục**. Nếu không cùng thì app sẽ báo thiếu biến cấu hình.

---

**Bước 2 — Chỉnh sửa `.env`** bằng bất kỳ editor nào (Notepad, VS Code…):

Chỉ cần đổi 2 đường dẫn quan trọng nhất:

```env
SOURCE_DIR=C:\đường\dẫn\thư\mục\nguồn
DEST_DIR=C:\đường\dẫn\thư\mục\đích
```

Ví dụ thực:

```env
SOURCE_DIR=D:\Download\Video_mới
DEST_DIR=E:\Kho_Video
```

Các biến còn lại giữ mặc định là được, chỉ đổi nếu cần.

---

**Bước 3 — Double-click `VideoCopyTool.exe`** để chạy. Console sẽ hiện ra:

```
────────────────────────────────────────────────────
  TOOL COPY VIDEO TỰ ĐỘNG - CHỐNG TRÙNG HASH
  Author : TRẦN ĐÌNH QUÂN
  Zalo   : 0375823061
────────────────────────────────────────────────────

[HH:MM:SS] [INFO ] Log file: …\video_copy.log
[HH:MM:SS] [INFO ] Cấu hình đã nạp:
[HH:MM:SS] [INFO ]   Thư mục nguồn   : D:\Download\Video_mới
[HH:MM:SS] [INFO ]   Thư mục đích    : E:\Kho_Video
…
[HH:MM:SS] [INFO ] ═══ Chu kỳ quét #1 ═══
```

Để đó chạy. Chương trình sẽ tự quét và copy video.

---

**Bước 4 — Dừng chương trình:** nhấn `Ctrl + C`, đợi hiện thông báo, rồi nhấn phím bất kỳ để đóng console.

---

### Chỉnh sửa cấu hình sau khi đã chạy

Không cần reinstall hay rebuild gì cả. Chỉ cần:

1. Dừng chương trình (`Ctrl + C`).
2. Mở `.env` bằng Notepad → sửa giá trị cần đổi → `Ctrl + S`.
3. Double-click `.exe` lại.

Chương trình sẽ đọc lại `.env` mới khi khởi động.

---

### Chỉnh sửa từng biến cụ thể

| Muốn làm gì                        | Sửa biến nào         | Ví dụ                                    |
|--------------------------------------|----------------------|------------------------------------------|
| Đổi thư mục nguồn                   | `SOURCE_DIR`         | `SOURCE_DIR=D:\Video_inbox`              |
| Đổi thư mục đích                    | `DEST_DIR`           | `DEST_DIR=E:\Kho_Video`                  |
| Quét nhanh hơn / chậm hơn          | `SCAN_INTERVAL`      | `SCAN_INTERVAL=5` (5 giây)              |
| Thêm/bỏ định dạng video           | `VIDEO_EXTENSIONS`   | `VIDEO_EXTENSIONS=.mp4,.mkv,.avi`        |
| Tắt log ra file                     | `LOG_FILE`           | Xóa giá trị: `LOG_FILE=`                |
| Reset lịch sử copy                  | —                    | Xóa file `history.json` cạnh `.exe`      |

---

### Các file tự sinh ra khi chạy

Sau lần chạy đầu, thư mục sẽ có thêm:

```
📂 VideoCopyTool\
 ├── VideoCopyTool.exe
 ├── .env
 ├── history.json          ← lịch sử copy (tự tạo)
 └── video_copy.log        ← log chi tiết (tự tạo)
```

- `history.json` — chứa danh sách video đã copy. Xóa file này nếu muốn copy lại từ đầu.
- `video_copy.log` — log toàn bộ quá trình, hữu ích để debug.

---

## 📋 Yêu cầu hệ thống

| Thứ gì | Phiên bản |
|--------|-----------|
| Python | 3.10+ |
| OS     | Windows (chính thức hỗ trợ) |

---

## 📌 Lưu ý

- `history.json` và `video_copy.log` tự tạo ở thư mục chứa `.exe` (hoặc `.py`) khi chạy lần đầu.
- Nếu muốn reset lịch sử → xóa file `history.json`.
- File video đang được download/copy dở sẽ bị bỏ qua và xử lý ở chu kỳ quét sau.

---

## 👤 Tác giả

**TRẦN ĐÌNH QUÂN**
Zalo: `0375823061`
