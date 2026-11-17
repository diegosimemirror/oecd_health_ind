# ============================================================
# PROCESO 4: Descargar las fichas metodológicas ("Sources and Methods")
# Insumo:    4_salidas/tablas/p02_conjuntos_seleccionados.csv (columna enlaces_metodologia)
# Resultado: 2_fichas_metodologicas/*.pdf / *.xlsx
#            4_salidas/tablas/p04_indice_fichas.csv  (qué ficha corresponde a cada conjunto)
# Las fichas explican, país por país, cómo se mide cada indicador y en qué se aparta
# de la definición OCDE: es lo que permite juzgar si los datos son comparables.
# ============================================================

# --- Paquetes ---
import requests, time, sys
from urllib.parse import unquote, urlparse   # convertir "%20" en espacios para nombrar archivos
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
FICHAS = PROYECTO / "2_fichas_metodologicas"
TABLAS = PROYECTO / "4_salidas" / "tablas"
FICHAS.mkdir(exist_ok=True)

# --- Paso 4.1: separar los enlaces de cada conjunto (vienen juntos, separados por espacios) ---
# .str.split().explode(): convierte "enlace1 enlace2" en dos filas
#   Antes: 1 fila por conjunto | Después: 1 fila por conjunto × enlace
conjuntos = pd.read_csv(TABLAS / "p02_conjuntos_seleccionados.csv")
enlaces = (conjuntos[["conjunto", "nombre", "enlaces_metodologia"]]
           .assign(url=conjuntos["enlaces_metodologia"].fillna("").str.split())
           .explode("url").dropna(subset=["url"]))
enlaces = enlaces[enlaces["url"].str.startswith("http")]
print("Enlaces (conjunto × enlace):", enlaces.shape[0], "| únicos:", enlaces["url"].nunique())

# --- Paso 4.2: clasificar el tipo de enlace ---
def tipo(url):
    ext = Path(urlparse(url).path).suffix.lower()
    return "documento" if ext in (".pdf", ".xlsx", ".xls", ".docx") else "pagina_web"
enlaces["tipo"] = enlaces["url"].map(tipo)

# --- Paso 4.3: descargar cada documento una sola vez ---
archivo_de = {}
for url in enlaces.loc[enlaces["tipo"] == "documento", "url"].unique():
    nombre = unquote(Path(urlparse(url).path).name)
    destino = FICHAS / nombre
    if not destino.exists():
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200:
                destino.write_bytes(r.content)
            print(r.status_code, nombre, flush=True)
        except requests.RequestException as e:
            print("ERROR", nombre, type(e).__name__)
        time.sleep(1)
    archivo_de[url] = nombre if destino.exists() else ""

enlaces["archivo_local"] = enlaces["url"].map(archivo_de).fillna("")

# --- Paso 4.4: verificar y guardar el índice ---
docs = enlaces[enlaces["tipo"] == "documento"]
print("Documentos descargados:", (docs["archivo_local"] != "").sum(), "de", len(docs),
      "| archivos distintos:", docs["archivo_local"].replace("", pd.NA).nunique())
enlaces.drop(columns="enlaces_metodologia").to_csv(
    TABLAS / "p04_indice_fichas.csv", index=False, encoding="utf-8-sig")

# --- Paso 4.5: bajar las sub-fichas ---
# Varias fichas son solo un índice con enlaces a una sub-ficha por indicador (p. ej. "4_2_Total
# calories supply"). Esas sub-fichas tienen la fuente y las notas de cada país.
# pymupdf: lee PDF; get_links() devuelve los enlaces que hay dentro de cada página
import pymupdf
SUBFICHAS = FICHAS / "subfichas"
SUBFICHAS.mkdir(exist_ok=True)
subfichas = []
for pdf in sorted(FICHAS.glob("*.pdf")):
    for pagina in pymupdf.open(pdf):
        for enlace in pagina.get_links():
            url = enlace.get("uri", "")
            if "webfs-els.oecd.org/files/Health-Statistics" in url and url.lower().endswith((".pdf", ".xlsx")):
                subfichas.append({"ficha_indice": pdf.name, "url": url,
                                  "archivo_local": unquote(Path(urlparse(url).path).name)})
subfichas = pd.DataFrame(subfichas).drop_duplicates("url")
for s in subfichas.itertuples():
    destino = SUBFICHAS / s.archivo_local
    if destino.exists() or (FICHAS / s.archivo_local).exists():
        continue
    r = requests.get(s.url, timeout=120)
    if r.status_code == 200:
        destino.write_bytes(r.content)
    time.sleep(1)
subfichas["descargada"] = subfichas["archivo_local"].map(
    lambda a: (SUBFICHAS / a).exists() or (FICHAS / a).exists())
print("Sub-fichas:", len(subfichas), "| descargadas:", subfichas["descargada"].sum())
subfichas.to_csv(TABLAS / "p04_indice_subfichas.csv", index=False, encoding="utf-8-sig")
