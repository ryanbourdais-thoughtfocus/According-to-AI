import os
from fpdf import FPDF
import json
from .orderfunction import generate_order_id

count_file = "report_count.json"
class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Analysis Report", align="C", ln=True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_title(self, title):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, title, align="C", ln=True)
        self.ln(10)

    def add_paragraph(self, text, bold= False, underline = False, same_line = False):
        style = "" 
        if bold: 
            style += "B"

        if underline:
            style += "U"  
        self.set_font("Arial", style, 12)
        self.multi_cell(0, 10, text)
        self.ln(10)

    def add_table(self, data):
        self.set_font("Arial", "B", 12)
        col_widths = [30, 100, 30]
        headers = ["Item", "Description", "Price"]

        # Header row
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, border=1, align="C")
        self.ln()

        # Table rows
        self.set_font("Arial", "", 12)
        for row in data:
            for i, item in enumerate(row):
                self.cell(col_widths[i], 10, item, border=1, align="C")
            self.ln()

def create_pdf_report(parsed_data = None):
    pdf = PDFReport()
    pdf.add_page()

    # Title
    pdf.add_title("Client Sentiment Analysis")

    # Body text
    
    order_id = generate_order_id()

    order_text = ("Report Id: " + order_id )
    pdf.add_paragraph(order_text)


    insertIntoPDF(parsed_data, pdf)        
    # Save the PDF
    file_name = order_id + ".pdf"
    pdf.output("storedPDF/"+file_name)

    print(f"PDF generated and saved as '{file_name}'")
    return file_name;

def load_report_count():
    if os.path.exists(count_file):
        with open(count_file, "r") as f:
            return json.load(f)
    return {}

def insertIntoPDF(dictValues, pdfreport) :
    for key, value in dictValues.items() :
        if isinstance(value, dict): 
            pdfreport.add_paragraph(f"{key.capitalize()}:", bold = True, underline = True)
            insertIntoPDF(value, pdfreport)
        else :  
            pdfreport.add_paragraph(f"{key.capitalize()}:", bold = True)
            pdfreport.add_paragraph(f"{value}")
