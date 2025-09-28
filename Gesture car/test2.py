import serial
import time
import random

# Change COM port to the one your HC-05 is assigned
bt_port = "COM3"  
baud_rate = 115200  

# Open serial connection
ser = serial.Serial(bt_port, baud_rate, timeout=1)
time.sleep(2)  # wait for connection

commands = ['F', 'B', 'L', 'R', 'S']  # Forward, Back, Left, Right, Stop


while True:
    cmd = random.choice(commands)
    ser.write(cmd.encode())   # send to HC-05 → Mega
    print(f"Sent: {cmd}")
    time.sleep(1)

