"""Run an isolated browser-smoke backend with signal-triggered stack dump."""

from __future__ import annotations

import faulthandler
import os
import signal
import sys
from pathlib import Path

import uvicorn


sys.path.insert(0, os.getcwd())
_dump = Path(os.environ["BROWSER_THREAD_DUMP_PATH"]).open("w", encoding="utf-8")
faulthandler.enable(file=_dump, all_threads=True)
faulthandler.register(signal.SIGUSR1, file=_dump, all_threads=True, chain=False)

uvicorn.run(
    "app.main:app",
    host="127.0.0.1",
    port=int(os.environ["BROWSER_BACKEND_PORT"]),
    log_level="warning",
)
