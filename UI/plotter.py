''' derived from : http://www.bemasher.net/archives/813

'''

import gobject
import matplotlib
matplotlib.use('GTKAgg')

import matplotlib.pyplot as plt
import serial
import time
import os

class pid_hotplate:

    def __init__(self,dev = 'dev/ttyACM0'):
        self.serial = serial.Serial(dev, baudrate=115200, writeTimeout=10)
        self.serial.open()
        self.write('R')
        self.write('g')

    def write(self, data):
        self.serial.write(data)

    def read_temp(self):
        self.write(' ')
        result = self.serial.readline().strip()
        print result
        return result

    def get_data(self):
        while True:
            data = self.read_temp().strip()
            #print data
            #time.sleep(0.5)


f = plt.figure()
current_pos = 0
temps = [20.0]
times = [0.0]
pad = 0.0
target = [20.0]

start_time = time.time()

def update():
    global current_pos
    global temps
    global times
    global target
    global pad

    #time.sleep(0.5)
    data = hotplate.read_temp().split(' ')
    current_pos = time.time() - start_time
   
    # If we got new data then append it to the list of
    # temperatures and trim to 500 points
    temps.append(float(data[1]))
    target.append(float(data[0]))
    times.append(current_pos)
    if len(temps) > 500:
        temps = temps[-500:]
        times = times[-500:]
        target = target[-500:]
   
    f.clear()
    f.suptitle("Live Temperature")
    a = f.add_subplot(111)
    a.grid(True)
    a.plot(times, temps)
    a.plot(times, target)
    plt.xlabel("Time (Seconds)")
    plt.ylabel(r'Temperature $^{\circ}$C')
   
    # Get the minimum and maximum temperatures these are
    # used for annotations and scaling the plot of data
    min_t = min(temps + target)
    max_t = max(temps + target)
   
   
    # Set the axis limits to make the data more readable
    a.axis([times[0],times[len(times)-1] + 1, min_t ,max_t])
   
    f.canvas.draw()
   
    return True


hotplate = pid_hotplate('/dev/ttyACM0')

def press(event):
    if len(event.key) == 1:
        hotplate.write(event.key)
        print event.key

f.canvas.mpl_connect('key_press_event', press)


# Execute update method every 500ms
gobject.idle_add(update)
#gobject.timeout_add(500, update)

# Display the plot
plt.show()

