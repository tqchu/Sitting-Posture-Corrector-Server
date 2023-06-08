import calendar
import os
import pickle
import time
from datetime import date, datetime

import httpx
import trio
from PIL import Image
from fastapi import FastAPI, UploadFile, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from ultralytics import YOLO

from dao import crud
from dao import database
from dao import models
import yolov8_od as od
from util.utils import get_body
from model import predict
keypoint_model = YOLO('M:/HK6/PBL5/Repos/FastAPIServer/weights/yolov8_pose_13_5.pt')
# keypoint_model = YOLO('yolov8-pose-224.pt')


def load_model():
    # model = YOLO('Sitting-Posture-Corrector-ML/ObjectDetection/runs/detect/train5/weights/s_best_yolov8.pt')
    model = YOLO('M:/HK6/PBL5/Repos/FastAPIServer/Sitting-Posture-Corrector-ML/ObjectDetection/runs/detect/train7/weights/best.pt')
    return model


app = FastAPI()
# Load object detection model
od_model = load_model()

# Load the saved forest model
current_directory = os.path.dirname(__file__)
with open(current_directory + '/Sitting-Posture-Corrector-ML/weights/head_forest.pkl', 'rb') as f:
    head_forest = pickle.load(f)
with open(current_directory + '/Sitting-Posture-Corrector-ML/model/back_forest.pkl', 'rb') as f:
    back_forest = pickle.load(f)
with open(current_directory + '/Sitting-Posture-Corrector-ML/model/leg_forest.pkl', 'rb') as f:
    leg_forest = pickle.load(f)
headers = {"Content-Type": "application/json",
           "Authorization": "key=AAAAvGINhmc:APA91bE9Rbm1ivQWOR_qs6VXSIa33u_KOIdzh8XHh2INN3Wt0XCqoSongiM7dcndqdXjPknkR6RCS-48o77j_tYeId6u5B5x4qm_scIPB95CdlTN106Xn-LTBEPvSg-H7z-2H3I7yORv"}

body = None
async def send_notification():
    async with httpx.AsyncClient() as client:
        response = await client.post("https://fcm.googleapis.com/fcm/send",headers= headers,json=body )

def notify_mobile(result, fcm_token):
    global body
    body = get_body(result, fcm_token)
    if body!=None:
        trio.run(send_notification)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
def update_device_ip(db: Session, user_id, ip):
    crud.update_device_ip(db, user_id, ip)
def update_db(result, user_id: int, db: Session):
    head = result[0][0]
    back = result[1][0]
    leg = result[2][0]
    correct_incr = 0
    if head == 1 and back == 1 and leg == 1:
        correct_incr = 1
    leaning_back_incr = 0
    leaning_forward_incr = 0
    if back == 2:
        leaning_back_incr = 1
    elif back == 3:
        leaning_forward_incr = 1
    record = crud.get_posture_data(db=db, user_id=user_id)
    if record is None:
        crud.create_posture_data(db=db, user_id=user_id, correct=correct_incr, forwarded_head= 1-head,leaning_back= leaning_back_incr, leaning_forward= leaning_forward_incr, wrong_leg= 1-leg)
    else:
        crud.update_posture_data(db =db, user_id = user_id, posture_data_id= record[0], correct=correct_incr, forwarded_head= 1-head,leaning_back= leaning_back_incr, leaning_forward= leaning_forward_incr, wrong_leg= 1-leg)
# Load alphapose model
# alphapose_model = alphapose.load_model()
# Load predict model
# predict_model = predict.load_model()
@app.get("/ip")
async def get_device_ip(db: Session = Depends(get_db)):
    return crud.get_device_ip(db, 1)[0]
@app.get("/")
async def root():
    return {"message": "Hello World"}
@app.post("/fcm")
async def fcm(body: dict, db: Session = Depends(get_db)):
    crud.update_fcm(db, body["user_id"] , body["fcm"])
    print("FCM updated: ", body["fcm"])
    return {"message": "Update successfully!"}
@app.post("/update_ip")
async def update_ip(ip: str,db: Session = Depends(get_db)):
    print("Ip updated: ", ip)
    update_device_ip(db,1, ip)
    return "Ip updated: " + ip
@app.post("/upload")
async def upload(file: UploadFile, db: Session = Depends(get_db)):
    # Tracking time
    init_millis = round(time.time() * 1000)

    image = Image.open(file.file)
    image = image.rotate(90, expand=True)
    image.save( "D:/Dataset/ORIGINAL/TYPE1_DONE_CHI_154/66"+ "/" + str(init_millis) + ".jpg")
    # Step 1: Preprocess image
    preprocessed_image = od.process_image(image, od_model)
    # For debugging
    preprocessed_image.save("preprocessed_image.jpg")
    # Tracking time
    preprocess_duration = round(time.time() * 1000) - init_millis
    print("Preprocessing duration:", preprocess_duration)
    # Step 2: Feature extraction and predict
    result = predict.predict(head_forest, back_forest, leg_forest, keypoint_model, preprocessed_image)
    # Tracking time
    print("Predict duration:", round(time.time() * 1000) - init_millis - preprocess_duration)
    print("Total duration:", round(time.time() * 1000) - init_millis)

    fcm_token = crud.get_fcm_token(db, 1)[0]

    # Step 3: Notify mobile app
    notify_mobile(result, fcm_token)
    # For debugging
    update_db(result, 1, db)
    print(result)
    return (int(result[0][0])) * 100 + (int(result[1][0])) * 10 + (int(result[2][0]))




@app.get("/accuracy/{user_id}/day/{day}")
def get_accuracy_for_day(user_id: int,day: date, db: Session = Depends(get_db)):
    result = crud.get_accuracy_for_day(db=db, user_id=user_id,day= day)
    return jsonable_encoder(models.AccuracyForADay(items= models.convert_to_array(result, 24)))

@app.get("/accuracy/{user_id}/this_week")
def get_accuracy_for_this_week(user_id: int,db: Session = Depends(get_db)):
    result = crud.get_accuracy_for_this_week(db=db, user_id=user_id)
    return jsonable_encoder(models.AccuracyOfDuration(items= models.convert_date_to_dict(result, 7)))

@app.get("/accuracy/{user_id}/this_month")
def get_accuracy_for_this_month(user_id: int,db: Session = Depends(get_db)):
    now = datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    result = crud.get_accuracy_for_this_month(db=db, user_id=user_id)
    return jsonable_encoder(models.AccuracyOfDuration(items= models.convert_date_to_dict(result, days_in_month)))


@app.get("/incorrect_percentage/{user_id}/day/{day}")
def get_incorrect_percentage_for_day(user_id: int,day: date, db: Session = Depends(get_db)):
    result = crud.get_incorrect_percentage_for_day(db=db, user_id=user_id, day= day)
    return jsonable_encoder(models.IncorrectPercentage(list = result))


@app.get("/incorrect_percentage/{user_id}/this_week")
def get_incorrect_percentage_for_this_week(user_id: int, db: Session = Depends(get_db)):
    result = crud.get_incorrect_percentage_for_this_week(db=db, user_id=user_id)
    return jsonable_encoder(models.IncorrectPercentage(list = result))


@app.get("/incorrect_percentage/{user_id}/this_month")
def get_incorrect_percentage_for_this_month(user_id: int, db: Session = Depends(get_db)):
    result = crud.get_incorrect_percentage_for_this_month(db=db, user_id=user_id)
    return jsonable_encoder(models.IncorrectPercentage(list = result))