from fastapi import FastAPI

app = FastAPI(title="AI-CMO Minimal")


@app.get("/health")
def health():
    return {"ok": True}
