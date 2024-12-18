import os
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import logging
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_text_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    page = reader.pages[0]
    if page.extract_text():
       return True
    return False

def add_text_to_pdf_page(page, text):
    try:
        packet = BytesIO()
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        can = canvas.Canvas(packet, pagesize=(width, height))
        # can = canvas.Canvas(packet, pagesize=A4)
        can.setFillColor(red)
        can.setFont("Helvetica", 16)
        x = width * 0.2  # 20% from left
        y = height * 0.80  # 95% from bottom
        #can.drawString(200, 790, text)
        can.drawString(x, y, text)
        can.save()
        
        packet.seek(0)
        new_pdf = PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        return page
    except Exception as e:
        logger.error(f"Error adding text to PDF page: {str(e)}")
        raise

def add_text_to_image(image, text, position, color=(255, 0, 0)):
    try: 
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", 20) 
        except OSError:
            logger.warning("Arial font not found, using default font")
            font = ImageFont.load_default()
        draw.text(position, text, fill=color, font=font)
        return image
    except Exception as e:
        logger.error(f"Error adding text to image: {str(e)}")
        raise

def image_to_pdf_stream(image):
    try:
        # Convert image to PDF format and return a BytesIO stream
        pdf_stream = BytesIO()
        image.save(pdf_stream, format='PDF')
        pdf_stream.seek(0)
        return pdf_stream
    except Exception as e:
        logger.error(f"Error converting image to PDF stream: {str(e)}")
        raise

def process_pdf(pdf_path, text, writer):
    if not os.path.exists(pdf_path):
     raise FileNotFoundError(f"Input PDF file not found: {pdf_path}")

    try:
        if is_text_pdf(pdf_path):            
            reader = PdfReader(pdf_path)

            for i, page in enumerate(reader.pages):
                if i == 0:                    
                    page_copy = writer.add_blank_page(
                        width=page.mediabox.width,
                        height=page.mediabox.height
                    )
                    page_copy.merge_page(page)
                    
                    modified_page = add_text_to_pdf_page(page, f"{text}")
                    writer.add_page(modified_page)
                else:
                    writer.add_page(page)
        else:            
            images = convert_from_path(pdf_path)

            for i, image in enumerate(images):
                page_to_add = None
                if i == 0:                 
                  page_to_add = add_text_to_image(image, f"{text}", (790, 50))
                else:
                    page_to_add = image

                image_pdf_stream = image_to_pdf_stream(page_to_add)
                new_pdf = PdfReader(image_pdf_stream)
                writer.add_page(new_pdf.pages[0])       
        logger.info(f"Successfully processed PDF: {pdf_path}")
        
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        raise

def process_pdfs_in_directory(directory_path, text_prefix, offset=0):
    
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Input directory not found: {directory_path}")

    try:
        pdf_files = sorted([f for f in os.listdir(directory_path) if f.endswith('.pdf')])
        
        if not pdf_files:
            logger.warning(f"No PDF files found in directory: {directory_path}")
            return []
        
        total_files = len(pdf_files)
        successful_files = total_files        
        
        writer = PdfWriter()        
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                pdf_path = os.path.join(directory_path, pdf_file)                
                text = f"{text_prefix} {offset + i + 1 : 04d}"               
                
                process_pdf(pdf_path, text, writer)
                
            except Exception as e:
                successful_files -= 1 
                logger.error(f"Error processing {pdf_file}: {str(e)}")
                continue        
        logger.info(f"Successfully processed {successful_files} out of {total_files} files")

        return successful_files, writer
    except Exception as e:
        logger.error(f"Error processing directory {directory_path}: {str(e)}")
        raise

def merge_pdfs(output_pdf_path, writer):
    try:       
        with open(output_pdf_path, "wb") as output_pdf_file:
            writer.write(output_pdf_file)
            output_pdf_file.flush()
            os.fsync(output_pdf_file.fileno())
        logger.info(f"Successfully merged PDFs into: {output_pdf_path}")
    
    except Exception as e:
        logger.error(f"Error merging PDFs: {str(e)}")
        raise

def cleanup_directory(directory_path):
    """Clean up all files in the specified directory and remove the directory itself."""
    try:
        if os.path.exists(directory_path):
            for file in os.listdir(directory_path):
                file_path = os.path.join(directory_path, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    logger.debug(f"Removed temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Error while deleting file {file_path}: {str(e)}")
            
            os.rmdir(directory_path)
            logger.info(f"Cleaned up temporary directory: {directory_path}")
    except Exception as e:
        logger.error(f"Error cleaning up directory {directory_path}: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='Process PDF files with numbering offset')
        parser.add_argument('--offset', type=int, default=0, 
                          help='Starting number offset for PDF numbering (default: 0)')
        args = parser.parse_args()

        input_directory = "pdfs"  # Lähdehakemisto, jossa PDF-tiedostot sijaitsevat   
        current_date = datetime.now().strftime("%Y-%m-%d")     
        final_output_path = f"yhdistetyt_laskut_{current_date}.pdf"  # Lopullinen yhdistetty PDF-tiedosto
        text_prefix = "Lasku "
    
        successful_count, writer = process_pdfs_in_directory(input_directory, text_prefix, args.offset)

        
        merge_pdfs(final_output_path, writer)
        print(f"Combined PDF file saved: {final_output_path}")
        print(f"Successfully processed {successful_count} files")
        
        if successful_count == 0:
            print("Warning: No files were processed successfully!")     
           
    except Exception as e:
        logger.error(f"Program failed: {str(e)}")
        print(f"An error occurred: {str(e)}")        