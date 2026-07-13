import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.fleet.models import Machine, RepairLog, KTGHistory, KTGMonthResult
from apps.fleet.services.ktg_service import (
    calculate_ktg_decrease_step,
    calculate_ktg_from_date,
)
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from django.utils import timezone as dj_timezone
import pytz

KTG_TICK_INTERVAL = 10


class FleetConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.channel_layer.group_add("fleet", self.channel_name)
        await self.accept()

        machines = await self.get_machines()
        await self.send(text_data=json.dumps({"type": "init", "machines": machines}))

        self.ktg_task = asyncio.create_task(self.ktg_loop())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("fleet", self.channel_name)
        if hasattr(self, "ktg_task"):
            self.ktg_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("action") == "toggle_repair":
            # Кнопка "в ремонт / завершить ремонт"
            machine_id = data.get("machine_id")
            user_id = self.scope["user"].id
            machine = await self.toggle_repair(machine_id, user_id)

            await self.channel_layer.group_send(
                "fleet", {"type": "fleet_update", "machine": machine}
            )

        elif data.get("action") == "set_repair_date":
            # Поле даты заполнено на dashboard
            # Машина автоматически становится в ремонте
            # КТГ пересчитывается сразу от введённой даты
            machine_id = data.get("machine_id")
            repair_date = data.get("repair_date")  # строка ISO формата
            user_id = self.scope["user"].id
            machine = await self.set_repair_date(machine_id, repair_date, user_id)

            await self.channel_layer.group_send(
                "fleet", {"type": "fleet_update", "machine": machine}
            )

    async def fleet_update(self, event):
        await self.send(
            text_data=json.dumps({"type": "update", "machine": event["machine"]})
        )

    async def ktg_loop(self):
        try:
            while True:
                await asyncio.sleep(KTG_TICK_INTERVAL)
                updated = await self.process_ktg_tick()

                for machine in updated:
                    await self.channel_layer.group_send(
                        "fleet", {"type": "fleet_update", "machine": machine}
                    )

        except asyncio.CancelledError:
            pass

    @database_sync_to_async
    def process_ktg_tick(self):
        step = calculate_ktg_decrease_step(KTG_TICK_INTERVAL)
        machines_in_repair = Machine.objects.filter(is_in_repair=True)
        updated = []
        # ПРОВЕРКА СБРОСА ЕЖЕМЕСЯЧНОГО КТГ

        # Берём все машины у которых задана дата сброса
        # Не только те что в ремонте — сброс касается всех
        now = datetime.now(timezone.utc)
        machines_to_reset = Machine.objects.filter(
            ktg_reset_at__isnull=False,  # дата сброса задана
            ktg_reset_at__lte=now,  # и она уже наступила
        )
        reset_ids = set(machines_to_reset.values_list("id", flat=True))

        for machine in machines_to_reset:
            # Сохраняем итог периода в KTGMonthResult
            # period_start — месяц назад от даты сброса
            KTGMonthResult.objects.create(
                machine=machine,
                value=machine.ktg_value,  # КТГ ДО сброса — это итог
                period_start=machine.ktg_reset_at - relativedelta(months=1),
                period_end=machine.ktg_reset_at,  # момент сброса
            )
            machine.ktg_value = 1.0
            # Сдвигаем дату сброса на месяц вперёд
            # relativedelta(months=1) правильно считает февраль, длинные месяцы
            if machine.repair_started_at is not None:
                machine.ktg_calc_from = now

            machine.ktg_reset_at = machine.ktg_reset_at + relativedelta(months=1)
            machine.save()
            updated.append(self._serialize(machine))

        for machine in machines_in_repair:
            if machine.id in reset_ids:
                continue
            if machine.ktg_calc_from is not None:
                calc_ktg = calculate_ktg_from_date(machine.ktg_calc_from)
                # Берём минимум — КТГ никогда не растёт в тике
                # Если calc_ktg > текущего — значит дата свежая, снижаем на шаг
                if calc_ktg < machine.ktg_value:
                    machine.ktg_value = calc_ktg
                else:
                    # Дата только что поставлена — снижаем на шаг от текущего
                    machine.ktg_value = round(machine.ktg_value - step, 6)
                    if machine.ktg_value < 0:
                        machine.ktg_value = 0

            machine.save()

            KTGHistory.objects.create(machine=machine, value=machine.ktg_value)

            updated.append(self._serialize(machine))

        return updated

    @database_sync_to_async
    def set_repair_date(self, machine_id, repair_date_str, user_id):
        """
        Устанавливает дату начала ремонта вручную.
        Машина автоматически становится в ремонте.
        КТГ пересчитывается сразу от введённой даты.
        """
        machine = Machine.objects.get(id=machine_id)

        # Парсим дату из строки формата datetime-local: '2026-06-15T08:00'
        repair_started_at = datetime.fromisoformat(repair_date_str)

        # Сохраняем дату
        machine.repair_started_at = repair_started_at
        machine.ktg_calc_from = repair_started_at
        # Автоматически ставим в ремонт
        machine.is_in_repair = True

        # Сразу пересчитываем КТГ от введённой даты
        machine.ktg_value = calculate_ktg_from_date(repair_started_at)
        machine.save()

        # Создаём лог ремонта если нет активного
        if not RepairLog.objects.filter(machine=machine, is_active=True).exists():
            RepairLog.objects.create(
                machine=machine,
                user_id=user_id,
                is_active=True,
                # Сохраняем введённую вручную дату
                repair_started_at=machine.repair_started_at,
            )

        return self._serialize(machine)

    @database_sync_to_async
    def get_machines(self):
        user = self.scope["user"]
        session = self.scope["session"]

        # Для админа и диспетчера — смотрим что выбрано в сессии
        # Они могут переключаться между участками
        if user.role in ("admin", "dispatcher"):
            section_id = session.get("viewed_section_id")
            if section_id:
                machines = (
                    Machine.objects.filter(section_id=section_id)
                    .select_related("section")
                    .order_by("name")
                )
            else:
                # Участок не выбран — показываем все машины
                machines = (
                    Machine.objects.all().select_related("section").order_by("name")
                )

        else:
            # Механик и viewer — только свой участок из профиля
            if user.section_id:
                machines = (
                    Machine.objects.filter(section_id=user.section_id)
                    .select_related("section")
                    .order_by("name")
                )
            else:
                machines = (
                    Machine.objects.all().select_related("section").order_by("name")
                )

        return [self._serialize(m) for m in machines]

    @database_sync_to_async
    def toggle_repair(self, machine_id, user_id):
        machine = Machine.objects.get(id=machine_id)
        machine.is_in_repair = not machine.is_in_repair

        if machine.is_in_repair:
            # Ставим дату начала ремонта если не введена вручную

            if (
                machine.repair_started_at is None
            ):  # при нажитии кнопки что бы дата сама ставилась.
                machine.repair_started_at = dj_timezone.now()
                machine.ktg_calc_from = machine.repair_started_at

            # НЕ пересчитываем КТГ при нажатии кнопки!
            # КТГ будет снижаться с текущего значения в следующем тике
            # Пересчёт только если дата введена вручную (repair_started_at в прошлом)

            if machine.ktg_calc_from is not None:
                calc_ktg = calculate_ktg_from_date(machine.ktg_calc_from)
                # Берём минимум — не даём КТГ расти выше текущего значения
                machine.ktg_value = min(machine.ktg_value, calc_ktg)
            machine.save()

            RepairLog.objects.create(
                machine=machine,
                user_id=user_id,
                is_active=True,
                # Сохраняем фактическую дату начала ремонта
                repair_started_at=machine.repair_started_at,
            )
        else:
            # Завершаем ремонт — очищаем дату
            machine.repair_started_at = None
            machine.ktg_calc_from = None
            machine.save()

            RepairLog.objects.filter(machine=machine, is_active=True).update(
                is_active=False, finished_at=dj_timezone.now()
            )

        return self._serialize(machine)

    def _localize_dt(self, dt, section):
        """
        Конвертирует UTC время в часовой пояс участка.
        Если участок не задан — используем UTC.
        """
        # Берём timezone участка или UTC если участка нет
        tz_name = section.timezone if section else "UTC"

        try:
            tz = pytz.timezone(tz_name)
        except pytz.exceptions.UnknownTimeZoneError:
            tz = pytz.utc

        # Конвертируем и возвращаем ISO строку
        return dt.astimezone(tz).isoformat()

    def _serialize(self, m):
        return {
            "id": m.id,
            "name": m.name,
            "board_number": m.board_number,
            "ktg_value": round(m.ktg_value, 6),
            "ktg_threshold": m.ktg_threshold,
            "is_in_repair": m.is_in_repair,
            "repair_started_at": (
                self._localize_dt(m.repair_started_at, m.section)
                if m.repair_started_at
                else None
            ),
        }
