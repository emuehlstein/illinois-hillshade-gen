"""
Local tile viewer for previewing hillshade output.
"""

import http.server
import json
import os
import socketserver
import sqlite3
import webbrowser
from pathlib import Path
from typing import Optional, Tuple


def generate_viewer_html(
    output_path: Path,
    tiles_path: str,
    county_name: str = "Illinois",
    style: str = "dark",
    dem_type: str = "DTM",
    exaggeration: float = 3.0,
    min_zoom: int = 10,
    max_zoom: int = 16,
    center_lat: float = 41.0,
    center_lon: float = -89.0,
    tile_format: str = "tiles",
    bounds: Optional[Tuple[float, float, float, float]] = None,
    geojson_path: Optional[str] = None,
) -> Path:
    """Generate a viewer HTML file for the tiles."""
    template_path = Path(__file__).parent / "templates" / "viewer.html"
    
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Default bounds from center (rough estimate)
    if not bounds:
        bounds = (center_lon - 0.2, center_lat - 0.15, center_lon + 0.2, center_lat + 0.15)
    
    # Simple template substitution
    html = template.replace("{{title}}", f"{county_name} Hillshade Viewer")
    html = html.replace("{{county_name}}", county_name)
    html = html.replace("{{style}}", style.title())
    html = html.replace("{{dem_type}}", dem_type.upper())
    html = html.replace("{{exaggeration}}", str(exaggeration))
    html = html.replace("{{min_zoom}}", str(min_zoom))
    html = html.replace("{{max_zoom}}", str(max_zoom))
    html = html.replace("{{center_lat}}", str(center_lat))
    html = html.replace("{{center_lon}}", str(center_lon))
    html = html.replace("{{initial_zoom}}", str(min_zoom + 1))
    html = html.replace("{{tiles_path}}", tiles_path)
    html = html.replace("{{format}}", tile_format)
    html = html.replace("{{bounds_json}}", json.dumps(list(bounds)))
    html = html.replace("{{geojson_path}}", geojson_path or "")
    
    output_path = Path(output_path)
    with open(output_path, 'w') as f:
        f.write(html)
    
    return output_path


class MBTilesHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves tiles from MBTiles + static files."""
    
    mbtiles_path: Optional[Path] = None
    
    def do_GET(self):
        if self.path.startswith('/tiles/') and self.mbtiles_path:
            self.serve_mbtiles_tile()
        else:
            super().do_GET()
    
    def serve_mbtiles_tile(self):
        """Serve a tile from the MBTiles database."""
        try:
            parts = self.path.replace('/tiles/', '').replace('.png', '').split('/')
            z, x, y = int(parts[0]), int(parts[1]), int(parts[2])
            y_tms = (2 ** z - 1) - y
            
            conn = sqlite3.connect(str(self.mbtiles_path))
            cursor = conn.execute(
                "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
                (z, x, y_tms)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', len(row[0]))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(row[0])
            else:
                self.send_error(404, 'Tile not found')
        except Exception as e:
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        pass


def serve_tiles(
    tiles_path: Path,
    port: int = 9999,
    open_browser: bool = True,
) -> None:
    """Start a local HTTP server to preview tiles."""
    tiles_path = Path(tiles_path)
    
    if tiles_path.suffix == '.mbtiles':
        serve_dir = tiles_path.parent
        MBTilesHandler.mbtiles_path = tiles_path
        handler = MBTilesHandler
    else:
        serve_dir = tiles_path.parent
        handler = http.server.SimpleHTTPRequestHandler
    
    os.chdir(serve_dir)
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/viewer.html"
        print(f"🌐 Tile server running at http://localhost:{port}")
        print(f"   Viewer: {url}")
        print(f"   Press Ctrl+C to stop\n")
        
        if open_browser:
            webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹️  Server stopped")
