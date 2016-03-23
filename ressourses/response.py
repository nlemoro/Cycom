__author__ = 'linard_f'

import json


class Response:
    # STATUS MACROS
    SUCCESS_STATUS = "OK"
    ERROR_STATUS = "ERROR"

    # MESSAGES MACROS
    SUCCESS_MSG = "response successful"
    ERROR_MSG = "response ERROR"

    def __init__(self, status, message, size=0, content=None):
        self.content = content
        self.message = message
        self.status = status
        self.size = size

    def __str__(self):
        return json.dumps(self.__dict__)

    # PUSH OBJECTS TO JSON IN CONTENT KEY (content: object)
    def push_content(self, content):
        self.content = content

