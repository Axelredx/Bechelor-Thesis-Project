
from pypdf import PdfReader, PdfWriter
import base64
from pathlib import Path
import sys
from utility.error_logger import Logger

######################
# PDF ANALYSIS TOOLS #
######################

class PDFAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger

    '''check if a pdf file has too many pages'''
    def __check_pdf_pages_number(self, file_path: Path) -> bool:
        try:
            pdf_reader = PdfReader(file_path)
            if len(pdf_reader.pages) > 10:
                return True
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: __check_pdf_pages_number) Error reading PDF {file_path}: {e}\n")
        return False

    '''if pdf has > 10 pages, creates a copy with only 10 page to send to Claude'''
    def __chop_pdf_pages(self, file_path: Path) -> Path:
        try:
            too_big_pdf = PdfReader(file_path)
            chopped_pdf = PdfWriter()
            # keep only the first 10 pages
            for page in too_big_pdf.pages[:10]:  
                chopped_pdf.add_page(page)
            # save the reduced PDF
            reduced_file_path = file_path.with_name(f"{file_path.stem}_reduced{file_path.suffix}")
            with open(reduced_file_path, 'wb') as f:
                chopped_pdf.write(f)

            self.logger.write_info_in_log_file(f"(at func: __chop_pdf_pages) Successfully chopped PDF {file_path} to {reduced_file_path}\n")
            return reduced_file_path
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: __chop_pdf_pages) Error chopping PDF {file_path}: {e}\n")

        return file_path

    '''encode and returns the classification response from Claude of pdf files'''
    def analyze_pdf(self, pdf_file_path: Path, company_name: str) -> tuple[Path, str, str, bool]:
        # 1st: encode
        try:
            # if the pdf has more than 10 pages, chop it and encode the first 10 pages
            if self.__check_pdf_pages_number(pdf_file_path):
                chopped_pdf_file_path = self.__chop_pdf_pages(pdf_file_path)
                with open(chopped_pdf_file_path, 'rb') as pdf_file:
                    pdf_data = pdf_file.read()
                    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            else:
                with open(pdf_file_path, 'rb') as pdf_file:
                    pdf_data = pdf_file.read()
                    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')

        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: analyze_pdf) Error encoding PDF file {pdf_file_path}: {e}\n")
            return pdf_file_path, "", company_name, False

        #2nd: return info to forward to claude
        try:
            self.logger.write_info_in_log_file(f"(at func: analyze_pdf) Successfully encoded PDF file {pdf_file_path}, forwarding to Claude\n")

            # check if forward chopped pd to claude:
            if self.__check_pdf_pages_number(pdf_file_path):
                return chopped_pdf_file_path, pdf_base64, company_name, True
            else:
                return pdf_file_path, pdf_base64, company_name, False

        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: __analyze_pdf) Error sending PDF file {pdf_file_path} to Claude: {e}\n")
            return pdf_file_path, "", company_name, False