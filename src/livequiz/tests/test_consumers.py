from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.auth import AuthMiddlewareStack, login
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.urls import re_path
from django.test import TestCase

from quiz.models import QuizModel
from livequiz.consumers import LiveQuizConsumer, LiveQuizHostConsumer
from livequiz.models import LiveQuizModel, QuizData


class LiveQuizConsumerTestCase(TestCase):
    def setUp(self):
        self.application = AuthMiddlewareStack(URLRouter([
            re_path(r'^testws/(?P<quiz_code>\w+)/$',
                    LiveQuizConsumer.as_asgi())
        ]))

    @database_sync_to_async
    def add_quiz_info(self, owner=None):
        if owner is None:
            owner = User.objects.create_user(username='troll', password='potato')
        
        return LiveQuizModel.objects.create_for_quiz(owner, QuizData(name='A Quiz', categories={})).code

    async def connect_with_code(self, code='ABCDE'):
        self.communicator = WebsocketCommunicator(
            self.application,
            f'/testws/{code}/'
        )
        await self.communicator.connect()

    def tearDown(self):
        async_to_sync(self.communicator.disconnect)()

    async def assertMessageType(self, msg_type: str):
        msg = await self.communicator.receive_json_from()
        self.assertEqual(
            msg_type,
            msg['type'],
            f'Expected the message type to be {msg_type} in msg {msg}'
        )


class TestGenericLiveQuizConsumer(LiveQuizConsumerTestCase):
    def setUp(self):
        self.application = AuthMiddlewareStack(URLRouter([
            re_path(r'^testws/(?P<quiz_code>\w+)/$',
                    LiveQuizConsumer.as_asgi())
        ]))
    
    def tearDown(self):
        async_to_sync(self.communicator.disconnect)()
    
    async def test_requires_livequiz_exists(self):
        await self.connect_with_code()

        await self.assertMessageType('error')

    async def test_success_when_quiz_exists(self):
        quiz_code = await self.add_quiz_info()

        await self.connect_with_code(quiz_code)

        await self.assertMessageType('info')

    async def test_success_sends_current_view(self):
        quiz_code = await self.add_quiz_info()

        await self.connect_with_code(quiz_code)

        await self.assertMessageType('info')
        await self.assertMessageType('set view')

    async def test_sends_terminate_when_quiz_killed(self):
        quiz_code = await self.add_quiz_info()

        await self.connect_with_code(quiz_code)
        await self.communicator.receive_json_from()  # Connect successfully
        await self.communicator.receive_json_from()  # Set the view
        await self.communicator.receive_json_from()  # Update buzz event

        await database_sync_to_async(
            lambda code: LiveQuizModel.objects.filter(code=code).delete()
        )(quiz_code)

        await self.assertMessageType('terminated')


class TestHostConsumer(LiveQuizConsumerTestCase):
    def setUp(self):
        self.application = AuthMiddlewareStack(URLRouter([
            re_path(r'^testws/(?P<quiz_code>\w+)/$',
                    LiveQuizHostConsumer.as_asgi())
        ]))

    @database_sync_to_async
    def add_user_info(self):
        user = User.objects.create_user(username='bob', password='sue')
        return user

    async def login_connect(self, user, code='ABCDEf'):
        org_func = LiveQuizHostConsumer.connect

        async def login_mock(consumer_self):
            await login(consumer_self.scope, user)
            await org_func(consumer_self)
        LiveQuizHostConsumer.connect = login_mock

        await self.connect_with_code(code)

        LiveQuizHostConsumer.connect = org_func

    async def test_requires_authentication(self):
        await self.connect_with_code()
        await self.assertMessageType('error')

    async def test_requires_quiz_ownership(self):
        user = await self.add_user_info()
        code = await self.add_quiz_info()
        await self.login_connect(user, code)

        await self.assertMessageType('error')

    async def test_accepts_quiz_owned_by_user(self):
        user = await self.add_user_info()
        quiz_code = await self.add_quiz_info(user)

        await self.login_connect(user, quiz_code)

        await self.assertMessageType('info')
