"""Entry point: ``python -m app`` starts the server (docs/development.md)."""

import os
import sys

import uvicorn

from app.main import create_app
from app.platform.log import configure_logging
from app.platform.settings import SettingsError, load_settings


def main() -> int:
    try:
        settings = load_settings(os.environ)
    except SettingsError as exc:
        # A console whose code page lacks Turkish letters must not turn this message into a crash.
        sys.stderr.reconfigure(errors="replace")  # type: ignore[union-attr]
        print(f"Uygulama başlatılamadı: {exc}", file=sys.stderr)
        return 2
    configure_logging()
    # One process, one worker (ADR 0002). uvicorn's access log is off: it would log query strings;
    # the request middleware writes the only request log line (docs/security.md). log_config=None
    # keeps uvicorn's own messages on the JSON handler configured above.
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        workers=1,
        access_log=False,
        log_config=None,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
