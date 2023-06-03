from datetime import datetime, date

from sqlalchemy import func, text
from sqlalchemy.orm import Session
from dao import models

def get_accuracy_for_day(db: Session, user_id: int, day: date):
    result = (
        db.query(
            models.PostureData.hour,
            (models.PostureData.correct / models.PostureData.active_time * 100).label("accuracy"),
        )
        .filter(models.PostureData.day == day)
        .filter(models.PostureData.user_id == user_id)
        .order_by(models.PostureData.hour)
        .all()
    )
    return result

def get_accuracy_for_this_week(db: Session, user_id: int):
    query = text("SELECT (WEEKDAY(day)) % 7 AS day_in_week_index,"
                 "DATE_FORMAT(day, '%d-%m')," \
            " AVG(correct / active_time)* 100 AS avg_accuracy" \
            " FROM posture_data WHERE user_id = :user_id  " \
            "AND WEEK(DATE_SUB(day, INTERVAL 1 DAY)) = WEEK(DATE_SUB(CURRENT_DATE, INTERVAL 1 DAY)) " \
            "AND MONTH(day) = MONTH(CURRENT_DATE)" \
            "AND YEAR(day) = YEAR(CURRENT_DATE)" \
            "GROUP BY DAY(day) ORDER BY  day_in_week_index ;")
    result = db.execute(query, {"user_id" : user_id}).fetchall()
    return result


def get_accuracy_for_this_month(db: Session, user_id: int):
    query = text("SELECT DAY(day) - 1  as day_in_month_index,"
                 "DATE_FORMAT(day, '%d-%m'), "
                 "AVG(correct / active_time)* 100 AS avg_accuracy "
                 "FROM posture_data WHERE user_id = :user_id  "
                 "AND MONTH(day) = MONTH(CURRENT_DATE) AND YEAR(day) = YEAR(CURRENT_DATE) "
                 "GROUP BY DAY(day) ORDER BY  day_in_month_index;")
    result = db.execute(query, {"user_id" : user_id}).fetchall()
    return result


def get_incorrect_percentage_for_day(db: Session, user_id: int, day: date):
    query = text("SELECT AVG(forwarded_head / active_time) * 100 AS avg_forwarded_head_percentage, "
                 "AVG(leaning_back / active_time) * 100 AS avg_leaning_back_percentage, "
                 "AVG(leaning_forward / active_time) * 100 AS avg_leaning_forward_percentage, "
                 "AVG(wrong_leg / active_time) * 100 AS avg_wrong_leg_percentage"
                 " FROM posture_data WHERE  day = :day AND user_id = :user_id;")
    result = db.execute(query, {"user_id" : user_id, "day": day}).fetchone()
    return result



def get_incorrect_percentage_for_this_week(db: Session, user_id: int):
    query = text("SELECT AVG(forwarded_head / active_time) * 100 AS avg_forwarded_head_percentage, "
                 "AVG(leaning_back / active_time) * 100 AS avg_leaning_back_percentage, "
                 "AVG(leaning_forward / active_time) * 100 AS avg_leaning_forward_percentage, "
                 "AVG(wrong_leg / active_time) * 100 AS avg_wrong_leg_percentage"
                 " FROM posture_data WHERE  WEEK(day) = WEEK(CURRENT_DATE) AND YEAR(day) = YEAR(CURRENT_DATE) AND user_id = :user_id;")
    result = db.execute(query, {"user_id" : user_id}).fetchone()
    return result
def get_incorrect_percentage_for_this_month(db: Session, user_id: int):
    query = text("SELECT AVG(forwarded_head / active_time) * 100 AS avg_forwarded_head_percentage, "
                 "AVG(leaning_back / active_time) * 100 AS avg_leaning_back_percentage, "
                 "AVG(leaning_forward / active_time) * 100 AS avg_leaning_forward_percentage, "
                 "AVG(wrong_leg / active_time) * 100 AS avg_wrong_leg_percentage"
                 " FROM posture_data WHERE  MONTH(day) = MONTH(CURRENT_DATE) AND YEAR(day) = YEAR(CURRENT_DATE) AND user_id = :user_id;")
    result = db.execute(query, {"user_id" : user_id}).fetchone()
    return result

def get_posture_data(db: Session, user_id: int):
    query = text("SELECT posture_data_id FROM posture_data "
                 "WHERE  hour = HOUR(CURRENT_TIME) "
                 "AND day = current_date and user_id = :user_id")
    result = db.execute(query, {"user_id" : user_id}).fetchone()
    return result

def create_posture_data(db: Session, user_id, correct, forwarded_head, leaning_back, leaning_forward, wrong_leg):
    query = text("INSERT INTO posture_data ( user_id, hour, day, active_time, correct, forwarded_head, leaning_back, leaning_forward, wrong_leg)"
                 " VALUES (:user_id, HOUR(CURRENT_TIME), CURRENT_DATE, 1, :correct, :forwarded_head,:leaning_back,:leaning_forward,:wrong_leg) ")
    db.execute(query, {"user_id": user_id, "correct": correct, "forwarded_head": forwarded_head,"leaning_back": leaning_back, "leaning_forward": leaning_forward, "wrong_leg": wrong_leg })
    db.commit()

def update_posture_data(db: Session, user_id, posture_data_id, correct, forwarded_head, leaning_back, leaning_forward, wrong_leg):
    query = text("UPDATE posture_data SET active_time = active_time+1, correct = correct + :correct, forwarded_head = forwarded_head + :forwarded_head,leaning_back = leaning_back+:leaning_back,  leaning_forward = leaning_forward +:leaning_forward, wrong_leg = wrong_leg+ :wrong_leg"
                 " WHERE posture_data_id =:posture_data_id and user_id = :user_id;")
    db.execute(query, {"user_id": user_id,"posture_data_id": posture_data_id, "correct": correct, "forwarded_head": forwarded_head,"leaning_back": leaning_back, "leaning_forward": leaning_forward, "wrong_leg": wrong_leg })
    db.commit()

def update_device_ip(db: Session, user_id, ip):
    query = text("UPDATE  device_ip SET ip = :ip WHERE user_id = :user_id")
    db.execute(query, {"user_id": user_id, "ip": ip})
    db.commit()

def get_device_ip(db: Session, user_id):
    query = text("SELECT ip FROM device_ip WHERE  user_id = :user_id")
    result = db.execute(query, {"user_id": user_id}).fetchone()
    return result
def update_fcm(db:Session, user_id, fcm):
    query = text("DELETE FROM fcm WHERE user_id = :user_id")
    db.execute(query, {"user_id": user_id})
    query = text("INSERT INTO  fcm VALUES (:user_id, :fcm)")
    db.execute(query, {"user_id": user_id, "fcm": fcm})
    db.commit()
def get_fcm_token(db:Session, user_id):
    query = text("SELECT fcm FROM fcm WHERE user_id = :user_id")
    result = db.execute(query, {"user_id": user_id}).fetchone()
    return result
