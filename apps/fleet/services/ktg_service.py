import calendar
from datetime import datetime, timezone

# Режим тестирования — True = быстрое снижение для демонстрации
# False = реальный расчёт по месяцу
TEST_MODE = True

# В тестовом режиме снижаем на столько за тик
TEST_STEP = 0.001  # за 10 сек = 0.001, за 100 тиков = 0.1


def get_seconds_in_month(dt=None):
    """
    Возвращает количество секунд в текущем месяце.
    Июнь (30 дней):   30 * 24 * 3600 = 2_592_000 сек
    Январь (31 день): 31 * 24 * 3600 = 2_678_400 сек
    Февраль (28):     28 * 24 * 3600 = 2_419_200 сек
    """
    if dt is None:
        dt = datetime.now()

    days_in_month = calendar.monthrange(dt.year, dt.month)[1]
    return days_in_month * 24 * 3600


def calculate_ktg_decrease_step(interval_seconds):
    """
    Считает шаг снижения КТГ за один тик.

    Реальный режим:
        шаг = interval_seconds / секунд_в_месяце
        Июнь, тик 10 сек: 10 / 2_592_000 = 0.0000038580

    Тестовый режим:
        фиксированный шаг TEST_STEP = 0.001
        видно невооружённым глазом
    """
    if TEST_MODE:
        return TEST_STEP

    seconds_in_month = get_seconds_in_month()
    step = interval_seconds / seconds_in_month
    return round(step, 10)


def calculate_ktg_from_date(repair_started_at):
    """
    Пересчитывает КТГ от даты начала ремонта.

    Формула:
        прошло_секунд = сейчас - repair_started_at
        КТГ = 1.0 - (прошло_секунд / секунд_в_месяце)

    Например машина в ремонте 15 дней в июне:
        прошло = 15 * 24 * 3600 = 1_296_000 сек
        КТГ = 1.0 - (1_296_000 / 2_592_000) = 0.5 = 50%
    """
    now = datetime.now(timezone.utc)

    if repair_started_at.tzinfo is None:
        repair_started_at = repair_started_at.replace(tzinfo=timezone.utc)

    elapsed_seconds = (now - repair_started_at).total_seconds()
    seconds_in_month = get_seconds_in_month(repair_started_at)

    ktg = 1.0 - (elapsed_seconds / seconds_in_month)
    ktg = max(0.0, min(1.0, ktg))

    return round(ktg, 6)