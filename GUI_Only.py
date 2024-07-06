from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QImage, QPixmap
import cv2,time,system_info, math
import numpy as np
import serial
import serial.tools.list_ports as list_ports

from ultralytics import YOLO
import torch
torch.cuda.set_device(0)

global mul_jog
mul_jog = 0

global _isAuto_run
_isAuto_run = False

global objpos
objpos = [0,0,0]
 
class ThreadClass(QThread):
    ImageUpdate = pyqtSignal(np.ndarray)
    loop = True
    status = pyqtSignal(str)
    
    def run(self):
        global _isAuto_run
        _isAuto_run = True
        
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,1024)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,576)
        model = YOLO("weights/3000pics - 100x35.pt")
        
        while self.loop:
            ret, fr = cap.read()  
  
            if ret:
                fr = fr[0:576, 150:865]
                fr = cv2.resize(fr, (0,0), fx=0.7,fy=0.7)
                results = model.predict(fr, imgsz=320, conf=0.3, device='0')
                result = results[0]
                box = result.obb
                  
                frame = cv2.imread('assets/background2.png')
                frame = cv2.resize(frame, (630,420))
                    
                if result:    
                    cords = box.xywhr[0].tolist()
                    x = round(cords[0])
                    y = round(cords[1])
                    val = cords[4]
                    r = round(math.degrees(val),2)
                    r = abs(r)
                    
                    if r > 180:
                        r = r-180
                        
                    status = "background-color: rgb(0,255,0)"
                    
                    guix = round(1.2587*x)
                    guiy = round(1.0417*y)
                    rect = ((guix, guiy), (110, 110), r)
                    boxx = cv2.boxPoints(rect) 
                    boxx = np.int0(boxx)
                    cv2.drawContours(frame,[boxx],0,(0,0,255),2)
                    cv2.circle(frame, (guix,guiy), 1, (0,0,255), 3)
                    
                else:
                    x = 0
                    y = 0
                    r = 0.0
                    status = "background-color: rgb(255,0,0)"
                
                global objpos
                objpos = [x,y,r]
            
            self.ImageUpdate.emit(frame)
            
            self.status.emit(status)
      
    def stop(self):
        self.loop = False
        
        global _isAuto_run
        _isAuto_run = False
        self.quit()

class boardInfoClass(QThread):
    cpu = pyqtSignal(float)
    ram = pyqtSignal(tuple)
    temp = pyqtSignal(float)
    
    def run(self):
        self.ThreadActive = True
        while self.ThreadActive:
            cpu = system_info.getCPU()
            ram = system_info.getRAM()
            temp = system_info.getTemp()
            self.cpu.emit(cpu)
            self.ram.emit(ram)
            self.temp.emit(temp)
            
    def stop(self):
        self.ThreadActive = False
        self.quit()


class Window_CommSetting(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("screens/comm_setting.ui",self)
        
class Window_ComingSoon(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("screens/comingsoon.ui",self)
        
class Window_About(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("screens/about.ui",self)
        

class MainWindow(QMainWindow):
    
    def show_manual_button(self):
        self.pb_xmin.setEnabled(True)
        self.pb_ymin.setEnabled(True)
        self.pb_zmin.setEnabled(True)
        self.pb_yawmin.setEnabled(True)
        self.pb_xplus.setEnabled(True)
        self.pb_yplus.setEnabled(True)
        self.pb_zplus.setEnabled(True)
        self.pb_yawplus.setEnabled(True)
        self.pb_grip.setEnabled(True)
        self.slider_jog.setEnabled(True)
        self.lbl_jog.setEnabled(True)
        self.pb_homing.setEnabled(True)
        self.plot_start.setEnabled(False)
        self.plot_stop.setEnabled(False)

    def hide_manual_button(self):
        self.pb_xmin.setEnabled(False)
        self.pb_ymin.setEnabled(False)
        self.pb_zmin.setEnabled(False)
        self.pb_yawmin.setEnabled(False)
        self.pb_xplus.setEnabled(False)
        self.pb_yplus.setEnabled(False)
        self.pb_zplus.setEnabled(False)
        self.pb_yawplus.setEnabled(False)
        self.pb_grip.setEnabled(False)
        self.slider_jog.setEnabled(False)
        self.lbl_jog.setEnabled(False)
        self.pb_homing.setEnabled(False)
        self.plot_start.setEnabled(True)
        self.plot_stop.setEnabled(True)
    
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("screens/main_interface.ui",self)
        
        #setting uiplot
        self.plot_start.clicked.connect(self.StartPlot)
        self.plot_stop.clicked.connect(self.StopPlot)
        
        #manual button
        self.hide_manual_button()
        self.cb_manual.clicked.connect(self.manualdrive)
        self.slider_jog.valueChanged.connect(self.leveljog)
        self.pb_grip.clicked.connect(self.man_grip)
        self.pb_xmin.clicked.connect(lambda:self.movemanualrobot(self.pb_xmin))
        self.pb_xplus.clicked.connect(lambda:self.movemanualrobot(self.pb_xplus))
        self.pb_ymin.clicked.connect(lambda:self.movemanualrobot(self.pb_ymin))
        self.pb_yplus.clicked.connect(lambda:self.movemanualrobot(self.pb_yplus))
        self.pb_zmin.clicked.connect(lambda:self.movemanualrobot(self.pb_zmin))
        self.pb_zplus.clicked.connect(lambda:self.movemanualrobot(self.pb_zplus))
        
        self.pb_yawmin.clicked.connect(lambda:self.movemanualrobotw(self.pb_yawmin))
        self.pb_yawplus.clicked.connect(lambda:self.movemanualrobotw(self.pb_yawplus))     
        
        #resource usage cpu
        self.resource_usage = boardInfoClass()
        self.resource_usage.start()
        self.resource_usage.cpu.connect(self.getCPU_usage)
        self.resource_usage.ram.connect(self.getRAM_usage)
        self.resource_usage.temp.connect(self.getTemp_usage)
        
        #homingrobot
        self.pb_homing.clicked.connect(self.sendDataHoming)
        
        #grab_object
        self.pb_grab.clicked.connect(self.sendDataPosition)
        
        #runtime start
        self.lcd_timer = QTimer()
        self.lcd_timer.timeout.connect(self.clock_func)
        self.lcd_timer.start()
        
        #
        self.pb_grab.setEnabled(False)
        self.stat_obj.setEnabled(False)
        
        #communication serial menu
        self.menuComm.triggered.connect(self.MenuSerialComm)
        self.win_showset = Window_CommSetting()
        self.win_showset.comm_portlist.addItems([comport.device for comport in list_ports.comports()])
        for x in serial.Serial.BAUDRATES:
            if (x >= 9600 and x <=115200):
                self.win_showset.comm_baudrate.addItems([str(x)])
        self.win_showset.comm_status.setPixmap(QPixmap('assets/disconnect.png'))
        self.win_showset.comm_test.clicked.connect(self.SerialCommTest)
        self.win_showset.comm_refresh.clicked.connect(self.SerialCommRefresh)
        
        #comingsoon menu
        self.actionNew_GCODE.triggered.connect(self.MenuComingSoon)
        self.actionOpen_GCODE_2.triggered.connect(self.MenuComingSoon)
        self.actionSave_GCODE.triggered.connect(self.MenuComingSoon)
        self.actionSave_As.triggered.connect(self.MenuComingSoon)
        self.win_comingsoon = Window_ComingSoon()
        
        #close menu
        self.actionExit.triggered.connect(self.MenuExit)

        #about menu
        self.actionAbout.triggered.connect(self.MenuAbout)
        self.win_about = Window_About()

        
    def manualdrive(self):
        if self.cb_manual.isChecked():
            self.show_manual_button()
            self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Manual Mode Active!")
            
        else:
            self.hide_manual_button()
            self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Manual Mode Deactive!")
    
    def movemanualrobot(self,button):
        global mul_jog
        
        manx = 0
        many = 0
        manz = 0
        
        if mul_jog > 0:
            if button.text() == 'X+':
                manx = 1*mul_jog
            elif button.text() == 'X-':
                manx = -1*mul_jog
            elif button.text() == 'Y+':
                many = 1*mul_jog
            elif button.text() == 'Y-':
                many = -1*mul_jog
            elif button.text() == 'Z+':
                manz = 1*mul_jog
            elif button.text() == 'Z-':
                manz = -1*mul_jog
            
            data = f"2,{manx},{many},{manz}"
            self.ser.write(data.encode('utf-8'))
            res_delta = self.ser.readline().decode('utf-8').strip()
            self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: {res_delta}")
        
            

    def movemanualrobotw(self,button):
        global mul_jog
        
        manyaw = 0
        
        if button.text() == 'YAW+':
            manyaw = 1*mul_jog
        elif button.text() == 'YAW-':
            manyaw = -1*mul_jog
            
        data = f"5,{manyaw}"
        self.ser.write(data.encode('utf-8'))
        res_delta = self.ser.readline().decode('utf-8').strip()
        self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: {res_delta}")        
    
    def leveljog(self):
        global mul_jog
        
        if self.slider_jog.value() == 0:
            self.lbl_jog.setText("x0")
            mul_jog = 0
        elif self.slider_jog.value() == 1:
            self.lbl_jog.setText("x1")
            mul_jog = 1
        elif self.slider_jog.value() == 2:
            self.lbl_jog.setText("x10")
            mul_jog = 10
        elif self.slider_jog.value() == 3:
            self.lbl_jog.setText("x50")
            mul_jog = 50
        elif self.slider_jog.value() == 4:
            self.lbl_jog.setText("x100")
            mul_jog = 100
            
    def man_grip(self):
        if self.pb_grip.isChecked():
            grip = 0
        else:
            grip = 1
        data = f"4,{grip}"
        self.ser.write(data.encode('utf-8')) 
        
    def MenuSerialComm(self):
        self.win_showset.show()
        
    def MenuComingSoon(self):
        self.win_comingsoon.show()
        
    def MenuAbout(self):
        self.win_about.show()
        
    def MenuExit(self):
        quit()
    
    def sendDataHoming(self):
        data = "3"
        self.ser.write(data.encode('utf-8'))
        self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Homing Delta Robot!")
    
    def sendDataPosition(self):
        global objpos
        
        rx = round((0.4296*objpos[0])-107.2,2)
        ry = round((-0.4588*objpos[1])+92.5,2)
        rz = -200
        rw = round(objpos[2],2)
        
        data = f"1,{rx},{ry},{rz},{rw}" #address,x,y,z,r
        self.ser.write(data.encode('utf-8'))
        self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Collecting Object at X={rx}; Y={ry}; YAW={rw} !")

    
    def SerialCommTest(self):
        prt = self.win_showset.comm_portlist.currentText()
        bdrt = self.win_showset.comm_baudrate.currentText()
        self.ser = serial.Serial(prt,int(bdrt))
        self.ser.close()
        self.ser.open()
        if self.ser.is_open == True:
            self.win_showset.comm_status.setPixmap(QPixmap('assets/connect.png'))
        else:
            self.win_showset.comm_status.setPixmap(QPixmap('assets/disconnect.png'))
            
    def SerialCommRefresh(self):
        self.win_showset.comm_portlist.clear()
        self.win_showset.comm_baudrate.clear()
        self.win_showset.comm_portlist.addItems([comport.device for comport in list_ports.comports()])
        for x in serial.Serial.BAUDRATES:
            if (x >= 9600 and x <=115200):
                self.win_showset.comm_baudrate.addItems([str(x)])
        self.win_showset.comm_status.setPixmap(QPixmap('assets/disconnect.png'))
        
    def StartPlot(self):
        self.Opencv = ThreadClass()
        self.Opencv.ImageUpdate.connect(self.opencv_emit)
        self.Opencv.start()
        self.plot_start.setEnabled(False)
        self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Object Detection Starting, Please wait..")
        
        self.Opencv.status.connect(self.getObj_status)
        
        self.cb_manual.setEnabled(False)
        
    def StopPlot(self):
        self.Opencv.stop()
        self.plot_start.setEnabled(True)
        self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Object Detection Stoped !")
        
        self.cb_manual.setEnabled(True)
        self.pb_grab.setEnabled(False)
        self.stat_obj.setEnabled(False)

    def opencv_emit(self, Image):

        #QPixmap format           
        original = self.cvt_cv_qt(Image)
        self.cam_view.setPixmap(original)

    def cvt_cv_qt(self, Image):
        offset = 5
        rgb_img = cv2.cvtColor(src=Image,code=cv2.COLOR_BGR2RGB)
        h,w,ch = rgb_img.shape
        bytes_per_line = ch * w
        cvt2QtFormat = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(cvt2QtFormat)

        return pixmap #QPixmap.fromImage(cvt2QtFormat)
#-----
    def getObj_status(self,status):
        self.stat_obj.setStyleSheet(status)
        if status == "background-color: rgb(0,255,0)":
            self.pb_grab.setEnabled(True)
        else :
            self.pb_grab.setEnabled(False)
            
    def getCPU_usage(self,cpu):
        self.com_cpu.setText(str(cpu) + "%")
        if cpu > 15: self.com_cpu.setStyleSheet("color: rgb(23, 63, 95);")
        if cpu > 25: self.com_cpu.setStyleSheet("color: rgb(32, 99, 155);")
        if cpu > 45: self.com_cpu.setStyleSheet("color: rgb(60, 174, 163);")
        if cpu > 65: self.com_cpu.setStyleSheet("color: rgb(246, 213, 92);")
        if cpu > 85: self.com_cpu.setStyleSheet("color: rgb(237, 85, 59);")
       
    def getRAM_usage(self,ram):
        self.com_ram.setText(str(ram[2]) + "%")
        if ram[2] > 15: self.com_ram.setStyleSheet("color: rgb(23, 63, 95);")
        if ram[2] > 25: self.com_ram.setStyleSheet("color: rgb(32, 99, 155);")
        if ram[2] > 45: self.com_ram.setStyleSheet("color: rgb(60, 174, 163);")
        if ram[2] > 65: self.com_ram.setStyleSheet("color: rgb(246, 213, 92);")
        if ram[2] > 85: self.com_ram.setStyleSheet("color: rgb(237, 85, 59);")
    
    def getTemp_usage(self,temp):
        self.com_temp.setText(str(temp) + "°C")
        if temp > 25: self.com_temp.setStyleSheet("color: rgb(23, 63, 95);")
        if temp > 35: self.com_temp.setStyleSheet("color: rgb(60, 174, 155);")
        if temp > 40: self.com_temp.setStyleSheet("color: rgb(246,213, 92);")
        if temp > 45: self.com_temp.setStyleSheet("color: rgb(237, 85, 59);")
        if temp > 50: self.com_temp.setStyleSheet("color: rgb(255, 0, 0);")

    def clock_func(self):
        self.DateTime = QDateTime.currentDateTime()
        self.clock.setText(self.DateTime.toString('hh:mm:ss'))
        self.date.setText(self.DateTime.toString('dd MMM yyyy'))
        
        global objpos
        if objpos[0]==0 and objpos[1]==0:
            rx = objpos[0]
            ry = objpos[1]
        else:
            rx = round((0.4296*objpos[0])-107.2,2)
            ry = round((-0.4588*objpos[1])+92.5,2)
            
        global _isAuto_run
        if _isAuto_run == True:
            self.ob_x.setText(str(rx))
            self.ob_y.setText(str(ry))
            self.ob_deg.setText(str(objpos[2]))
        elif _isAuto_run == False:
            self.cam_view.setPixmap(QPixmap('assets/background2.png'))
            self.ob_x.setText("0")
            self.ob_y.setText("0")
            self.ob_deg.setText("0.0")
            objpos = [0,0,0]
            
    
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
