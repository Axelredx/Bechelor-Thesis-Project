import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Tuple
import sys
from utility.error_logger import Logger
from utility.ocr import OCR
import datetime

try:
    load_dotenv()
except Exception as e:
    raise e    
class ClaudeInfoExtractor:
    def __init__(self, logger: Logger, script_path: Path = None) -> None:
        self.logger = logger
        self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        try:
            self.client = anthropic.Anthropic(
                api_key=self.claude_api_key,
            )
        except anthropic.AuthenticationError:
            raise Exception("Invalid Anthropic API key. Please check your environment variables.")
        # decide wich version of the claude model to use
        self.claude_model = "claude-3-5-haiku-20241022"

        if script_path is None:
            script_path = Path(__file__)

        self.script_dir = script_path.parent
        self.path_DUMP = self.script_dir.parent / "DUMP"

        # (benchmark uses)
        self.token_counter = OCR(self.logger)

    def claude_extract_info(self, file_path: Path, file_encoded: str, file_category: str) -> Tuple[str, str]:
        prompt_info = f'''Sei un assistente AI che aiuta ad estrarre informazioni
                            importanti dai documenti.
                            Analizza il contenuto del documento fornito ed estrai 
                            le informazioni chiave, seguendo il seguente schema di database 
                            non relazionale:
                            - sender: mittente del documento (se applicabile)
                            - receiver: destinatario del documento (se applicabile)
                            - subject: oggetto o titolo del documento (se applicabile)
                            - total_cost: costo totale menzionato nel documento (se applicabile)
                            - document_date: data rilevante menzionata nel documento (se applicabile)
                            Se un campo non è presente o non applicabile, restituisci "N/A" per quel campo.
                            Ricorda sempre di mettere i dati tra virgolette doppie (esempio-> "total_cost": "104.00").
                            ritorna total_cost sempre in formato numerico float con due cifre decimali (esempio-> "total_cost": "7201.08").
                            Ritorna la data in formato DD-MM-YYYY (esempio-> "document_date": "25-12-2023").
                            Rispondi SOLO con il JSON, senza aggiungere altro testo o spiegazioni.'''
        
        try: 
            if file_path.suffix.lower() == ".pdf":
                prompt_info = prompt_info+ f'''Ricorda di NON ritornare MAI una spiegazioni, metadati.'''
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
                    max_tokens = 150,
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
                    max_tokens=150,
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
                    max_tokens=150,
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
                    max_tokens=150,
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
                    max_tokens=150,
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
                    max_tokens=150,
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
                    max_tokens=150,
                )

        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: claude_extract_info) Error during Claude response: {e}")
            return "ERROR"
        
        if response.content[0].text.strip() == None or response.content[0].text.strip() == "":
            self.logger.write_warning_in_log_file(f"(at func: claude_extract_info) Claude did not return a valid response for {file_path.name}.")
            return "ERROR"

        self.logger.write_info_in_log_file(f"(at func: claude_extract_info) Successfully obtained Claude response for {file_path.name}")
        #self.logger.write_schema_in_log_file(f"{response.content[0].text.strip()}")

        return self.post_process_extraction(response.content[0].text.strip(), file_category, file_path)

    def post_process_extraction(self, schema_extracted: str, file_category: str, file_path: Path) -> Tuple[str, str]:
        now = datetime.datetime.now()
        iso_string = now.strftime("%Y-%m-%dT%H:%M:%S")
        prompt_info = f'''Sei un assistente AI che aiuta ad aggiungere informazioni ai dati estratti da documenti.
                            Prendi il seguente JSON: {schema_extracted} e aggiungi le seguenti mettendole in testa:
                            - filename: nome del file (metti "{file_path.name}")
                            - file_extension: estensione del file (metti "{file_path.suffix[1:]}")
                            - binary_file_content: contenuto del file (metti '/binary')
                            - file_size: dimensione del file in byte (metti '/size')
                            - file_hash: hash univoco del file (metti '/hash')
                            - mime_type: tipo MIME del file
                            - file_category: categoria del file (metti "{file_category}")
                            - upload_date: data di caricamento nel DB (metti "{iso_string}")
                            Ritorna il JSON COMPLETO con le nuove informazioni AGGIUNTE in cima.
                            Rispondi SOLO con il JSON, senza aggiungere altro testo o spiegazioni.'''

        try:
            #### TOKEN BENCHMARKING ####
            # counting tokens via anthropic estimation
            self.token_counter.anthropic_token_estimator(self.client, "adjust.query", "no.encoding", self.claude_model, prompt_info)
            ############################

            response = self.client.messages.create(
                model = self.claude_model,
                system = prompt_info,
                messages = [{
                        "role": "user",
                        "content": prompt_info
                    }],
                max_tokens=500,
            )
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: post_process_extraction) Error during Claude response: {e}")
            return "Error interpreting response.", iso_string

        self.logger.write_info_in_log_file(f"(at func: post_process_extraction) Successfully interpreted response")
        return response.content[0].text.strip(), iso_string