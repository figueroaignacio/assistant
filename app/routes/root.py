import time

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

START_TIME = time.time()


@router.get("/", response_class=PlainTextResponse)
async def root():
    elapsed = int(time.time() - START_TIME)
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        uptime = f"{hours}h {minutes}m {seconds}s"
    elif minutes:
        uptime = f"{minutes}m {seconds}s"
    else:
        uptime = f"{seconds}s"

    banner = f"""

  ███╗   ██╗ █████╗  ██████╗██╗  ██╗ ██████╗      █████╗ ██╗
  ████╗  ██║██╔══██╗██╔════╝██║  ██║██╔═══██╗    ██╔══██╗██║
  ██╔██╗ ██║███████║██║     ███████║██║   ██║    ███████║██║
  ██║╚██╗██║██╔══██║██║     ██╔══██║██║   ██║    ██╔══██║██║
  ██║ ╚████║██║  ██║╚██████╗██║  ██║╚██████╔╝    ██║  ██║██║
  ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝  ╚═╝╚═╝

   █████╗ ███████╗███████╗██╗███████╗████████╗ █████╗ ███╗   ██╗████████╗
  ██╔══██╗██╔════╝██╔════╝██║██╔════╝╚══██╔══╝██╔══██╗████╗  ██║╚══██╔══╝
  ███████║███████╗███████╗██║███████╗   ██║   ███████║██╔██╗ ██║   ██║
  ██╔══██║╚════██║╚════██║██║╚════██║   ██║   ██╔══██║██║╚██╗██║   ██║
  ██║  ██║███████║███████║██║███████║   ██║   ██║  ██║██║ ╚████║   ██║
  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝

  ──────────────────────────────────────────────────────────────────────
    Nacho AI Assistant — backend that actually knows things            v1.0.0
  ──────────────────────────────────────────────────────────────────────

    "Built to answer questions about Nacho.
     Not your questions. His questions about himself."

  ──────────────────────────────────────────────────────────────────────
    ENDPOINTS
  ──────────────────────────────────────────────────────────────────────

    POST  /chat                     → Talk to Nacho's AI brain
    GET   /portfolio/projects       → Projects
    GET   /portfolio/experience     → Work experience
    POST  /portfolio/summarize      → Summarize a project body
    GET   /docs                     → Swagger UI

  ──────────────────────────────────────────────────────────────────────
    STATUS   RUNNING (probably)
    UPTIME   {uptime}
    AUTHOR   Ignacio Figueroa
    LICENSE  Don't pretend you built this.
  ──────────────────────────────────────────────────────────────────────

"""
    return banner
