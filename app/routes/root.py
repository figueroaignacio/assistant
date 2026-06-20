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

    POST  /api/v1/chat              → Talk to Nacho's AI brain
    GET   /api/v1/portfolio         → Portfolio data
    GET   /api/v1/portfolio/work    → Work experience
    GET   /api/v1/portfolio/skills  → Skills
    GET   /api/v1/portfolio/bio     → Bio

  ──────────────────────────────────────────────────────────────────────
    STATUS   RUNNING (probably)
    UPTIME   {uptime}
    AUTHOR   Ignacio Figueroa
    LICENSE  Don't pretend you built this.
  ──────────────────────────────────────────────────────────────────────

"""
    return banner
