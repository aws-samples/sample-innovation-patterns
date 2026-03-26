"""Output formatting for CLI commands."""

import click


def info(msg: str) -> None:
    """Print informational message to stderr."""
    click.echo(msg, err=True)


def error(msg: str) -> None:
    """Print error message to stderr."""
    click.echo(f"Error: {msg}", err=True)


def result(msg: str) -> None:
    """Print result to stdout (for machine consumption)."""
    click.echo(msg)


def table(headers: list[str], rows: list[list[str]]) -> None:
    """Print simple aligned table to stdout."""
    if not rows:
        return
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    result(fmt.format(*headers))
    result(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        result(fmt.format(*row))
