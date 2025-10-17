import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Tuple
import sys
from utility.error_logger import Logger
from utility.ocr import OCR
from utility.benchmarker import TimeEstimator
from analyzers.pdf_analyzer import PDFAnalyzer
from analyzers.msg_analyzer import MsgAnalyzer
from analyzers.eml_analyzer import EmlAnalyzer
from analyzers.xls_analyzer import ExcelAnalyzer
from analyzers.img_analyzer import ImgAnalyzer
from analyzers.docx_analyzer import DocxAnalyzer
from analyzers.csv_analyzer import CsvAnalyzer
from analyzers.txt_analyzer import TxtAnalyzer
from .claude_info_extractor import ClaudeInfoExtractor
from controllers.file_operations import FileOperations
from .claude_db_contexter import ClaudeQueryCreator
from controllers.utils import Utils
from models.document import DocumentModel
from models.file_categories import FileCategory
from controllers.doc_category_operations import DocCategoryOperations


# .env variables
try:
    load_dotenv()
except Exception as e:
    raise e

class ClaudeDocClassificator:
    def __init__(self, script_path: Path = None):
        self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        try:
            self.client = anthropic.Anthropic(
                api_key = self.claude_api_key,
            )
        except anthropic.AuthenticationError:
            raise Exception("Auth Error: check API key")

        # decide wich version of the claude model to use
        self.claude_model = "claude-3-5-haiku-20241022"

        # locate script path & build relative paths
        if script_path is None:
            script_path = Path(__file__)

        self.script_dir = script_path.parent
        self.path_DUMP = self.script_dir.parent / "DUMP"

        # Dict of company info: {"company_name": str, "id": str}
        self.company_dict = {}
        
        #doc types & descriptions
        self.doc_type = ""
        self.doc_type_descr = ""

        # UTILITY
        self.logger = Logger()
        # (benchmark uses)
        self.token_counter = OCR(self.logger)
        self.time_estimator = TimeEstimator()

        # ANALYZERS
        self.pdf_analyzer = PDFAnalyzer(self.logger)
        self.msg_analyzer = MsgAnalyzer(self.logger)
        self.eml_analyzer = EmlAnalyzer(self.logger)
        self.xls_analyzer = ExcelAnalyzer(self.logger)
        self.img_analyzer = ImgAnalyzer(self.logger)
        self.docx_analyzer = DocxAnalyzer(self.logger)
        self.csv_analyzer = CsvAnalyzer(self.logger)
        self.txt_analyzer = TxtAnalyzer(self.logger)
        
        # OTHER
        self.claude_extractor = ClaudeInfoExtractor(self.logger)
        self.file_ops = FileOperations()
        self.db_context_creator = ClaudeQueryCreator()
        self.utils = Utils()
        self.doc_category_ops = DocCategoryOperations()

    #################################
    #### DIRECTORY HANDLING TOOLS ###
    #################################

    '''return true if directory exists'''
    def check_dir_exists(self, path: Path) -> bool:
        return path.exists() and path.is_dir()

    '''return true if directory has files'''
    def dir_has_files(self, path: Path) -> tuple[bool, int]:
        try:
            count = 0
            for item in path.iterdir():
                if item.is_file():
                    count += 1
        except Exception as e:
            self.logger.write_warning_in_log_file(f"(at func: dir_has_files) Error checking directory {path} for files: {e}")
        return count > 0, count

    '''check if directory exists, if not create it'''
    def __check_for_dir_or_create(self, path: Path) -> Path:
        try:
            if not self.check_dir_exists(path):
                self.logger.write_info_in_log_file(f"(at func: __check_for_dir_or_create) Directory {path} does not exist. Creating it...")
                path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: __check_for_dir_or_create) Error checking or creating directory {path}: {e}")
        return path

    '''moves files between directories'''
    def move_files(self, src: Path, dest: Path, file_name: str) -> None:
        try:
            for item in src.iterdir():
                if item.is_file() and item.name == file_name:
                    item.rename(dest / item.name)
            has_files, file_count = self.dir_has_files(dest)
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: move_files) Error moving file {file_name} from {src} to {dest}: {e}")

    '''formatting file type name (e.g. 'fatture telefoniche' -> 'fatture-telefoniche')'''
    def __format_text(self, text: str) -> str:
        return text.replace(" ", "-")
    
    ###############################
    # GENERAL PREPROCESSING TOOLS #
    ###############################

    '''returns true if file is compatible with analyzation system, based on its extension'''
    def __is_file_considerable(self, file_path: Path) -> bool:
        if not file_path.exists():
            self.logger.write_warning_in_log_file(f"(at func: __is_file_considerable) File {file_path} does not exist.")
            return False

        # Check if file is in the list of supported types
        supported_extensions = ['.pdf', '.msg', '.eml', '.xls', '.xlsx', '.xlsm', '.xlsb', '.odf', '.ods', '.odt',
                                '.jpg', '.jpeg', '.png', '.gif', '.docx', '.csv', '.txt', '.text']
        if file_path.suffix.lower() not in supported_extensions:
            return False

        return True

    '''returns the content of a file based on its type extension'''
    def __analyze_file(self, file_path: Path, file_extension: str, company_name: str) -> Tuple[str, str]:

        response = "ERROR"
        # 'normalize' file extension
        file_extension = file_extension.lower()

        if file_extension == '.pdf':
            pdf_path, pdf_base64, pdf_company_name, is_chopped = self.pdf_analyzer.analyze_pdf(file_path, company_name)
            response, file_encoded = self.__claude_response(pdf_path, pdf_base64, pdf_company_name)
            if is_chopped:
                # if the pdf forwarded was chopped, delete the chopped file
                pdf_path.unlink(missing_ok=True)

        elif file_extension == '.msg':
            msg_path, msg_data, msg_company_name = self.msg_analyzer.analyze_msg(file_path, company_name)
            response, file_encoded = self.__claude_response(msg_path, msg_data, msg_company_name)

        elif file_extension == '.eml':
            eml_path, eml_data, eml_company_name = self.eml_analyzer.analyze_eml(file_path, company_name)
            response, file_encoded = self.__claude_response(eml_path, eml_data, eml_company_name)

        elif file_extension in ['.xls', '.xlsx', '.xlsm', 
                                '.xlsb', '.odf', '.ods', '.odt']:
            xls_path, xls_data, xls_company_name = self.xls_analyzer.analyze_excel(file_path, company_name)
            response, file_encoded = self.__claude_response(xls_path, xls_data, xls_company_name)

        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            img_path, img_base64, img_company_name = self.img_analyzer.analyze_image(file_path, company_name)
            response, file_encoded = self.__claude_response(img_path, img_base64, img_company_name)

        elif file_extension == '.docx':
            docx_path, docx_content, docx_company_name = self.docx_analyzer.analyze_docx(file_path, company_name)
            response, file_encoded = self.__claude_response(docx_path, docx_content, docx_company_name)

        elif file_extension == '.csv':
            csv_path, csv_content, csv_company_name = self.csv_analyzer.analyze_csv(file_path, company_name)
            response, file_encoded = self.__claude_response(csv_path, csv_content, csv_company_name)

        elif file_extension in ['.txt', '.text']:
            txt_path, txt_content, txt_company_name = self.txt_analyzer.analyze_text(file_path, company_name)
            response, file_encoded = self.__claude_response(txt_path, txt_content, txt_company_name)

        return response, file_encoded

    '''given a file Claude classifies it and moves it to the corresponding directory'''
    def preprocess_file(self) -> str:
        # start timer estimation (benchmark uses)
        self.time_estimator.start_counting_time()

        for item in self.path_DUMP.iterdir():
            if self.__is_file_considerable(item):
                # skip analysis if already in db
                if self.utils.check_file_in_db(item):
                    continue

                #1st obtain file extension type
                file_name, file_extension = os.path.splitext(item.name)
                self.logger.write_info_in_log_file(f"(at func: preprocess_file) Processing file: {file_name} with extension {file_extension}")

                #2nd get classification from claude based on its extension
                company_name = "company_name"
                claude_classification_response, file_encoded = self.__analyze_file(item, file_extension, company_name)
                self.logger.write_info_in_log_file(f"(at func: preprocess_file) Claude's response about {company_name} document: {claude_classification_response}")

                claude_info_extracted, exact_time = self.claude_extractor.claude_extract_info(item, file_encoded, claude_classification_response)
                # create/update the db context with the new info extracted
                self.db_context_creator.create_db_context(claude_info_extracted)

                #3rd upload file to DB
                upload_code = self.file_ops.upload_to_db(item, claude_classification_response, claude_info_extracted, exact_time)

                #4th delete file in DUMP folder
                if upload_code == 1:
                    item.unlink(missing_ok=True)
                    self.logger.write_info_in_log_file(f"(at func: preprocess_file) Deleted file {item.name} from DUMP folder after successful upload.")
                else:
                    self.logger.write_warning_in_log_file(f"(at func: preprocess_file) File {item.name} not deleted from DUMP folder due to upload error.")

                # update total operations counter (benchmark uses)
                self.time_estimator.total_operations += 1


        # stop timer estimation (benchmark uses)
        self.time_estimator.estimate_total_time_and_op()

    ##########################
    # CLAUDE HANDLING TOOLS  #
    ##########################

    '''Claude file evaluation'''
    def __claude_response(self, file_path: Path, file_encoded: str, company_name: str) -> Tuple[str, str]:

        claude_type_choice, full_type_description = self.doc_type, self.doc_type_descr

        # prompt given to claude (alongide the file)
        prompt_info = f'''Sei un categorizzatore di documenti dell'azienda {company_name}. Leggi il contenuto 
                            del file e, se corrisponde ad uno dei seguenti tipi dati: {claude_type_choice} che hanno
                            le seguenti descrizioni: {full_type_description}, ritorna il nome del tipo di file
                            RITORNA il nome, altrimenti ritorna FAIL. Ritorna SEMPRE SOLO un solo nome O FAIL.'''

        try: 
            if file_path.suffix.lower() == ".pdf":
                #### TOKEN BENCHMARKING ####
                # counting tokens via anthropic estimation
                self.token_counter.anthropic_token_estimator(self.client, file_path.name, file_encoded, self.claude_model, prompt_info)
                ############################

                response = self.client.messages.create(
                    model = self.claude_model,
                    system = prompt_info,
                    messages = [{
                            "role": "user",
                            "content": [
                                {
                                    "type": "document",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "application/pdf",
                                        "data": file_encoded
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt_info
                                }
                            ]
                        }],
                    # max_tokens number is very low because we only want the category
                    # and not the whole document content
                    max_tokens = 20,
                )

            elif file_path.suffix.lower() in [".msg", ".eml"]:
                # modify prompt for specific .msg usage (encoding file directly in the prompt)
                prompt_info = prompt_info+ f''' Nello specifico analizzami la seguente mail: {file_encoded}.
                                                Ricorda di NON ritornare MAI una spiegazioni, metadati.'''

                #### TOKEN BENCHMARKING ####
                # counting tokens via anthropic estimation
                self.token_counter.anthropic_token_estimator(self.client, file_path.name, file_encoded, self.claude_model, prompt_info)
                ############################

                response = self.client.messages.create(
                    model=self.claude_model,
                    system=prompt_info,
                    messages=[{
                            "role": "user",
                            "content": prompt_info
                        }],
                    max_tokens=20,
                )
                
            elif file_path.suffix.lower() in [".xls", ".xlsx", ".xlsm", ".xlsb", ".odf", ".ods", ".odt"]:
                # modify prompt for specific excel usage (encoding file directly in the prompt)
                prompt_info = prompt_info + f''' Nello specifico analizzami il seguente file Excel: {file_encoded}.
                                                Ricorda di NON ritornare MAI una spiegazioni, metadati.'''
                
                #### TOKEN BENCHMARKING ####
                # counting tokens via anthropic estimation
                self.token_counter.anthropic_token_estimator(self.client, file_path.name, file_encoded, self.claude_model, prompt_info)
                ############################

                response = self.client.messages.create(
                    model = self.claude_model,
                    system = prompt_info,
                    messages = [{
                            "role": "user",
                            "content": prompt_info
                        }],
                    max_tokens=20,
                )

            elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:

                prompt_info = prompt_info + f''' Nello specifico analizzami la seguente immagine.
                                                Ricorda di NON ritornare MAI una spiegazioni, metadati.'''
                
                #### TOKEN BENCHMARKING ####
                # counting tokens via anthropic estimation
                self.token_counter.anthropic_token_estimator(self.client, file_path.name, file_encoded, self.claude_model, prompt_info)
                ############################

                if file_path.suffix.lower() == '.jpg':
                    image_media_type = 'image/jpeg'
                elif file_path.suffix.lower() == '.jpeg':
                    image_media_type = 'image/jpeg'
                elif file_path.suffix.lower() == '.png':
                    image_media_type = 'image/png'
                elif file_path.suffix.lower() == '.gif':
                    image_media_type = 'image/gif'

                response = self.client.messages.create(
                    model = self.claude_model,
                    system = prompt_info,
                    messages = [{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": image_media_type,
                                        "data": file_encoded,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": prompt_info
                                }
                            ],
                        }],
                    max_tokens=20,
                )

            elif file_path.suffix.lower() == '.docx':
                # modify prompt for specific docx usage (encoding file directly in the prompt)
                prompt_info = prompt_info + f''' Nello specifico analizzami il seguente documento: {file_encoded}.
                                                Ricorda di NON ritornare MAI una spiegazioni, metadati.'''
                
                #### TOKEN BENCHMARKING ####
                # counting tokens via anthropic estimation
                self.token_counter.anthropic_token_estimator(self.client, file_path.name, file_encoded, self.claude_model, prompt_info)
                ############################

                response = self.client.messages.create(
                    model = self.claude_model,
                    system = prompt_info,
                    messages = [{
                            "role": "user",
                            "content": prompt_info
                        }],
                    max_tokens=20,
                )

            elif file_path.suffix.lower() == '.csv':
                # modify prompt for specific csv usage (encoding file directly in the prompt)
                prompt_info = prompt_info + f''' Nello specifico analizzami il seguente file CSV: {file_encoded}.
                                                Ricorda di NON ritornare MAI una spiegazioni, metadati.'''
                
                #### TOKEN BENCHMARKING ####
                # counting tokens via anthropic estimation
                self.token_counter.anthropic_token_estimator(self.client, file_path.name, file_encoded, self.claude_model, prompt_info)
                ############################

                response = self.client.messages.create(
                    model = self.claude_model,
                    system = prompt_info,
                    messages = [{
                            "role": "user",
                            "content": prompt_info
                        }],
                    max_tokens=20,
                )

            elif file_path.suffix.lower() in ['.txt', '.text']:
                # modify prompt for specific text usage (encoding file directly in the prompt)
                prompt_info = prompt_info + f''' Nello specifico analizzami il seguente testo: {file_encoded}.
                                                Ricorda di NON ritornare MAI una spiegazioni, metadati.'''
                
                #### TOKEN BENCHMARKING ####
                # counting tokens via anthropic estimation
                self.token_counter.anthropic_token_estimator(self.client, file_path.name, file_encoded, self.claude_model, prompt_info)
                ############################

                response = self.client.messages.create(
                    model = self.claude_model,
                    system = prompt_info,
                    messages = [{
                            "role": "user",
                            "content": prompt_info
                        }],
                    max_tokens=20,
                )

        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: __claude_response) Error during Claude response: {e}")
            return "ERROR"
        
        if response.content[0].text.strip() == None or response.content[0].text.strip() == "":
            self.logger.write_warning_in_log_file(f"(at func: __claude_response) Claude did not return a valid response for {file_path.name}.")
            return "ERROR"

        return response.content[0].text.strip(), file_encoded

    ######################
    # MAIN PREPROCESSING #
    ######################
    def main_preprocessing(self):
        try:
            self.doc_type, self.doc_type_descr = self.doc_category_ops.get_file_category_str()
            self.__check_for_dir_or_create(self.path_DUMP)
            self.logger.write_info_in_log_file(f"(at func: main_preprocessing) Analyzing {self.path_DUMP} directory...")
            self.preprocess_file()
            self.logger.write_info_in_log_file(f"(at func: main_preprocessing) Preprocessing completed successfully.")
        
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: main_preprocessing) Error during preprocessing: {e}")
        
        return
