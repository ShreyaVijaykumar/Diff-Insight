from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from backend.utils.file_reader import read_diff_file
from backend.utils.risk import compute_risk
from backend.llm.analyzer import analyze_diff

app = FastAPI()

# Get the absolute path to the project root (diffinsight/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Mount static folder with absolute path
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend" / "static"), name="static")

# Jinja templates folder with absolute path
templates = Jinja2Templates(directory=BASE_DIR / "frontend")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze(file: UploadFile, mode: str = Form("reviewer")):
    diff_text = read_diff_file(file)
    risk = compute_risk(diff_text)
    report = analyze_diff(diff_text, risk, mode)
    return JSONResponse({"risk": risk.lower(), "analysis": report})
