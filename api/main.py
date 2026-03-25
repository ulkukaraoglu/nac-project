from fastapi import FastAPI

app = FastAPI(title="nac-api")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

