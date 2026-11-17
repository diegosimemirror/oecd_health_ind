# ============================================================
# PROCESO 6: Clasificar cada indicador en el marco HSPA de la OCDE (2024)
# Insumo:    4_salidas/tablas/p02_indicadores.csv (224 indicadores)
#            PDF "Rethinking Health System Performance Assessment" (Figura 2.1, tablas 3.1-3.14)
# Resultado: 4_salidas/tablas/p06_clasificacion_marco.csv  (+ copia .xlsx)
# Columnas que se agregan:
#   nombre_es          nombre en español
#   caja / subcaja     dónde se ubica en la figura del marco
#   transversales      eficiencia, equidad, sostenibilidad, resiliencia (si el documento lo indica)
#   fuente_asignacion  "Tabla 3.x" si el documento lo pone como ejemplo; "por analogía" si es un
#                      indicador parecido al ejemplo; "Criterio propio" si el documento no lo dice
#   tipo_fuente        quién produce el dato (reportado por países / encuesta OCDE / estimación)
# ============================================================

# --- Paquetes ---
import pandas as pd   # tablas; también escribe Excel (usa openpyxl por dentro)
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROYECTO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
TABLAS = PROYECTO / "4_salidas" / "tablas"

# --- Paso 6.1: las cajas del marco (Figura 2.1) ---
# Cada subcaja pertenece a una caja. El orden sigue la figura, de arriba hacia abajo.
CAJA_DE_SUBCAJA = {
    "Salud individual y poblacional": "1. Salud individual y poblacional",
    "Ambiental": "2. Contexto del sistema de salud",
    "Social y demográfico": "2. Contexto del sistema de salud",
    "Económico y comercial": "2. Contexto del sistema de salud",
    "Factores de riesgo": "2. Contexto del sistema de salud",
    "Acceso y cobertura": "3. Servicios de salud e intervenciones de salud pública",
    "Calidad": "3. Servicios de salud e intervenciones de salud pública",
    "Necesidades y preferencias": "4. Necesidades y preferencias de las personas",
    "Gasto y financiamiento": "5. Recursos, características y políticas",
    "Fuerza laboral": "5. Recursos, características y políticas",
    "Datos y digital": "5. Recursos, características y políticas",
    "Tecnologías y farmacéuticos": "5. Recursos, características y políticas",
    "Gobernanza": "5. Recursos, características y políticas",
    "Conocimiento e innovación": "5. Recursos, características y políticas",
}

# --- Paso 6.2: asignación indicador por indicador ---
# Formato: id_indicador: (nombre en español, subcaja, transversales, fuente de la asignación)
S, AMB, ECO, RIE = "Salud individual y poblacional", "Ambiental", "Económico y comercial", "Factores de riesgo"
ACC, CAL, NEC = "Acceso y cobertura", "Calidad", "Necesidades y preferencias"
GAS, FZA, TEC, GOB = "Gasto y financiamiento", "Fuerza laboral", "Tecnologías y farmacéuticos", "Gobernanza"
T39, T37, T35, T310 = "Tabla 3.9", "Tabla 3.7", "Tabla 3.5", "Tabla 3.10"
AN = " (por analogía)"
CP = "Criterio propio"

ASIGNACION = {
    # ---------- Contexto: ambiental ----------
    "DF_GHGHC|GHG": ("Emisiones de gases de efecto invernadero del sector salud", AMB, "Sostenibilidad", "Sección 3.2.1"),
    "DF_EXP_MORSC|DALY": ("Años de vida ajustados por discapacidad atribuibles a riesgos ambientales", AMB, "", "Tabla 3.2" + AN),
    "DF_EXP_MORSC|MOR": ("Muertes prematuras atribuibles a riesgos ambientales", AMB, "", "Tabla 3.5"),
    "DF_EXP_MORSC|SC": ("Costo de bienestar de las muertes prematuras por riesgos ambientales", AMB, "", "Tabla 3.2" + AN),
    "DF_EXP_MORSC|VSL": ("Valor estadístico de la vida (parámetro de valoración)", AMB, "", CP),
    # ---------- Contexto: económico y comercial ----------
    "DF_SOC_EMPLOY|HSE": ("Empleo total en salud y servicios sociales", ECO, "", "Tabla 3.4"),
    "DF_AWDI|WKAB": ("Días de ausencia laboral por enfermedad", ECO, "", "Tabla 3.4" + AN),
    # ---------- Contexto: factores de riesgo ----------
    "DF_HEALTH_LVNG_AC|AC": ("Consumo de alcohol (litros por persona)", RIE, "", T35),
    "DF_HEALTH_LVNG_BW|SP_OBS": ("Población con obesidad", RIE, "", T35),
    "DF_HEALTH_LVNG_BW|SP_OVRGHT": ("Población con sobrepeso", RIE, "", T35),
    "DF_HEALTH_LVNG_BW|SP_OVRGHT_OBS": ("Población con sobrepeso u obesidad", RIE, "", T35),
    "DF_HEALTH_LVNG_FSC|CLS": ("Disponibilidad de calorías por persona", RIE, "", T35 + AN),
    "DF_HEALTH_LVNG_FSC|FRS": ("Disponibilidad de frutas por persona", RIE, "", T35 + AN),
    "DF_HEALTH_LVNG_FSC|FTS": ("Disponibilidad de grasas por persona", RIE, "", T35 + AN),
    "DF_HEALTH_LVNG_FSC|PRS": ("Disponibilidad de proteínas por persona", RIE, "", T35 + AN),
    "DF_HEALTH_LVNG_FSC|SGS": ("Disponibilidad de azúcar por persona", RIE, "", T35 + AN),
    "DF_HEALTH_LVNG_FSC|VGS": ("Disponibilidad de verduras por persona", RIE, "", T35 + AN),
    "DF_HEALTH_LVNG_FSC|SP_CFRD": ("Población que come fruta a diario", RIE, "", T35 + AN),
    "DF_HEALTH_LVNG_FSC|SP_CVGD": ("Población que come verduras a diario", RIE, "", T35),
    "DF_HEALTH_LVNG_TC|SP_DS": ("Población que fuma a diario", RIE, "", T35),
    "DF_HEALTH_LVNG_TC|TBC": ("Consumo de tabaco (gramos por persona)", RIE, "", T35 + AN),
    "DF_HEALTH_LVNG_VP|SP_RVPU": ("Población que usa vapeadores con regularidad", RIE, "", "Sección 3.2.4"),
    # ---------- Salud individual y poblacional ----------
    "DF_LE|LFEXP": ("Esperanza de vida", S, "Equidad", "Tabla 3.1"),
    "DF_LE|LFEXPDFM": ("Diferencia de esperanza de vida (mujeres menos hombres)", S, "Equidad", "Tabla 3.13"),
    "DF_LE|LFEXPDMF": ("Diferencia de esperanza de vida (hombres menos mujeres)", S, "Equidad", "Tabla 3.13"),
    "DF_AM|AVM": ("Mortalidad evitable", S, "", "Tabla 3.1"),
    "DF_AM|PREVM": ("Mortalidad prevenible", S, "", "Tabla 3.1"),
    "DF_AM|TRTM": ("Mortalidad tratable", S, "Eficiencia", "Tabla 3.1"),
    "DF_COM|CSEM": ("Mortalidad por causa de muerte", S, "", "Tabla 3.1"),
    "DF_PYLL|PYLL": ("Años potenciales de vida perdidos", S, "", "Sección 3.1"),
    "DF_MIM|INM": ("Mortalidad infantil", S, "", "Tabla 3.2" + AN),
    "DF_MIM|MATM": ("Mortalidad materna", S, "", "Tabla 3.2" + AN),
    "DF_MIM|NEOM": ("Mortalidad neonatal", S, "", "Tabla 3.2" + AN),
    "DF_MIM|PERM": ("Mortalidad perinatal", S, "", "Tabla 3.2" + AN),
    "DF_IH_LB|LOWB": ("Bajo peso al nacer", S, "", CP),
    "DF_PHS|PHS": ("Salud autopercibida", S, "", "Tabla 3.1"),
    "DF_PHS_SES|PHS": ("Salud autopercibida según nivel socioeconómico", S, "Equidad", "Tabla 3.12"),
    "DF_C|CNCR": ("Incidencia de cáncer", S, "", "Tabla 3.13"),
    "DF_CD|COMMD": ("Incidencia de enfermedades transmisibles", S, "", CP),
    "DF_I|IRTA": ("Lesionados en accidentes de tránsito", S, "", CP),
    "DF_MORTALITY|M": ("Mortalidad semanal por todas las causas", S, "", "Tabla 3.1"),
    "DF_MORTALITY_EXCESS|EM": ("Mortalidad en exceso (semanal)", S, "Resiliencia", "Tabla 3.1 y 3.14"),
    "DF_MORTALITY_COVID|MCVD19": ("Mortalidad semanal por COVID-19", S, "Resiliencia", CP),
    # ---------- Servicios: acceso y cobertura ----------
    "DF_HEALTH_PROT|HIC": ("Cobertura de seguro de salud de la población", ACC, "", "Tabla 3.8"),
    "DF_PE|COSKCOST": ("Consultas omitidas por su costo", ACC, "Equidad", "Tabla 3.8 y 3.12"),
    "DF_PE|MTSKCOST": ("Exámenes, tratamientos o controles omitidos por su costo", ACC, "Equidad", "Tabla 3.8 y 3.12"),
    "DF_PE|PMSKCOST": ("Medicamentos recetados no comprados por su costo", ACC, "Equidad", "Tabla 3.8 y 3.12"),
    "DF_CONSULT|CONSULT": ("Consultas médicas por persona (presenciales y a distancia)", ACC, "", "Tabla 3.8"),
    "DF_WAITING|WAIT": ("Tiempos de espera para cirugía electiva (pacientes según tiempo de espera)", ACC, "", "Tabla 3.8"),
    "DF_WAITING|WAIT_MEAN": ("Tiempo de espera promedio para cirugía electiva", ACC, "", "Tabla 3.8"),
    "DF_WAITING|WAIT_MEDIAN": ("Tiempo de espera mediano para cirugía electiva", ACC, "", "Tabla 3.8"),
    "DF_HEALTH_LTCR_RECIPIENT|LTCR": ("Personas que reciben cuidados de largo plazo", ACC, "Equidad", "Tabla 3.13 (subcaja: criterio propio)"),
    "DF_HEALTH_LTCR_FAC_OWNER|LTCR": ("Personas en cuidados de largo plazo según propiedad del establecimiento", ACC, "", CP),
    # ---------- Servicios: calidad ----------
    "DF_IMMUN|IMMUN": ("Cobertura de vacunación", CAL, "", T39),
    "DF_SCREEN|SCREEN": ("Tamizaje de cáncer", CAL, "", T39),
    "DF_AC|IHWTHIPS": ("Cirugía de fractura de cadera iniciada dentro de los 2 días del ingreso", CAL, "", T39 + AN),
    "DF_AC|MORTAMIH": ("Mortalidad a 24 horas por infarto agudo de miocardio (mismo ingreso)", CAL, "", T39 + AN),
    "DF_AC|MORTAMII": ("Mortalidad a 30 días por infarto agudo de miocardio (mismo ingreso)", CAL, "", T39),
    "DF_AC|MORTAMIO": ("Mortalidad a 30 días por infarto agudo de miocardio (datos enlazados)", CAL, "", T39),
    "DF_AC|MORTHSTI": ("Mortalidad a 30 días por ACV hemorrágico (mismo ingreso)", CAL, "", T39 + AN),
    "DF_AC|MORTHSTO": ("Mortalidad a 30 días por ACV hemorrágico (datos enlazados)", CAL, "", T39 + AN),
    "DF_AC|MORTISTI": ("Mortalidad a 30 días por ACV isquémico (mismo ingreso)", CAL, "", T39),
    "DF_AC|MORTISTO": ("Mortalidad a 30 días por ACV isquémico (datos enlazados)", CAL, "", T39),
    "DF_PC|ADMRASTH": ("Hospitalizaciones evitables por asma", CAL, "Eficiencia", T39 + AN),
    "DF_PC|ADMRCHFL": ("Hospitalizaciones evitables por insuficiencia cardíaca", CAL, "Eficiencia", T39 + AN),
    "DF_PC|ADMRCOPD": ("Hospitalizaciones evitables por EPOC", CAL, "Eficiencia", T39),
    "DF_PC|ADMRDBUC": ("Hospitalizaciones evitables por diabetes", CAL, "Eficiencia", T39),
    "DF_PC|ADMRDMAI": ("Amputación mayor de pierna en personas con diabetes", CAL, "", T39 + AN),
    "DF_PC|ADMRDMAO": ("Amputación menor de pierna en personas con diabetes", CAL, "", T39 + AN),
    "DF_PC|ASCOCOMP": ("Hospitalizaciones evitables por asma y EPOC", CAL, "Eficiencia", T39),
    "DF_CC|CCBRNTSR": ("Supervivencia neta a 5 años: cáncer de mama", CAL, "", T39),
    "DF_CC|CCCLNTSR": ("Supervivencia neta a 5 años: cáncer de colon", CAL, "", T39),
    "DF_CC|CCCVNTSR": ("Supervivencia neta a 5 años: cáncer de cuello uterino", CAL, "", T39),
    "DF_CC|CCLKNTSR": ("Supervivencia neta a 5 años: leucemia linfoblástica aguda infantil", CAL, "", T39),
    "DF_CC|CCLUNTSR": ("Supervivencia neta a 5 años: cáncer de pulmón", CAL, "", T39),
    "DF_CC|CCRTNTSR": ("Supervivencia neta a 5 años: cáncer de recto", CAL, "", T39),
    "DF_CC|CCSTNTSR": ("Supervivencia neta a 5 años: cáncer de estómago", CAL, "", T39),
    "DF_MH|EXCEBIPO": ("Exceso de mortalidad en personas con trastorno bipolar", CAL, "", T39 + AN),
    "DF_MH|EXCESCHI": ("Exceso de mortalidad en personas con esquizofrenia", CAL, "", T39 + AN),
    "DF_IC|ICCHFACM": ("Insuficiencia cardíaca: mortalidad a 365 días del alta", CAL, "", T39),
    "DF_IC|ICCHFCF": ("Insuficiencia cardíaca: letalidad a 30 días del ingreso", CAL, "", T39),
    "DF_IC|ICCHFMACR": ("Insuficiencia cardíaca: muerte o reingreso por cualquier causa a 365 días", CAL, "", T39),
    "DF_IC|ICCHFMDSR": ("Insuficiencia cardíaca: muerte o reingreso por la misma causa a 365 días", CAL, "", T39),
    "DF_IC|ICISCACM": ("ACV isquémico: mortalidad a 365 días del alta", CAL, "", T39),
    "DF_IC|ICISCMACR": ("ACV isquémico: muerte o reingreso por cualquier causa a 365 días", CAL, "", T39),
    "DF_IC|ICISCMDSR": ("ACV isquémico: muerte o reingreso por la misma causa a 365 días", CAL, "", T39),
    "DF_IC|ICISCPHT": ("Antihipertensivos recetados 12 a 18 meses después de un ACV isquémico", CAL, "", T39 + AN),
    "DF_IC|ICISCPTR": ("Antitrombóticos recetados 12 a 18 meses después de un ACV isquémico", CAL, "", T39 + AN),
    "DF_PIPC|PRABCQDD": ("Cefalosporinas y quinolonas como proporción de los antibióticos", CAL, "Eficiencia", T39 + AN),
    "DF_PIPC|PRABOUDD": ("Volumen total de antibióticos recetados", CAL, "Eficiencia", "Tabla 3.9 y 3.11"),
    "DF_PIPC|PRBZLAOP": ("Adultos mayores con benzodiacepinas de acción prolongada", CAL, "", T39),
    "DF_PIPC|PRBZOZDD": ("Adultos mayores con uso prolongado de benzodiacepinas", CAL, "", T39),
    "DF_PIPC|PRDMPADD": ("Personas con diabetes con antihipertensivo de primera elección", CAL, "", T39),
    "DF_PIPC|PRDMPCDD": ("Personas con diabetes con receta de medicamento para el colesterol", CAL, "", T39 + AN),
    "DF_PIPC|PROPOUDD": ("Volumen total de opioides recetados", CAL, "", T39),
    "DF_PIPC|PRPPANTI": ("Personas de 65 años o más con antipsicóticos recetados", CAL, "", T39 + AN),
    "DF_PIPC|PRPPOPFH": ("Personas de 45 años o más que toman 10 o más medicamentos a la vez", CAL, "", T39 + AN),
    "DF_PIPC|PRPPOPFL": ("Personas de 45 años o más que toman entre 5 y 9 medicamentos a la vez", CAL, "", T39 + AN),
    "DF_PIPC|PRPPOPFM": ("Personas de 75 años o más que toman más de 5 medicamentos a la vez", CAL, "", T39 + AN),
    "DF_PS|OBSTVDWI": ("Trauma obstétrico en parto vaginal con instrumento", CAL, "", T39),
    "DF_PS|OBSTVDWO": ("Trauma obstétrico en parto vaginal sin instrumento", CAL, "", T39),
    "DF_PS|POSTDVSP": ("Trombosis venosa profunda tras reemplazo de cadera o rodilla (mismo ingreso)", CAL, "", T39 + AN),
    "DF_PS|POSTDVSW": ("Trombosis venosa profunda tras reemplazo de cadera o rodilla (30 días)", CAL, "", T39 + AN),
    "DF_PS|POSTPESP": ("Embolia pulmonar tras reemplazo de cadera o rodilla (mismo ingreso)", CAL, "", T39 + AN),
    "DF_PS|POSTPESW": ("Embolia pulmonar tras reemplazo de cadera o rodilla (30 días)", CAL, "", T39 + AN),
    "DF_PS|POSTSESP": ("Sepsis tras cirugía abdominopélvica (mismo ingreso)", CAL, "", T39),
    "DF_PS|POSTSESW": ("Sepsis tras cirugía abdominopélvica (30 días)", CAL, "", T39),
    "DF_PSC|COM_ERR": ("Cultura de seguridad: comunicación sobre errores", CAL, "", T39),
    "DF_PSC|COM_OP": ("Cultura de seguridad: apertura de la comunicación", CAL, "", T39),
    "DF_PSC|HANDOFF": ("Cultura de seguridad: traspasos e intercambio de información", CAL, "", T39),
    "DF_PSC|HOSP_SUP": ("Cultura de seguridad: apoyo de la dirección del hospital", CAL, "", T39),
    "DF_PSC|HOURS": ("Cultura de seguridad: horas trabajadas por semana en el hospital", CAL, "", T39 + AN),
    "DF_PSC|LEARNING": ("Cultura de seguridad: aprendizaje y mejora continua", CAL, "", T39),
    "DF_PSC|RATING": ("Cultura de seguridad: calificación de la seguridad del paciente", CAL, "", T39),
    "DF_PSC|REPORT": ("Cultura de seguridad: reporte de eventos adversos", CAL, "", T39),
    "DF_PSC|RESPONSE": ("Cultura de seguridad: respuesta ante errores", CAL, "", T39),
    "DF_PSC|STAFFING": ("Cultura de seguridad: dotación de personal y ritmo de trabajo", CAL, "", T39),
    "DF_PSC|SUPER_SUP": ("Cultura de seguridad: apoyo de supervisores y líderes clínicos", CAL, "", T39),
    "DF_PSC|TEAMWORK": ("Cultura de seguridad: trabajo en equipo", CAL, "", T39),
    "DF_EOLC|MORTACUT": ("Muertes en hospitalización de agudos (total)", CAL, "", "Sección 3.3.3"),
    "DF_EOLC|MORTACAL": ("Muertes en hospitalización de agudos: Alzheimer y otras demencias", CAL, "", "Sección 3.3.3"),
    "DF_EOLC|MORTACCA": ("Muertes en hospitalización de agudos: cáncer", CAL, "", "Sección 3.3.3"),
    "DF_EOLC|MORTACCD": ("Muertes en hospitalización de agudos: enfermedades cardiovasculares", CAL, "", "Sección 3.3.3"),
    "DF_EOLC|MORTACCR": ("Muertes en hospitalización de agudos: enfermedades respiratorias crónicas", CAL, "", "Sección 3.3.3"),
    "DF_EOLC|MORTHOSP": ("Muertes en el hospital (total)", CAL, "", "Sección 3.3.3"),
    "DF_EOLC|MORTHSPC": ("Muertes en el hospital: cáncer", CAL, "", "Sección 3.3.3"),
    "DF_EOLC|MORTHSPD": ("Muertes en el hospital: enfermedades cardiovasculares", CAL, "", "Sección 3.3.3"),
    "DF_EOLC|MORTHSPL": ("Muertes en el hospital: Alzheimer y otras demencias", CAL, "", "Sección 3.3.3"),
    "DF_EOLC|MORTHSPR": ("Muertes en el hospital: enfermedades respiratorias crónicas", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POPREEQH": ("Cadera: salud reportada por el paciente antes de operarse (EQ-5D-5L)", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POPSTEQH": ("Cadera: salud reportada por el paciente después de operarse (EQ-5D-5L)", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POCHGEQH": ("Cadera: cambio en la salud reportada por el paciente (EQ-5D-5L)", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POPREOHS": ("Cadera: puntaje Oxford antes de operarse", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POPSTOHS": ("Cadera: puntaje Oxford después de operarse", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POCHGOHS": ("Cadera: cambio en el puntaje Oxford", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POPREEQK": ("Rodilla: salud reportada por el paciente antes de operarse (EQ-5D-5L)", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POPSTEQK": ("Rodilla: salud reportada por el paciente después de operarse (EQ-5D-5L)", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POCHGEQK": ("Rodilla: cambio en la salud reportada por el paciente (EQ-5D-5L)", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POPREOKS": ("Rodilla: puntaje Oxford antes de operarse", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POPSTOKS": ("Rodilla: puntaje Oxford después de operarse", CAL, "", "Sección 3.3.3"),
    "DF_HKP|POCHGOKS": ("Rodilla: cambio en el puntaje Oxford", CAL, "", "Sección 3.3.3"),
    # ---------- Necesidades y preferencias de las personas ----------
    "DF_PE|HPRCORES": ("Médico trata al paciente con cortesía y respeto", NEC, "", T37 + AN),
    "DF_PE|HPREXCLA": ("Médico da explicaciones fáciles de entender", NEC, "", T37),
    "DF_PE|HPRGOASK": ("Médico da oportunidad de hacer preguntas", NEC, "", T37 + AN),
    "DF_PE|HPRIPDEC": ("Médico involucra al paciente en las decisiones", NEC, "", T37),
    "DF_PE|HPRTIPAT": ("Médico dedica suficiente tiempo en la consulta", NEC, "", T37),
    "DF_PE|RHPCORES": ("Médico habitual trata al paciente con cortesía y respeto", NEC, "", T37 + AN),
    "DF_PE|RHPEXCLA": ("Médico habitual da explicaciones fáciles de entender", NEC, "", T37),
    "DF_PE|RHPGOASK": ("Médico habitual da oportunidad de hacer preguntas", NEC, "", T37 + AN),
    "DF_PE|RHPIPDEC": ("Médico habitual involucra al paciente en las decisiones", NEC, "", T37),
    "DF_PE|RHPTIPAT": ("Médico habitual dedica suficiente tiempo en la consulta", NEC, "", T37),
    "DF_MHPREM|MPCBEXPL": ("Salud mental comunitaria: explicaciones fáciles de entender", NEC, "", T37 + AN),
    "DF_MHPREM|MPCBINVO": ("Salud mental comunitaria: participación del paciente en decisiones", NEC, "", T37 + AN),
    "DF_MHPREM|MPCBRESP": ("Salud mental comunitaria: trato con cortesía y respeto", NEC, "", T37 + AN),
    "DF_MHPREM|MPCBTIME": ("Salud mental comunitaria: tiempo suficiente con el paciente", NEC, "", T37 + AN),
    "DF_MHPREM|MPIPEXPL": ("Salud mental hospitalaria: explicaciones fáciles de entender", NEC, "", T37 + AN),
    "DF_MHPREM|MPIPINVO": ("Salud mental hospitalaria: participación del paciente en decisiones", NEC, "", T37 + AN),
    "DF_MHPREM|MPIPRESP": ("Salud mental hospitalaria: trato con cortesía y respeto", NEC, "", T37 + AN),
    "DF_MHPREM|MPIPTIME": ("Salud mental hospitalaria: tiempo suficiente con el paciente", NEC, "", T37 + AN),
    # PaRIS: experiencias -> necesidades y preferencias; resultados de salud -> salud individual
    "DF_PARIS|PCCPOSOUT": ("PaRIS: atención centrada en la persona (% con experiencia positiva)", NEC, "", "Sección 3.3.1"),
    "DF_PARIS|PCCSCORE": ("PaRIS: atención centrada en la persona (puntaje)", NEC, "", "Sección 3.3.1"),
    "DF_PARIS|ECPOSOUT": ("PaRIS: coordinación de la atención (% con experiencia positiva)", NEC, "", "Sección 3.3.1"),
    "DF_PARIS|ECSCORE": ("PaRIS: coordinación de la atención (puntaje)", NEC, "", "Sección 3.3.1"),
    "DF_PARIS|EQPOSOUT": ("PaRIS: calidad percibida de la atención (% positiva)", NEC, "", "Sección 3.3.1"),
    "DF_PARIS|CSMPOSOUT": ("PaRIS: confianza para manejar su propia salud (% positiva)", NEC, "", "Sección 3.3.1"),
    "DF_PARIS|THPOSOUT": ("PaRIS: confianza en el sistema de salud (% positiva)", NEC, "", "Sección 3.3.1"),
    "DF_PARIS|GHPOSOUT": ("PaRIS: salud general (% con resultado positivo)", S, "", CP),
    "DF_PARIS|PHPOSOUT": ("PaRIS: salud física (% con resultado positivo)", S, "", CP),
    "DF_PARIS|PHSCORE": ("PaRIS: salud física (puntaje)", S, "", CP),
    "DF_PARIS|MHPOSOUT": ("PaRIS: salud mental (% con resultado positivo)", S, "", CP),
    "DF_PARIS|MHSCORE": ("PaRIS: salud mental (puntaje)", S, "", CP),
    "DF_PARIS|SFPOSOUT": ("PaRIS: funcionamiento social (% con resultado positivo)", S, "", CP),
    "DF_PARIS|WBINDEX": ("PaRIS: bienestar (índice OMS-5)", S, "", CP),
    "DF_PARIS|WBPOSOUT": ("PaRIS: bienestar (% con resultado positivo)", S, "", CP),
    # ---------- Recursos: gasto y financiamiento ----------
    "DF_SHA|EXP_HEALTH": ("Gasto en salud", GAS, "Sostenibilidad", T310),
    "DF_SHA_FS|REVENUE": ("Ingresos de los esquemas de financiamiento de la salud", GAS, "Sostenibilidad", "Sección 3.5.2"),
    "DF_SHA_HK|CAPITAL_FORM": ("Inversión de capital en salud (formación bruta de capital)", GAS, "Resiliencia", "Tabla 3.10 y 3.14"),
    "DF_SHA_FP|COST": ("Costo de los insumos de los proveedores de salud", GAS, "", CP),
    "DF_SHA_COV|EXP_COVID": ("Gasto relacionado con la COVID-19", GAS, "Resiliencia", CP),
    # ---------- Recursos: fuerza laboral ----------
    "DF_PHYS|HSE": ("Médicos", FZA, "", T310),
    "DF_PHYS_AGE_SEX|HSE": ("Médicos por edad y sexo", FZA, "Equidad", "Tabla 3.10 y 3.13"),
    "DF_PHYS_CAT|HSE": ("Médicos por categoría (generales y especialistas)", FZA, "", T310),
    "DF_NURSE|HSE": ("Enfermeras", FZA, "", T310),
    "DF_NURS_AGE_SEX|HSE": ("Enfermeras por edad y sexo", FZA, "", T310 + AN),
    "DF_MIDWIFE|HSE": ("Obstetras (parteras)", FZA, "", T310 + AN),
    "DF_DNST|HSE": ("Dentistas", FZA, "", T310 + AN),
    "DF_PHST|HSE": ("Farmacéuticos", FZA, "", T310),
    "DF_PSIO|HSE": ("Fisioterapeutas", FZA, "", T310 + AN),
    "DF_CARE|HSE": ("Personal de cuidados (cuidadores)", FZA, "", T310 + AN),
    "DF_GRAD|HSG": ("Graduados en carreras de salud", FZA, "", T310),
    "DF_HOSP_EMP|HE": ("Empleo en hospitales", FZA, "", T310),
    "DF_REMUN|AI": ("Remuneración de profesionales de salud", FZA, "", T310),
    "DF_HEALTH_WFMI|HW": ("Profesionales de salud según país de formación o nacimiento", FZA, "", T310),
    "DF_HEALTH_WFMI|HW_AI": ("Profesionales de salud formados en el extranjero que llegan cada año", FZA, "", T310 + AN),
    "DF_HEALTH_WFMI|HW_NB": ("Profesionales de salud nacidos en el país", FZA, "", T310 + AN),
    "DF_HEALTH_LTCR_WORKER|FLTE": ("Trabajadores formales de cuidados de largo plazo", FZA, "Equidad", "Tabla 3.13"),
    "DF_HEALTH_LTCR_WORKER|FTE_FLTE": ("Trabajadores de cuidados de largo plazo (tiempo completo equivalente)", FZA, "", "Tabla 3.13" + AN),
    # ---------- Recursos: tecnologías y farmacéuticos (incluye infraestructura) ----------
    "DF_BEDS_FUNC|HB": ("Camas hospitalarias por función", TEC, "Resiliencia", "Tabla 3.10 y 3.14"),
    "DF_BEDS_SECT|HB": ("Camas hospitalarias por sector (público y privado)", TEC, "", T310),
    "DF_BEDS_ICU|HBU_ICU": ("Camas de cuidados intensivos (UCI)", TEC, "Resiliencia", "Tabla 3.14"),
    "DF_BEDS_ICU|HBU_ICU_A": ("Camas de UCI para adultos", TEC, "Resiliencia", "Tabla 3.14"),
    "DF_BEDS_ICU|HBU_ICU_N": ("Camas de UCI neonatal", TEC, "Resiliencia", "Tabla 3.14"),
    "DF_BEDS_ICU|HBU_ICU_P": ("Camas de UCI pediátrica", TEC, "Resiliencia", "Tabla 3.14"),
    "DF_BEDS_ICU|HBU_CC_A": ("Camas de cuidados críticos para adultos", TEC, "Resiliencia", "Tabla 3.14"),
    "DF_BEDS_ICU|HBO_ICU_A_GT80": ("Días con ocupación de UCI de adultos sobre 80 %", TEC, "Resiliencia", "Tabla 3.14"),
    "DF_BEDS_ICU|HBO_ICU_A_GT95": ("Días con ocupación de UCI de adultos sobre 95 %", TEC, "Resiliencia", "Tabla 3.14"),
    "DF_HOSP|H": ("Hospitales", TEC, "", "Sección 3.4.4"),
    "DF_MED_TECH|MTU": ("Disponibilidad de tecnología médica (tomógrafos, resonadores, etc.)", TEC, "", T310),
    "DF_DIAG_EXAM|EXAM": ("Exámenes diagnósticos (tomografías, resonancias, etc.)", TEC, "", T310),
    "DF_HOSP_DISCHARGE|DISCHARGE": ("Egresos hospitalarios por diagnóstico", TEC, "", T310),
    "DF_AGGR|DISCHARGE": ("Egresos hospitalarios (total)", TEC, "", T310),
    "DF_AGGR|BED_DAY": ("Días-cama hospitalarios", TEC, "", T310 + AN),
    "DF_AGGR|OCC_RATE": ("Tasa de ocupación de camas", TEC, "Resiliencia", "Tabla 3.10 y 3.14"),
    "DF_AGGR|STAY": ("Estancia hospitalaria promedio (total)", TEC, "Eficiencia", "Tabla 3.11 (subcaja: criterio propio)"),
    "DF_HOSP_AV_LENGTH|STAY": ("Estancia hospitalaria promedio por diagnóstico", TEC, "Eficiencia", "Tabla 3.11 (subcaja: criterio propio)"),
    "DF_SURG_PROC|PRC": ("Procedimientos quirúrgicos", TEC, "Eficiencia", "Tabla 3.11 (subcaja: criterio propio)"),
    "DF_HEALTH_LTCR_BED|LTCB": ("Camas en establecimientos de cuidados de largo plazo", TEC, "", T310 + AN),
    "DF_HEALTH_LTCR_FAC_OWNER|LTCB": ("Camas de cuidados de largo plazo según propiedad", TEC, "", T310 + AN),
    "DF_HEALTH_LTCR_FAC_OWNER|LTCF": ("Establecimientos de cuidados de largo plazo según propiedad", TEC, "", CP),
    "DF_PHMC_CONSUM|PH_CON": ("Consumo de medicamentos (dosis diarias definidas)", TEC, "", T310),
    "DF_PHMC_SALES|PH_SALES": ("Ventas de medicamentos", TEC, "", T310),
    "DF_GEN_MRKT|PH_MARKET": ("Participación de los genéricos en el mercado farmacéutico", TEC, "Eficiencia", "Tabla 3.10 y 3.11"),
    # ---------- Recursos: gobernanza ----------
    "DF_HSCS2023|TODAS": ("Encuesta de características de los sistemas de salud, ronda 2023", GOB, "", "Sección 3.4.6"),
    "DF_HSCS|TODAS": ("Encuesta de características de los sistemas de salud, rondas 2012-2018", GOB, "", "Sección 3.4.6"),
}

# --- Paso 6.3: tipo de fuente (quién produce el dato) ---
# Verificado en las fichas y sub-fichas metodológicas (2_fichas_metodologicas/)
ESTIMACIONES = {"DF_GHGHC": "Estimación de la OCDE",
                "DF_EXP_MORSC": "Estimación de la OCDE con datos del estudio GBD (IHME)",
                "DF_CC": "Estudio CONCORD (London School of Hygiene & Tropical Medicine)",
                "DF_C": "Estimación de la IARC (GLOBOCAN)",
                "DF_AWDI": "Estimación de la OCDE con encuestas de fuerza laboral",
                "DF_SOC_EMPLOY": "La OCDE lo toma de las cuentas nacionales",
                # Disponibilidad de alimentos: FAOSTAT para todos los países (sub-fichas 4_1 a 4_4)
                "DF_HEALTH_LVNG_FSC|CLS": "FAO (FAOSTAT)", "DF_HEALTH_LVNG_FSC|FRS": "FAO (FAOSTAT)",
                "DF_HEALTH_LVNG_FSC|FTS": "FAO (FAOSTAT)", "DF_HEALTH_LVNG_FSC|PRS": "FAO (FAOSTAT)",
                "DF_HEALTH_LVNG_FSC|SGS": "FAO (FAOSTAT)", "DF_HEALTH_LVNG_FSC|VGS": "FAO (FAOSTAT)"}
ENCUESTAS_OCDE = {"DF_PARIS": "Encuesta PaRIS de la OCDE (participación voluntaria)",
                  "DF_HSCS2023": "Encuesta HSCS de la OCDE (participación voluntaria)",
                  "DF_HSCS": "Encuesta HSCS de la OCDE (participación voluntaria)"}
def tipo_fuente(id_indicador):
    df = id_indicador.split("|")[0]
    for clave in (id_indicador, df):          # primero se busca el indicador, luego el conjunto
        if clave in ESTIMACIONES:
            return "Estimación o fuente internacional", ESTIMACIONES[clave]
    if df in ENCUESTAS_OCDE:
        return "Encuesta voluntaria de la OCDE", ENCUESTAS_OCDE[df]
    return "Reportado por el país", "Cuestionarios de OECD Health Statistics / HCQO"

# --- Paso 6.4: unir la asignación con la tabla de indicadores ---
indicadores = pd.read_csv(TABLAS / "p02_indicadores.csv")
faltan = set(indicadores["id_indicador"]) - set(ASIGNACION)
sobran = set(ASIGNACION) - set(indicadores["id_indicador"])
print("Indicadores sin asignar:", faltan or "ninguno", "| asignaciones sin indicador:", sobran or "ninguna")

# pd.DataFrame.from_dict(orient="index"): convierte el diccionario en tabla (1 fila por indicador)
asignacion = (pd.DataFrame.from_dict(ASIGNACION, orient="index",
                                     columns=["nombre_es", "subcaja", "transversales", "fuente_asignacion"])
              .rename_axis("id_indicador").reset_index())
asignacion["caja"] = asignacion["subcaja"].map(CAJA_DE_SUBCAJA)
asignacion[["tipo_fuente", "detalle_fuente"]] = asignacion["id_indicador"].map(tipo_fuente).tolist()

# .merge(): como BUSCARV en Excel; pega las columnas nuevas a cada indicador
#   Antes: 224 × 7 | Después: 224 × 14
clasificacion = indicadores.merge(asignacion, on="id_indicador", how="left")
clasificacion = clasificacion[[
    "id_indicador", "nombre_es", "nombre_en", "caja", "subcaja", "transversales",
    "fuente_asignacion", "tipo_fuente", "detalle_fuente", "conjunto", "codigo_medida",
    "conjunto_nombre_en", "subtemas_ocde", "enlaces_metodologia"]]

# --- Paso 6.5: verificar ---
print(clasificacion.shape)
print(clasificacion.groupby(["caja", "subcaja"]).size().to_string())
print(clasificacion["tipo_fuente"].value_counts().to_string())
print("Subcajas sin indicadores:", sorted(set(CAJA_DE_SUBCAJA) - set(clasificacion["subcaja"])))

clasificacion.to_csv(TABLAS / "p06_clasificacion_marco.csv", index=False, encoding="utf-8-sig")
clasificacion.to_excel(TABLAS / "p06_clasificacion_marco.xlsx", index=False)
