from bs4 import BeautifulSoup
from fastapi import Response
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import requests
import io

def getPdf(html_content):

    soup = BeautifulSoup(html_content, "html.parser")
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                        rightMargin=72, leftMargin=72,
                        topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    for elem in soup.contents:
        if elem.name == "h1":
            story.append(Paragraph(elem.get_text(), styles["Heading1"]))
        elif elem.name == "p":
            story.append(Paragraph(elem.get_text(), styles["Normal"]))
        elif elem.name == "figure" or elem.name == "img":
            img_tag = elem.find("img")
            caption = elem.find("figcaption")
            if img_tag:
                img_data = requests.get(img_tag["src"]).content
                img_buffer = io.BytesIO(img_data)
                story.append(Image(img_buffer, width=5*inch, height=3*inch))
            if caption:
                story.append(Paragraph(caption.get_text(), styles["Italic"]))
        story.append(Spacer(1, 12))

    doc.build(story)

    buffer.seek(0)
    return Response(
        content=buffer.read(),
        media_type="application/pdf"
    )
