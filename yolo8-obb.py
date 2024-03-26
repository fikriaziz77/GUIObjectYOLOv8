from ultralytics import YOLO
from PIL import Image
import cv2, math, time
import numpy as np
import torch

#torch.cuda.set_device(0)
model = YOLO("/weight/3000pics - 100x35.pt")

cap = cv2.VideoCapture(0)
prev_time = 0
curr_time = 0
frame_count = 0
fps = 0
font = cv2.FONT_HERSHEY_PLAIN
color = (255,0,0)

while True:
    ret, unscale_fr = cap.read()  
    
  
    if ret:

        unflip_frame = cv2.resize(unscale_fr, (320, 240))
        frame = cv2.flip(unflip_frame,1)

        results = model.predict(frame, imgsz=320, conf=0.5)
        result = results[0]
        box = result.obb

        for box in result.obb:
            class_id = result.names[box.cls[0].item()]
            cords = box.xywhr[0].tolist()
            cords_corner = box.xyxyxyxy[0].tolist()
            conf = round(box.conf[0].item(), 2)
            
            px1 = int(cords_corner[0][0])
            py1 = int(cords_corner[0][1])
            cv2.circle(frame, (px1,py1), 2, (0,0,255), 2)

            px2 = int(cords_corner[1][0])
            py2 = int(cords_corner[1][1])
            cv2.circle(frame, (px2,py2), 2, (0,255,0), 2)

            x = round(cords[0])
            y = round(cords[1])
            w = round(cords[2])
            h = round(cords[3])
            val = cords[4]

            r = round(math.degrees(val),2)
            rect = ((x, y), (w, h), r)
            box = cv2.boxPoints(rect) 
            box = np.int0(box)
            cv2.drawContours(frame,[box],0,color,1)
            cv2.putText(frame, f"{class_id} :  {round(val,2)}rad-{r}deg",(x,y), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0), 2)

        # Calculate FPS
        curr_time = time.time()
        frame_count += 1
        if curr_time - prev_time >= 1:
            fps = frame_count / (curr_time - prev_time)
            frame_count = 0
            prev_time = curr_time

        fps_text = f"FPS: {int(fps)}"
        cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        cv2.imshow("Camera FPS", frame)

    if cv2.waitKey(1) == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
