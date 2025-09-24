from docx import Document
from pathlib import Path
import sys
from utility.error_logger import Logger

###################################
# DOCUMENT (.docx) HANDLING TOOLS #
###################################

class DocxAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger

    '''analyze docx files and send to claude for classification (NOTE: .doc will fail)'''
    def analyze_docx(self, docx_file_path: Path, company_name: str) -> tuple[Path, str, str]:
        try:
            doc = Document(docx_file_path.name)
            doc_content = []

            # 1st extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    doc_content.append(paragraph.text.strip())

            # 2nd extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            doc_content.append(cell.text.strip())

            content_to_send = "\n".join(doc_content)
            self.logger.write_info_in_log_file(f"(at func: analyze_docx) Successfully processed .docx file {docx_file_path}\n")

            # Limit content length to 10000 characters (optimization purpose)
            return docx_file_path, content_to_send[:10000], company_name
        
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: analyze_docx) Error processing .docx file {docx_file_path}: {e}\n")
            return docx_file_path, "", company_name