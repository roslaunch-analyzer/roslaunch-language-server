import logging

from pygls.server import LanguageServer

from roslaunch_language_server.logger import LSPLogHandler

server = LanguageServer("roslaunch-language-server", version="0.1.0")

# logging.basicConfig(handlers=[logging.StreamHandler()], level=logging.DEBUG)

# Set up logging
logger = logging.getLogger("ls-logger")
logger.setLevel(logging.DEBUG)
lsp_handler = LSPLogHandler(server)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
lsp_handler.setFormatter(formatter)
logger.addHandler(lsp_handler)

# logging.basicConfig(
#     handlers=[LSPLogHandler(server)],
#     level=logging.DEBUG,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
# )

# logger = logging.getLogger("ls-logger")
