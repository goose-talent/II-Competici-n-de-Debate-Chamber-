import os
import re
import subprocess
import pymysql
from docx import Document
from docx.oxml.ns import qn


conn = pymysql.connect(  
    host="autorack.proxy.rlwy.net",
    port=15743,
    user="root",
    password="kLghFoiHnqHxeGFjzmmGQaqLUjrVfHBr",
    database="railway"
)
    


CARPETA_SALIDA = "Diplomas"

os.makedirs(CARPETA_SALIDA, exist_ok=True)

def limpiar_nombre(texto):
    return re.sub(r'[<>:"/\\|?*]', "_", str(texto))
def limpiar_nombre_centro_diploma(nombre):
    nombre = re.sub(r'\bceip\b', '', nombre, flags=re.IGNORECASE)
    nombre = re.sub(r'\bcolegio\b', '', nombre, flags=re.IGNORECASE)
    nombre = re.sub(r'\bde prácticas\b', '', nombre, flags=re.IGNORECASE)
    nombre = re.sub(r'\bde practicas\b', '', nombre, flags=re.IGNORECASE)
    nombre = re.sub(r'CPR INF-PRI-SEC', '', nombre, flags=re.IGNORECASE)
    nombre = re.sub(r'"', '', nombre)
    nombre = re.sub(r'\s+', ' ', nombre)
    return nombre.strip()
def rellenar_diploma(nombre, centro, plantilla, output_pdf):

    doc = Document(plantilla)

    for t in doc.element.body.iter(qn('w:t')):

        if t.text:
            if "Nombre y apellido" in t.text:
                t.text = nombre

            elif "Nombre del centro educativo" in t.text:
                t.text = limpiar_nombre_centro_diploma(centro)

    output_docx = output_pdf.replace(".pdf", ".docx")

    doc.save(output_docx)

    subprocess.run([
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        os.path.dirname(output_pdf),
        output_docx
    ])

    pdf_generado = output_docx.replace(".docx", ".pdf")

    if os.path.exists(pdf_generado):
        os.rename(pdf_generado, output_pdf)

    if os.path.exists(output_docx):
        os.remove(output_docx)

with conn.cursor() as cur:

    cur.execute("""
        SELECT
            d.nombre,
            d.apellidos,
            c.denominacion
        FROM debatientes d
        JOIN centros c
            ON d.centro = c.denominacion
    """)

    debatientes = cur.fetchall()

for nombre, apellidos, centro in debatientes:

    nombre_completo = f"{nombre} {apellidos}"

    carpeta_centro = os.path.join(
        CARPETA_SALIDA,
        limpiar_nombre(centro)
    )

    os.makedirs(carpeta_centro, exist_ok=True)

    ruta_pdf = os.path.join(
        carpeta_centro,
        f"{limpiar_nombre(nombre_completo)}.pdf"
    )

    rellenar_diploma(
        nombre_completo,
        centro,
        "diploma_participante.docx",
        ruta_pdf
    )

with conn.cursor() as cur:

    cur.execute("""
        SELECT
            p.nombre,
            c.denominacion
        FROM profesores p
        JOIN centros c
            ON p.centro_id = c.id
    """)

    profesores = cur.fetchall()

for nombre, centro in profesores:

    carpeta_centro = os.path.join(
        CARPETA_SALIDA,
        limpiar_nombre(centro)
    )

    os.makedirs(carpeta_centro, exist_ok=True)

    ruta_pdf = os.path.join(
        carpeta_centro,
        f"PROFESOR_{limpiar_nombre(nombre)}.pdf"
    )
    rellenar_diploma(
        nombre,
        centro,
        "diploma_formador.docx",
        ruta_pdf
)

conn.close()

print("PDFs generados correctamente")