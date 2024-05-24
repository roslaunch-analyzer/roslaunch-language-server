import logging

from pygls.server import LanguageServer


class LSPLogHandler(logging.Handler):
    """
    Custom log handler to send log messages to the Language Server.
    """

    def __init__(self, ls: LanguageServer):
        super().__init__()
        self.ls = ls

    def emit(self, record):
        try:
            msg = self.format(record)
            self.ls.show_message_log(msg)
        except Exception:
            self.handleError(record)
