import logging
import os
from datetime import datetime


class Logger:
    """
    Custom logging class that provides a unified logging setup for the project.
    """

    def __init__(self, log_dir="logs", log_file="application", level=logging.DEBUG):
        """
        Initializes the logger.

        Parameters:
            log_dir (str): Directory where logs will be stored.
            log_file (str): Base name of the log file.
            level (int): Logging level (e.g., logging.DEBUG).
        """
        self.log_dir = log_dir
        self.log_file = f"{log_file} {datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
        self.level = level
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """
        Configures the logger and its handlers.

        Returns:
            logging.Logger: Configured logger instance.
        """
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            log_path = os.path.join(self.log_dir, self.log_file)

            # Create and configure logger
            logger = logging.getLogger(__name__)
            logger.setLevel(self.level)

            # Avoid adding duplicate handlers
            if not logger.hasHandlers():
                # File handler
                file_handler = logging.FileHandler(log_path)
                file_handler.setLevel(self.level)

                # Console handler
                console_handler = logging.StreamHandler()
                console_handler.setLevel(self.level)

                # Formatter
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)

                # Add handlers
                logger.addHandler(file_handler)
                logger.addHandler(console_handler)

            return logger
        except (OSError, IOError) as e:
            raise RuntimeError(f"Failed to set up logger: {e}")

    def get_logger(self):
        """
        Returns the configured logger instance.

        Returns:
            logging.Logger: Configured logger instance.
        """
        return self.logger


# Unit Test Examples
if __name__ == "__main__":
    try:
        logger_instance = Logger()
        logger = logger_instance.get_logger()
        logger.info("Logger setup complete and working.")
    except RuntimeError as e:
        print(f"Error during logger setup: {e}")