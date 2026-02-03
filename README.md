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
Zalo: `0375823061`# AutoCopyVideo
