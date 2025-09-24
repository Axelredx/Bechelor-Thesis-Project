from pathlib import Path
import extract_msg
import sys
from utility.error_logger import Logger

##############################
# .msg (MAIL) ANALYSIS TOOLS #
##############################

class MsgAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger

    def analyze_msg(self, msg_file_path: Path, company_name: str) -> tuple[Path, dict, str]:
        msg = None
        try:
            msg = extract_msg.openMsg(msg_file_path)

            subject = msg.subject if msg.subject else "No Subject"
            body = msg.body if msg.body else "No Body"
            sender = msg.sender if msg.sender else "Unknown Sender"
            date = msg.date if msg.date else "Unknown Date"
            destination = msg.to if msg.to else "Unknown Destination"

            # simulate a json structure
            json_data = {
                "mittente": sender,
                "data": date,
                "oggetto": subject,
                "corpo": body,
                "destinazione": destination,
                "allegati": []
            }

            # search for attachments
            if hasattr(msg, 'attachments') and msg.attachments:
                for i, attachment in enumerate(msg.attachments):
                    filename = (getattr(attachment, 'longFilename', None) or 
                            getattr(attachment, 'shortFilename', None) or 
                            f"attachment_{i+1}")
                    
                    json_data["allegati"].append({
                        "filename": filename,
                        "content_type": getattr(attachment, 'contentType', 'unknown'),
                        "size": getattr(attachment, 'size', 0)
                    })

            self.logger.write_info_in_log_file(f"(at func: analyze_msg) Successfully processed .msg file {msg_file_path}\n")
            msg.close()

            return msg_file_path, json_data, company_name
        
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: analyze_msg) Error processing .msg file {msg_file_path}: {e}\n")
            return msg_file_path, {}, company_name
