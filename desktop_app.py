"""
TikSnap Desktop — cửa sổ app bọc giao diện web (Flask + pywebview).
Chạy: python desktop_app.py
"""
import os
import socket
import sys
import threading
import time

# Bật chế độ desktop TRƯỚC khi import app (lưu vào Downloads Windows)
os.environ["TIKSNAP_DESKTOP"] = "1"

from app import app  # noqa: E402


def find_free_port(start=8765, end=8865):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 8765


def wait_for_server(host, port, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def start_flask(port):
    # Tắt reloader để không spawn process phụ trong cửa sổ desktop
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)


def main():
    try:
        import webview
    except ImportError:
        print("Chưa cài pywebview. Chạy: pip install pywebview")
        sys.exit(1)

    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    thread = threading.Thread(target=start_flask, args=(port,), daemon=True)
    thread.start()

    if not wait_for_server("127.0.0.1", port):
        print("Không khởi động được server nội bộ.")
        sys.exit(1)

    # Icon của cửa sổ Windows lấy từ TikSnap.exe (đã embed tiksnap.ico lúc build)
    webview.create_window(
        title="TikSnap — TikTok / Instagram / Facebook / YouTube",
        url=url,
        width=980,
        height=820,
        min_size=(480, 640),
        background_color="#09090b",
    )
    webview.start()


if __name__ == "__main__":
    main()
