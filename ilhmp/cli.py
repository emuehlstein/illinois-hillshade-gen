"""
Illinois Hillshade Generator CLI

Usage:
    ilhmp download putnam --dem dtm
    ilhmp hillshade ./putnam_dtm.tif --style dark --exaggeration 3
    ilhmp tile ./putnam_hillshade.tif --zoom 10-16 --format mbtiles
    ilhmp run putnam --dem dtm --style dark --zoom 10-16
    ilhmp view ./output/tiles --port 9999
    ilhmp boundary putnam -o putnam.geojson
"""

import json
import subprocess
import typer
from typing import Optional
from pathlib import Path
from rich.console import Console

from . import download, hillshade, tile, counties, viewer

app = typer.Typer(
    name="ilhmp",
    help="Download Illinois ILHMP elevation data and generate styled hillshade tiles",
    add_completion=False,
)
console = Console()


class _nullctx:
    """No-op context manager used to skip Rich status spinners in JSON mode."""
    def __enter__(self): return self
    def __exit__(self, *_): pass


def reproject_to_4326(input_path: Path, output_path: Path) -> Path:
    """Reproject raster to EPSG:4326 for web mapping."""
    cmd = [
        "gdalwarp",
        "-t_srs", "EPSG:4326",
        "-r", "bilinear",
        "-co", "COMPRESS=DEFLATE",
        "-co", "TILED=YES",
        "-co", "BIGTIFF=IF_SAFER",
        str(input_path),
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdalwarp failed: {result.stderr}")
    return output_path


@app.command()
def run(
    county: str = typer.Argument(..., help="County name (e.g., 'putnam', 'cook')"),
    dem: str = typer.Option("dtm", "--dem", "-d", help="DEM type: dtm or dsm"),
    style: str = typer.Option("dark", "--style", "-s", help="Color style: dark, light, tactical, terrain, gray"),
    exaggeration: float = typer.Option(3.0, "--exaggeration", "-z", help="Vertical exaggeration factor"),
    zoom: str = typer.Option("10-16", "--zoom", help="Zoom range (e.g., '10-16')"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    cache_dir: Optional[Path] = typer.Option(None, "--cache-dir", help="Directory for intermediate files (raw DEM, reprojected TIF, hillshade). Defaults to output dir."),
    source_zip: Optional[Path] = typer.Option(None, "--source-zip", help="Use a local ZIP instead of downloading. Still extracts and converts."),
    source: Optional[Path] = typer.Option(None, "--source", help="Use an existing GeoTIFF directly. Skips download and extraction."),
    pmtiles: bool = typer.Option(False, "--pmtiles", help="Also generate PMTiles output"),
    view: bool = typer.Option(False, "--view", "-v", help="Launch viewer after completion"),
    json_out: bool = typer.Option(False, "--json", help="Output structured JSON instead of Rich text"),
    force_recompute: bool = typer.Option(False, "--force-recompute", help="Bypass the grayscale hillshade cache and recompute from scratch."),
):
    """
    Full pipeline: download → reproject → hillshade → tile for a county.
    """
    county_info = counties.get_county(county)
    if not county_info:
        if json_out:
            print(json.dumps({"error": f"Unknown county: {county}"}))
        else:
            console.print(f"[red]Unknown county: {county}[/red]")
            console.print("Run 'ilhmp counties' to list available counties")
        raise typer.Exit(1)

    if source and not source.exists():
        msg = f"Source file not found: {source}"
        print(json.dumps({"error": msg})) if json_out else console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)

    if source_zip and not source_zip.exists():
        msg = f"Source ZIP not found: {source_zip}"
        print(json.dumps({"error": msg})) if json_out else console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)

    output_dir = output or Path(f"./{county.lower()}-hillshade")
    output_dir.mkdir(parents=True, exist_ok=True)

    intermediates_dir = cache_dir or output_dir
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)

    if not json_out:
        console.print(f"\n[bold]Illinois Hillshade Generator[/bold]")
        console.print(f"   County: {county_info['name']}")
        console.print(f"   DEM: {dem.upper()}")
        console.print(f"   Style: {style}")
        console.print(f"   Zoom: {zoom}")
        console.print(f"   Output: {output_dir}")
        if cache_dir:
            console.print(f"   Cache: {cache_dir}")
        console.print()

    # Step 1: Acquire DEM
    dem_path = intermediates_dir / f"{county.lower()}_{dem.lower()}.tif"
    if source:
        # Use provided GeoTIFF directly — no download or extraction needed
        dem_path = source
        if not json_out:
            console.print(f"[yellow]⏩[/yellow] Using source: {dem_path}")
    elif dem_path.exists():
        if not json_out:
            console.print(f"[yellow]⏩[/yellow] Using cached: {dem_path}")
    elif source_zip:
        if not json_out:
            console.print("[bold]Step 1/5:[/bold] Extracting from local ZIP...")
        download.extract_local_zip(source_zip, dem_path)
        if not json_out:
            console.print(f"[green]✓[/green] Extracted: {dem_path}")
    else:
        if not json_out:
            console.print("[bold]Step 1/5:[/bold] Downloading elevation data...")
        download.download_county(county, dem, dem_path)
        if not json_out:
            console.print(f"[green]✓[/green] Downloaded: {dem_path}")

    # Step 2: Reproject to WGS84
    dem_4326 = intermediates_dir / f"{county.lower()}_{dem.lower()}_4326.tif"
    if not dem_4326.exists():
        if not json_out:
            console.print("[bold]Step 2/5:[/bold] Reprojecting to WGS84...")
        with console.status("[green]Reprojecting...") if not json_out else _nullctx():
            reproject_to_4326(dem_path, dem_4326)
        if not json_out:
            console.print(f"[green]✓[/green] Reprojected: {dem_4326}")
    else:
        if not json_out:
            console.print(f"[yellow]⏩[/yellow] Using cached: {dem_4326}")

    # Step 3: Hillshade
    hs_path = intermediates_dir / f"{county.lower()}_hillshade_{style}_z{exaggeration}.tif"
    if not hs_path.exists() or force_recompute:
        if not json_out:
            console.print(f"[bold]Step 3/5:[/bold] Generating {style} hillshade...")
        with console.status("[green]Generating hillshade...") if not json_out else _nullctx():
            hillshade.generate(
                dem_4326, hs_path,
                style=style,
                exaggeration=exaggeration,
                cache_dir=intermediates_dir,
                force_recompute=force_recompute,
            )
        if not json_out:
            console.print(f"[green]✓[/green] Hillshade: {hs_path}")
    else:
        if not json_out:
            console.print(f"[yellow]⏩[/yellow] Using cached: {hs_path}")

    # Step 4: Generate tiles
    min_zoom, max_zoom = map(int, zoom.split("-"))
    tiles_dir = output_dir / f"tiles_{style}"

    if not json_out:
        console.print(f"[bold]Step 4/5:[/bold] Generating tiles z{min_zoom}-{max_zoom}...")
    with console.status("[green]Generating tiles...") if not json_out else _nullctx():
        tile.generate_tiles_direct(hs_path, tiles_dir, min_zoom, max_zoom)
    if not json_out:
        console.print(f"[green]✓[/green] Tiles: {tiles_dir}")

    # Step 5: Generate viewer
    if not json_out:
        console.print("[bold]Step 5/5:[/bold] Creating viewer...")

    # Try to get/generate boundary
    try:
        from . import boundaries
        boundary_path = output_dir / f"{county.lower()}.geojson"
        if not boundary_path.exists():
            boundaries.get_county_geojson(county, boundary_path)
        geojson_path = f"{county.lower()}.geojson"
    except Exception:
        geojson_path = None

    bounds = county_info.get("bounds", (-89.5, 40.0, -88.0, 42.5))
    center_lon = (bounds[0] + bounds[2]) / 2
    center_lat = (bounds[1] + bounds[3]) / 2

    viewer_path = viewer.generate_viewer_html(
        output_dir / "viewer.html",
        tiles_path=f"tiles_{style}",
        county_name=county_info["name"],
        style=style,
        dem_type=dem.upper(),
        exaggeration=exaggeration,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        center_lat=center_lat,
        center_lon=center_lon,
        tile_format="tiles",
        bounds=bounds,
        geojson_path=geojson_path,
    )
    if not json_out:
        console.print(f"[green]✓[/green] Viewer: {viewer_path}")

    # MBTiles (always generated)
    mbtiles_path = output_dir / f"{county.lower()}-hillshade-{style}.mbtiles"
    if not json_out:
        console.print(f"[dim]Packing MBTiles...[/dim]")
    with console.status("[green]Packing MBTiles...") if not json_out else _nullctx():
        tile.generate_mbtiles_from_dir(tiles_dir, mbtiles_path)
    if not json_out:
        console.print(f"[green]✓[/green] MBTiles: {mbtiles_path}")

    pmtiles_path = None
    if pmtiles:
        pmtiles_path = output_dir / f"{county.lower()}-hillshade-{style}.pmtiles"
        with console.status("[green]Converting to PMTiles...") if not json_out else _nullctx():
            tile.convert_to_pmtiles(mbtiles_path, pmtiles_path)
        if not json_out:
            console.print(f"[green]✓[/green] PMTiles: {pmtiles_path}")

    if json_out:
        result = {
            "county": county_info["name"],
            "dem": dem.upper(),
            "style": style,
            "output_dir": str(output_dir.resolve()),
            "files": {
                "dem": str(dem_path.resolve()),
                "dem_4326": str(dem_4326.resolve()),
                "hillshade": str(hs_path.resolve()),
                "tiles_dir": str(tiles_dir.resolve()),
                "mbtiles": str(mbtiles_path.resolve()),
                "viewer": str(viewer_path.resolve()),
                "geojson": str((output_dir / geojson_path).resolve()) if geojson_path else None,
                "pmtiles": str(pmtiles_path.resolve()) if pmtiles_path else None,
            },
        }
        print(json.dumps(result, indent=2))
    else:
        console.print(f"\n[bold green]Complete![/bold green]")
        console.print(f"   Tiles: {tiles_dir}")
        console.print(f"   Viewer: {viewer_path}")

    if view:
        if not json_out:
            console.print(f"\n[bold]Launching viewer...[/bold]")
        viewer.serve_tiles(tiles_dir, port=9999)


@app.command("download")
def download_cmd(
    county: str = typer.Argument(..., help="County name"),
    dem: str = typer.Option("dtm", "--dem", "-d", help="DEM type: dtm or dsm"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path"),
    source_zip: Optional[Path] = typer.Option(None, "--source-zip", help="Use a local ZIP instead of downloading from ISGS."),
):
    """Download (or extract) elevation data for a county (full 1m resolution)."""
    county_info = counties.get_county(county)
    if not county_info:
        console.print(f"[red]Unknown county: {county}[/red]")
        raise typer.Exit(1)

    output_path = output or Path(f"./{county.lower()}_{dem.lower()}.tif")

    if source_zip:
        if not source_zip.exists():
            console.print(f"[red]Source ZIP not found: {source_zip}[/red]")
            raise typer.Exit(1)
        console.print(f"[bold]Extracting {county_info['name']} {dem.upper()} from local ZIP...[/bold]")
        download.extract_local_zip(source_zip, output_path)
    else:
        console.print(f"[bold]Downloading {county_info['name']} {dem.upper()}...[/bold]")
        download.download_county(county, dem, output_path)
    console.print(f"[green]✓[/green] Saved: {output_path}")


@app.command("hillshade")
def hillshade_cmd(
    input_dem: Path = typer.Argument(..., help="Input DEM GeoTIFF"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path"),
    style: str = typer.Option("dark", "--style", "-s", help="Color style"),
    exaggeration: float = typer.Option(3.0, "--exaggeration", "-z", help="Z factor"),
    azimuth: float = typer.Option(315.0, "--azimuth", help="Sun azimuth"),
    altitude: float = typer.Option(45.0, "--altitude", help="Sun altitude"),
):
    """Generate styled hillshade from a DEM."""
    if not input_dem.exists():
        console.print(f"[red]File not found: {input_dem}[/red]")
        raise typer.Exit(1)
    
    output_path = output or input_dem.with_name(f"{input_dem.stem}_hillshade_{style}.tif")
    
    console.print(f"[bold]Generating {style} hillshade...[/bold]")
    with console.status(f"[green]Processing..."):
        hillshade.generate(
            input_dem, output_path,
            style=style,
            exaggeration=exaggeration,
            azimuth=azimuth,
            altitude=altitude
        )
    
    console.print(f"[green]✓[/green] Saved: {output_path}")


@app.command("tile")
def tile_cmd(
    input_raster: Path = typer.Argument(..., help="Input hillshade GeoTIFF"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path"),
    zoom: str = typer.Option("10-16", "--zoom", help="Zoom range"),
    format: str = typer.Option("mbtiles", "--format", "-f", help="Output format: mbtiles or pmtiles"),
):
    """Generate map tiles from a hillshade raster."""
    if not input_raster.exists():
        console.print(f"[red]File not found: {input_raster}[/red]")
        raise typer.Exit(1)
    
    min_zoom, max_zoom = map(int, zoom.split("-"))
    ext = ".pmtiles" if format == "pmtiles" else ".mbtiles"
    output_path = output or input_raster.with_suffix(ext)
    
    console.print(f"[bold]Generating {format} tiles (z{min_zoom}-{max_zoom})...[/bold]")
    with console.status(f"[green]Processing..."):
        if format == "pmtiles":
            tmp_mbtiles = output_path.with_suffix(".mbtiles.tmp")
            tile.generate_mbtiles(input_raster, tmp_mbtiles, min_zoom, max_zoom)
            tile.convert_to_pmtiles(tmp_mbtiles, output_path)
            tmp_mbtiles.unlink()
        else:
            tile.generate_mbtiles(input_raster, output_path, min_zoom, max_zoom)
    
    console.print(f"[green]✓[/green] Saved: {output_path}")


@app.command("view")
def view_cmd(
    tiles_path: Path = typer.Argument(..., help="Path to tiles directory or .mbtiles file"),
    port: int = typer.Option(9999, "--port", "-p", help="HTTP port"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't open browser"),
):
    """Launch a local viewer for generated tiles."""
    if not tiles_path.exists():
        console.print(f"[red]Not found: {tiles_path}[/red]")
        raise typer.Exit(1)
    
    viewer.serve_tiles(tiles_path, port=port, open_browser=not no_browser)


@app.command("boundary")
def boundary_cmd(
    county: str = typer.Argument(..., help="County name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output GeoJSON path"),
    all_counties: bool = typer.Option(False, "--all", "-a", help="Download all counties"),
    json_out: bool = typer.Option(False, "--json", help="Output structured JSON instead of Rich text"),
):
    """Download county boundary as GeoJSON."""
    from . import boundaries

    if all_counties:
        if not json_out:
            console.print("[bold]Downloading all Illinois county boundaries...[/bold]")
        with console.status("[green]Processing...") if not json_out else _nullctx():
            path = boundaries.get_all_counties_geojson(output)
        if json_out:
            print(json.dumps({"geojson": str(Path(path).resolve())}))
        else:
            console.print(f"[green]✓[/green] Saved: {path}")
    else:
        if not json_out:
            console.print(f"[bold]Downloading {county} county boundary...[/bold]")
        with console.status("[green]Processing...") if not json_out else _nullctx():
            path = boundaries.get_county_geojson(county, output)
        if json_out:
            print(json.dumps({"county": county, "geojson": str(Path(path).resolve())}))
        else:
            console.print(f"[green]✓[/green] Saved: {path}")


@app.command("counties")
def list_counties(
    available: bool = typer.Option(False, "--available", "-a", help="Only show counties with data"),
    json_out: bool = typer.Option(False, "--json", help="Output structured JSON instead of a Rich table"),
):
    """List Illinois counties with ILHMP data availability."""
    all_counties = counties.list_all()
    if available:
        all_counties = [c for c in all_counties if c.get("dtm_url") or c.get("dsm_url")]

    if json_out:
        # Emit full catalog as JSON array
        output = []
        for county in all_counties:
            output.append({
                "id": county["id"],
                "name": county["name"],
                "fips": county["fips"],
                "district": county["district"],
                "year": county.get("year"),
                "dtm_url": county.get("dtm_url"),
                "dsm_url": county.get("dsm_url"),
                "dtm_imageserver_url": county.get("dtm_imageserver_url"),
                "dsm_imageserver_url": county.get("dsm_imageserver_url"),
                "bounds": county.get("bounds"),
            })
        print(json.dumps(output, indent=2))
    else:
        from rich.table import Table

        table = Table(title="Illinois Counties with ILHMP Data")
        table.add_column("County", style="cyan")
        table.add_column("FIPS", style="dim")
        table.add_column("DTM", style="green")
        table.add_column("DSM", style="green")
        table.add_column("Year")

        for county in all_counties:
            table.add_row(
                county["name"],
                county["fips"],
                "✓" if county.get("dtm_url") else "—",
                "✓" if county.get("dsm_url") else "—",
                county.get("year", "—"),
            )

        console.print(table)


if __name__ == "__main__":
    app()
