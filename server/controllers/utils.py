import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from typing import List
import sys
from utility.error_logger import Logger
from utility.ocr import OCR
import hashlib
import mimetypes
import datetime
import json
from models.document import DocumentModel

class Utils:
    def  __init__(self) -> None:
        self.logger = Logger()
    
    # return True if file with same hash exists in db, else False
    def check_file_in_db(self, file_path: Path) -> bool:
        try:
            with open(file_path, 'rb') as f:
                binary_file_content = f.read()
            file_hash = hashlib.md5(binary_file_content).hexdigest()
            if DocumentModel.objects(file_hash=file_hash).first():
                self.logger.write_info_in_log_file(f"(WARNING) File already exists in DB: {file_path.name}")
                return True
            return False
        except Exception as e:
            self.logger.write_error_in_log_file(f"Error checking file in DB: {e}")
            return False