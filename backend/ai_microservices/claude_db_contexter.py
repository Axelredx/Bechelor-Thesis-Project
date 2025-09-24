import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from typing import List
import sys
from utility.error_logger import Logger
from utility.ocr import OCR

try:
    load_dotenv()
except Exception as e:
    raise e
    
class ClaudeQueryCreator:
    def __init__(self, script_path: Path = None) -> None:
        self.logger = Logger()
        self.token_counter = OCR(self.logger)
        self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        try:
            self.client = anthropic.Anthropic(
                api_key=self.claude_api_key,
            )
        except anthropic.AuthenticationError:
            raise Exception("Invalid Anthropic API key. Please check your environment variables.")

        # decide wich version of the claude model to use
        self.claude_model = "claude-3-5-haiku-20241022"

    def create_db_context(self, info_extracted: str) -> None:
        prompt_info = f'''Sei un assistente AI che aiuta a tenere traccia delle informazioni 
        che sono archiviate in un database non relazionale (MongoDB). I documenti che vengono salvati
        nel database hanno questa struttura di modello:
        {{
            filename: stringa, nome del file,
            file_extension: stringa, estensione del file,
            binary_file_content: contenuto binario del file,
            file_size: intero, dimensione del file in byte,
            file_hash: stringa, hash univoco del file per evitare duplicati,
            mime_type: stringa, tipo MIME del file,
            file_category: stringa, categoria del file,
            upload_date: data e ora di caricamento del file nel database,
            sender: stringa opzionale, mittente del documento,
            receiver: stringa opzionale, destinatario del documento,
            subject: stringa opzionale, oggetto del documento,
            total_cost: numero opzionale, costo totale associato al documento,
            document_date: data opzionale, ricavata dalle informazioni estratte dal documento,
            meta = {{
                'collection': 'documents',  
                'indexes': ['filename', 'upload_date', 'file_hash']
            }}
        }}''' 

        #check if db context exists -> add it to prompt, if not create it
        if self.logger.check_for_schema_log_file().exists():
            with open(self.logger.check_for_schema_log_file(), 'r') as file:
                schema_info = file.read()
                prompt_info += f'''Le informazioni che sono state archiviate nel database sono le seguenti:
                                    {schema_info}'''
                prompt_info += f'''Date le seguenti informazioni: {info_extracted}, estratte dal file analizzato 
                                    che verranno archiviate nel database, aggiorna la struttura del database. 
                                    NON ritornare MAI una spegazione.'''
        else:
            prompt_info += '''Attualmente non sono disponibili informazioni sullo schema del database.'''
            prompt_info += f'''Date le seguenti informazioni: {info_extracted}, estratte dal file analizzato 
                                che verranno archiviate nel database, crea la nuova struttura del database. 
                                NON ritornare MAI una spegazione.'''
        
        try:
            #### TOKEN BENCHMARKING ####
            # counting tokens via anthropic estimation
            self.token_counter.anthropic_token_estimator(self.client, "DB.context", "no.encoding", self.claude_model, prompt_info)
            ############################

            response = self.client.messages.create(
                model = self.claude_model,
                system = prompt_info,
                messages = [{
                        "role": "user",
                        "content": prompt_info
                    }],
                max_tokens=1000,
            )
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: create_db_context) Error during Claude response: {e}")

        self.logger.write_info_in_log_file(f"(at func: create_db_context) Successfully obtained Claude response for schema_file")
        self.logger.write_schema_in_log_file(f"{response.content[0].text.strip()}")

    def delete_in_db_context(self, info_to_delete: str) -> None:
        prompt_info = f'''Sei un assistente AI che aiuta a tenere traccia delle informazioni 
        che sono archiviate in un database non relazionale (MongoDB). I documenti che vengono salvati
        nel database hanno questa struttura di modello:
        {{
            filename: stringa, nome del file,
            file_extension: stringa, estensione del file,
            binary_file_content: contenuto binario del file,
            file_size: intero, dimensione del file in byte,
            file_hash: stringa, hash univoco del file per evitare duplicati,
            mime_type: stringa, tipo MIME del file,
            file_category: stringa, categoria del file,
            upload_date: data e ora di caricamento del file nel database,
            sender: stringa opzionale, mittente del documento,
            receiver: stringa opzionale, destinatario del documento,
            subject: stringa opzionale, oggetto del documento,
            total_cost: numero opzionale, costo totale associato al documento,
            document_date: data opzionale, ricavata dalle informazioni estratte dal documento,
            meta = {{
                'collection': 'documents',  
                'indexes': ['filename', 'upload_date', 'file_hash']
            }}
        }}''' 

        with open(self.logger.check_for_schema_log_file(), 'r') as file:
            schema_info = file.read()
            prompt_info += f'''Le informazioni che sono state archiviate nel database sono le seguenti:
                                {schema_info}, cancella da esse le seguenti informazioni: {info_to_delete}.
                                NON ritornare MAI una spegazione.'''
        
        try:
            #### TOKEN BENCHMARKING ####
            # counting tokens via anthropic estimation
            self.token_counter.anthropic_token_estimator(self.client, "DB.context", "no.encoding", self.claude_model, prompt_info)
            ############################

            response = self.client.messages.create(
                model = self.claude_model,
                system = prompt_info,
                messages = [{
                        "role": "user",
                        "content": prompt_info
                    }],
                max_tokens=1000,
            )
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: delete_in_db_context) Error during Claude response: {e}")

        self.logger.write_info_in_log_file(f"(at func: delete_in_db_context) Successfully obtained Claude response for new schema_file")
        self.logger.write_schema_in_log_file(f"{response.content[0].text.strip()}")