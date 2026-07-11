# Đưa TikSnap lên Website (dùng được trên iPhone)

## Desktop app có bị ảnh hưởng không?

**Không.**

| | Desktop `.exe` | Website |
|--|----------------|---------|
| Chạy ở đâu | Máy Windows local | Server trên internet |
| Code dùng chung | Có | Có |
| Ảnh hưởng lẫn nhau | **Không** | **Không** |
| File tải về | `Downloads` trên PC | Tải xuống của iPhone/máy user |

- App trên máy bạn: vẫn dùng `TikSnap.exe` như cũ  
- Bạn bè đã cài `.exe`: **không cần làm gì**, app họ không đổi  
- Website: thêm **một cách dùng** qua link Safari  

---

## Cách deploy (Render — miễn phí)

1. Tạo tài khoản: https://render.com  
2. **New → Web Service**  
3. Kết nối GitHub repo chứa project này (hoặc upload)  
4. Cấu hình:
   - **Build command:** `pip install -r requirements-web.txt`
   - **Start command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 4`
5. Deploy → nhận link dạng `https://tiksnap-xxxx.onrender.com`  
6. Trên iPhone: mở Safari → vào link → dán URL TikTok → tải  
7. (Tuỳ chọn) **Chia sẻ → Thêm vào Màn hình chính**

### Railway.app (tương tự)

```bash
# Cài Railway CLI hoặc dùng web UI
# Start: gunicorn wsgi:app --bind 0.0.0.0:$PORT --timeout 120
```

---

## Chạy web local (thử trước khi deploy)

```powershell
cd tiktok-downloader
.\venv\Scripts\activate
pip install -r requirements-web.txt
# Không set TIKSNAP_DESKTOP → chế độ web
python wsgi.py
```

Mở http://localhost:5000 (giả lập website).

---

## Lưu ý

- Hosting free có thể **ngủ** khi không dùng (mở lại chậm 30–60s).  
- TikTok có thể chặn IP server công cộng → đôi khi tải lỗi.  
- Chỉ dùng cá nhân / có quyền hợp pháp.  
- Desktop app **không** cần server web để chạy.
