"""Genera el catálogo público JS desde el JSON compartido. No contiene secretos."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def sync():
    data = json.loads((ROOT / 'data/catalogo.json').read_text())
    text = "'use strict';\n// Generado por python3 server/sync_catalog.py; editar data/catalogo.json.\nwindow.AYLIN_CATALOG = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\nObject.freeze(AYLIN_CATALOG.categories);\nAYLIN_CATALOG.products.forEach(p => { p.variants.forEach(Object.freeze); Object.freeze(p.variants); Object.freeze(p); });\nObject.freeze(AYLIN_CATALOG.products); Object.freeze(AYLIN_CATALOG);\n"
    (ROOT / 'js/catalogo.js').write_text(text)
if __name__ == '__main__': sync()
