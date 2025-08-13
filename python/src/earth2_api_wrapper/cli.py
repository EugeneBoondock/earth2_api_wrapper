import json
import os
import typer
from typing import List

from .client import Earth2Client

app = typer.Typer(help="Earth2 API CLI (Python)")


def _client_from_env() -> Earth2Client:
    return Earth2Client(cookie_jar=os.getenv("E2_COOKIE"), csrf_token=os.getenv("E2_CSRF"))


@app.command()
def trending():
    client = _client_from_env()
    res = client.get_trending_places()
    typer.echo(json.dumps(res, indent=2))


@app.command()
def territory_winners():
    client = _client_from_env()
    res = client.get_territory_release_winners()
    typer.echo(json.dumps(res, indent=2))


@app.command()
def property(id: str):  # noqa: A002
    client = _client_from_env()
    res = client.get_property(id)
    typer.echo(json.dumps(res, indent=2))


@app.command()
def market(
    country: str = typer.Option(None),
    tier: str = typer.Option(None),
    tile_class: str = typer.Option(None),
    tile_count: str = typer.Option(None),
    page: int = typer.Option(1),
    items: int = typer.Option(100),
    search: str = typer.Option(""),
    term: list[str] = typer.Option(None),
):
    client = _client_from_env()
    res = client.search_market(
        country=country,
        landfieldTier=tier,
        tileClass=tile_class,
        tileCount=tile_count,
        page=page,
        items=items,
        search=search,
        searchTerms=term or [],
    )
    typer.echo(json.dumps(res, indent=2))


@app.command()
def leaderboard(
    type: str = typer.Option("players"),  # noqa: A002
    sort_by: str = typer.Option("tiles_count"),
    country: str = typer.Option(None),
    continent: str = typer.Option(None),
):
    client = _client_from_env()
    res = client.get_leaderboard(type, sort_by=sort_by, country=country, continent=continent)
    typer.echo(json.dumps(res, indent=2))


@app.command()
def resources(property_id: str):
    client = _client_from_env()
    res = client.get_resources(property_id)
    typer.echo(json.dumps(res, indent=2))


@app.command()
def avatar_sales():
    client = _client_from_env()
    res = client.get_avatar_sales()
    typer.echo(json.dumps(res, indent=2))


@app.command()
def user(user_id: str):
    client = _client_from_env()
    res = client.get_user_info(user_id)
    typer.echo(json.dumps(res, indent=2))


@app.command()
def users(user_ids: List[str] = typer.Argument(..., help="List of user IDs")):
    client = _client_from_env()
    res = client.get_users(user_ids)
    typer.echo(json.dumps(res, indent=2))


@app.command()
def my_favorites():
    client = _client_from_env()
    res = client.get_my_favorites()
    typer.echo(json.dumps(res, indent=2))


if __name__ == "__main__":
    app()


