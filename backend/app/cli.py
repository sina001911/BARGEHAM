"""Command-line interface for BARGEHAM."""
from __future__ import annotations

import asyncio

import click

from app.config import settings
from app.database import async_session_maker, engine, init_db
from app.users.service import init_default_roles


@click.group()
def cli() -> None:
    """BARGEHAM CLI."""


@cli.command("init-db")
def init_db_cmd() -> None:
    """Create all database tables and seed default roles."""
    asyncio.run(_init_db())


async def _init_db() -> None:
    await init_db()
    async with async_session_maker() as session:
        await init_default_roles(session)
    click.echo("Database initialized and default roles seeded.")


@cli.command("version")
def version_cmd() -> None:
    """Print the application version."""
    click.echo(f"{settings.app_name} v{settings.app_version}")


if __name__ == "__main__":
    cli()