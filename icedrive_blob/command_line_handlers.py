"""Handlers for CLI programs."""

import sys

from .app import BlobApp, ClientApp


def client() -> int:
    """Handler for 'ice-calculator-client'."""
    app = ClientApp()
    return app.main(sys.argv)


def server() -> int:
    """Handler for 'ice-calculator-server'."""
    app = BlobApp()
    return app.main(sys.argv)