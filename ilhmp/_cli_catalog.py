"""
Catalog, serve, and publish commands for ilhmp CLI.
Appended to cli.py via import at module load time.
"""
# This file is imported by cli.py at the bottom.
# It registers new commands on the shared `app` typer instance.

import json
import subprocess as _sp
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .cli import app, console
from . import tile


# ── Repo root (parent of ilhmp/) ─────────────────────────────────────────────
_REPO_ROOT = Path(__file__).parent.parent


def _find_tool(name: str) -> str:
    import shutil, os
    found = shutil.which(name)
    if found:
        return found
    hb = f"/opt/homebrew/bin/{name}"
    if os.path.isfile(hb):
        return hb
    return name


# ── catalog ───────────────────────────────────────────────────────────────────

@app.command("catalog")
def catalog_cmd(
    action: str = typer.Argument("list", help="Action: list | add | remove | scan"),
    path: Optional[Path] = typer.Argument(None, help="MBTiles path (add) or dir (scan)"),
    tile_id: Optional[str] = typer.Option(None, "--id", help="Tile ID (remove)"),
    county: Optional[str] = typer.Option(None, "--county", "-c"),
    dem: str = typer.Option("dtm", "--dem"),
    exaggeration: Optional[str] = typer.Option(None, "--exag", "-z"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t"),
    catalog_path: Optional[Path] = typer.Option(None, "--catalog"),
    json_out: bool = typer.Option(False, "--json"),
):
    """Manage the local tile catalog (web/catalog.json)."""
    from . import catalog as cat_mod

    cat_path = catalog_path or cat_mod.DEFAULT_CATALOG

    if action == "list":
        entries = cat_mod.list_entries(cat_path, county=county)
        if json_out:
            print(json.dumps(entries, indent=2))
            return
        if not entries:
            console.print("[dim]No tiles in catalog.[/dim]")
            console.print(f"[dim]Catalog: {cat_path}[/dim]")
            return
        console.print(f"\n[bold]Catalog[/bold] ({len(entries)} tiles) — {cat_path}\n")
        for e in entries:
            z = e.get("zoom") or []
            zoom_s = f"z{z[0]}-{z[1]}" if len(z) == 2 else ""
            size_s = f"{e.get('size_mb', 0):.0f}MB"
            local_s = "✓local" if e.get("local_mbtiles") and Path(e["local_mbtiles"]).exists() else ""
            pm_s = "✓pmtiles" if e.get("pmtiles") else ""
            console.print(
                f"   [cyan]{e['county']:12}[/cyan] [bold]{e.get('theme','?'):22}[/bold]"
                f" {zoom_s:8} {size_s:8} {local_s} {pm_s}"
            )
        console.print()

    elif action == "add":
        if not path:
            console.print("[red]Usage: ilhmp catalog add <file.mbtiles>[/red]")
            raise typer.Exit(1)
        paths = sorted(path.parent.glob(path.name)) if "*" in str(path) else [path]
        for mp in paths:
            if not mp.exists():
                console.print(f"[red]Not found: {mp}[/red]")
                continue
            entry = cat_mod.add_entry(
                mp, cat_path,
                county=county, theme=theme, dem=dem, exaggeration=exaggeration,
            )
            if json_out:
                print(json.dumps(entry, indent=2))
            else:
                z = entry.get("zoom") or ["?", "?"]
                console.print(
                    f"[green]✓[/green] [bold]{entry['id']}[/bold]"
                    f" → {entry['county']} / {entry.get('theme','?')}"
                    f" z{z[0]}-{z[1]} ({entry.get('size_mb',0):.0f}MB)"
                )

    elif action == "remove":
        rid = tile_id or (path.stem if path else None)
        if not rid:
            console.print("[red]Usage: ilhmp catalog remove --id <tile-id>[/red]")
            raise typer.Exit(1)
        if cat_mod.remove_entry(rid, cat_path, county=county):
            console.print(f"[green]✓[/green] Removed: {rid}")
        else:
            console.print(f"[yellow]Not found: {rid}[/yellow]")

    elif action == "scan":
        search = [path or Path(".")]
        unregistered = cat_mod.find_unregistered(search, cat_path)
        if json_out:
            print(json.dumps([str(p) for p in unregistered], indent=2))
            return
        if not unregistered:
            console.print("[green]All mbtiles are registered.[/green]")
            return
        console.print(f"\n[bold]Unregistered mbtiles[/bold] ({len(unregistered)})\n")
        for p in unregistered:
            console.print(f"   {p}")
        console.print("\nRun [bold]ilhmp catalog add <path>[/bold] to register.")

    else:
        console.print(f"[red]Unknown action: {action}. Use: list | add | remove | scan[/red]")
        raise typer.Exit(1)


# ── serve ─────────────────────────────────────────────────────────────────────

@app.command("serve")
def serve_cmd(
    port: int = typer.Option(9999, "--port", "-p"),
    catalog_path: Optional[Path] = typer.Option(None, "--catalog"),
    extra_dirs: Optional[str] = typer.Option(None, "--dirs", help="Extra tile dirs (comma-sep)"),
):
    """
    Serve all locally registered tiles from catalog.json.

    Opens a viewer at http://localhost:<port> with a layer switcher
    for every tile registered via 'ilhmp catalog add'.
    """
    import http.server
    import socketserver
    import threading
    import webbrowser
    from . import catalog as cat_mod

    cat_path = catalog_path or cat_mod.DEFAULT_CATALOG
    catalog = cat_mod.load(cat_path)

    local_entries = []
    serve_roots = set()

    for c_key, c_data in catalog.get("counties", {}).items():
        for t in c_data.get("tiles", []):
            mb = t.get("local_mbtiles")
            if mb and Path(mb).exists():
                local_entries.append({"county": c_key, **t})
                serve_roots.add(str(Path(mb).parent.resolve()))

    if extra_dirs:
        for d in extra_dirs.split(","):
            d = d.strip()
            if Path(d).is_dir():
                serve_roots.add(str(Path(d).resolve()))

    if not local_entries:
        console.print("[yellow]No local tiles found in catalog.[/yellow]")
        console.print("Run [bold]ilhmp catalog add <path>[/bold] to register tiles.")
        raise typer.Exit(1)

    # Find deepest common ancestor of all tile dirs
    roots = sorted(serve_roots)
    if len(roots) == 1:
        serve_dir = roots[0]
    else:
        parts_list = [Path(r).parts for r in roots]
        common = []
        for group in zip(*parts_list):
            if len(set(group)) == 1:
                common.append(group[0])
            else:
                break
        serve_dir = str(Path(*common)) if common else str(Path.cwd())

    # Build layer list for the viewer
    layers = []
    for e in local_entries:
        mb = e.get("local_mbtiles", "")
        z = e.get("zoom") or [9, 16]
        label = f"{e['county']} / {e.get('theme','?')} z{z[0]}-{z[1]}"
        # Find tiles dir
        mb_path = Path(mb)
        tiles_candidate = mb_path.parent / f"tiles-{mb_path.stem}"
        if not tiles_candidate.exists():
            candidates = list(mb_path.parent.glob("tiles-*"))
            tiles_candidate = candidates[0] if candidates else None
        if tiles_candidate and tiles_candidate.exists():
            try:
                rel_tiles = tiles_candidate.relative_to(serve_dir)
                tile_url = f"{rel_tiles}/{{z}}/{{x}}/{{y}}.png"
            except ValueError:
                tile_url = f"{tiles_candidate}/{{z}}/{{x}}/{{y}}.png"
        else:
            tile_url = None
        if tile_url:
            layers.append({"label": label, "url": tile_url, "county": e["county"], "theme": e.get("theme")})

    # Write viewer
    index_path = Path(serve_dir) / "_ilhmp_serve.html"
    _write_serve_viewer(index_path, layers)

    console.print(f"\n[bold]ilhmp serve[/bold]")
    console.print(f"   {len(local_entries)} tiles | {len(layers)} viewable")
    console.print(f"   Root: {serve_dir}")
    console.print(f"   URL:  http://localhost:{port}")
    console.print("   Ctrl+C to stop\n")

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=serve_dir, **kw)
        def log_message(self, fmt, *args):
            pass

    url = f"http://localhost:{port}/_ilhmp_serve.html"
    threading.Thread(target=lambda: (
        __import__("time").sleep(0.5), webbrowser.open(url)
    ), daemon=True).start()

    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            if index_path.exists():
                index_path.unlink()


def _write_serve_viewer(path: Path, layers: list) -> None:
    layers_json = json.dumps(layers, indent=2)
    html = f"""<!DOCTYPE html>
<html><head>
<title>ilhmp — local tiles</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#0d1117}}
#map{{position:absolute;top:0;bottom:0;width:100%}}
#ctrl{{position:absolute;top:12px;left:50%;transform:translateX(-50%);z-index:1000;
  background:rgba(0,0,0,.88);color:#e6edf3;padding:10px 16px;border-radius:10px;
  display:flex;align-items:center;gap:8px;box-shadow:0 2px 16px rgba(0,0,0,.6)}}
#ctrl label{{color:#8b949e;font-size:12px}}
#layer-sel{{background:#161b22;color:#e6edf3;border:1px solid #30363d;padding:6px 10px;
  border-radius:6px;font-size:13px;cursor:pointer;min-width:260px}}
.nb{{background:#21262d;color:#e6edf3;border:1px solid #30363d;padding:6px 12px;
  border-radius:6px;font-size:16px;cursor:pointer}}
.nb:hover{{background:#30363d}}
#info{{position:absolute;top:12px;right:12px;z-index:1000;
  background:rgba(0,0,0,.8);color:#8b949e;padding:10px 14px;border-radius:8px;font-size:12px;line-height:1.7}}
#info strong{{color:#58a6ff}}
#op{{position:absolute;bottom:28px;left:12px;z-index:1000;
  background:rgba(0,0,0,.8);color:#8b949e;padding:10px 14px;border-radius:8px;font-size:12px}}
#bm{{position:absolute;bottom:28px;right:12px;z-index:1000;display:flex;gap:6px}}
.bm{{background:rgba(0,0,0,.8);color:#8b949e;border:1px solid #30363d;padding:6px 10px;
  border-radius:6px;font-size:12px;cursor:pointer}}
.bm.on{{background:#1f3a5f;border-color:#58a6ff;color:#e6edf3}}
</style>
</head><body>
<div id="map"></div>
<div id="ctrl">
  <button class="nb" id="prev">◀</button>
  <label>Layer</label>
  <select id="layer-sel"></select>
  <button class="nb" id="next">▶</button>
</div>
<div id="info"><strong id="lbl">—</strong><br><span id="desc"></span></div>
<div id="op">
  <label>Opacity: <span id="opv">90%</span></label><br>
  <input type="range" id="ops" min="0" max="100" value="90" style="width:120px">
</div>
<div id="bm">
  <button class="bm on" data-b="dark">Dark</button>
  <button class="bm" data-b="light">Light</button>
  <button class="bm" data-b="sat">Satellite</button>
  <button class="bm" data-b="none">None</button>
</div>
<script>
const LAYERS={layers_json};
const BMS={{
  dark:L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{maxZoom:19,attribution:'© CartoDB'}}),
  light:L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{maxZoom:19,attribution:'© CartoDB'}}),
  sat:L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',{{maxZoom:19,attribution:'© Esri'}}),
  none:null
}};
const map=L.map('map',{{center:[41.2,-89.3],zoom:10}});
BMS.dark.addTo(map);
let curBm=BMS.dark,curLayer=null,idx=0;
const sel=document.getElementById('layer-sel');
LAYERS.forEach((l,i)=>{{const o=document.createElement('option');o.value=i;o.textContent=l.label;sel.appendChild(o)}});
function load(i){{
  if(curLayer)map.removeLayer(curLayer);
  const l=LAYERS[i];
  curLayer=L.tileLayer(l.url,{{tms:true,minZoom:9,maxZoom:16,maxNativeZoom:16,
    opacity:document.getElementById('ops').value/100,attribution:'ilhmp'}});
  curLayer.addTo(map);
  sel.value=i; idx=i;
  document.getElementById('lbl').textContent=l.label;
  document.getElementById('desc').textContent=l.county+' / '+l.theme;
}}
sel.addEventListener('change',e=>load(+e.target.value));
document.getElementById('prev').addEventListener('click',()=>load((idx-1+LAYERS.length)%LAYERS.length));
document.getElementById('next').addEventListener('click',()=>load((idx+1)%LAYERS.length));
document.getElementById('ops').addEventListener('input',e=>{{
  document.getElementById('opv').textContent=e.target.value+'%';
  if(curLayer)curLayer.setOpacity(e.target.value/100);
}});
document.querySelectorAll('.bm').forEach(b=>b.addEventListener('click',()=>{{
  document.querySelectorAll('.bm').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');
  if(curBm)map.removeLayer(curBm);
  curBm=BMS[b.dataset.b];
  if(curBm){{curBm.addTo(map);if(curLayer)curLayer.bringToFront();}}
}}));
document.addEventListener('keydown',e=>{{
  if(e.key==='ArrowRight')load((idx+1)%LAYERS.length);
  if(e.key==='ArrowLeft')load((idx-1+LAYERS.length)%LAYERS.length);
}});
if(LAYERS.length)load(0);
</script>
</body></html>"""
    path.write_text(html)


# ── serve (push mbtiles to tiles.exaggeratedrelief.com) ─────────────────────

# Default tile server config — matches TOOLS.md
_TILE_SERVER_HOST = "ubuntu@3.20.103.82"
_TILE_SERVER_KEY  = str(Path.home() / ".ssh" / "mapserver-ec2.pem")
_TILE_SERVER_DIR  = "/data/tiles"
_TILE_SERVER_CADDY = "/data/Caddyfile"
_TILE_SERVER_DOMAIN = "tiles.exaggeratedrelief.com"
_TILE_SERVER_LEGACY_DOMAIN = "tiles.chicagooffline.com"


def _scp_to_tile_server(local: Path, key: str = _TILE_SERVER_KEY,
                         host: str = _TILE_SERVER_HOST,
                         remote_dir: str = _TILE_SERVER_DIR) -> None:
    r = _sp.run(
        ["scp", "-i", key, "-o", "StrictHostKeyChecking=no",
         str(local), f"{host}:{remote_dir}/"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"scp failed: {r.stderr.strip()}")


def _ssh(cmd: str, key: str = _TILE_SERVER_KEY,
          host: str = _TILE_SERVER_HOST) -> str:
    r = _sp.run(
        ["ssh", "-i", key, "-o", "StrictHostKeyChecking=no", host, cmd],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ssh failed: {r.stderr.strip()}")
    return r.stdout.strip()


def _tile_server_list(key: str = _TILE_SERVER_KEY,
                      host: str = _TILE_SERVER_HOST,
                      remote_dir: str = _TILE_SERVER_DIR) -> list[str]:
    """Return list of mbtiles filenames currently on the tile server."""
    out = _ssh(f"ls {remote_dir}/*.mbtiles 2>/dev/null", key=key, host=host)
    return [Path(p).name for p in out.splitlines() if p.strip()]


def _ensure_caddy_vhost(key: str = _TILE_SERVER_KEY,
                         host: str = _TILE_SERVER_HOST,
                         caddy_path: str = _TILE_SERVER_CADDY,
                         domain: str = _TILE_SERVER_DOMAIN) -> bool:
    """Add tiles.exaggeratedrelief.com vhost to Caddyfile if missing. Returns True if changed."""
    current = _ssh(f"cat {caddy_path}", key=key, host=host)
    if domain in current:
        return False
    new_block = f"""
{domain} {{
    header {{
        Access-Control-Allow-Origin *
        Access-Control-Allow-Methods \"GET, OPTIONS\"
        Access-Control-Allow-Headers \"Content-Type\"
    }}

    handle /* {{
        reverse_proxy mbtileserver:8000 {{
            header_up X-Forwarded-Host {{host}}
            header_up X-Forwarded-Proto {{scheme}}
        }}
    }}
}}
"""
    append_cmd = f"echo '{new_block}' | sudo tee -a {caddy_path} > /dev/null"
    _ssh(append_cmd, key=key, host=host)
    # Reload Caddy gracefully
    _ssh("cd /data && docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile",
         key=key, host=host)
    return True


@app.command("push")
def push_cmd(
    mbtiles: Path = typer.Argument(..., help="MBTiles file to push to tiles.exaggeratedrelief.com"),
    host: str = typer.Option(_TILE_SERVER_HOST, "--host", help="SSH host (user@ip)"),
    key: str = typer.Option(_TILE_SERVER_KEY, "--key", help="SSH key path"),
    remote_dir: str = typer.Option(_TILE_SERVER_DIR, "--dir", help="Remote tile directory"),
    setup_domain: bool = typer.Option(True, "--setup-domain/--no-setup-domain",
                                       help="Add tiles.exaggeratedrelief.com Caddy vhost if missing"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    json_out: bool = typer.Option(False, "--json"),
):
    """
    Push a local mbtiles to tiles.exaggeratedrelief.com.

    Copies the file to /data/tiles/ on the tile server via SCP.
    mbtileserver auto-discovers new files — no restart needed.
    Optionally adds the tiles.exaggeratedrelief.com Caddy vhost if missing.

    URL after push:
      https://tiles.exaggeratedrelief.com/services/{stem}
      https://tiles.exaggeratedrelief.com/services/{stem}/tiles/{z}/{x}/{y}.png
    """
    mbtiles = mbtiles.resolve()
    if not mbtiles.exists():
        console.print(f"[red]Not found: {mbtiles}[/red]")
        raise typer.Exit(1)

    stem = mbtiles.stem
    size_mb = mbtiles.stat().st_size // 1_048_576
    remote_path = f"{remote_dir}/{mbtiles.name}"

    console.print(f"\n[bold]ilhmp push[/bold]  {'[yellow](dry run)[/yellow]' if dry_run else ''}")
    console.print(f"   MBTiles:  {mbtiles.name} ({size_mb}MB)")
    console.print(f"   Target:   {host}:{remote_path}")
    console.print(f"   URL:      https://{_TILE_SERVER_DOMAIN}/services/{stem}")

    if dry_run:
        console.print("\n[yellow]Dry run — no changes made.[/yellow]")
        return

    # 1. Check if already present
    console.print("\n[bold]1/3[/bold] Checking remote...")
    try:
        existing = _tile_server_list(key=key, host=host, remote_dir=remote_dir)
    except Exception as e:
        console.print(f"[red]Could not reach tile server:[/red] {e}")
        raise typer.Exit(1)

    if mbtiles.name in existing:
        console.print(f"[yellow]Already present: {mbtiles.name}[/yellow] — re-uploading to overwrite")
    else:
        console.print(f"[dim]{len(existing)} files on server[/dim]")

    # 2. SCP
    console.print(f"\n[bold]2/3[/bold] Uploading ({size_mb}MB)...")
    try:
        _scp_to_tile_server(mbtiles, key=key, host=host, remote_dir=remote_dir)
    except Exception as e:
        console.print(f"[red]Upload failed:[/red] {e}")
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] {mbtiles.name} → {host}:{remote_dir}/")

    # 3. Ensure Caddy vhost
    console.print(f"\n[bold]3/3[/bold] Caddy vhost...")
    if setup_domain:
        try:
            changed = _ensure_caddy_vhost(key=key, host=host)
            if changed:
                console.print(f"[green]✓[/green] Added {_TILE_SERVER_DOMAIN} vhost + reloaded Caddy")
            else:
                console.print(f"[dim]{_TILE_SERVER_DOMAIN} vhost already present[/dim]")
        except Exception as e:
            console.print(f"[yellow]Caddy vhost setup failed (not fatal):[/yellow] {e}")
    else:
        console.print("[dim]Skipped (--no-setup-domain)[/dim]")

    console.print(f"\n[bold green]Done![/bold green]")
    console.print(f"   Preview: https://{_TILE_SERVER_DOMAIN}/services/{stem}/map")
    console.print(f"   XYZ:     https://{_TILE_SERVER_DOMAIN}/services/{stem}/tiles/{{z}}/{{x}}/{{y}}.png")

    if json_out:
        print(json.dumps({
            "id": stem,
            "file": mbtiles.name,
            "size_mb": size_mb,
            "url": f"https://{_TILE_SERVER_DOMAIN}/services/{stem}",
            "xyz": f"https://{_TILE_SERVER_DOMAIN}/services/{stem}/tiles/{{z}}/{{x}}/{{y}}.png",
        }, indent=2))


@app.command("push-all")
def push_all_cmd(
    directory: Path = typer.Argument(..., help="Directory containing mbtiles to push"),
    host: str = typer.Option(_TILE_SERVER_HOST, "--host"),
    key: str = typer.Option(_TILE_SERVER_KEY, "--key"),
    remote_dir: str = typer.Option(_TILE_SERVER_DIR, "--dir"),
    skip_existing: bool = typer.Option(True, "--skip-existing/--overwrite",
                                        help="Skip files already present on server"),
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    """
    Push all mbtiles in a directory to tiles.exaggeratedrelief.com.

    Useful for bulk-uploading a county's theme set after generation.
    """
    directory = directory.resolve()
    files = sorted(directory.rglob("*.mbtiles"))
    if not files:
        console.print(f"[yellow]No mbtiles found in {directory}[/yellow]")
        raise typer.Exit(1)

    console.print(f"\n[bold]ilhmp push-all[/bold]  {'[yellow](dry run)[/yellow]' if dry_run else ''}")
    console.print(f"   Directory: {directory}")
    console.print(f"   Files:     {len(files)}")

    try:
        existing = _tile_server_list(key=key, host=host, remote_dir=remote_dir)
    except Exception as e:
        console.print(f"[red]Could not reach tile server:[/red] {e}")
        raise typer.Exit(1)

    skipped = 0
    pushed = 0
    failed = 0

    for f in files:
        size_mb = f.stat().st_size // 1_048_576
        if skip_existing and f.name in existing:
            console.print(f"   [dim]skip[/dim]  {f.name} ({size_mb}MB) — already present")
            skipped += 1
            continue
        if dry_run:
            console.print(f"   [cyan]would push[/cyan]  {f.name} ({size_mb}MB)")
            pushed += 1
            continue
        try:
            _scp_to_tile_server(f, key=key, host=host, remote_dir=remote_dir)
            console.print(f"   [green]✓[/green] {f.name} ({size_mb}MB)")
            pushed += 1
        except Exception as e:
            console.print(f"   [red]✗[/red] {f.name}: {e}")
            failed += 1

    console.print(f"\n[bold]Done[/bold] — pushed {pushed}, skipped {skipped}, failed {failed}")
    if failed:
        raise typer.Exit(1)


# ── publish ───────────────────────────────────────────────────────────────────

@app.command("publish")
def publish_cmd(
    mbtiles: Path = typer.Argument(..., help="MBTiles file to publish"),
    county: Optional[str] = typer.Option(None, "--county", "-c"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t"),
    dem: str = typer.Option("dtm", "--dem"),
    exaggeration: Optional[str] = typer.Option(None, "--exag", "-z"),
    s3_bucket: str = typer.Option("exaggeratedrelief", "--bucket"),
    catalog_path: Optional[Path] = typer.Option(None, "--catalog"),
    no_pr: bool = typer.Option(False, "--no-pr", help="Skip GitHub PR"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    json_out: bool = typer.Option(False, "--json"),
):
    """
    Publish a local mbtiles: convert to PMTiles, upload to S3, update catalog, open PR.

    Steps:
      1. pmtiles convert → {name}.pmtiles
      2. aws s3 cp → s3://{bucket}/tiles/{name}.pmtiles
      3. Update web/catalog.json
      4. Write requests/{name}.yaml (status: completed, source: local)
      5. git commit + push + gh pr create
    """
    from . import catalog as cat_mod

    mbtiles = mbtiles.resolve()
    if not mbtiles.exists():
        console.print(f"[red]Not found: {mbtiles}[/red]")
        raise typer.Exit(1)

    cat_path = catalog_path or cat_mod.DEFAULT_CATALOG
    parsed = cat_mod.parse_mbtiles_name(mbtiles.name)
    county = county or parsed["county"]
    theme = theme or parsed["theme"]
    exaggeration = exaggeration or parsed["exaggeration"]
    tile_id = mbtiles.stem
    pmtiles_name = f"{tile_id}.pmtiles"
    pmtiles_path = mbtiles.parent / pmtiles_name
    s3_key = f"tiles/{pmtiles_name}"

    console.print(f"\n[bold]ilhmp publish[/bold]  {'[yellow](dry run)[/yellow]' if dry_run else ''}")
    console.print(f"   MBTiles:  {mbtiles}")
    console.print(f"   County:   {county}  Theme: {theme}  Exag: {exaggeration}x")
    console.print(f"   S3:       s3://{s3_bucket}/{s3_key}")

    if dry_run:
        console.print("\n[yellow]Dry run — no changes made.[/yellow]")
        return

    # 1. Convert
    console.print("\n[bold]1/4[/bold] Converting to PMTiles...")
    pmtiles_bin = _find_tool("pmtiles")
    r = _sp.run([pmtiles_bin, "convert", str(mbtiles), str(pmtiles_path)],
                capture_output=True, text=True)
    if r.returncode != 0:
        console.print(f"[red]pmtiles failed:[/red] {r.stderr}")
        raise typer.Exit(1)
    size_mb = pmtiles_path.stat().st_size // 1_048_576
    console.print(f"[green]✓[/green] {pmtiles_path.name} ({size_mb}MB)")

    # 2. Upload
    console.print("\n[bold]2/4[/bold] Uploading to S3...")
    r = _sp.run([
        "aws", "s3", "cp", str(pmtiles_path), f"s3://{s3_bucket}/{s3_key}",
        "--content-type", "application/x-protobuf",
        "--cache-control", "max-age=86400",
    ], capture_output=True, text=True)
    if r.returncode != 0:
        console.print(f"[red]S3 upload failed:[/red] {r.stderr}")
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] s3://{s3_bucket}/{s3_key}")

    # 3. Catalog
    console.print("\n[bold]3/4[/bold] Updating catalog.json...")
    entry = cat_mod.add_entry(
        mbtiles, cat_path,
        county=county, theme=theme, dem=dem, exaggeration=exaggeration,
        pmtiles_path=pmtiles_path,
    )
    console.print(f"[green]✓[/green] Catalog: {tile_id}")

    # 4. PR
    if not no_pr:
        console.print("\n[bold]4/4[/bold] Opening PR...")
        zoom_str = entry.get("zoom_str", "9-16")
        req_path = _REPO_ROOT / "requests" / f"{tile_id}.yaml"
        req_path.write_text(
            f"county: {county}\n"
            f"dem: {dem}\n"
            f"theme: {theme}\n"
            f"exaggeration: {exaggeration}\n"
            f'zoom: "{zoom_str}"\n'
            f"status: completed\n"
            f"source: local\n"
            f"generated_at: {entry['generated_at']}\n"
        )
        branch = f"local/{tile_id}"
        for cmd in [
            ["git", "-C", str(_REPO_ROOT), "checkout", "-b", branch],
            ["git", "-C", str(_REPO_ROOT), "add", str(cat_path), str(req_path)],
            ["git", "-C", str(_REPO_ROOT), "commit", "-m", f"feat: local tile {tile_id}"],
            ["git", "-C", str(_REPO_ROOT), "push", "-u", "origin", branch],
        ]:
            r = _sp.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                console.print(f"[red]git:[/red] {r.stderr.strip()}")
                raise typer.Exit(1)

        gh = _find_tool("gh")
        pr = _sp.run([
            gh, "pr", "create",
            "--title", f"feat: local tile {tile_id}",
            "--body", (
                f"Local generation — {county} / {theme} / {exaggeration}x / z{zoom_str}\n\n"
                f"PMTiles: `s3://{s3_bucket}/{s3_key}`"
            ),
            "--base", "main",
        ], capture_output=True, text=True, cwd=str(_REPO_ROOT))
        if pr.returncode == 0:
            console.print(f"[green]✓[/green] PR: {pr.stdout.strip()}")
        else:
            console.print(f"[yellow]Push ok, gh pr create failed:[/yellow] {pr.stderr.strip()}")

    console.print(f"\n[bold green]Done![/bold green] {tile_id} published.")
    if json_out:
        print(json.dumps(entry, indent=2))
