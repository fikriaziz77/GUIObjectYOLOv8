from ultralytics import YOLO
from PIL import Image
import cv2, math, time
import numpy as np
import torch

torch.cuda.set_device(0)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,1024)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,576)
model = YOLO("weights/3000pics - 100x35.pt")

prev_time = 0
curr_time = 0
frame_count = 0
fps = 0
font = cv2.FONT_HERSHEY_PLAIN
color = (255,0,0)
run_prog = True
conf = 0 
x = 0
y = 0
r = 0.0

def getobloct():
    valx = x
    valy = y
    return [valx,valy]


while run_prog:
    ret, frame = cap.read()  
  
    if ret:
        frame = frame[0:576, 150:865]
        frame = cv2.resize(frame, (0,0), fx=0.7,fy=0.7)
        results = model.predict(frame, imgsz=320, conf=0.3, device='0')
        result = results[0]
        box = result.obb
        if result:
            for box in result.obb:
                class_id = result.names[box.cls[0].item()]
                cords = box.xywhr[0].tolist()
                cords_corner = box.xyxyxyxy[0].tolist()
                conf = round(box.conf[0].item(), 2)
                
                #px1 = int(cords_corner[0][0])
                #py1 = int(cords_corner[0][1])
                #cv2.circle(frame, (px1,py1), 2, (0,0,255), 2)

                #px2 = int(cords_corner[1][0])
                #py2 = int(cords_corner[1][1])
                #cv2.circle(frame, (700,400), 2, (0,255,0), 2)

                x = round(cords[0])
                y = round(cords[1])
                w = round(cords[2])
                h = round(cords[3])
                val = cords[4]

                r = round(math.degrees(val),2)
                r = abs(r)
                rect = ((x, y), (w, h), r)
                box = cv2.boxPoints(rect) 
                box = np.int0(box)
                cv2.drawContours(frame,[box],0,color,1)
                #cv2.putText(frame, f"{x},{y},{r}",(2,2), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0), 2)
        else:
            x = 0
            y = 0
            r = 0.0
        # Calculate FPS
        curr_time = time.time()
        frame_count += 1
        if curr_time - prev_time >= 1:
            fps = frame_count / (curr_time - prev_time)
            frame_count = 0
            prev_time = curr_time

        fps_text = f"FPS: {round(fps,2)}"
        cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        conf_text = f"Conf: {conf*100}%"
        cv2.putText(frame, conf_text, (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        fxy_text = f"Coor Frame: {x},{y}"
        cv2.putText(frame, fxy_text, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)                
        
        if x==0 and y==0:
            rx = x
            ry = y
        else:
            rx = round((0.4296*x)-107.2,2)
            ry = round((-0.4588*y)+92.5,2)
        
        rxy_text = f"Coor Real: {rx},{ry}"
        cv2.putText(frame, rxy_text, (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)        
        
        r_text = f"Orient: {r}"
        cv2.putText(frame, r_text, (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)        

        
        cv2.imshow("Camera FPS", frame)
        
    if cv2.waitKey(1) == ord('q'):
        break 
        
# Release resources

cap.release()
cv2.destroyAllWindows()
