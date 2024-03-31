from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QImage, QPixmap
import cv2,time,system_info, rand_num
import numpy as np
import serial
import serial.tools.list_ports as list_ports

global objpos 
objpos = [0,0]

class ThreadClass(QThread):
    ImageUpdate = pyqtSignal(np.ndarray)
    loop = True
    
    def loc2pix(self, x,y):
        xx = (9*x)+360
        yy = (-10*y)+200
        return [xx,yy]
    
    def run(self):
        while self.loop:
            frame = cv2.imread('assets/background.png')
            frame = cv2.resize(frame, (720,400))
            
            global objpos
            objpos = rand_num.get()
            robloct = self.loc2pix(0,0)
            cv2.circle(frame, (robloct[0],robloct[1]), 4, (255,0,255), 4)
            
            obloct = self.loc2pix(objpos[0],objpos[1])
            cv2.circle(frame, (obloct[0],obloct[1]), 4, (0,255,0), 4)
            self.ImageUpdate.emit(frame)
      
    def stop(self):
        self.loop = False
        
        frame = cv2.imread('assets/background.png')
        frame = cv2.resize(frame, (720,400))
        self.ImageUpdate.emit(frame)
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
        
        #setting uiplot
        self.plot_start.clicked.connect(self.StartPlot)
        self.plot_stop.clicked.connect(self.StopPlot)

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
        
        
        
    def manualdrive(self):
        if self.cb_manual.isChecked():
            self.show_manual_button()
        else:
            self.hide_manual_button()    
        
    def MenuSerialComm(self):
        self.win_showset.show()
        
    def SerialCommTest(self):
        self.win_showset.comm_status.setPixmap(QPixmap('assets/connect.png'))  
        
    def StartPlot(self):
        #self.msgbox.append(f"{self.DateTime.toString('hh:mm:ss')}: Camera ({self.cam_list.currentText()}) Start")
        # Opencv QThread
        self.Opencv = ThreadClass()
        self.Opencv.ImageUpdate.connect(self.opencv_emit)
        self.Opencv.start()
        self.plot_start.setEnabled(False)

    def StopPlot(self):
        
        self.Opencv.stop()
        #self.cam_view.setPixmap(QPixmap('assets/background.png'))
        self.plot_start.setEnabled(True)
        
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
        
        global objpos
        self.ob_x.setText(str(objpos[0]))
        self.ob_y.setText(str(objpos[1]))
        
    def getObj_pos(self):
        pass
    
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
