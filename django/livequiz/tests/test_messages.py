from unittest.mock import Mock, patch
from django.test import TestCase

import livequiz.messages as module

class TestParentClientMessageClass(TestCase):
    def test_subclass_must_implement_handle_message(self):
        class Terrible(module.ClientMessage):
            MESSAGE_KEY = 'valid'
        with self.assertRaises(TypeError):
            Terrible()

    
    def test_subclass_must_implement_message_key(self):
        with self.assertRaises(NameError):
            class NotGreat(module.ClientMessage):
                async def handle_message(self, socket, data: dict) -> None:
                    pass
    
    def test_subclass_key_must_be_unique(self):
        class Goodie(module.ClientMessage):
            MESSAGE_KEY = 'a'
            async def handle_message(self, socket, data: dict) -> None:
                pass
        
        with self.assertRaises(KeyError):
            class Baddie(module.ClientMessage):
                MESSAGE_KEY = 'a'
                async def handle_message(self, socket, data: dict) -> None:
                    pass
    
    async def test_throws_error_if_no_suitable_message_handler_found(self):
        with self.assertRaises(module.UnexpectedMessageException):
            await module.ClientMessage.handle(None, {'type': 'unexpected', 'payload': None})
    
    async def test_throws_error_if_malformed_base_message(self):
        with self.assertRaises(module.UnexpectedMessageException):
            await module.ClientMessage.handle(None, 'Wait... this is bad')

    async def test_data_passed_to_handler(self):
        class Tester(module.ClientMessage):
            MESSAGE_KEY = 'test'
            def __init__(self, data):
                pass
            async def handle_message(self, socket, data: dict) -> None:
                pass
        
        with patch.object(Tester, 'handle_message') as mock:
            await module.ClientMessage.handle(None, {'type': 'test', 'payload': None})
            mock.assert_called_once_with(None, None)