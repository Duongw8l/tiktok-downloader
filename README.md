# TikSnap — TikTok Downloader (không watermark)

Trang web local: dán link TikTok → xem thông tin → tải **MP4** hoặc **MP3**.

## Cảnh báo

- Có thể vi phạm Điều khoản dịch vụ TikTok.
- Chỉ dùng **cá nhân**, video bạn tự quay, hoặc có quyền hợp pháp.
- **Không** re-upload / phân phối nội dung người khác.

## Yêu cầu

- Python 3.10+
- **ffmpeg** (cần để ghép video / xuất MP3)
  - Windows: https://ffmpeg.org — giải nén và thêm vào PATH
  - Kiểm tra: `ffmpeg -version`

## Cài đặt (Windows)

```powershell
cd tiktok-downloader
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 1) Chạy web (trình duyệt)

```powershell
python app.py
```

Mở: **http://localhost:5000**

### 2) Chạy app Desktop (cửa sổ riêng)

```powershell
python desktop_app.py
```

Hoặc double-click: **`run_desktop.bat`**

Đóng cửa sổ = thoát app.

### 3) Đóng gói thành .exe (tùy chọn)

```powershell
pip install pyinstaller
# hoặc double-click build_exe.bat
```

File ra: `dist\TikSnap.exe`

## Cấu trúc

```
tiktok-downloader/
├── app.py
├── requirements.txt
├── downloads/          # file tạm (tự xóa sau 2 giờ)
└── templates/
    └── index.html
```

## API

- `POST /api/info` — body: `{ "url": "..." }`
- `POST /api/download` — body: `{ "url": "...", "format": "video" | "audio" }`
