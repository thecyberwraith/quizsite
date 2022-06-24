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
from livequiz.models import LiveQuizModel


def asyncSelfManage(func):
    async def testFunc(s, *args, **kwargs):
        await s.asyncSetUp()
        await func(s, *args, **kwargs)
        await s.asyncTearDown()
    return testFunc


class LiveQuizConsumerTestCase(TestCase):
    async def asyncSetUp(self):
        self.application = AuthMiddlewareStack(URLRouter([
            re_path(r'^testws/(?P<quiz_code>\w+)/$',
                    LiveQuizConsumer.as_asgi())
        ]))

    @database_sync_to_async
    def add_quiz_info(self, owner=None):
        quiz = QuizModel.objects.create(name='A Quiz', owner=owner)
        return LiveQuizModel.objects.create_for_quiz(quiz.id).code

    async def connect_with_code(self, code='ABCDE'):
        self.communicator = WebsocketCommunicator(
            self.application,
            f'/testws/{code}/'
        )
        await self.communicator.connect()

    async def asyncTearDown(self):
        await self.communicator.disconnect()

    async def assertMessageType(self, msg_type: str):
        msg = await self.communicator.receive_json_from()
        self.assertEqual(
            msg_type,
            msg['type'],
            f'Expected the message type to be {msg_type} in msg {msg}'
        )


class TestGenericLiveQuizConsumer(LiveQuizConsumerTestCase):
    @asyncSelfManage
    async def test_requires_livequiz_exists(self):
        await self.connect_with_code()

        await self.assertMessageType('error')

    @asyncSelfManage
    async def test_success_when_quiz_exists(self):
        quiz_code = await self.add_quiz_info()

        await self.connect_with_code(quiz_code)

        await self.assertMessageType('info')

    @asyncSelfManage
    async def test_success_sends_current_view(self):
        quiz_code = await self.add_quiz_info()

        await self.connect_with_code(quiz_code)

        await self.assertMessageType('info')
        await self.assertMessageType('set view')

    @asyncSelfManage
    async def test_sends_terminate_when_quiz_killed(self):
        quiz_code = await self.add_quiz_info()

        await self.connect_with_code(quiz_code)
        await self.communicator.receive_json_from()  # Connect successfully
        await self.communicator.receive_json_from()  # Set the view

        await database_sync_to_async(
            lambda code: LiveQuizModel.objects.delete(quiz_code=code)
        )(quiz_code)

        await self.assertMessageType('terminated')


class TestHostConsumer(LiveQuizConsumerTestCase):
    async def asyncSetUp(self):
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

    @asyncSelfManage
    async def test_requires_authentication(self):
        await self.connect_with_code()
        await self.assertMessageType('error')

    @asyncSelfManage
    async def test_requires_quiz_ownership(self):
        user = await self.add_user_info()
        code = await self.add_quiz_info()
        await self.login_connect(user, code)

        await self.assertMessageType('error')

    @asyncSelfManage
    async def test_accepts_quiz_owned_by_user(self):
        user = await self.add_user_info()
        quiz_code = await self.add_quiz_info(user)

        await self.login_connect(user, quiz_code)

        await self.assertMessageType('info')
