"""
* Omnitils CLI Application
* Internal CLI utilities, primarily used for testing and deployment.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
import typer

from omnitils._cli.test import app as app_test


app = typer.Typer(
    name="omnitils"
)
app.add_typer(app_test)
