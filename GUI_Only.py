from PyQt5 import uic
from PyQt5.QtMultimedia import QCameraInfo
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QMenuBar
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QTimer, QDateTime, Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
import cv2,time,sys,system_info
import numpy as np
import random as rnd
import serial
import serial.tools.list_ports as list_ports

class ThreadClass(QThread):
    ImageUpdate = pyqtSignal(np.ndarray)
    FPS = pyqtSignal(int)
    global camIndex

    def run(self):
        Capture = cv2.VideoCapture(camIndex)
        Capture.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
        Capture.set(cv2.CAP_PROP_FRAME_WIDTH,640)
        
        self.ThreadActive = True
        prev_frame_time = 0
        new_frame_time = 0
        while self.ThreadActive:
            #fps camera
            ret,frame_cap = Capture.read()
            flip_frame = cv2.flip(src=frame_cap,flipCode=1)
            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
            if ret:
                self.ImageUpdate.emit(flip_frame)
                self.FPS.emit(fps)
    
    def stop(self):
        self.ThreadActive = False
        fps = 0
        self.FPS.emit(fps)
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
        
class Window_No_Camera_Available(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("screens/camera.ui",self)

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
    
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("screens/main_interface.ui",self)
        
        #setting camera
        global emptycam
        self.online_cam = QCameraInfo.availableCameras()
        self.cam_list.addItems([c.description() for c in self.online_cam])
        if not self.online_cam:
            emptycam = True
        else:
            emptycam = False
        self.cam_stop.setEnabled(False)
        self.cam_start.clicked.connect(self.StartWebCam)
        self.cam_stop.clicked.connect(self.StopWebcam)
        self.no_cam_avail = Window_No_Camera_Available()

        #manual button
        self.hide_manual_button()
        self.cb_manual.clicked.connect(self.manualdrive)
        
        #resource usage cpu
        self.resource_usage = boardInfoClass()
        self.resource_usage.start()
        self.resource_usage.cpu.connect(self.getCPU_usage)
        self.resource_usage.ram.connect(self.getRAM_usage)
        self.resource_usage.temp.connect(self.getTemp_usage)

        #runtime start
        self.lcd_timer = QTimer()
        self.lcd_timer.timeout.connect(self.clock_func)
        self.lcd_timer.start()
        
        #communication serial menu
        self.menuComm.triggered.connect(self.MenuSerialComm)
        self.win_showset = Window_CommSetting()
        self.win_showset.comm_portlist.addItems([comport.device for comport in list_ports.comports()])
        for x in serial.Serial.BAUDRATES:
            if (x >= 4800 and x <=115200):
                self.win_showset.comm_baudrate.addItems([str(x)])
        self.win_showset.comm_parity.addItems([x for x in serial.Serial.PARITIES])
        self.win_showset.comm_bytesz.addItems([str(x) for x in serial.Serial.BYTESIZES])
        self.win_showset.comm_stopbits.addItems([str(x) for x in serial.Serial.STOPBITS])
        self.win_showset.comm_status.setPixmap(QPixmap('assets/disconnect.png'))
        self.win_showset.comm_test.clicked.connect(self.SerialCommTest)
        
    def manualdrive(self, pin):
        if self.cb_manual.isChecked():
            self.show_manual_button()
        else:
            self.hide_manual_button()    
        
    def MenuSerialComm(self):
        self.win_showset.show()
        
    def SerialCommTest(self):
        self.win_showset.comm_status.setPixmap(QPixmap('assets/connect.png'))  
        
    def StartWebCam(self,pin):
        try:
            global emptycam
            if emptycam == False:
                self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Camera ({self.cam_list.currentText()}) Start")
                self.cam_stop.setEnabled(True)
                self.cam_start.setEnabled(False)

                global camIndex
                camIndex = self.cam_list.currentIndex()
                
                # Opencv QThread
                self.Opencv = ThreadClass()
                self.Opencv.ImageUpdate.connect(self.opencv_emit)
                self.Opencv.FPS.connect(self.get_FPS)
                self.Opencv.start()
            else :
                self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Can`t find camera device !")
                self.no_cam_avail.show()
                
        except Exception as error :
            pass

    
    def StopWebcam(self,pin):
        
        import time
        self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Camera ({self.cam_list.currentText()}) Stopped")
        self.cam_start.setEnabled(True)
        self.cam_stop.setEnabled(False)
        self.Opencv.stop()

        # Set Icon back to stop state
        self.cam_view.setPixmap(QPixmap('assets/nocamera.jpg'))
        self.cam_view.setScaledContents(True)
        



    def opencv_emit(self, Image):

        #QPixmap format           
        original = self.cvt_cv_qt(Image)

        self.cam_view.setPixmap(original)
        self.cam_view.setScaledContents(True)

    def cvt_cv_qt(self, Image):
        offset = 5
        rgb_img = cv2.cvtColor(src=Image,code=cv2.COLOR_BGR2RGB)
        h,w,ch = rgb_img.shape
        bytes_per_line = ch * w
        cvt2QtFormat = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(cvt2QtFormat)

        return pixmap #QPixmap.fromImage(cvt2QtFormat)
#-----

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
        self.com_temp.setText(str(temp) + "C")
        if temp > 30: self.com_temp.setStyleSheet("color: rgb(23, 63, 95);")
        if temp > 35: self.com_temp.setStyleSheet("color: rgb(60, 174, 155);")
        if temp > 40: self.com_temp.setStyleSheet("color: rgb(246,213, 92);")
        if temp > 45: self.com_temp.setStyleSheet("color: rgb(237, 85, 59);")
        if temp > 50: self.com_temp.setStyleSheet("color: rgb(255, 0, 0);")
        
    def get_FPS(self,fps):
        self.com_fps.setText(str(fps))
        if fps > 1: self.com_fps.setStyleSheet("color: red;")
        if fps > 10: self.com_fps.setStyleSheet("color: rgb(245, 170, 62);")
        if fps > 16: self.com_fps.setStyleSheet("color: green;")


    def clock_func(self):
        self.DateTime = QDateTime.currentDateTime()
        self.clock.setText(self.DateTime.toString('hh:mm:ss'))
        self.date.setText(self.DateTime.toString('dd MMM yyyy'))
    
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
