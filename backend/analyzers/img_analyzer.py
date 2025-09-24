from pathlib import Path
import sys
from PIL import Image
import io
import base64
from utility.error_logger import Logger

########################
# IMAGE HANDLING TOOLS #
########################

class ImgAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger

    '''analyze image files and send to claude for classification (it supports: .jpg, .jpeg, .png, .gif)'''
    def analyze_image(self, image_file_path: Path, company_name: str) -> tuple[Path, str, str]:
        max_image_size = 5 * 1024 * 1024  # max 5 MB
        max_image_dimensions = 1568  # 1568 pixels (max advised for Claude)

        try:
            with Image.open(image_file_path) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                original_size = image_file_path.stat().st_size
                
                if original_size > max_image_size:
                    compressed_image_bytes = self.__compress_image(img, image_file_path, image_file_path.suffix)
                    
                    # if img still too big, compress it further
                    while len(compressed_image_bytes) > max_image_size:
                        self.logger.write_info_in_log_file(f"(at func: analyze_image) Compressed image size ({len(compressed_image_bytes) / (1024 * 1024):.2f} MB) still exceeds 5 MB, compressing further...\n")
                        compressed_image_bytes = self.__compress_image(img, image_file_path, image_file_path.suffix, quality=70)
                    
                    img_base64 = base64.b64encode(compressed_image_bytes).decode('utf-8')
                else:

                    buffer = io.BytesIO()
                    image_format = 'JPEG' if image_file_path.suffix.lower() in ['.jpg', '.jpeg'] else 'PNG'
                    img.save(buffer, format=image_format, quality=85, optimize=True)
                    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                self.logger.write_info_in_log_file(f"(at func: analyze_image) Successfully processed image file {image_file_path}\n")
                return image_file_path, img_base64, company_name
                
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: analyze_image) Error processing image file {image_file_path}: {e}\n")
            return image_file_path, "", company_name

    '''Compress an image to reduce its file size & return the compressed bytes'''
    def __compress_image(self, image: Image.Image, image_file_path: Path, file_extension: str, quality: int = 85) -> bytes:
        try:
            buffer = io.BytesIO()
            
            if file_extension.lower() in ['.jpg', '.jpeg']:
                image.save(buffer, format='JPEG', quality=quality, optimize=True)
            elif file_extension.lower() == '.png':
                image.save(buffer, format='PNG', optimize=True)
            elif file_extension.lower() == '.webp':
                image.save(buffer, format='WEBP', quality=quality, optimize=True)
            else:
                image.save(buffer, format='JPEG', quality=quality, optimize=True)
            
            return buffer.getvalue()
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at func: __compress_image) Error compressing image {image_file_path}: {e}\n")
            return b""
