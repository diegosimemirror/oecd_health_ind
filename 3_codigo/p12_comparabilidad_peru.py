# ============================================================
# PROCESO 12: Comparabilidad de los datos de Perú ("medir bien para compararse")
# Insumo:    4_salidas/datos_procesados/p07_observaciones.parquet (marcas OBS_STATUS de cada dato)
#            4_salidas/tablas/p11_prioridades_peru.csv (indicadores y situación de Perú)
#            2_fichas_metodologicas/ (PDF y Excel con notas por país)
# Resultado: 4_salidas/tablas/p12_comparabilidad_peru.csv  (1 fila por indicador que Perú reporta)
#            4_salidas/tablas/p12_notas_peru_fichas.csv    (extractos de las fichas que mencionan a Perú)
# Marcas que pone la OCDE a un dato (OBS_STATUS, código estándar SDMX):
#   A = normal, B = quiebre de serie, D = la definición difiere, E = estimado, P = provisional, M = faltante
# ============================================================

# --- Paquetes ---
import pandas as pd
import pymupdf          # leer el texto de los PDF
import openpyxl         # leer los Excel de "Sources and Methods" (encuestas HCQO)
import re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
TABLAS = PROYECTO / "4_salidas" / "tablas"
FICHAS = PROYECTO / "2_fichas_metodologicas"
MARCAS = {"B": "quiebre de serie", "D": "definición distinta", "E": "estimado", "P": "provisional"}

# --- Paso 12.1: marcas de calidad en los datos de Perú ---
obs = pd.read_parquet(PROYECTO / "4_salidas" / "datos_procesados" / "p07_observaciones.parquet",
                      filters=[("REF_AREA", "==", "PER")])
print("Observaciones de Perú:", obs.shape)
# Solo el último año de cada indicador (lo que se compararía hoy)
ultimo = obs[obs["anio"] == obs.groupby("id_indicador")["anio"].transform("max")]
marcas = (ultimo.assign(marca=ultimo["OBS_STATUS"].fillna("A"))
          .groupby("id_indicador")["marca"].value_counts(normalize=True).mul(100).round(1)
          .unstack(fill_value=0))
for m in MARCAS:
    if m not in marcas:
        marcas[m] = 0.0
marcas = marcas[list(MARCAS)].rename(columns={m: f"pct_{n.replace(' ', '_')}" for m, n in MARCAS.items()})
marcas["ultimo_anio_peru"] = obs.groupby("id_indicador")["anio"].max()

# --- Paso 12.2: notas sobre Perú en las fichas (PDF) ---
notas = []
for pdf in sorted(list(FICHAS.glob("*.pdf")) + list((FICHAS / "subfichas").glob("*.pdf"))):
    texto = " ".join(p.get_text() for p in pymupdf.open(pdf))
    texto = re.sub(r"\s+", " ", texto)
    for m in re.finditer(r"\bPeru\b", texto):
        notas.append({"archivo": pdf.name, "extracto": texto[m.start(): m.start() + 500]})
        break   # el primer párrafo sobre Perú suele ser el de fuente y notas
# --- Paso 12.3: notas sobre Perú en los Excel de las encuestas HCQO ---
for xlsx in sorted(FICHAS.glob("*.xlsx")):
    libro = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    encontrado = False
    for hoja in libro.worksheets:
        for fila in hoja.iter_rows(values_only=True):
            celdas = [str(c) for c in fila if c is not None]
            if any(re.fullmatch(r"Peru", c.strip()) for c in celdas):
                notas.append({"archivo": xlsx.name, "extracto": " | ".join(celdas)[:500]})
                encontrado = True
                break
        if encontrado:
            break
notas = pd.DataFrame(notas)
# El texto sigue con el país siguiente en orden alfabético: se corta ahí
SIGUIENTES = r"\s(?:Romania|Russia|Saudi Arabia|Serbia|Singapore|South Africa|Thailand|Ukraine|Unclassified - Non classifié Romania)\b"
notas["extracto"] = notas["extracto"].map(lambda t: re.split(SIGUIENTES, t)[0].strip())
notas["sin_datos"] = notas["extracto"].str.contains("Data not available")

# --- Paso 12.3b: a qué conjunto pertenece cada ficha ---
indice = pd.read_csv(TABLAS / "p04_indice_fichas.csv")[["conjunto", "archivo_local"]]
sub = pd.read_csv(TABLAS / "p04_indice_subfichas.csv").merge(
    indice.rename(columns={"archivo_local": "ficha_indice"}), on="ficha_indice")[["conjunto", "archivo_local"]]
mapa = pd.concat([indice, sub]).dropna().drop_duplicates()
notas = notas.merge(mapa, left_on="archivo", right_on="archivo_local", how="left").drop(columns="archivo_local")
# Se descartan menciones que no son notas de país (p. ej. bibliografía de un artículo)
notas = notas[notas["extracto"].str.match(r"Peru\s") & notas["conjunto"].notna()]
print("Notas sobre Perú en fichas:", len(notas), "| de ellas 'Data not available':", notas["sin_datos"].sum())
notas_conjunto = (notas[~notas["sin_datos"]].groupby("conjunto")["extracto"]
                  .apply(lambda s: " || ".join(s.str.replace(r"^Peru\s+", "", regex=True).str[:400]))
                  .rename("fuente_peru_segun_ficha").reset_index())
notas_conjunto["conjunto_corto"] = notas_conjunto["conjunto"].str.split("@").str[1]

# --- Paso 12.4: unir con la situación de Perú ---
prioridades = pd.read_csv(TABLAS / "p11_prioridades_peru.csv")
comparabilidad = (prioridades[["id_indicador", "nombre_es", "caja", "subcaja", "pct_actualizado", "prioridad",
                               "peru_otra_variante_diferencia"]]
                  .merge(marcas.reset_index(), on="id_indicador", how="inner"))
comparabilidad["conjunto_corto"] = comparabilidad["id_indicador"].str.split("|").str[0]
comparabilidad = comparabilidad.merge(notas_conjunto[["conjunto_corto", "fuente_peru_segun_ficha"]],
                                      on="conjunto_corto", how="left")
comparabilidad["alertas"] = comparabilidad.apply(
    lambda f: "; ".join([f"{f[c]:.0f} % {n}" for c, n in
                         [("pct_definición_distinta", "con definición distinta"), ("pct_estimado", "estimado"),
                          ("pct_quiebre_de_serie", "con quiebre de serie"), ("pct_provisional", "provisional")]
                         if f[c] > 0]
                        + ([f"otra variante: {f['peru_otra_variante_diferencia']}"]
                           if isinstance(f["peru_otra_variante_diferencia"], str) else [])), axis=1)

# --- Paso 12.5: verificar ---
print("Indicadores que Perú reporta (elegibles):", len(comparabilidad))
print("Con alguna alerta:", (comparabilidad["alertas"] != "").sum())
print(comparabilidad.loc[comparabilidad["alertas"] != "", ["nombre_es", "alertas"]].to_string(index=False))
print("Indicadores de Perú con fuente declarada en la ficha:", comparabilidad["fuente_peru_segun_ficha"].notna().sum())
print(notas.assign(extracto=notas["extracto"].str[:120])[["conjunto", "extracto"]].to_string(index=False))

comparabilidad.to_csv(TABLAS / "p12_comparabilidad_peru.csv", index=False, encoding="utf-8-sig")
notas.to_csv(TABLAS / "p12_notas_peru_fichas.csv", index=False, encoding="utf-8-sig")
