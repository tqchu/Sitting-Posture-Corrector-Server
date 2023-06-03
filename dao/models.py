from datetime import datetime, timedelta
import statistics
from typing import List

from sqlalchemy import Column, Integer, String, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship

from dao.database import Base
def convert_to_array(data, length):
    hours = [None] * length
    for hour, value in data:
        hours[hour] = float(value)
    return hours


def convert_date_to_array( data, length):
    hours = [None] * length
    for index, datestr, value in data:
        hours[index] = float(value)
    return hours


def convert_date_to_dict( lst, n):
    result = {}

    array_with_none = convert_date_to_array(lst, n)
    if len(lst) == 0:
        today = datetime.today()
        if n == 7:
            start_date = today - timedelta(days=today.weekday())
        else:
            start_date = datetime(today.year, today.month, 1)
    else:
        start_date = datetime.strptime(lst[0][1], '%d-%m') - timedelta(days=lst[0][0])
    for i in range(n):
        # date str
        date_str = datetime.strftime(start_date + timedelta(days=i), '%d-%m')
        # value
        value = array_with_none[i]
        result[date_str] = value
    return result

class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)

    posture_data = relationship("PostureData", back_populates="user")

class PostureData(Base):
    __tablename__ = "posture_data"

    posture_data_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    hour = Column(Integer, nullable=False)
    day = Column(Date, nullable=False)
    active_time = Column(Integer, nullable=False)
    correct = Column(Integer, nullable=False)
    forwarded_head = Column(Integer, nullable=False)
    leaning_back = Column(Integer, nullable=False)
    leaning_forward = Column(Integer, nullable=False)
    wrong_leg = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "hour", "day", name="unique_hour_user"),)

    user = relationship("User", back_populates="posture_data")

class AccuracyForADay:
    items: List
    average: float

    def __init__(self, hours: List, day: int):
        self.items = hours
        self.average = day

    def __init__(self, items: List):
        self.items = items
        filtered_values = [x for x in self.items if x is not None]
        if len(filtered_values) == 0:
            self.average = None
        else:
            self.average= statistics.mean(filtered_values)


class AccuracyOfDuration:
    items: dict
    average: float

    def __init__(self, items: dict, day: int):
        self.items = items
        self.average = day

    def __init__(self, items: dict):
        self.items = items
        filtered_values = [x for x in self.items.values() if x is not None]
        if len(filtered_values) == 0:
            self.average = None
        else:
            self.average = statistics.mean(filtered_values)

class IncorrectPercentage:
    forwarded_head: float
    leaning_back: float
    leaning_forward: float
    wrong_leg: float

    def __init__(self, list: List):
        self.forwarded_head = list[0]
        self.leaning_back = list[1]
        self.leaning_forward = list[2]
        self.wrong_leg = list[3]