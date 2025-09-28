import socket

PC_PORT = 4210
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.bind(("0.0.0.0", PC_PORT))

print("PC receiver running... Waiting for data...")

while True:
    data, addr = recv_sock.recvfrom(1024)
    print(f"From ESP32 {addr}: {data.decode()}")
