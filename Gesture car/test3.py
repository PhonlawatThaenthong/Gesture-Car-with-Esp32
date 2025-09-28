import socket
import serial
import time

# 🔹 Bluetooth settings
bt_port = "COM5"   # Change to your HC-05 COM port
baud_rate = 115200

# Open Bluetooth serial connection
ser = serial.Serial(bt_port, baud_rate, timeout=1)
time.sleep(2)  # wait for HC-05 connection
print(f"Connected to HC-05 on {bt_port}")

# 🔹 UDP settings (receive from Hand ESP32)
PC_PORT = 4210
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.bind(("0.0.0.0", PC_PORT))

print("PC middleware running...")

# 🔹 Mapping table
mapping = {
    "F": "W",  # forward → W
    "B": "S",  # back → S
    "L": "A",  # left → A
    "R": "D",  # right → D
    "S": "X"   # stop → X
}

while True:
    # 1️⃣ Receive UDP from Hand ESP32
    data, addr = recv_sock.recvfrom(1024)
    cmd = data.decode("utf-8").strip()

    print(f"From Hand ESP32: {cmd}")

    # 2️⃣ Transform command
    transformed = mapping.get(cmd, "X")

    # 3️⃣ Send to Mega via Bluetooth
    print(f"Send to Mega (BT): {transformed}")
    ser.write(transformed.encode())

    # 4️⃣ Try to read any reply from Mega
    reply = ser.readline().decode("utf-8").strip()
    if reply:
        print(f"From Mega: {reply}")
