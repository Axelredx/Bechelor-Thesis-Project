import tiktoken
import pdfplumber
import base64
import anthropic
from pathlib import Path
from .error_logger import Logger

class OCR:
    def __init__(self, logger: Logger):
        self.logger = logger
        # model encoder based for Claude API usage
        self.encoder = tiktoken.get_encoding("cl100k_base")

    #############################
    # ANTHROPIC TOKEN ESTIMATOR #
    #############################
    
    '''token estimator by Anthropic'''
    def anthropic_token_estimator(self, api_client: any, file_name: str, encoded_file: str, claude_model: str, prompt: str) -> None:
        try:
            if file_name.endswith('.pdf'):
                response = api_client.messages.count_tokens(
                    model=claude_model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": encoded_file
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }]
                )

            elif file_name.endswith('.jpg') or file_name.endswith('.jpeg') or file_name.endswith('.png') or file_name.endswith('.gif'):

                if file_name.endswith('.jpg'):
                    image_media_type = 'image/jpeg'
                elif file_name.endswith('.jpeg'):
                    image_media_type = 'image/jpeg'
                elif file_name.endswith('.png'):
                    image_media_type = 'image/png'
                elif file_name.endswith('.gif'):
                    image_media_type = 'image/gif'

                response = api_client.messages.count_tokens(
                    model=claude_model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_media_type,
                                    "data": encoded_file
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }]
                )

            # all tokens are in prompt! (in :str format)
            else:

                response = api_client.messages.count_tokens(
                    model=claude_model,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

            self.logger.write_info_in_log_file(f"Estimated tokens by Anthropic API: {response.input_tokens}")
        except Exception as e:
            self.logger.write_warning_in_log_file(f"(at func: anthropic_token_estimator) Error estimating tokens with Anthropic API: {e}")