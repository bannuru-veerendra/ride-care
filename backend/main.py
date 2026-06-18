from fastapi import FastAPI

app = FastAPI(title="RideCare", description="A personal vehicle companion app for riders", version="1.0.0")

@app.get("/health")
async def health():
    return {"message": "OK"}