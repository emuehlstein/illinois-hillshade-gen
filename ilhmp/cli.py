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

from . import download, hillshade, tile, counties, viewer, layers as layers_mod
from .hillshade import ShadingMode
from .auto_exag import compute_auto_exaggeration
from . import themes as themes_mod

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
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Named theme preset (overrides style/shading/exaggeration). Run 'ilhmp themes' to list."),
    style: str = typer.Option("dark", "--style", "-s", help="Color style: dark, light, tactical, terrain, gray"),
    exaggeration: str = typer.Option("3.0", "--exaggeration", "-z", help="Vertical exaggeration factor or 'auto'"),
    zoom: str = typer.Option("10-16", "--zoom", help="Zoom range (e.g., '10-16')"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    cache_dir: Optional[Path] = typer.Option(None, "--cache-dir", help="Directory for intermediate files (raw DEM, reprojected TIF, hillshade). Defaults to output dir."),
    source_zip: Optional[Path] = typer.Option(None, "--source-zip", help="Use a local ZIP instead of downloading. Still extracts and converts."),
    source: Optional[Path] = typer.Option(None, "--source", help="Use an existing GeoTIFF directly. Skips download and extraction."),
    pmtiles: bool = typer.Option(False, "--pmtiles", help="Also generate PMTiles output"),
    view: bool = typer.Option(False, "--view", "-v", help="Launch viewer after completion"),
    json_out: bool = typer.Option(False, "--json", help="Output structured JSON instead of Rich text"),
    force_recompute: bool = typer.Option(False, "--force-recompute", help="Bypass the grayscale hillshade cache and recompute from scratch."),
    shading: str = typer.Option("multidirectional", "--shading", help="Shading mode: standard, multidirectional, combined, igor, composite"),
    color_mode: str = typer.Option("ramp", "--color-mode", help="Color mode: tint (legacy) or ramp (default)"),
    composite_weights: Optional[str] = typer.Option(None, "--composite-weights", help="Composite weights as 'multi,igor,combined' (e.g. '0.6,0.3,0.1')"),
    ramp: Optional[Path] = typer.Option(None, "--ramp", help="Custom GDAL color-relief ramp file"),
    legacy: bool = typer.Option(False, "--legacy", help="Restore v1 behavior (standard shading, tint color mode)"),
):
    """
    Full pipeline: download → reproject → hillshade → tile for a county.
    """
    # Apply theme defaults if specified (CLI args still override)
    if theme:
        t = themes_mod.get_theme(theme)
        if not t:
            msg = f"Unknown theme: {theme}. Run 'ilhmp themes' to list."
            print(json.dumps({"error": msg})) if json_out else console.print(f"[red]{msg}[/red]")
            raise typer.Exit(1)
        # Theme provides defaults; explicit CLI flags override
        # Typer doesn't expose which options were explicitly set, so we check
        # against the declared defaults to detect user overrides.
        if style == "dark":  # default → use theme
            style = t.ramp
        if exaggeration == "3.0":  # default → use theme
            exaggeration = t.exaggeration
        if zoom == "10-16":  # default → use theme
            zoom = t.default_zoom
        if shading == "multidirectional":  # default → use theme
            shading = t.shading
        if color_mode == "ramp":  # default → use theme
            color_mode = t.color_mode
        if not composite_weights and t.shading == "composite":
            composite_weights = ",".join(str(w) for w in t.composite_weights)
        if not json_out:
            console.print(f"[dim]Using theme: {t.name} — {t.description}[/dim]\n")

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

    # Parse shading mode
    try:
        shading_mode = ShadingMode(shading)
    except ValueError:
        console.print(f"[red]Unknown shading mode: {shading}[/red]")
        raise typer.Exit(1)

    # Parse composite weights
    parsed_weights = None
    if composite_weights:
        try:
            parts = [float(x) for x in composite_weights.split(",")]
            if len(parts) != 3:
                raise ValueError
            parsed_weights = tuple(parts)
        except ValueError:
            console.print("[red]--composite-weights must be 'multi,igor,combined' (e.g. '0.6,0.3,0.1')[/red]")
            raise typer.Exit(1)

    if not json_out:
        console.print(f"\n[bold]Illinois Hillshade Generator[/bold]")
        console.print(f"   County: {county_info['name']}")
        console.print(f"   DEM: {dem.upper()}")
        console.print(f"   Style: {style}")
        console.print(f"   Shading: {shading_mode.value}")
        console.print(f"   Color mode: {color_mode}")
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

    # Resolve exaggeration (may be 'auto')
    if exaggeration.lower() == "auto":
        exag_float = compute_auto_exaggeration(dem_4326)
        if not json_out:
            console.print(f"[dim]Auto-exaggeration computed: {exag_float:.2f}[/dim]")
    else:
        try:
            exag_float = float(exaggeration)
        except ValueError:
            console.print(f"[red]Invalid exaggeration value: {exaggeration}[/red]")
            raise typer.Exit(1)

    # Step 3: Hillshade
    hs_path = intermediates_dir / f"{county.lower()}_hillshade_{style}_z{exag_float}_{shading_mode.value}.tif"
    if not hs_path.exists() or force_recompute:
        if not json_out:
            console.print(f"[bold]Step 3/5:[/bold] Generating {style} hillshade...")
        with console.status("[green]Generating hillshade...") if not json_out else _nullctx():
            hillshade.generate(
                dem_4326, hs_path,
                style=style,
                exaggeration=exag_float,
                cache_dir=intermediates_dir,
                force_recompute=force_recompute,
                shading_mode=shading_mode,
                color_mode=color_mode,
                composite_weights=parsed_weights,
                ramp_file=ramp,
                legacy=legacy,
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


@app.command("layers")
def layers_cmd(
    county: str = typer.Argument(..., help="County name (e.g., 'putnam', 'cook')"),
    dem: str = typer.Option("dtm", "--dem", "-d", help="DEM type: dtm or dsm"),
    output: str = typer.Option("aspect,slope,roughness,TRI", "--output", "-o", help="Comma-separated layers to generate: aspect,slope,roughness,TRI"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Output directory"),
    cache_dir: Optional[Path] = typer.Option(None, "--cache-dir", help="Cache directory for intermediate files"),
    source: Optional[Path] = typer.Option(None, "--source", help="Use an existing GeoTIFF directly"),
    json_out: bool = typer.Option(False, "--json", help="Output structured JSON"),
):
    """Generate auxiliary terrain layers (aspect, slope, roughness, TRI) for a county."""
    county_info = counties.get_county(county)
    if not county_info:
        if json_out:
            print(json.dumps({"error": f"Unknown county: {county}"}))
        else:
            console.print(f"[red]Unknown county: {county}[/red]")
        raise typer.Exit(1)

    out_dir = output_dir or Path(f"./{county.lower()}-layers")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve DEM path (reuse cached reprojected TIF if available)
    cache = cache_dir or out_dir
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)

    if source:
        dem_path = source
    else:
        dem_path = cache / f"{county.lower()}_{dem.lower()}_4326.tif"
        if not dem_path.exists():
            # Fall back to unrectified DEM
            dem_path = cache / f"{county.lower()}_{dem.lower()}.tif"
        if not dem_path.exists():
            msg = f"DEM not found: {dem_path}. Run 'ilhmp run {county}' first or pass --source."
            if json_out:
                print(json.dumps({"error": msg}))
            else:
                console.print(f"[red]{msg}[/red]")
            raise typer.Exit(1)

    requested = [l.strip() for l in output.split(",")]
    layer_map = {
        "aspect": layers_mod.generate_aspect,
        "slope": layers_mod.generate_slope,
        "roughness": layers_mod.generate_roughness,
        "TRI": layers_mod.generate_tri,
        "tri": layers_mod.generate_tri,
    }

    results = {}
    for layer_name in requested:
        fn = layer_map.get(layer_name)
        if fn is None:
            console.print(f"[yellow]Unknown layer '{layer_name}', skipping[/yellow]")
            continue
        out_file = out_dir / f"{county.lower()}_{layer_name}.tif"
        if not json_out:
            console.print(f"[bold]Generating {layer_name}...[/bold]")
        with console.status(f"[green]{layer_name}...") if not json_out else _nullctx():
            result_path = fn(dem_path, out_file, cache_dir=cache_dir)
        results[layer_name] = str(result_path.resolve())
        if not json_out:
            console.print(f"[green]✓[/green] {layer_name}: {result_path}")

    if json_out:
        print(json.dumps({"county": county_info["name"], "layers": results}, indent=2))
    else:
        console.print(f"\n[bold green]Done![/bold green] Generated: {', '.join(results.keys())}")


@app.command("themes")
def themes_cmd(
    show: Optional[str] = typer.Option(None, "--show", help="Show details for a specific theme"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter themes by tag"),
    json_out: bool = typer.Option(False, "--json", help="Output structured JSON"),
):
    """List available themes or show details for a specific theme."""
    if show:
        t = themes_mod.get_theme(show)
        if not t:
            msg = f"Unknown theme: {show}"
            print(json.dumps({"error": msg})) if json_out else console.print(f"[red]{msg}[/red]")
            raise typer.Exit(1)
        if json_out:
            print(json.dumps(t.to_dict(), indent=2))
        else:
            console.print(f"\n[bold]{t.name}[/bold]")
            console.print(f"   {t.description}")
            console.print(f"\n   [dim]Parameters:[/dim]")
            console.print(f"   Ramp:          {t.ramp}")
            console.print(f"   Color mode:    {t.color_mode}")
            console.print(f"   Shading:       {t.shading}")
            if t.shading == "composite":
                console.print(f"   Weights:       multi={t.composite_weights[0]}, igor={t.composite_weights[1]}, combined={t.composite_weights[2]}")
            console.print(f"   Exaggeration:  {t.exaggeration}")
            console.print(f"   Terrain type:  {t.terrain_type}")
            console.print(f"   Default zoom:  {t.default_zoom}")
            console.print(f"   Tags:          {', '.join(t.tags)}")
            console.print(f"\n   [dim]Equivalent CLI:[/dim]")
            console.print(f"   ilhmp run <county> {' '.join(t.to_cli_args())}")
    else:
        all_themes = themes_mod.list_themes(tag=tag)
        if json_out:
            print(json.dumps([t.to_dict() for t in all_themes], indent=2))
        else:
            console.print(f"\n[bold]Available Themes[/bold] ({len(all_themes)})")
            console.print()
            for t in all_themes:
                tags_str = f" [dim][{', '.join(t.tags)}][/dim]" if t.tags else ""
                console.print(f"   [bold cyan]{t.name:<18}[/bold cyan] {t.description[:70]}{'...' if len(t.description) > 70 else ''}{tags_str}")
            console.print(f"\n   Use [bold]ilhmp themes --show <name>[/bold] for details.")
            console.print(f"   Use [bold]ilhmp run <county> --theme <name>[/bold] to apply.\n")


if __name__ == "__main__":
    app()
