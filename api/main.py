"""
Backward-compatibility shim.

Compose/uvicorn artık `app.main:app` kullanıyor, ama eski bir referans varsa
bu dosya çalışmaya devam etsin diye gerçek FastAPI instance'ını buradan import ediyoruz.
"""

from app.main import app  

