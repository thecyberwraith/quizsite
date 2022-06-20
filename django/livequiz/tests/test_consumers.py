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
from livequiz.consumers import LiveQuizHostConsumer
from livequiz.models import LiveQuizModel


def asyncSelfManage(func):
    async def testFunc(s, *args, **kwargs):
        await s.asyncSetUp()
        await func(s, *args, **kwargs)
        await s.asyncTearDown()
    return testFunc


class TestHostConsumerConnectionStates(TestCase):
    async def asyncSetUp(self):
        self.application = AuthMiddlewareStack(URLRouter([
            re_path(r'^testws/(?P<quiz_code>\w+)/$',
                    LiveQuizHostConsumer.as_asgi())
        ]))

    @database_sync_to_async
    def add_user_info(self):
        user = User.objects.create_user(username='bob', password='sue')
        return user

    @database_sync_to_async
    def add_quiz_info(self, owner=None):
        quiz = QuizModel.objects.create(name='A Quiz', owner=owner)
        return LiveQuizModel.objects.create_for_quiz(quiz.id).code

    async def login_connect(self, user, code='ABCDEf'):
        org_func = LiveQuizHostConsumer.connect

        async def login_mock(consumer_self):
            await login(consumer_self.scope, user)
            await org_func(consumer_self)
        LiveQuizHostConsumer.connect = login_mock

        await self.connect_with_code(code)

        LiveQuizHostConsumer.connect = org_func

    async def connect_with_code(self, code='ABCDE'):
        self.communicator = WebsocketCommunicator(
            self.application,
            f'/testws/{code}/'
        )
        await self.communicator.connect()

    async def asyncTearDown(self):
        await self.communicator.disconnect()

    @asyncSelfManage
    async def test_requires_authentication(self):
        await self.connect_with_code()
        response = await self.communicator.receive_json_from()
        self.assertIn('error', response)

    @asyncSelfManage
    async def test_requires_livequiz_exists(self):
        user = await self.add_user_info()
        await self.login_connect(user)

        self.assertIn(
            'error',
            await self.communicator.receive_json_from()
        )

    @asyncSelfManage
    async def test_requires_quiz_ownership(self):
        user = await self.add_user_info()
        code = await self.add_quiz_info()
        await self.login_connect(user, code)

        self.assertIn(
            'error',
            await self.communicator.receive_json_from()
        )

    @asyncSelfManage
    async def test_accepts_quiz_owned_by_user(self):
        user = await self.add_user_info()
        quiz_code = await self.add_quiz_info(user)

        await self.login_connect(user, quiz_code)

        self.assertNotIn(
            'error',
            await self.communicator.receive_json_from()
        )
