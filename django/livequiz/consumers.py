from channels.generic.websocket import AsyncJsonWebsocketConsumer

class LiveQuizConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.game_code = self.scope['url_route']['kwargs']['live_quiz_id']
        self.room_group_name = 'live_quiz_%s' % self.game_code

        await self.accept()

    async def disconnect(self, code):
        return await super().disconnect(code)

    async def receive_json(self, content: dict):
        await self.send_json({'message': f'Someone sent {content["message"]}'})