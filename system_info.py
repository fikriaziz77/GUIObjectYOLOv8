
import psutil

def getCPU():
    return psutil.cpu_percent(interval=1)

def getRAM():
    return psutil.virtual_memory()

def getTemp():
    temps = psutil.sensors_temperatures()
    for name, entries in temps.items():
        for entry in entries:
            line = entry.current
    
    return line

            