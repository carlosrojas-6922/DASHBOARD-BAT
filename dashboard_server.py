from concurrent.futures import ThreadPoolExecutor
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen
import json


ROOT = Path(__file__).resolve().parent
PUBLISHED_SHEETS = {
    "transporte": {
        "base": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpBOuVF4QhZe1_PHMW9I-NVIyQ90EtOnkgl64STbH3tJupebUigPjAlqQp0RlIbBShFSc4VFUhMkCX/pub?output=csv&gid=",
        "sheets": [
            {"index": 0, "gid": "1886662094", "name": "% Indicador general operación"},
            {"index": 1, "gid": "0", "name": "% Ontime"},
            {"index": 2, "gid": "1110150784", "name": "% Infull"},
            {"index": 7, "gid": "1237360999", "name": "Detalle Infull"},
            {"index": 3, "gid": "374847431", "name": "% Efectividad"},
            {"index": 4, "gid": "2061749740", "name": "% Retorno documental"},
            {"index": 5, "gid": "758399382", "name": "% Ocupación vehicular"},
            {"index": 6, "gid": "1894820028", "name": "Averías / Hurtos"},
        ],
    },
    "almacenamiento": {
        "base": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQl82isymo-mRMYkh7NCiFo_-eduaG-EomFQhNhNKFstvZtmh0NQf-txlrgUJgor95_SZD78VZvyzmL/pub?output=csv&gid=",
        "sheets": [
            {"index": 0, "gid": "0", "name": "Inventario cíclico"},
            {"index": 1, "gid": "69258331", "name": "% Ocupación bodega día Celta"},
            {"index": 2, "gid": "754815625", "name": "Cantidad ingresos"},
            {"index": 3, "gid": "1782333461", "name": "Armado cigarrillo Celta"},
        ],
    },
}


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path != "/api/google-sheets":
            return super().do_GET()

        source = parse_qs(parsed.query).get("source", [""])[0]
        config = PUBLISHED_SHEETS.get(source)
        if config is None:
            return self._json(400, {"error": "Fuente de datos no reconocida."})

        def download(sheet):
            url = config["base"] + sheet["gid"]
            request = Request(url, headers={"User-Agent": "BAT-Dashboard/1.0"})
            with urlopen(request, timeout=35) as response:
                csv = response.read().decode("utf-8-sig")
            return {**sheet, "csv": csv}

        try:
            with ThreadPoolExecutor(max_workers=min(8, len(config["sheets"]))) as pool:
                sheets = list(pool.map(download, config["sheets"]))
            return self._json(200, {"sheets": sheets})
        except (URLError, TimeoutError, OSError, UnicodeDecodeError) as exc:
            return self._json(502, {"error": f"No se pudieron consultar las hojas publicadas: {exc}"})

    def _json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def list_directory(self, path):
        self.send_error(403, "Directory listing is disabled")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), DashboardHandler)
    print("Dashboard BAT disponible en http://127.0.0.1:8765/dashboard-bat.html")
    print("Cierra esta ventana para detener el servidor local.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
