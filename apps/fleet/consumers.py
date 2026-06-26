import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.fleet.models import Machine, RepairLog


class FleetConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.channel_layer.group_add('fleet', self.channel_name)
        await self.accept()

        machines = await self.get_machines()
        await self.send(text_data=json.dumps({
            'type': 'init',
            'machines': machines
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('fleet', self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('action') == 'toggle_repair':
            machine_id = data.get('machine_id')
            user_id = self.scope['user'].id
            machine = await self.toggle_repair(machine_id, user_id)

            await self.channel_layer.group_send('fleet', {
                'type': 'fleet_update',
                'machine': machine
            })

    async def fleet_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update',
            'machine': event['machine']
        }))

    @database_sync_to_async
    def get_machines(self):
        return [
            self._serialize(m)
            for m in Machine.objects.all().order_by('name')
        ]

    @database_sync_to_async
    def toggle_repair(self, machine_id, user_id):
        machine = Machine.objects.get(id=machine_id)
        machine.is_in_repair = not machine.is_in_repair
        machine.save()

        if machine.is_in_repair:
            RepairLog.objects.create(
                machine=machine,
                user_id=user_id,
                is_active=True
            )
        else:
            RepairLog.objects.filter(
                machine=machine,
                is_active=True
            ).update(is_active=False)

        return self._serialize(machine)

    def _serialize(self, m):
        return {
            'id': m.id,
            'name': m.name,
            'board_number': m.board_number,
            'ktg_value': round(m.ktg_value, 4),
            'ktg_threshold': m.ktg_threshold,
            'is_in_repair': m.is_in_repair,
        }