from fastapi import FastAPI

app = FastAPI(title="nac-api")


@app.get("/healthz")
def healthz():
    # Local-dev iskelet: iş mantığı yok, sadece servislerin ayağa kalktığını doğrulamak için.
    return {"status": "ok"}

