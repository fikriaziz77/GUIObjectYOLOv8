import serial, time
from datetime import datetime
import numpy as np

prt = 'COM11'
bdr = 9600
bytsz = 8 
prty = "N"
stpb = 1

kirim = []
terima = []
ser = serial.Serial(port=prt , baudrate=bdr , bytesize=bytsz , parity=prty , stopbits=stpb , timeout=1 )

b = 0
while b <= 10:
    current_time = time.time()
    dt_object = datetime.fromtimestamp(current_time)
    formatted_time = dt_object.strftime("%S.%f")
    kirim.append(float(formatted_time))
    print(f"kirim ke-{b}:{formatted_time}")
    i = 0 
    while i <= 1 :
        ser.write("g".encode())
        data = ser.readline().decode().rstrip()
        i += 1

    current_time = time.time()
    dt_object = datetime.fromtimestamp(current_time)
    formatted_time = dt_object.strftime("%S.%f")    
    terima.append(float(formatted_time))
    print(f"terima '{data}' ke-{b}:{formatted_time}")

    b += 1

print(kirim)
print(terima)
arr_kirim = np.array(kirim)
arr_terima = np.array(terima)
print(abs(arr_kirim - arr_terima))
exit()
