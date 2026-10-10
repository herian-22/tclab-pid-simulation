"""Unduh dataset publik TCLab ke data/raw/. Jalankan dari mesin Anda (butuh internet)."""

import pathlib
import urllib.request

URL = "https://jckantor.github.io/CBE32338/data/tclab-data.csv"
DEST = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw" / "tclab-data.csv"

DEST.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(URL, DEST)
print(f"Tersimpan: {DEST} ({DEST.stat().st_size} bytes)")
