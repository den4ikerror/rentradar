import logging
from collections import deque

LOG_BUFFER = deque(maxlen=150)


class MemoryLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            LOG_BUFFER.append(msg)
        except Exception:
            pass


def setup_memory_logging():
    handler = MemoryLogHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
    logging.getLogger("rentfinder").setLevel(logging.INFO)

