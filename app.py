# app.py
import io
from math import pi
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Kružnice — rozmístění bodů", layout="centered")

st.title("Kružnice — rozmístění bodů (Streamlit)")

# --- UI: vstupy ---
with st.sidebar:
    st.header("Parametry úlohy")
    center_x = st.number_input("Střed: x", value=0.0, step=0.5, format="%.3f")
    center_y = st.number_input("Střed: y", value=0.0, step=0.5, format="%.3f")
    radius = st.number_input("Poloměr r", value=50.0, min_value=0.0, step=0.5, format="%.3f")
    n_points = st.number_input("Počet bodů (n)", value=12, min_value=1, step=1)
    point_color = st.color_picker("Barva bodů", value="#ff5722")
    point_size = st.number_input("Velikost bodu (px)", value=6, min_value=1)
    start_angle = st.number_input("Počáteční úhel (°)", value=0.0, format="%.3f")
    units = st.text_input("Jednotky os", value="m")
    show_grid = st.checkbox("Zobrazit mřížku", value=True)

    st.markdown("---")
    st.header("Export / autor")
    # >>> Předvyplněno jméno a kontakt autora <<<
    author = st.text_input("Jméno autora", value="Tomáš Paluch")
    contact = st.text_input("Kontakt (email/telefon)", value="tomikpaluch@gmail.com")

st.markdown(
    "Nastav parametry vlevo a klikni **Vykreslit**. Stáhnout můžeš PNG, SVG a PDF (PDF obsahuje parametry a autora/kontakt)."
)

if st.button("Vykreslit"):
    st.experimental_rerun()

# --- Vykreslení pomocí matplotlib ---
def create_figure(cx, cy, r, n, color, psize, start_deg, units_label, show_grid_flag):
    fig, ax = plt.subplots(figsize=(8, 6))
    start_rad = np.deg2rad(start_deg)
    angles = start_rad + np.linspace(0, 2 * pi, int(n), endpoint=False)
    xs = cx + r * np.cos(angles)
    ys = cy + r * np.sin(angles)

    circle = plt.Circle((cx, cy), r, fill=False, linewidth=1, color="#0b1220")
    ax.add_patch(circle)

    ax.scatter(xs, ys, s=(psize ** 2), color=color, edgecolors="black", linewidths=0.4, zorder=3)
    for i, (x, y) in enumerate(zip(xs, ys), start=1):
        ax.text(x + psize * 0.8, y + psize * 0.3, str(i), fontsize=9, zorder=4)

    lim_margin = max(20, r * 0.2)
    xmin = min(cx - r, cx) - lim_margin
    xmax = max(cx + r, cx) + lim_margin
    ymin = min(cy - r, cy) - lim_margin
    ymax = max(cy + r, cy) + lim_margin

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal", adjustable="box")

    if show_grid_flag:
        ax.grid(True, which="major", linestyle="--", linewidth=0.6)

    x_ticks = ax.get_xticks()
    y_ticks = ax.get_yticks()
    ax.set_xticklabels([f"{t:g} {units_label}" if units_label else f"{t:g}" for t in x_ticks])
    ax.set_yticklabels([f"{t:g} {units_label}" if units_label else f"{t:g}" for t in y_ticks])

    ax.axhline(0, color="#64748b", linewidth=1)
    ax.axvline(0, color="#64748b", linewidth=1)

    ax.set_xlabel(f"x [{units_label}]" if units_label else "x")
    ax.set_ylabel(f"y [{units_label}]" if units_label else "y")
    ax.set_title("Kružnice a rozmístěné body")

    plt.tight_layout()
    return fig

fig = create_figure(center_x, center_y, radius, n_points, point_color, point_size, start_angle, units, show_grid)
st.pyplot(fig)

# --- Export soubory ---
buf_png = io.BytesIO()
fig.savefig(buf_png, format="png", dpi=200)
buf_png.seek(0)

buf_svg = io.BytesIO()
fig.savefig(buf_svg, format="svg")
buf_svg.seek(0)

# PDF export
def create_pdf_bytes(img_bytes_io, params: dict):
    buffer = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=(width, height))

    # Nadpis
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, height - 40, "Kružnice — vykreslení bodů")

    # Autor + kontakt
    c.setFont("Helvetica", 10)
    c.drawString(30, height - 58, f"Autor: {params.get('author','—')}    Kontakt: {params.get('contact','—')}")

    # Obrázek
    img = Image.open(img_bytes_io)
    img_w, img_h = img.size
    max_w = width - 60
    max_h = height - 140
    ratio = min(max_w / img_w, max_h / img_h)
    render_w = img_w * ratio
    render_h = img_h * ratio
    x = (width - render_w) / 2
    y = (height - render_h) / 2 - 20
    img_reader = ImageReader(img)
    c.drawImage(img_reader, x, y, width=render_w, height=render_h)

    # Druhá stránka s parametry
    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 40, "Parametry úlohy")
    c.setFont("Helvetica", 10)
    line_y = height - 70
    step = 18
    entries = [
        ("Střed (x,y)", f"{params.get('center_x','')} , {params.get('center_y','')} {params.get('units','')}"),
        ("Poloměr r", f"{params.get('radius','')} {params.get('units','')}"),
        ("Počet bodů n", f"{params.get('n_points','')}"),
        ("Počáteční úhel", f"{params.get('start_angle','')} °"),
        ("Barva bodů", f"{params.get('point_color','')}"),
        ("Velikost bodu (px)", f"{params.get('point_size','')}"),
    ]
    for k, v in entries:
        c.drawString(40, line_y, f"{k}: {v}")
        line_y -= step

    # pevná poznámka s podpisem
    c.drawString(30, line_y - 20, "© Tomáš Paluch, 2025 — tomikpaluch@gmail.com")
    c.save()
    buffer.seek(0)
    return buffer

pdf_bytes_io = io.BytesIO(buf_png.getvalue())
pdf_buffer = create_pdf_bytes(pdf_bytes_io, {
    "author": author,
    "contact": contact,
    "center_x": center_x,
    "center_y": center_y,
    "radius": radius,
    "n_points": n_points,
    "start_angle": start_angle,
    "point_color": point_color,
    "point_size": point_size,
    "units": units,
})

st.download_button("Stáhnout PNG", data=buf_png.getvalue(), file_name="kruznice_vykresleni.png", mime="image/png")
st.download_button("Stáhnout SVG", data=buf_svg.getvalue(), file_name="kruznice_vykresleni.svg", mime="image/svg+xml")
st.download_button("Stáhnout PDF", data=pdf_buffer.getvalue(), file_name="kruznice_vykresleni.pdf", mime="application/pdf")

# --- Info ---
with st.expander("Info o aplikaci a použité technologie (klikni pro otevření)"):
    st.markdown("""
    **Popis:** Aplikace vykreslí kružnici a rovnoměrně rozmístěné body podle zadaných parametrů.
    
    **Použité technologie:**
    - Streamlit (web app)
    - Matplotlib, NumPy pro vykreslení
    - Pillow (PIL) pro práci s obrázky
    - ReportLab pro generování PDF

    **Export:**
    - PNG (bitmapa)
    - SVG (vektor)
    - PDF (PDF obsahuje vložené PNG a stránku s parametry + podpis autora)
    """)

if st.checkbox("Ukázat tabulku souřadnic bodů"):
    start_rad = np.deg2rad(start_angle)
    angles = start_rad + np.linspace(0, 2 * pi, int(n_points), endpoint=False)
    xs = center_x + radius * np.cos(angles)
    ys = center_y + radius * np.sin(angles)
    import pandas as pd
    df = pd.DataFrame({"index": np.arange(1, int(n_points) + 1), "x": np.round(xs, 6), "y": np.round(ys, 6)})
    st.dataframe(df)
