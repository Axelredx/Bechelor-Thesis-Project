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
class ClaudeInterpreter:
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

    '''Given a string (NLP by the user), gives back True if user want back files, False otherwise'''
    def wants_files(self, user_input_nlp: str) -> bool:
        prompt_info = f'''Sei un assistente AI che aiuta a interpretare richieste in linguaggio naturale.
                        Data la seguente richiesta dell'utente: {user_input_nlp},
                        rispondi con "True" se l'utente vuole ricevere indietro i documenti
                        o "False" se vuole solo informazioni testuali.
                        Fornisci solo "True" o "False", NON fornire MAI spiegazioni.'''
        
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
                max_tokens=10,
            )
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: wants_files) Error during Claude response: {e}")
            return False

        self.logger.write_info_in_log_file(f"(at func: wants_files) Successfully interpreted user intent")
        return response.content[0].text.strip().lower() == "true"

    def interpret_response(self, info: str, user_request: str) -> str:
        prompt_info = f'''Sei un assistente AI che aiuta a interpretare informazioni ricavate da documenti
                            presenti nel database non relazionale MongoDB e soddisfare la richiesta dell'utente.
                            Le informazioni che devi interpretare sono le seguenti: {info}, e la 
                            richiesta dell'utente è: {user_request}.
                            Fornisci un'interpretazione CHIARA e COINCISA delle informazioni in linguaggio naturale. 
                            NON fornire MAI spiegazioni sul come hai ottenuto l'interpretazione.'''
        try:
            #### TOKEN BENCHMARKING ####
            # counting tokens via anthropic estimation
            self.token_counter.anthropic_token_estimator(self.client, "interpreting.db", "no.encoding", self.claude_model, prompt_info)
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
            self.logger.write_error_in_log_file(f"(at func: interpret_response) Error during Claude response: {e}")
            return "Error interpreting response."
        
        self.logger.write_info_in_log_file(f"(at func: interpret_response) Successfully interpreted response")
        return response.content[0].text.strip()
    
    def interpret_file_categories(self, user_input_nlp: str) -> str:
        prompt_info = f'''Sei un assistente AI che aiuta ad estrarre informazioni 
                            da una stringa in linguaggio natuarale. 
                            Data la seguente stringa: {user_input_nlp},
                            estrai e fornisci SOLO le categorie di documenti.
                            NON fornire MAI spiegazioni.
                            (se trovi solo una categoria, non inventartene altre ma restituisci
                            solo quella che hai trovato).'''
        
        prompt_info = prompt_info + "Se ritieni di non comprendere la richiesta, rispondi con 'NO'."
        
        try:
            #### TOKEN BENCHMARKING ####
            # counting tokens via anthropic estimation
            self.token_counter.anthropic_token_estimator(self.client, "file.categories", "no.encoding", self.claude_model, prompt_info)
            ############################

            response = self.client.messages.create(
                model = self.claude_model,
                system = prompt_info,
                messages = [{
                        "role": "user",
                        "content": prompt_info
                    }],
                max_tokens=300,
            )
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: interpret_file_categories) Error during Claude response: {e}")
            return "Error interpreting file categories."

        self.logger.write_info_in_log_file(f"(at func: interpret_file_categories) Successfully interpreted file categories")
        return response.content[0].text.strip()
    
    def interpret_file_descr(self, user_input_nlp: str) -> str:
        prompt_info = f'''Sei un assistente AI che aiuta ad estrarre informazioni 
                            da una stringa in linguaggio natuarale. 
                            Data la seguente stringa: {user_input_nlp},
                            estrai e fornisci le categorie di documenti, seguite dalla descrizione.
                            (esempio -> BOLLE: documenti di trasporto, FATTURE: fatture di acquisto o vendita, ...)
                            NON fornire MAI spiegazioni.
                            (se trovi solo una categoria, non inventartene altre ma restituisci
                            solo quella che hai trovato con la sua descrizione).'''
        try:
            #### TOKEN BENCHMARKING ####
            # counting tokens via anthropic estimation
            self.token_counter.anthropic_token_estimator(self.client, "file.descr", "no.encoding", self.claude_model, prompt_info)
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
            self.logger.write_error_in_log_file(f"(at func: interpret_file_descr) Error during Claude response: {e}")
            return "Error interpreting file description."

        self.logger.write_info_in_log_file(f"(at func: interpret_file_descr) Successfully interpreted file description")
        return response.content[0].text.strip()