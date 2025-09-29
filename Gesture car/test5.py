import pygame, serial, serial.tools.list_ports, sys, time

def find_serial_port():
    ports = serial.tools.list_ports.comports()
    if not ports: sys.exit("No COM ports found")
    return serial.Serial("COM3", 9600, timeout=1)  # change to /dev/ttyUSB0 on Odroid

ser = find_serial_port()
pygame.init()
W, H, G = 1000, 1000, 20
screen = pygame.display.set_mode((W, H))
font = pygame.font.SysFont("Arial", 20)
big_font = pygame.font.SysFont("Arial", 60, bold=True)
cols, rows = W//G, H//G

# 🚗 Car starts in the middle
x, y = cols//2, rows//2
trail, last_cmd, block = [], "S", False
esp_status = ""              # 🔹 ESP32-B connection status
arm_status = "Not pressed"   # 🔹 Button state
clock = pygame.time.Clock()
last_move_time = time.time()

# 🔹 Mega send control
last_sent_cmd = None
last_sent_arm = None
last_send_time_cmd = 0
last_send_time_arm = 0
SEND_INTERVAL = 0.4   # 400 ms between sends

# 🔹 block timeout
block_until = 0

def draw_grid():
    for i in range(0, W, G):
        pygame.draw.line(screen,(60,60,60),(i,0),(i,H))
    for j in range(0, H, G):
        pygame.draw.line(screen,(60,60,60),(0,j),(W,j))

def draw():
    screen.fill((0,0,0))
    draw_grid()

    # Trail
    for p in trail:
        pygame.draw.rect(screen,(0,100,255),(p[0]*G,p[1]*G,G,G))

    # 🚗 Car
    car = pygame.Rect(x*G,y*G,G,G)
    pygame.draw.rect(screen,(255,0,0),car); pygame.draw.rect(screen,(255,255,255),car,1)

    # CMD status
    screen.blit(font.render(f"CMD:{last_cmd}",1,(0,255,0)),(10,10))

    # ESP32-B status
    if esp_status:
        screen.blit(font.render(f"ESP32-B: {esp_status}",1,(0,200,255)),(10,35))

    # Arm status
    screen.blit(font.render(f"Arm : {arm_status}",1,(255,255,0)),(10,60))

    # BLOCK text
    if block:
        txt = big_font.render("BLOCK", True, (255,0,0))
        rect = txt.get_rect(center=(W//2, H//2))
        screen.blit(txt, rect)

    pygame.display.flip()

def move(c):
    global x,y,last_move_time
    if block and c not in ["b","B"]:  
        return   # 🚫 ignore other moves while blocked
    if time.time() - last_move_time < 1: 
        return
    last_move_time = time.time()
    steps = 2 if c in ["F","B","L","R"] else 1
    for _ in range(steps):
        trail.append((x,y))
        if c.lower()=="f": y=max(0,y-1)
        if c.lower()=="b": y=min(rows-1,y+1)
        if c.lower()=="l": x=max(0,x-1)
        if c.lower()=="r": x=min(cols-1,x+1)

def detect(ax,ay):
    if 5<ay<=8: return "r"
    if ay>8: return "R"
    if -8<=ay<-5: return "l"
    if ay<-8: return "L"
    if 5<ax<=8: return "f"
    if ax>8: return "F"
    if -8<=ax<-5: return "b"
    if ax<-8: return "B"
    return "S"

while True:
    for e in pygame.event.get():
        if e.type==pygame.QUIT: 
            ser.write(b"S\n")  # send stop before quit
            pygame.quit(); ser.close(); sys.exit()

    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue

        # --- Gyro + Button data ---
        if "," in line:
            parts = line.split(",")
            if len(parts) == 3:
                try:
                    ax, ay, btn = float(parts[0]), float(parts[1]), int(parts[2])
                except ValueError:
                    continue  # skip invalid

                # Gyro control
                cmd = detect(ax, ay)
                if not (block and cmd not in ["b","B"]):  
                    # allow only B/b when blocked
                    last_cmd = cmd
                    move(last_cmd)

                    # Send movement if changed
                    now = time.time()
                    if last_cmd != last_sent_cmd and (now - last_send_time_cmd) >= SEND_INTERVAL:
                        ser.write((last_cmd+"\n").encode())
                        last_sent_cmd = last_cmd
                        last_send_time_cmd = now

                # Button state → Arm (always processed, even if blocked)
                new_arm_status = "pressed" if btn == 1 else "Not pressed"
                if new_arm_status != arm_status:
                    arm_status = new_arm_status
                    now = time.time()
                    if (arm_status != last_sent_arm) and (now - last_send_time_arm) >= SEND_INTERVAL:
                        if arm_status == "pressed":
                            ser.write(b"u\n")
                        else:
                            ser.write(b"i\n")
                        last_sent_arm = arm_status
                        last_send_time_arm = now

        # --- Block flag ---
        elif "block" in line.lower():
            block = True
            block_until = time.time() + 1.0  

        # --- ESP32-B connection status ---
        elif any(word in line for word in ["Connecting","Connected","Reconnected","Failed"]):
            esp_status = line  

    if block and time.time() > block_until:
        block = False

    draw()
    clock.tick(30)