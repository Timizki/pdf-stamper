import os
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont

def is_text_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        if page.extract_text():
            return True
    return False

def add_text_to_pdf_page(page, text):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFillColor(red)
    can.drawString(300, 790, text)
    can.save()
    
    packet.seek(0)
    new_pdf = PdfReader(packet)
    page.merge_page(new_pdf.pages[0])
    return page

def add_text_to_image(image, text, position, color=(255, 0, 0)):
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text(position, text, fill=color, font=font)
    return image

def process_pdf(pdf_path, output_pdf_path, text):
    if is_text_pdf(pdf_path):
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            modified_page = add_text_to_pdf_page(page, f"{text}")
            writer.add_page(modified_page)

        with open(output_pdf_path, "wb") as output_pdf_file:
            writer.write(output_pdf_file)

    else:
        images = convert_from_path(pdf_path)
        temp_images = []

        for i, image in enumerate(images):
            image_with_text = add_text_to_image(image, f"{text}", (50, 50))
            temp_image_path = f"temp_page_{i+1}.png"
            image_with_text.save(temp_image_path)
            temp_images.append(temp_image_path)

        writer = PdfWriter()

        for temp_image_path in temp_images:
            img = Image.open(temp_image_path)
            packet = BytesIO()
            c = canvas.Canvas(packet, pagesize=A4)
            c.drawImage(temp_image_path, 0, 0, A4[0], A4[1])
            c.save()
            
            packet.seek(0)
            new_pdf = PdfReader(packet)
            writer.add_page(new_pdf.pages[0])
            
            os.remove(temp_image_path)

        with open(output_pdf_path, "wb") as output_pdf_file:
            writer.write(output_pdf_file)

def process_pdfs_in_directory(directory_path, output_directory, text_prefix):
    # Listaa kaikki PDF-tiedostot hakemistossa ja järjestä ne aakkosjärjestykseen
    pdf_files = sorted([f for f in os.listdir(directory_path) if f.endswith('.pdf')])

    # Luo output-hakemisto, jos sitä ei ole
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_files = []

    for i, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(directory_path, pdf_file)
        output_pdf_path = os.path.join(output_directory, f"processed-{i+1 : 04d}_{pdf_file}")
        text = f"{text_prefix} {i + 1 : 04d}"

        # Käsittele PDF-tiedosto
        process_pdf(pdf_path, output_pdf_path, text)
        output_files.append(output_pdf_path)
    
    return output_files

def merge_pdfs(pdf_files, output_pdf_path):
    pdf_writer = PdfWriter()

    for pdf_file in pdf_files:
        pdf_reader = PdfReader(pdf_file)
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
    
    with open(output_pdf_path, "wb") as output_pdf_file:
        pdf_writer.write(output_pdf_file)

# Käyttö
input_directory = "pdfs"  # Lähdehakemisto, jossa PDF-tiedostot sijaitsevat
output_directory = "processed"  # Hakemisto, johon käsitellyt tiedostot tallennetaan
final_output_path = "final_combined.pdf"  # Lopullinen yhdistetty PDF-tiedosto
text_prefix = "Lasku "

# Käsittele kaikki PDF:t hakemistossa
processed_files = process_pdfs_in_directory(input_directory, output_directory, text_prefix)

# Yhdistä kaikki käsitellyt PDF-tiedostot yhdeksi PDF:ksi
merge_pdfs(processed_files, final_output_path)

print(f"Yhdistetty PDF-tiedosto tallennettu: {final_output_path}")
