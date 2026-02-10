"""
* Omnitils CLI Application
* Internal CLI utilities, primarily used for testing and deployment.
* Copyright (c) Hexproof Systems <dev@hexproof.io>
* LICENSE: Mozilla Public License 2.0
"""
import click

from omnitils._cli.testing import testing_group


@click.group(commands={'test': testing_group})
def omnitils_cli():
    pass


# Export the main CLI Object
OmnitilsCLI = omnitils_cli()
__all__ = ['OmnitilsCLI']
