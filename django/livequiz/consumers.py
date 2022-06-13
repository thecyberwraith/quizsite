from channels.generic.websocket import AsyncJsonWebsocketConsumer

class LiveQuizConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, code):
        return await super().disconnect(code)

    async def receive_json(self, content: dict):
        await self.send_json({'message': f'Someone sent {content["message"]}'})