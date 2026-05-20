from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from datetime import datetime
from io import BytesIO
import pandas as pd


def add_page_footer(canvas, doc):
    """
    # Add page footer: horizontal line + page number
    """
    # PDF metadata
    canvas.setAuthor("")
    canvas.setTitle("")
    canvas.setSubject("")
    
    width, height = A4

    # --- Draw horizontal line ---
    line_y = 40
    canvas.setLineWidth(0.5)
    canvas.line(30, line_y, width - 30, line_y)

    # --- Page number (bottom-right, under the line) ---
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"

    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(width - 30, 25, text)


def format_value(x):
    """
    In columns of dataframe where there are strings and numeric values,
    integers are displayed as float (e.g. 2 is shown as 2.0).
    This function helps to display integers as integer.
    """
    if isinstance(x, float):
        if x.is_integer():
            return str(int(x))  # 2.0 → "2"
    return str(x)


def df_to_table(df, hide_index=False):
    """
    Convert dataframe to table
    """
    if hide_index:
        # Don't display index
        df_reset = df.copy()
        headers = df.columns.tolist()
    else:
        # Convert index to a column
        df_reset = df.reset_index()
        # Add empty header for index column
        headers = [""] + df.columns.tolist()

    # Replace NaN with "—" WITHOUT changing numeric types
    df_reset = df_reset.where(pd.notna(df_reset), "—")

    # Format values and assemble data
    data = [headers] + df_reset.map(format_value).values.tolist()

    table = Table(data)
    table.setStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ])
    return table


def image_with_aspect(buffer, width):
    img = ImageReader(buffer)
    w, h = img.getSize()
    aspect = h / w
    return Image(buffer, width=width, height=width * aspect)


def plotly_fig_to_image(fig, width=900, height=540, scale=3):
    """
    Convert Plotly figure to PNG image buffer using Kaleido.
    """
    img_bytes = fig.to_image(format="png", engine="kaleido", 
                             width=width, height=height, 
                             scale=scale)
    return BytesIO(img_bytes)


def generate_pdf_report(
    counts_df,
    stats_df,
    centers,
    closure_dates,
    time_unit,
    hide_index,
    fig_bar,
    fig_line,
    fig_donut,
    estimation_df=None,
    metrics_func=None 
):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    # -------------------------
    # Title
    elements.append(Paragraph("Monitoring Report", styles['Title']))
    elements.append(Spacer(1, 10))

    # Date (centered)
    # Create centered style
    center_style = ParagraphStyle(
        name="Center",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor="grey"
    )
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    elements.append(Paragraph(f"Generated on: {now}", center_style))
    elements.append(Spacer(1, 20))

    # -------------------------
    # Tables
    elements.append(Paragraph("Subject Counts", styles['Heading2']))
    elements.append(df_to_table(counts_df, hide_index))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Statistical Measures", styles['Heading2']))
    elements.append(df_to_table(stats_df))
    elements.append(Spacer(1, 20))

     # -------------------------
    # Metrics
    if metrics_func is not None:
        metrics_data = []

        for center in centers:
            last, delta = metrics_func(counts_df, center, closure_dates)
            metrics_data.append([center, last, delta])

        metrics_table = Table(
            [["Center", "Last value", "Change (%)"]] + metrics_data
        )

        metrics_table.setStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ])

        elements.append(Paragraph(f"Last {time_unit.lower()} activity", styles['Heading2']))
        elements.append(metrics_table)
        elements.append(Spacer(1, 20))

    # -------------------------
    # Estimation
    if estimation_df is not None:
        elements.append(Paragraph("Estimation", styles['Heading2']))
        elements.append(df_to_table(estimation_df))
        elements.append(Spacer(1, 20))

    # -------------------------
    # Figures
    
    bar_img = plotly_fig_to_image(fig_bar)
    line_img = plotly_fig_to_image(fig_line)
    donute_img = plotly_fig_to_image(fig_donut)

    elements.append(Paragraph("Counts by Center", styles['Heading2']))
    image = image_with_aspect(bar_img, width=500)
    elements.append(image)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Cumulative Counts", styles['Heading2']))
    image = image_with_aspect(line_img, width=500)
    elements.append(image)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Total Subject Distribution", styles['Heading2']))
    image = image_with_aspect(donute_img, width=500)
    elements.append(image)
    elements.append(Spacer(1, 20))

    # -------------------------
    # Build PDF with page numbers
    doc.build(elements, onFirstPage=add_page_footer, onLaterPages=add_page_footer)

    buffer.seek(0)
    return buffer


