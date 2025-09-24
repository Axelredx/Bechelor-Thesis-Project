import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from typing import List
import sys
from utility.error_logger import Logger
from utility.ocr import OCR
import datetime

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
        
    '''Given db context and user request (in NLP), create the query to be run on the DB'''
    def create_db_query(self, user_input_nlp: str) -> str:
        now = datetime.datetime.now()
        
        if self.logger.check_for_schema_log_file().exists():
            with open(self.logger.check_for_schema_log_file(), 'r') as file:
                db_context = file.read()
        else:
            return "No database context available."
        
        prompt_info = f'''Sei un assistente AI che aiuta a creare query per un database 
                            non relazionale (MongoDB). Dato il contesto del database: {db_context}
                            e la richiesta dell'utente in linguaggio naturale: {user_input_nlp}, 
                            e tenendo conto che i modelli salvati nel database seguono il seguente:
                            SCHEMA DATABASE (DocumentModel):
                                - filename: stringa (required, max 255 char)
                                - file_extension: stringa (required, max 10 char) 
                                - file_size: intero (required)
                                - file_hash: stringa (required, unique)
                                - mime_type: stringa (required)
                                - file_category: stringa (required)
                                - upload_date: DateTime (default: now, formato ISO, è la data di 
                                    quando il documento è stato caricato nel database)
                                - sender: stringa (opzionale)
                                - receiver: stringa (opzionale) 
                                - subject: stringa (opzionale)
                                - total_cost: float (opzionale)
                                - document_date: DateTime (opzionale, formato ISO, è la data 
                                    presente nel documento stesso, es. data fattura)
                            elabora la query MongoDB corretta per soddisfare la richiesta dell'utente.
                            Fornisci solo la query, NON fornire MAI spiegazioni. 
                            ricordati che oggi è {now.strftime("%Y-%m-%d")}.
                            Ricorda Genera SOLO query MongoDB valide per Python/MongoEngine. 
                            Segui queste regole:
                            1. **Formato JSON valido**: 
                                - Usa sempre virgolette doppie per le chiavi
                                - NON usare sintassi JavaScript
                            2. **Operatori MongoDB**:
                                - Usa sempre virgolette doppie per: '$gte', '$lte', '$gt', '$lt', '$in', '$nin', '$ne'
                            3. **Date e orari**:
                                - NON usare: new Date(), Date(), ISODate()
                                - Per date relative, calcola e fornisci la data specifica
                                - USA il formato ISO per le date (es. "2024-11-30T00:00:00")
                            4. **Struttura della risposta**:
                                - Restituisci SOLO il filtro JSON, non la query completa
                                - NON includere: db.collection.find(), .limit(), .sort()
                                - Per stringhe usa regex case-insensitive
                                - Per numeri usa operatori standard
                            '''
        prompt_info = prompt_info + "Se ritieni di non comprendere la richiesta, rispondi con 'NO'."

        try:
            #### TOKEN BENCHMARKING ####
            # counting tokens via anthropic estimation
            self.token_counter.anthropic_token_estimator(self.client, "DB.query", "no.encoding", self.claude_model, prompt_info)
            ############################

            response = self.client.messages.create(
                model = self.claude_model,
                system = prompt_info,
                messages = [{
                        "role": "user",
                        "content": prompt_info
                    }],
                max_tokens=200,
            )
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: create_db_query) Error during Claude response: {e}")

        self.logger.write_info_in_log_file(f"(at func: create_db_query) Successfully created query")
        return response.content[0].text.strip()
