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
    DOWNLOAD_DIR = _user_downloads_dir()
else:
    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR") or os.path.join(
        tempfile.gettempdir(), "tiksnap_web"
    )

TEMPLATE_DIR = os.path.join(RESOURCE_DIR, "templates")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATE_DIR)

SUPPORTED_HINT = "TikTok, Instagram, Facebook, YouTube (Shorts)"

PLATFORM_RULES = [
    (
        "TikTok",
        [
            r"tiktok\.com",
            r"vm\.tiktok\.com",
            r"vt\.tiktok\.com",
        ],
    ),
    (
        "Instagram",
        [
            r"(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/",
            r"(?:www\.)?instagr\.am/",
        ],
    ),
    (
        "Facebook",
        [
            r"(?:www\.)?facebook\.com/",
            r"(?:www\.)?fb\.watch/",
            r"(?:www\.)?fb\.com/",
            r"m\.facebook\.com/",
        ],
    ),
    (
        "YouTube",
        [
            r"(?:www\.)?youtube\.com/",
            r"(?:www\.)?youtu\.be/",
            r"(?:www\.)?m\.youtube\.com/",
        ],
    ),
]


def detect_platform(url: str):
    url = (url or "").strip()
    for name, patterns in PLATFORM_RULES:
        if any(re.search(p, url, re.I) for p in patterns):
            return name
    return None


def is_supported_url(url: str) -> bool:
    return detect_platform(url) is not None


def format_for_platform(platform: str | None) -> str:
    """Chọn format theo nền tảng (desktop/web không giới hạn 50MB như Telegram)."""
    if platform == "YouTube":
        # Ưu tiên mp4; fallback best. Shorts thường 1 file; video dài có thể cần ffmpeg merge.
        return (
            "best[ext=mp4][height<=1080]/"
            "best[height<=1080][ext=mp4]/"
            "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo[height<=1080]+bestaudio/"
            "best[ext=mp4]/best"
        )
    if platform in ("Instagram", "Facebook"):
        return "best[ext=mp4]/best"
    # TikTok + mặc định
    return "best[ext=mp4]/best"


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


def sanitize_filename(name, default="video"):
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


def friendly_error(err: Exception, platform: str | None) -> str:
    msg = str(err)
    low = msg.lower()
    if "login" in low or "private" in low or "cookies" in low or "sign in" in low:
        return (
            f"{platform or 'Nguồn'} yêu cầu đăng nhập / video riêng tư. "
            "Chỉ tải được video công khai."
        )
    if "ffmpeg" in low or "ffprobe" in low:
        return (
            "Cần cài ffmpeg để ghép video/audio (thường gặp YouTube). "
            "Tải https://ffmpeg.org và thêm vào PATH."
        )
    if "unsupported url" in low:
        return f"Link không hỗ trợ. Hỗ trợ: {SUPPORTED_HINT}."
    return msg


@app.route("/")
def index():
    return render_template("index.html", is_desktop=IS_DESKTOP)


@app.route("/api/health")
def health():
    return jsonify(
        {
            "ok": True,
            "mode": "desktop" if IS_DESKTOP else "web",
            "platforms": ["TikTok", "Instagram", "Facebook", "YouTube"],
        }
    )


@app.route("/api/info", methods=["POST"])
def get_video_info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": f"Vui lòng dán link ({SUPPORTED_HINT})"}), 400

    platform = detect_platform(url)
    if not platform:
        return jsonify(
            {"error": f"Link không hợp lệ. Hỗ trợ: {SUPPORTED_HINT}"}
        ), 400

    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "noplaylist": True,
            "playlistend": 1,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if info.get("_type") == "playlist" and info.get("entries"):
            info = info["entries"][0] or info

        return jsonify(
            {
                "success": True,
                "title": info.get("title") or "Không có tiêu đề",
                "uploader": (
                    info.get("uploader")
                    or info.get("channel")
                    or info.get("creator")
                    or "Unknown"
                ),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "platform": platform,
                "download_folder": DOWNLOAD_DIR if IS_DESKTOP else None,
                "mode": "desktop" if IS_DESKTOP else "web",
            }
        )
    except Exception as e:
        return jsonify(
            {"error": f"Lỗi khi lấy thông tin: {friendly_error(e, platform)}"}
        ), 500


@app.route("/api/download", methods=["POST"])
def download_video():
    clean_old_files()
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": f"Vui lòng dán link ({SUPPORTED_HINT})"}), 400

    platform = detect_platform(url)
    if not platform:
        return jsonify(
            {"error": f"Link không hợp lệ. Hỗ trợ: {SUPPORTED_HINT}"}
        ), 400

    unique_id = str(uuid.uuid4())[:8]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outtmpl = os.path.join(
        DOWNLOAD_DIR, f"{FILE_PREFIX}{stamp}_{unique_id}_%(title).60B.%(ext)s"
    )

    try:
        ydl_opts = {
            "format": format_for_platform(platform),
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "playlistend": 1,
            "retries": 3,
        }
        prefer_exts = [".mp4", ".webm", ".mkv"]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            prepared = ydl.prepare_filename(info)

        if info.get("_type") == "playlist" and info.get("entries"):
            info = info["entries"][0] or info

        filename = resolve_final_path(info, prepared, unique_id, prefer_exts)

        if not filename or not os.path.isfile(filename):
            return jsonify({"error": "Không tìm thấy file sau khi tải"}), 500

        title = sanitize_filename(info.get("title") or "video")
        ext = os.path.splitext(filename)[1].lower() or ".mp4"
        final_name = f"{FILE_PREFIX}{platform}_{title}_{unique_id}{ext}"
        final_path = os.path.join(DOWNLOAD_DIR, final_name)

        if os.path.abspath(filename) != os.path.abspath(final_path):
            if os.path.isfile(final_path):
                final_name = f"{FILE_PREFIX}{platform}_{title}_{stamp}_{unique_id}{ext}"
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
        mime = "video/mp4" if ext == ".mp4" else "application/octet-stream"

        if IS_DESKTOP:
            return jsonify(
                {
                    "success": True,
                    "filename": os.path.basename(filename),
                    "path": filename,
                    "folder": DOWNLOAD_DIR,
                    "format": "MP4",
                    "platform": platform,
                    "mode": "desktop",
                    "message": f"Đã lưu vào Downloads: {os.path.basename(filename)}",
                }
            )

        return send_file(
            filename,
            as_attachment=True,
            download_name=safe_name,
            mimetype=mime,
        )

    except Exception as e:
        return jsonify(
            {"error": f"Lỗi tải xuống: {friendly_error(e, platform)}"}
        ), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    mode = "desktop" if IS_DESKTOP else "web"
    print(f"TikSnap ({mode}) http://0.0.0.0:{port}")
    print(f"Platforms: {SUPPORTED_HINT}")
    if IS_DESKTOP:
        print(f"File tải: {DOWNLOAD_DIR}")
    app.run(
        debug=not IS_DESKTOP and os.environ.get("FLASK_DEBUG") == "1",
        host="0.0.0.0",
        port=port,
    )
