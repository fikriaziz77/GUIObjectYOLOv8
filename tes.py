import cv2

frame = cv2.imread('assets/background.png')
cv2.circle(frame, (600,200),3, (0,255,0), 3)
cv2.circle(frame, (386,306),3, (0,255,255), 3)

cv2.imshow("hallo",frame)

cv2.waitKey(0) 

cv2.destroyAllWindows() 