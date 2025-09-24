import os
from pathlib import Path

class DevelopTool:
    def __init__(self, script_path=None) -> None:
        # locate script path & build relative paths
        if script_path is None:
            script_path = Path(__file__)
        
        self.script_dir = script_path.parent.parent
        self.path_DUMP = self.script_dir / "DUMP" 

    def cleaner(self) -> None:
        if not self.path_DUMP.exists():
            return
        self.__clean_subfolder()

    def __delete_subfolder(self, dir: Path) -> None:
        os.rmdir(dir)

    def __clean_subfolder(self) -> None:
        for dir in self.path_DUMP.iterdir():
            if dir.is_dir():
                for subdir in dir.iterdir():
                    for item in subdir.iterdir():
                        if item.is_file():
                            item.unlink(missing_ok=True)
                    self.__delete_subfolder(subdir)
            elif dir.is_file():
                dir.unlink(missing_ok=True)

def main():
    cleaner_tool = DevelopTool()  
    try:
        cleaner_tool.cleaner()
    except Exception as e:
        print(f"Error during cleaning: {e}")
if __name__ == "__main__":
    main()