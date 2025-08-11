from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timezone
import os, socket

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

@app.get("/healthz")
def healthz():
    return {"status":"ok","ts":datetime.now(timezone.utc).isoformat()}

@app.get("/api")
def api_root():
    return {
        "service":"demo-fastapi",
        "host":socket.gethostname(),
        "env":os.environ.get("ENV","dev"),
        "ts":datetime.now(timezone.utc).isoformat()
    }

@app.get("/", response_class=HTMLResponse)
def root_page(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "ts": datetime.now(timezone.utc).isoformat()}
    )
