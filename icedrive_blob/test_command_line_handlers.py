"""Handlers for CLI programs."""

import sys

from .app import BlobApp, ClientApp


def test_client() -> int:
    """Handler for 'ice-calculator-client'."""
    app = ClientApp()
    return app.main(sys.argv)


def test_server() -> int:
    """Handler for 'ice-calculator-server'."""
    app = BlobApp()
    return app.main(sys.argv) 