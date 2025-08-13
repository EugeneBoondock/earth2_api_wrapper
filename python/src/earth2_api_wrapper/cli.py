import json
import os
import typer
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text
from tabulate import tabulate

from .client import Earth2Client

app = typer.Typer(help="Earth2 API CLI (Python)")
console = Console()


def _client_from_env() -> Earth2Client:
    return Earth2Client(cookie_jar=os.getenv("E2_COOKIE"), csrf_token=os.getenv("E2_CSRF"))


def format_price(price: float) -> str:
    return f"${price:,.2f}"


def format_number(num: int) -> str:
    return f"{num:,}"


def log_success(message: str) -> None:
    console.print(f"✓ {message}", style="green")


def log_error(message: str) -> None:
    console.print(f"✗ {message}", style="red")


def log_info(message: str) -> None:
    console.print(f"ℹ {message}", style="blue")


@app.command()
def login(
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Email address"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="Password", hide_input=True)
):
    """Authenticate with Earth2 using Kinde OAuth flow"""
    client = Earth2Client()
    
    email = email or os.getenv("E2_EMAIL")
    password = password or os.getenv("E2_PASSWORD")
    
    if not email or not password:
        log_error("Email and password are required. Use --email and --password or set E2_EMAIL and E2_PASSWORD environment variables.")
        raise typer.Exit(1)
    
    log_info("Starting Earth2 Kinde OAuth authentication flow...")
    log_info("This may take a moment as we navigate through multiple redirects...")
    
    result = client.authenticate(email, password)
    
    if result["success"]:
        log_success(result["message"])
        log_info("Session cookies have been stored for this session.")
        log_info('You can now use authenticated endpoints like "e2 my-favorites"')
        
        # Test the session
        log_info("Testing session validity...")
        session_check = client.check_session_validity()
        if session_check["isValid"]:
            log_success("Session is valid and ready to use!")
        else:
            log_error("Session validation failed. You may need to try again.")
    else:
        log_error(result["message"])
        log_error("OAuth authentication failed. Please check your credentials and try again.")
        raise typer.Exit(1)


@app.command()
def check_session():
    """Check if current session is still valid"""
    client = _client_from_env()
    
    if not client.cookie_jar:
        log_error('No session found. Please run "e2 login" first.')
        raise typer.Exit(1)
    
    log_info("Checking session validity...")
    result = client.check_session_validity()
    
    if result["isValid"]:
        log_success("Session is valid!")
    else:
        log_error("Session is invalid or expired.")
        if result["needsReauth"]:
            log_info('Please run "e2 login" to re-authenticate.')
        raise typer.Exit(1)


@app.command()
def trending(json_output: bool = typer.Option(False, "--json", help="Output raw JSON")):
    """Get trending places"""
    client = _client_from_env()
    res = client.get_trending_places()
    
    if json_output:
        typer.echo(json.dumps(res, indent=2))
        return
    
    console.print("\n🌍 [bold blue]Trending Places[/bold blue]\n")
    
    if not res["data"]:
        log_info("No trending places found")
        return
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Place")
    table.add_column("Country")
    table.add_column("Tier")
    table.add_column("Tiles Sold")
    table.add_column("Tile Price")
    table.add_column("Days")
    
    for place in res["data"]:
        table.add_row(
            place.get("placeName") or "N/A",
            place.get("country") or "N/A",
            f"T{place['tier']}" if place.get("tier") else "N/A",
            format_number(place["tilesSold"]) if place.get("tilesSold") else "N/A",
            format_price(place["tilePrice"]) if place.get("tilePrice") else "N/A",
            format_number(place["timeframeDays"]) if place.get("timeframeDays") else "N/A"
        )
    
    console.print(table)


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
    term: List[str] = typer.Option(None),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Search marketplace"""
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
    
    if json_output:
        typer.echo(json.dumps(res, indent=2))
        return
    
    console.print("\n🏪 [bold blue]Marketplace Search Results[/bold blue]\n")
    log_info(f"Found {format_number(res['count'])} total properties")
    
    if not res["items"]:
        log_info("No properties match your search criteria")
        return
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Description", max_width=30)
    table.add_column("Location", max_width=25)
    table.add_column("Country")
    table.add_column("Tier")
    table.add_column("Tiles")
    table.add_column("Total Price")
    table.add_column("Price/Tile")
    
    for item in res["items"][:20]:  # Show first 20
        description = (item.get("description") or "N/A")
        if len(description) > 30:
            description = description[:27] + "..."
            
        location = (item.get("location") or "N/A")
        if len(location) > 25:
            location = location[:22] + "..."
        
        table.add_row(
            description,
            location,
            item.get("country") or "N/A",
            f"T{item['tier']}" if item.get("tier") else "N/A",
            format_number(item["tileCount"]) if item.get("tileCount") else "N/A",
            format_price(item["price"]) if item.get("price") else "N/A",
            format_price(item["ppt"]) if item.get("ppt") else "N/A"
        )
    
    console.print(table)
    
    if len(res["items"]) > 20:
        log_info(f"Showing first 20 of {len(res['items'])} results. Use --json to see all.")


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


