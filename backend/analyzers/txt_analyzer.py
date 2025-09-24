from pathlib import Path
import sys
from utility.error_logger import Logger

#####################################
# TEXT (.txt, .text) HANDLING TOOLS #
#####################################

class TxtAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger

    '''analyze text files and send to claude for classification'''
    def analyze_text(self, text_file_path: Path, company_name: str) -> tuple[Path, str, str]:
        try:
            with open(text_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                content_to_send = content[:10000]
            
            self.logger.write_info_in_log_file(f"(at func: analyze_text) Successfully processed text file {text_file_path}\n") 

            return text_file_path, content_to_send, company_name
        
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: analyze_text) Error processing text file {text_file_path}: {e}\n")
            return text_file_path, "", company_name