import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Union, Dict, Any, Tuple
import sys
from utility.error_logger import Logger
import json
from models.file_categories import FileCategory

try:
    load_dotenv()
except Exception as e:
    raise RuntimeError(f"Error loading .env file: {e}")
class DocCategoryOperations:
    def __init__(self) -> None:
        self.logger = Logger()

    '''Check if any category&description strings exist in the database'''
    def str_exists_in_db(self) -> bool:
        try:
            existing_categories = FileCategory.objects()
            return existing_categories.count() > 0
        except Exception as e:
            self.logger.write_error_in_log_file(f"(in str_exists_in_db) Error checking categories in DB: {e}")
            return False

    def save_file_categories_str(self, full_string_passed: str, category_str: str) -> bool:
        try:
            new_category = FileCategory(full_file_category_and_descr_string=full_string_passed, file_category_string=category_str)
            new_category.save()
            self.logger.write_info_in_log_file(f"(INFO) Category '{category_str}' (and descr.) added successfully.")
            return True
        except Exception as e:
            self.logger.write_error_in_log_file(f"(in save_file_categories_str) Error adding category '{category_str}': {e}")
            return False

    def update_file_category_str(self, full_new_string: str, new_category_str: str) -> bool:
        try:
            category = FileCategory.objects().first()
            if category:
                category.full_file_category_and_descr_string = full_new_string
                category.file_category_string = new_category_str
                category.save()
                self.logger.write_info_in_log_file(f"(INFO) Category updated to '{new_category_str}'.")
                return True
            else:
                self.save_file_categories_str(full_new_string, new_category_str)
                self.logger.write_warning_in_log_file(f"(WARNING) Category not found for update. Creating new category '{new_category_str}'.")
                return False
        except Exception as e:
            self.logger.write_error_in_log_file(f"(in update_file_category_str) Error updating file category: {e}")
            return False

    def get_file_category_str(self) -> Tuple[str, str]:
        try:
            category = FileCategory.objects().first()
            if category:
                return category.file_category_string, category.full_file_category_and_descr_string
            else:
                self.logger.write_warning_in_log_file(f"(WARNING) No file categories found in DB.")
                return "", ""
        except Exception as e:
            self.logger.write_error_in_log_file(f"(in get_file_category_str) Error retrieving file category: {e}")
            return "", ""
        
    def delete_all_categories(self) -> bool:
        try:
            FileCategory.objects.delete()
            self.logger.write_info_in_log_file(f"(INFO) All file categories deleted successfully.")
            return True
        except Exception as e:
            self.logger.write_error_in_log_file(f"(in delete_all_categories) Error deleting all file categories: {e}")
            return False
