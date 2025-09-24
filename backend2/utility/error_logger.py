from pathlib import Path
import time

class Logger:
    def __init__(self, log_script_path: Path = None):
        if log_script_path is None:
            self.parent_path = Path(__file__).parent.parent
        else:
            self.parent_path = log_script_path.parent.parent

        self.log_file_path = self.parent_path / "LOGFILE"

    '''return true if directory exists'''
    def __check_dir_exists(self) -> bool:
        return self.log_file_path.exists() and self.log_file_path.is_dir()

    '''return true if log directory has error_log file'''
    def __log_dir_has_error_logs(self) -> bool:
        for item in self.log_file_path.iterdir():
            if item.is_file() and 'error_log_file_created' in item.name and item.suffix == '.txt':
                return True
        return False
    
    '''return true if log directory has schema file'''
    def __log_dir_has_schema_files(self) -> bool:
        for item in self.log_file_path.iterdir():
            if item.is_file() and 'schema_log_file' in item.name and item.suffix == '.txt':
                return True
        return False
    
    '''return true if log directory has log file'''
    def __log_dir_has_log_files(self) -> bool:
        for item in self.log_file_path.iterdir():
            if item.is_file() and 'logs_file' in item.name and item.suffix == '.txt':
                return True
        return False

    '''check if directory exists, if not create it'''
    def __check_for_log_dir(self) -> Path:
        if not self.__check_dir_exists():
            self.log_file_path.mkdir(parents=True, exist_ok=True)
        return self.log_file_path

    '''check if error log file exists, if not create it'''
    def __check_for_error_log_file(self) -> Path:
        if not self.__log_dir_has_error_logs():
            error_log_file = self.log_file_path / f"error_log_file_created_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            error_log_file.touch()
            return error_log_file
        else:
            for item in self.log_file_path.iterdir():
                if item.is_file() and item.suffix == '.txt' and 'error_log_file_created' in item.name:
                    return item

    '''check if schema file exists, if not create it'''
    def check_for_schema_log_file(self) -> Path:
        if not self.__log_dir_has_schema_files():
            schema_log_file = self.log_file_path / f"schema_log_file.txt"
            schema_log_file.touch()
            return schema_log_file
        else:
            for item in self.log_file_path.iterdir():
                if item.is_file() and item.suffix == '.txt' and 'schema' in item.name:
                    return item

    '''check if log file exists, if not create it'''
    def __check_for_log_file(self) -> Path:
        if not self.__log_dir_has_log_files():
            log_file = self.log_file_path / f"logs_file.txt"
            log_file.touch()
            return log_file
        else:
            for item in self.log_file_path.iterdir():
                if item.is_file() and item.suffix == '.txt' and 'logs_file' in item.name:
                    return item

    '''delete last error log file if is  2 days old'''
    def __delete_old_error_log_file(self) -> None:
        for log_file in self.log_file_path.glob("*.txt"):
            if log_file.stat().st_mtime < time.time() - 2 * 86400 and 'error_log_file_created' in log_file.name:  # 2 days in seconds
                log_file.unlink()
            
            #delete file if more than 1mb
            elif log_file.stat().st_size > 1 * 1024 * 1024 and 'error_log_file_created' in log_file.name:  # 1 MB in bytes
                log_file.unlink()

    '''delete last schema log file'''
    def __delete_old_schema_log_file(self) -> None:
        for log_file in self.log_file_path.glob("*.txt"):
            if 'schema_log_file' in log_file.name: 
                log_file.unlink()

    '''delete last log file if is  2 days old'''
    def __delete_old_log_file(self) -> None:
        for log_file in self.log_file_path.glob("*.txt"):
            if log_file.stat().st_mtime < time.time() - 2 * 86400 and 'logs_file' in log_file.name:  # 2 days in seconds
                log_file.unlink()
                        
            elif log_file.stat().st_size > 1 * 1024 * 1024 and 'logs_file' in log_file.name:  # 1 MB in bytes
                log_file.unlink()

    '''write error message to log file'''
    def write_error_in_log_file(self, error_message: str) -> None:
        self.__check_for_log_dir()
        self.__delete_old_error_log_file()
        log_file = self.__check_for_error_log_file()

        with open(log_file, 'a') as file:
            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - ERROR: {error_message}\n")

    '''write warning message to log file'''
    def write_warning_in_log_file(self, warning_message: str) -> None:
        self.__check_for_log_dir()
        self.__delete_old_error_log_file()
        log_file = self.__check_for_error_log_file()

        with open(log_file, 'a') as file:
            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - WARNING: {warning_message}\n")
            
    '''write schema message to schema log file'''
    def write_schema_in_log_file(self, schema_message: str) -> None:
        self.__check_for_log_dir()
        self.__delete_old_schema_log_file()
        log_file = self.check_for_schema_log_file()

        with open(log_file, 'a') as file:
            file.write(f"{schema_message}")
            
    '''write info message to log file'''
    def write_info_in_log_file(self, info_message: str) -> None:
        self.__check_for_log_dir()
        self.__delete_old_log_file()
        log_file = self.__check_for_log_file()

        with open(log_file, 'a') as file:
            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO: {info_message}\n")
