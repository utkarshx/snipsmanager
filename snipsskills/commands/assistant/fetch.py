# -*-: coding utf-8 -*-

import os
import shutil
import time

from ..base import Base
from ..login import Login
from ...utils.http_helpers import fetch_url
from ...utils.os_helpers import write_binary_file, file_exists
from ...utils.cache import Cache

from snipsskills import SNIPS_CACHE_DIR

from snipsskillscore import pretty_printer as pp

class AssistantFetcherException(Exception):
    pass

# pylint: disable=too-few-public-methods
class AssistantFetcher(Base):

    SNIPS_TEMP_ASSISTANT_FILENAME = "assistant.zip"
    SNIPS_TEMP_ASSISTANT_PATH = os.path.join(SNIPS_CACHE_DIR, SNIPS_TEMP_ASSISTANT_FILENAME)
    CONSOLE_ASSISTANT_URL = "https://external-gateway.snips.ai/v1/assistant/{}/download"

    def run(self):
        """ Command runner.

        Docopt command:
        
        snipsskills fetch assistant [--id=<id> --url=<url> --file=<filename>]
        """

        aid = self.options['--id']
        url = self.options['--url']
        file = self.options['--file']

        try:
            AssistantFetcher.fetch(aid=aid, url=url, file=file)
        except Exception as e:
            pp.perror(str(e))


    @staticmethod
    def fetch(aid=None, url=None, file=None):
        pp.pcommand("Fetching assistant.")

        if aid is None and url is None and file is None:
            raise AssistantFetcherException("Error fetching assistant. Please provide an assistant ID, a public URL, or a filename.")

        if url:
            AssistantFetcher.download_public_assistant(url)
        elif aid:
            AssistantFetcher.download_console_assistant(aid)
        elif file:
            AssistantFetcher.copy_local_file(file)


    @staticmethod
    def download_public_assistant(url):
        message = pp.ConsoleMessage("Downloading assistant from {}".format(url))
        message.start()
        try:
            content = fetch_url(url)
            message.done()
        except:
            raise AssistantFetcherException("Error downloading assistant. Please make sure the assistant URL is correct.")

        message = pp.ConsoleMessage("Saving assistant to {}".format(AssistantFetcher.SNIPS_TEMP_ASSISTANT_PATH))
        message.start()
        write_binary_file(AssistantFetcher.SNIPS_TEMP_ASSISTANT_PATH, content)
        message.done()

    @staticmethod
    def download_console_assistant(aid):
        token = Cache.get_login_token()
        if token is None:
            try:
                token = Login.login(greeting="Please enter your Snips Console credentials to download your assistant.", silent=True)
            except Exception as e:
                raise AssistantFetcherException("Error logging in: {}".format(str(e)))

        message = pp.ConsoleMessage("Fetching assistant $GREEN{}$RESET from the Snips Console".format(aid))
        try:
            message.start()
            url = AssistantFetcher.get_console_url(aid)
            content = fetch_url(url, headers={'Authorization': token, 'Accept': 'application/json'})
            message.done()
        except Exception:
            message.done()
            raise AssistantFetcherException("Error fetching assistant from the console. Please make sure the ID is correct, and that you are signed in.")

        message = pp.ConsoleMessage("Saving assistant to {}".format(AssistantFetcher.SNIPS_TEMP_ASSISTANT_PATH))
        message.start()
        write_binary_file(AssistantFetcher.SNIPS_TEMP_ASSISTANT_PATH, content)
        message.done()


    @staticmethod
    def copy_local_file(file_path):
        message = pp.ConsoleMessage("Copying file {} to {}".format(file_path, AssistantFetcher.SNIPS_TEMP_ASSISTANT_PATH))
        message.start()
        
        error = None
        if not file_exists(file_path):
            error = "Error: failed to locate file {}.".format(file_path)
        else:
            try:
                shutil.copy2(file_path, AssistantFetcher.SNIPS_TEMP_ASSISTANT_PATH)
            except Exception as e:
                error = "Error: failed to copy file {}. Make sure you have write permissions to {}.".format(file_path, AssistantFetcher.SNIPS_TEMP_ASSISTANT_PATH)

        if error is not None:
            message.error()
            raise AssistantFetcherException(error)
        else:
            message.done()

    
    @staticmethod
    def get_console_url(aid):
        return AssistantFetcher.CONSOLE_ASSISTANT_URL.format(aid)