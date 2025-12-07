from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from src.models import Report
from src.logger import logger

app = FastAPI(title="Arr Cleaner Report")

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Global report storage
current_report: Report = None


def set_report(report: Report):
    """Set the current report to display"""
    global current_report
    current_report = report
    logger.info("[green]Report loaded into web server[/green]")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main report page"""
    # Convert Pydantic model to dict for template rendering
    report_dict = current_report.model_dump() if current_report else None
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "report": report_dict}
    )


@app.get("/api/report")
async def get_report():
    """Get report as JSON"""
    if current_report:
        return current_report.model_dump()
    return {"error": "No report available"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}
