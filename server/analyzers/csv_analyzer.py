from pathlib import Path
import sys
import csv
from utility.error_logger import Logger

#######################
# .csv HANDLING TOOLS #
#######################

class CsvAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger

    '''analyze CSV files and send to claude for classification'''
    def analyze_csv(self, csv_file_path: Path, company_name: str) -> tuple[Path, str, str]:
        try:
            with open(csv_file_path.name, 'r', encoding='utf-8', newline='') as file:
                csv_reader = csv.reader(file)
                content = []
                for row in csv_reader:
                    content.append(','.join(row))

                content_to_send = '\n'.join(content)
                
            self.logger.write_info_in_log_file(f"(at func: analyze_csv) Successfully processed .csv file {csv_file_path}\n")

            # Limit content length to 10000 characters (optimization purpose)
            return csv_file_path, content_to_send[:10000], company_name
        
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: analyze_csv) Error processing .csv file {csv_file_path}: {e}\n")
            return csv_file_path, "", company_name