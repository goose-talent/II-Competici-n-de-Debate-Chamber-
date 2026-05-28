import os
import re
import subprocess

import mysql.connector
from docx import Document
from docx.oxml.ns import qn
from PyPDF2 import PdfMerger
from docx.shared import Pt

PLANTILLA = "gafete_plantilla_nuevo.docx"
CARPETA_SALIDA = "gafetes"

SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

os.makedirs(CARPETA_SALIDA, exist_ok=True)

def calcular_tamano(nombre):
    n = len(nombre)

    if n <= 12:
        return 36
    elif n <= 18:
        return 32
    elif n <= 24:
        return 28
    elif n <= 30:
        return 24
    else:
        return 20
def partir_nombre(nombre):

    palabras = nombre.split()

    if len(palabras) <= 2:
        return nombre

    mitad = len(palabras) // 2

    return (
        " ".join(palabras[:mitad])
        + "\n" +
        " ".join(palabras[mitad:])
    )
def limpiar_nombre_centro(nombre):
    nombre = re.sub(r'\bceip\b', '', nombre, flags=re.IGNORECASE)
    nombre = re.sub(r'\bcolegio\b', '', nombre, flags=re.IGNORECASE)
    nombre = re.sub(r'\bde prácticas\b', '', nombre, flags=re.IGNORECASE)
    nombre = re.sub(r'\bde practicas\b', '', nombre, flags=re.IGNORECASE)

    nombre = re.sub(r'\s+', ' ', nombre)

    return nombre.strip()
def rellenar_gafete(nombre_centro, output_path):

    doc = Document(PLANTILLA)
    nombre_centro = limpiar_nombre_centro(nombre_centro)

    sz = calcular_tamano(nombre_centro)

    body = doc.element.body

    for t in body.iter(qn('w:t')):
        if t.text and 'NOMBRE DEL CENTRO' in t.text:

            t.text = nombre_centro.upper()

            r = t.getparent()

            rPr = r.find(qn('w:rPr'))

            if rPr is None:
                from docx.oxml import OxmlElement
                rPr = OxmlElement('w:rPr')
                r.insert(0, rPr)

            sz_elem = rPr.find(qn('w:sz'))

            if sz_elem is None:
                from docx.oxml import OxmlElement
                sz_elem = OxmlElement('w:sz')
                rPr.append(sz_elem)

            sz_elem.set(qn('w:val'), str(sz * 2))

    doc.save(output_path)

conn = mysql.connector.connect(
    host="autorack.proxy.rlwy.net",
    port=15743,
    user="root",
    password="kLghFoiHnqHxeGFjzmmGQaqLUjrVfHBr",
    database="railway"
)

cursor = conn.cursor()

cursor.execute("""
SELECT DISTINCT nombre_equipo
FROM equipos
WHERE nombre_equipo IS NOT NULL
  AND nombre_equipo <> ''
ORDER BY nombre_equipo
""")

nombres = [fila[0] for fila in cursor.fetchall()]

cursor.close()
conn.close()

nombres.extend([
    "STAFF",
    "JUEZ"
])

pdfs_generados = []

for nombre in nombres:

    nombre_archivo = re.sub(
        r'[<>:"/\\|?*]',
        '_',
        nombre
    )

    docx_path = os.path.join(
        CARPETA_SALIDA,
        f"{nombre_archivo}.docx"
    )

    pdf_path = os.path.join(
        CARPETA_SALIDA,
        f"{nombre_archivo}.pdf"
    )

    rellenar_gafete(
        nombre,
        docx_path
    )

    subprocess.run(
        [
            SOFFICE,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            CARPETA_SALIDA,
            docx_path
        ],
        check=True
    )

    if os.path.exists(pdf_path):
        pdfs_generados.append(pdf_path)

    print(f"OK -> {nombre}")

if pdfs_generados:

    merger = PdfMerger()

    for pdf in pdfs_generados:
        merger.append(pdf)

    pdf_final = os.path.join(
        CARPETA_SALIDA,
        "gafetes_todos.pdf"
    )

    merger.write(pdf_final)
    merger.close()

    print(f"PDF final creado: {pdf_final}")

print("Proceso terminado")
        
        