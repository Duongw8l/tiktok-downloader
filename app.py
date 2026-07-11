from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import sys
import uuid
import re
import shutil
import tempfile
from datetime import datetime, timedelta


def _resource_dir():
    """Thư mục resource (templates khi đóng gói PyInstaller)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _user_downloads_dir():
    """Thư mục Downloads của Windows (C:\\Users\\...\\Downloads)."""
    home = os.path.expanduser("~")
    userprofile = os.environ.get("USERPROFILE") or home
    candidates = [
        os.path.join(userprofile, "Downloads"),
        os.path.join(home, "Downloads"),
        os.path.join(home, "Tải xuống"),
        os.path.join(home, "downloads"),
    ]
    for path in candidates:
        if path and os.path.isdir(path):
            return path
    fallback = os.path.join(userprofile, "Downloads")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def _is_desktop_mode():
    """Desktop app (.exe / desktop_app.py) vs website server."""
    if os.environ.get("TIKSNAP_DESKTOP") == "1":
        return True
    if getattr(sys, "frozen", False):
        return True
    return False


IS_DESKTOP = _is_desktop_mode()
RESOURCE_DIR = _resource_dir()
FILE_PREFIX = "TikSnap_"

if IS_DESKTOP:
    # Máy local: lưu vào Downloads của Windows
    DOWNLOAD_DIR = _user_downloads_dir()
else:
    # Website: thư mục tạm trên server (file gửi về trình duyệt user)
    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR") or os.path.join(
        tempfile.gettempdir(), "tiksnap_web"
    )

TEMPLATE_DIR = os.path.join(RESOURCE_DIR, "templates")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATE_DIR)


def is_valid_tiktok_url(url):
    patterns = [
        r"https?://(www\.)?tiktok\.com/@[\w.-]+/video/\d+",
        r"https?://(www\.)?tiktok\.com/t/[\w]+",
        r"https?://vm\.tiktok\.com/[\w]+/?",
        r"https?://vt\.tiktok\.com/[\w]+/?",
        r"https?://m\.tiktok\.com/v/\d+",
        r"https?://(www\.)?tiktok\.com/@[\w.-]+/photo/\d+",
    ]
    return any(re.search(p, url.strip()) for p in patterns)


def clean_old_files():
    """Xóa file TikSnap_* cũ (chỉ file của app)."""
    now = datetime.now()
    max_age = timedelta(hours=24 if IS_DESKTOP else 2)
    try:
        for f in os.listdir(DOWNLOAD_DIR):
            if not f.startswith(FILE_PREFIX):
                continue
            path = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(path):
                if now - datetime.fromtimestamp(os.path.getmtime(path)) > max_age:
                    try:
                        os.remove(path)
                    except OSError:
                        pass
    except OSError:
        pass


def sanitize_filename(name, default="tiktok"):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name or default)
    name = name.strip(" .") or default
    return name[:80]


def find_downloaded_file(unique_id, prefer_ext=None):
    needle = f"_{unique_id}_"
    candidates = []
    for f in os.listdir(DOWNLOAD_DIR):
        if needle in f and os.path.isfile(os.path.join(DOWNLOAD_DIR, f)):
            candidates.append(f)
    if not candidates:
        return None
    if prefer_ext:
        for f in candidates:
            if f.lower().endswith(prefer_ext.lower()):
                return os.path.join(DOWNLOAD_DIR, f)
    for ext in (".mp4", ".webm", ".mkv"):
        for f in candidates:
            if f.lower().endswith(ext):
                return os.path.join(DOWNLOAD_DIR, f)
    return os.path.join(DOWNLOAD_DIR, candidates[0])


def resolve_final_path(info, prepared, unique_id, prefer_exts):
    paths = []
    if prepared:
        paths.append(prepared)
        base, _ = os.path.splitext(prepared)
        for ext in prefer_exts:
            paths.append(base + ext)

    for item in info.get("requested_downloads") or []:
        fp = item.get("filepath")
        if fp:
            paths.append(fp)

    for p in paths:
        if p and os.path.isfile(p):
            return p

    for ext in prefer_exts:
        found = find_downloaded_file(unique_id, ext)
        if found:
            return found
    return find_downloaded_file(unique_id)


@app.route("/")
def index():
    return render_template("index.html", is_desktop=IS_DESKTOP)


@app.route("/api/health")
def health():
    return jsonify({"ok": True, "mode": "desktop" if IS_DESKTOP else "web"})


@app.route("/api/info", methods=["POST"])
def get_video_info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Vui lòng dán link TikTok"}), 400

    if not is_valid_tiktok_url(url):
        return jsonify({"error": "Link TikTok không hợp lệ"}), 400

    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify(
            {
                "success": True,
                "title": info.get("title") or "Không có tiêu đề",
                "uploader": info.get("uploader") or info.get("creator") or "Unknown",
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "download_folder": DOWNLOAD_DIR if IS_DESKTOP else None,
                "mode": "desktop" if IS_DESKTOP else "web",
            }
        )
    except Exception as e:
        return jsonify({"error": f"Lỗi khi lấy thông tin: {str(e)}"}), 500


@app.route("/api/download", methods=["POST"])
def download_video():
    clean_old_files()
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Vui lòng dán link TikTok"}), 400

    if not is_valid_tiktok_url(url):
        return jsonify({"error": "Link không hợp lệ"}), 400

    unique_id = str(uuid.uuid4())[:8]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outtmpl = os.path.join(
        DOWNLOAD_DIR, f"{FILE_PREFIX}{stamp}_{unique_id}_%(title).60B.%(ext)s"
    )

    try:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }
        prefer_exts = [".mp4", ".webm", ".mkv"]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            prepared = ydl.prepare_filename(info)

        filename = resolve_final_path(info, prepared, unique_id, prefer_exts)

        if not filename or not os.path.isfile(filename):
            return jsonify({"error": "Không tìm thấy file sau khi tải"}), 500

        title = sanitize_filename(info.get("title") or "tiktok")
        ext = os.path.splitext(filename)[1].lower() or ".mp4"
        final_name = f"{FILE_PREFIX}{title}_{unique_id}{ext}"
        final_path = os.path.join(DOWNLOAD_DIR, final_name)

        if os.path.abspath(filename) != os.path.abspath(final_path):
            if os.path.isfile(final_path):
                final_name = f"{FILE_PREFIX}{title}_{stamp}_{unique_id}{ext}"
                final_path = os.path.join(DOWNLOAD_DIR, final_name)
            try:
                os.replace(filename, final_path)
            except OSError:
                shutil.copy2(filename, final_path)
                try:
                    os.remove(filename)
                except OSError:
                    pass
            filename = final_path

        safe_name = sanitize_filename(os.path.splitext(final_name)[0]) + ext

        # Desktop: lưu sẵn trên máy → báo đường dẫn
        if IS_DESKTOP:
            return jsonify(
                {
                    "success": True,
                    "filename": os.path.basename(filename),
                    "path": filename,
                    "folder": DOWNLOAD_DIR,
                    "format": "MP4",
                    "mode": "desktop",
                    "message": f"Đã lưu vào Downloads: {os.path.basename(filename)}",
                }
            )

        # Website / iPhone: gửi file về trình duyệt (Safari tải về máy)
        return send_file(
            filename,
            as_attachment=True,
            download_name=safe_name,
            mimetype="video/mp4",
        )

    except Exception as e:
        return jsonify({"error": f"Lỗi tải xuống: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    mode = "desktop" if IS_DESKTOP else "web"
    print(f"TikSnap ({mode}) http://0.0.0.0:{port}")
    if IS_DESKTOP:
        print(f"File tải: {DOWNLOAD_DIR}")
    app.run(debug=not IS_DESKTOP and os.environ.get("FLASK_DEBUG") == "1", host="0.0.0.0", port=port)
