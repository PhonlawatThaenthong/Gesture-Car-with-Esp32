import pygame, serial, serial.tools.list_ports, sys, time

def find_serial_port():
    ports = serial.tools.list_ports.comports()
    if not ports: sys.exit("No COM ports found")
    return serial.Serial("COM3", 9600, timeout=1)  # COM3 for pc / /dev/ttyUSB0 for odroid

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
esp_status = ""   # 🔹 store latest ESP32-B status
clock = pygame.time.Clock()
last_move_time = time.time()

# 🔹 control how often we send to Mega
last_send_time = 0
SEND_INTERVAL = 0.4   # 200 ms between sends

# 🔹 block timeout (reset if no "block" seen recently)
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

    # ESP32-B connection status (top-left under CMD)
    if esp_status:
        screen.blit(font.render(f"ESP32-B: {esp_status}",1,(0,200,255)),(10,35))

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
        if e.type==pygame.QUIT: pygame.quit(); ser.close(); sys.exit()

    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()
        if "," in line:  # Gyro data
            ax,ay = map(float,line.split(","))
            cmd = detect(ax,ay)

            # 🔹 If blocked → only accept backward (b/B), else ignore
            if block and cmd not in ["b","B"]:
                continue  # skip sending & moving
            else:
                last_cmd = cmd

            move(last_cmd)

            # 🔹 only send if enough time passed
            now = time.time()
            if now - last_send_time >= SEND_INTERVAL:
                ser.write((last_cmd+"\n").encode())
                last_send_time = now

        elif "block" in line.lower():  # Block flag
            block = True
            block_until = time.time() + 1.0  # keep blocked for 1 second after last "block"

        elif any(word in line for word in ["Connecting","Connected","Reconnected","Failed"]):
            esp_status = line  # 🔹 save ESP32-B status

    # 🔹 reset block if timeout passed
    if block and time.time() > block_until:
        block = False

    draw()
    clock.tick(30)
