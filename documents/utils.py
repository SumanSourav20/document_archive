import subprocess
import os

def convert_to_pdf(input_path, output_pdf_path):
    subprocess.run([
        "libreoffice", "--headless", "--convert-to", "pdf", "--outdir",
        os.path.dirname(output_pdf_path), input_path
    ], check=True)

def convert_pdf_to_pdfa(input_pdf, output_pdfa):
    subprocess.run([
        "gs",
        "-dPDFA=3",  # PDF/A-2, change to 1 or 3 if needed
        "-dBATCH",
        "-dNOPAUSE",
        "-dNOOUTERSAVE",
        "-sProcessColorModel=DeviceRGB",
        "-sDEVICE=pdfwrite",
        "-sPDFACompatibilityPolicy=1",
        f"-sOutputFile={output_pdfa}",
        input_pdf
    ], check=True)
