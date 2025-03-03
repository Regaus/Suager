from typing import Type

from regaus import time


#  def save():
#     pickle.dump(birthdays, open("data/birthdays.pickle", "wb+"), protocol=pickle.DEFAULT_PROTOCOL)


def birthdays_today(bot: str) -> list["Birthday"]:
    """ Returns list of people who have their birthday right now and have not yet got the birthday status """
    return [birthday for birthday in birthdays[bot].values() if birthday.is_birthday() and not birthday.has_role]


def birthdays_ended(bot: str) -> list["Birthday"]:
    """ Returns list of people no longer have their birthday but still have the birthday status """
    return [birthday for birthday in birthdays[bot].values() if not birthday.is_birthday() and birthday.has_role]


class Birthday:
    def __init__(self, uid: int, birthday: time.date, tz: time.tzinfo, bot: str, has_role: bool = False):
        self.uid: int = uid
        self.birthday_date: time.date = birthday
        self.tz: time.tzinfo = tz
        self.time_class: Type[time.Earth] = self.birthday_date.time_class
        self.has_role: bool = has_role  # This is only used to store whether the person's birthday has been noticed by the bots, so it's False by default
        self.bot: str = bot
        self.start_time = time.time(6, 0, 0) if self.bot == "cobble" else time.time()  # Kargadian birthdays start at 6:00
        self.push_birthday()

    def now(self) -> time.datetime:
        return time.datetime.now(time.timezone.utc, self.time_class)

    @property
    def birthday(self) -> time.datetime:
        return time.datetime.combine(self.birthday_date, self.start_time, self.tz)

    @property
    def birthday_utc(self) -> time.datetime:
        return self.birthday.as_tz(time.timezone.utc)

    @property
    def birthday_end(self) -> time.datetime:
        return self.birthday_utc + time.timedelta(days=1)

    def is_birthday(self) -> bool:
        return self.birthday_utc <= self.now() <= self.birthday_end

    def push_birthday(self):
        while self.now() > self.birthday_end:
            self.birthday_date.replace_self(year=self.birthday_date.year + 1)

    def __repr__(self):
        return f"{self.__class__.__module__}.{self.__class__.__qualname__}({self.uid}, {self.birthday_date!r}, {self.tz!r}, {self.bot!r})"

    def __str__(self):
        return f"{self.birthday_date.iso()} TZ{time.format_offset(self.tz.utcoffset(self.birthday_utc.to_earth_time().to_datetime().replace(tzinfo=None)))}"


birthdays: dict[str, dict[int, Birthday]] = {}
# try:
#     birthdays = pickle.load(open("data/birthdays.pickle", "rb"))  # It should automatically determine the protocol version
# except (FileNotFoundError, EOFError):
#     birthdays = {}
