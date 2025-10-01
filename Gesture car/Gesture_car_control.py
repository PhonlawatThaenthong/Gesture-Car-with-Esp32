import pygame, serial, serial.tools.list_ports, sys, time

def find_serial_port():
    ports = serial.tools.list_ports.comports()
    if not ports: sys.exit("No COM ports found")
    return serial.Serial("COM4", 9600, timeout=1)  # change to /dev/ttyUSB0 on Odroid

ser = find_serial_port()
pygame.init()
W, H, G = 600, 600, 20
screen = pygame.display.set_mode((W, H))
font = pygame.font.SysFont("Arial", 20)
big_font = pygame.font.SysFont("Arial", 60, bold=True)
cols, rows = W//G, H//G

# 🚗 Car starts in the middle
x, y = cols//2, rows//2
trail_colors = {}  # (x,y) : color state, True=red, False=blue
last_cmd, block = "S", False
esp_status = ""              
arm_status = "Not pressed"   
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

# ===== เลือกโหมด =====
print("เลือกโหมด:")
print("1 = Gyro Mode (ค่าเซนเซอร์ ESP32)")
print("2 = Keyboard Mode (กดปุ่มบนคีย์บอร์ด)")
mode = input("เลือก (1/2): ").strip()
if mode not in ["1","2"]:
    print("ค่าไม่ถูกต้อง -> ใช้โหมด Gyro")
    mode = "1"
use_gyro = (mode == "1")

def draw_grid():
    for i in range(0, W, G):
        pygame.draw.line(screen,(60,60,60),(i,0),(i,H))
    for j in range(0, H, G):
        pygame.draw.line(screen,(60,60,60),(0,j),(W,j))

def draw():
    screen.fill((0,0,0))
    draw_grid()

    # Trail
    for pos, is_red in trail_colors.items():
        color = (255,0,0) if is_red else (0,100,255)
        pygame.draw.rect(screen,color,(pos[0]*G,pos[1]*G,G,G))

    # 🚗 Car
    car = pygame.Rect(x*G,y*G,G,G)
    pygame.draw.rect(screen,(255,0,0),car)
    pygame.draw.rect(screen,(255,255,255),car,1)

    # CMD status
    screen.blit(font.render(f"CMD:{last_cmd}",1,(0,255,0)),(10,10))

    # ESP32-B / Keyboard status
    if use_gyro:
        if esp_status:
            screen.blit(font.render(f"ESP32-B: {esp_status}",1,(0,200,255)),(10,35))
    else:
        screen.blit(font.render("Keyboard Mode Active",1,(0,200,255)),(10,35))

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
        return
    if time.time() - last_move_time < 0.5:
        return
    last_move_time = time.time()

    # Add current position to trail_colors
    if (x,y) in trail_colors:
        trail_colors[(x,y)] = not trail_colors[(x,y)]  # สลับสี
    else:
        trail_colors[(x,y)] = False  # ครั้งแรกเป็นน้ำเงิน

    # Move
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
            ser.write(b"S\n")
            pygame.quit(); ser.close(); sys.exit()

        # ===== Keyboard Mode Event =====
        if not use_gyro and e.type == pygame.KEYDOWN:
            if block and e.key not in [pygame.K_DOWN]:
                continue

            if e.key == pygame.K_UP: cmd = "f"
            elif e.key == pygame.K_DOWN: cmd = "b"
            elif e.key == pygame.K_LEFT: cmd = "l"
            elif e.key == pygame.K_RIGHT: cmd = "r"
            elif e.key == pygame.K_SPACE: cmd = "S"
            elif e.key == pygame.K_a: 
                arm_status = "pressed"
                ser.write(b"u\n")
                last_sent_arm = arm_status
                continue
            elif e.key == pygame.K_z:
                arm_status = "Not pressed"
                ser.write(b"i\n")
                last_sent_arm = arm_status
                continue
            else: cmd = "S"

            # Move and send once
            last_cmd = cmd
            move(last_cmd)
            ser.write((last_cmd+"\n").encode())
            last_sent_cmd = last_cmd

            # Step mode: กลับไป S
            move("S")
            ser.write(b"S\n")
            last_cmd = "S"
            last_sent_cmd = "S"

    # ===== Gyro Mode (ไม่แก้ไข) =====
    if use_gyro:
        while ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            if "," in line:
                parts = line.split(",")
                if len(parts) == 3:
                    try:
                        ax, ay, btn = float(parts[0]), float(parts[1]), int(parts[2])
                    except ValueError:
                        continue
                    cmd = detect(ax, ay)
                    if not (block and cmd not in ["b","B"]):  
                        last_cmd = cmd
                        move(last_cmd)
                        now = time.time()
                        if last_cmd != last_sent_cmd and (now - last_send_time_cmd) >= SEND_INTERVAL:
                            ser.write((last_cmd+"\n").encode())
                            last_sent_cmd = last_cmd
                            last_send_time_cmd = now
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
            elif "block" in line.lower():
                block = True
                block_until = time.time() + 1.0  
            elif any(word in line for word in ["Connecting","Connected","Reconnected","Failed"]):
                esp_status = line  

    if block and time.time() > block_until:
        block = False

    draw()
    clock.tick(30)