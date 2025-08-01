import pytest
from schedule import Customer, Schedule

CAPACITY_PER_HOUR = 3
UNDER_CAPACITY = 1
# TEST_CUSTOMER = Customer("asdf", "010-1111-2222")
# TEST_CUSTOMER_WITH_MAIL = Customer("asdf", "010-1111-2222", "test@test.com")

from communication import SmsSender, MailSender
from booking_scheduler import BookingScheduler
from datetime import datetime, timedelta

TEST_TIME = datetime.strptime("2025/08/01 09:00", "%Y/%m/%d %H:%M")


class TestableBookingScheduler(BookingScheduler):
    def __init__(self, capacity_per_hour, date_time):
        super().__init__(capacity_per_hour)
        self._date_time = date_time

    def get_now(self):
        return datetime.strptime(self._date_time, "%Y/%m/%d %H:%M")


@pytest.fixture
def customer(mocker):
    customer = mocker.Mock()
    customer.get_email.return_value = None
    return customer


@pytest.fixture
def customer_with_mail(mocker):
    customer = mocker.Mock()
    customer.get_email.return_value = "test@test.com"
    return customer


@pytest.fixture
def booking_scheduler():
    return BookingScheduler(CAPACITY_PER_HOUR)


@pytest.fixture
def booking_scheduler_with_sms_mock(mocker):
    booking_scheduler = BookingScheduler(CAPACITY_PER_HOUR)
    testable_sms_sender = mocker.Mock()
    booking_scheduler.set_sms_sender(testable_sms_sender)
    return booking_scheduler, testable_sms_sender


@pytest.fixture
def booking_scheduler_with_mail_mock(mocker):
    booking_scheduler = BookingScheduler(CAPACITY_PER_HOUR)
    testable_mail_sender = mocker.Mock()
    booking_scheduler.set_mail_sender(testable_mail_sender)
    return booking_scheduler, testable_mail_sender


def test_예약은_정시에만_가능하다_정시가_아닌경우_예약불가(booking_scheduler):
    test_time = datetime.strptime("2025/08/01 09:05", "%Y/%m/%d %H:%M")
    customer = Customer("asdf", "010-1111-2222")
    schedule = Schedule(test_time, 1, customer)

    with pytest.raises(ValueError):
        booking_scheduler.add_schedule(schedule)


def test_예약은_정시에만_가능하다_정시인_경우_예약가능(booking_scheduler, customer):
    schedule = Schedule(TEST_TIME, UNDER_CAPACITY, customer)

    booking_scheduler.add_schedule(schedule)
    assert booking_scheduler.has_schedule(schedule)


def test_시간대별_인원제한이_있다_같은_시간대에_Capacity_초과할_경우_예외발생(booking_scheduler, customer):
    schedule = Schedule(TEST_TIME, UNDER_CAPACITY, customer)

    booking_scheduler.add_schedule(schedule)
    booking_scheduler.add_schedule(schedule)
    booking_scheduler.add_schedule(schedule)
    with pytest.raises(ValueError, match="Number of people is over restaurant capacity per hour"):
        booking_scheduler.add_schedule(schedule)


def test_시간대별_인원제한이_있다_같은_시간대가_다르면_Capacity_차있어도_스케쥴_추가_성공(booking_scheduler, customer):
    schedule = Schedule(TEST_TIME, UNDER_CAPACITY, customer)
    booking_scheduler.add_schedule(schedule)
    booking_scheduler.add_schedule(schedule)
    booking_scheduler.add_schedule(schedule)

    new_schedule = Schedule(TEST_TIME + timedelta(hours=1), UNDER_CAPACITY, customer)
    booking_scheduler.add_schedule(new_schedule)
    booking_scheduler.add_schedule(new_schedule)
    booking_scheduler.add_schedule(new_schedule)

    assert booking_scheduler.has_schedule(schedule)
    assert booking_scheduler.has_schedule(new_schedule)


def test_예약완료시_SMS는_무조건_발송(booking_scheduler_with_sms_mock, customer):
    booking_scheduler, sms_mock = booking_scheduler_with_sms_mock
    schedule = Schedule(TEST_TIME, UNDER_CAPACITY, customer)
    booking_scheduler.add_schedule(schedule)
    sms_mock.send.assert_called()


def test_이메일이_없는_경우에는_이메일_미발송(booking_scheduler_with_mail_mock, customer):
    booking_scheduler, mail_mock = booking_scheduler_with_mail_mock
    schedule = Schedule(TEST_TIME, UNDER_CAPACITY, customer)
    booking_scheduler.add_schedule(schedule)
    mail_mock.send_mail.assert_not_called()


def test_이메일이_있는_경우에는_이메일_발송(booking_scheduler_with_mail_mock, customer_with_mail):
    booking_scheduler, mail_mock = booking_scheduler_with_mail_mock
    schedule = Schedule(TEST_TIME, UNDER_CAPACITY, customer_with_mail)
    booking_scheduler.add_schedule(schedule)
    mail_mock.send_mail.assert_called_once()


def test_현재날짜가_일요일인_경우_예약불가_예외처리(mocker, customer):
    mock_get_now = mocker.patch(
        'booking_scheduler.BookingScheduler.get_now',
    return_value = datetime.strptime("2021/03/28 17:00", "%Y/%m/%d %H:%M"))
    booking_scheduler = BookingScheduler(CAPACITY_PER_HOUR)
    schedule = Schedule(TEST_TIME, UNDER_CAPACITY, customer)

    with pytest.raises(ValueError):
        booking_scheduler.add_schedule(schedule)


def test_현재날짜가_일요일이_아닌경우_예약가능(mocker, customer):
    mock_get_now = mocker.patch(
        'booking_scheduler.BookingScheduler.get_now',
    return_value = datetime.strptime("2024/06/03 17:00", "%Y/%m/%d %H:%M"))
    booking_scheduler = BookingScheduler(CAPACITY_PER_HOUR)
    schedule = Schedule(TEST_TIME, UNDER_CAPACITY, customer)
    booking_scheduler.add_schedule(schedule)
    assert booking_scheduler.has_schedule(schedule)
