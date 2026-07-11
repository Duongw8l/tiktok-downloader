"""Entry point cho production (gunicorn / Render / Railway)."""
from app import app

# gunicorn wsgi:app
application = app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
