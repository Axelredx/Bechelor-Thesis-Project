import email
from email import policy
from email.parser import BytesParser
from pathlib import Path
from utility.error_logger import Logger

###############################
# .eml (EMAIL) ANALYSIS TOOLS #
###############################

class EmlAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger

    '''analyze eml files and send to claude for classification'''
    def analyze_eml(self, eml_file_path: Path, company_name: str) -> tuple[Path, dict, str]:
        try:
            with open(eml_file_path, 'rb') as file:
                msg = BytesParser(policy=policy.default).parse(file)

                # 1st Extract main information
                subject = msg.get('Subject', 'Nessun oggetto')
                sender = msg.get('From', 'Mittente sconosciuto')
                date = msg.get('Date', 'Data sconosciuta')

                # 2nd Extract body content
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body += part.get_content()
                        elif part.get_content_type() == "text/html" and not body:
                            # use HTML content if no plain text is available
                            body += part.get_content()
                else:
                    body = msg.get_content()

                content_to_send = {
                    "mittente": sender,
                    "data": date,
                    "oggetto": subject,
                    "corpo": body
                }

                self.logger.write_info_in_log_file(f"(at func: analyze_eml) Successfully processed .eml file {eml_file_path}\n")
                return eml_file_path, content_to_send, company_name
            
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: analyze_eml) Error reading EML file {eml_file_path}: {e}\n")
            return "", {}, company_name