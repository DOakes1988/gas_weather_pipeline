import os
import logging

logger = logging.getLogger(__name__)

class FileTracker:
    def __init__(self, history_file):
        self.history_file = os.path.abspath(history_file)
        self.opened_files = set()
        self._load_history()
        logger.info("FileTracker initialized")

    """ Reads previously processed files into memory on startup """
    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                # Strip newlines and pull valid paths into tracking set
                self.opened_files = {line.strip() for line in f if line.strip()}

    """ Only opens a file if it hasn't been processed before """
    def open_file(self, filepath, mode="r", *args, **kwargs):
        # Normalize path to avoid duplicate entries from relative paths
        abs_path = os.path.abspath(filepath)

        if abs_path in self.opened_files:
            logging.error(f"Skipping: {abs_path} already processed")
            return None

        # Process file open request
        try:
            file_object = open(abs_path, mode, *args, **kwargs)

            # Immediately add successful open to log in case of crash
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(f"{abs_path}\n")

            self.opened_files.add(abs_path)
            return file_object

        except FileNotFoundError:
            logger.error(f": {abs_path} does not exist")
        except PermissionError:
            logger.error(f"Permission denied: {abs_path}")
        except Exception as e:
            logger.error(f": {abs_path} \n{e}")