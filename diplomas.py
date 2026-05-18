from docxtpl import DocxTemplate
import mysql.connector
import os
import subprocess
import streamlit as st

conexion = mysql.connector.connect(
    host=st.secrets["MYSQL_HOST"],
    port=st.secrets["MYSQL_PORT"],
    user=st.secrets["MYSQL_USER"],
    password=st.secrets["MYSQL_PASSWORD"],
    database=st.secrets["MYSQL_DATABASE"]
    )

cursor = conexion.cursor(dictionary=True)

os.makedirs("diplomas", exist_ok=True)

def convertir_pdf(nombre):
    subprocess.run([
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", "diplomas",
        f"diplomas/{nombre}"
    ])

cursor.execute("SELECT nombre, apellidos, dni FROM debatientes")
debatientes = cursor.fetchall()

for p in debatientes:
    doc = DocxTemplate("DIPLOMA_DEBATIENTE.docx")

    context = {
        "nombre": f"{p['nombre']} {p['apellidos']}",
        "dni": p["dni"]
    }

    doc.render(context)

    archivo = f"diploma_{p['nombre']}_{p['apellidos']}.docx"
    doc.save(f"diplomas/{archivo}")
    convertir_pdf(archivo)

cursor.execute("SELECT tutor AS nombre_for, tutor_dni, centro FROM equipos")
formadores = cursor.fetchall()

vistos = set()

for f in formadores:
    if f["tutor_dni"] in vistos:
        continue
    vistos.add(f["tutor_dni"])

    doc = DocxTemplate("DIPLOMA_FORMADORES.docx")

    context = {
        "nombre_for": f["nombre_for"],
        "dni_for": f["tutor_dni"],
        "centro": f["centro"]
    }

    doc.render(context)

    archivo = f"diploma_formador_{f['nombre_for']}.docx"
    doc.save(f"diplomas/{archivo}")
    convertir_pdf(archivo)

print("Diplomas generados correctamente")