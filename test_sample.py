import pygame, sys, time

# ---------- PYGAME ----------
pygame.init()
W, H, G = 800, 800, 20
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Car Control Sample (Keyboard Only)")
font = pygame.font.SysFont("Arial", 20)
big_font = pygame.font.SysFont("Arial", 60, bold=True)
cols, rows = W//G, H//G

# ---------- GAME STATE ----------
x, y = cols//2, rows//2
trail, last_cmd, block = [], "S", False
esp_status = "Connected"
arm_status = "Not pressed"
clock = pygame.time.Clock()
last_move_time = time.time()
block_until = 0

# ---------- DRAW ----------
def draw_grid():
    for i in range(0, W, G):
        pygame.draw.line(screen,(60,60,60),(i,0),(i,H))
    for j in range(0, H, G):
        pygame.draw.line(screen,(60,60,60),(0,j),(W,j))

def draw():
    screen.fill((0,0,0))
    draw_grid()

    for p in trail:
        pygame.draw.rect(screen,(0,100,255),(p[0]*G,p[1]*G,G,G))

    car = pygame.Rect(x*G,y*G,G,G)
    pygame.draw.rect(screen,(255,0,0),car)
    pygame.draw.rect(screen,(255,255,255),car,1)

    screen.blit(font.render(f"CMD:{last_cmd}",1,(0,255,0)),(10,10))
    screen.blit(font.render(f"ESP32-B: {esp_status}",1,(0,200,255)),(10,35))
    screen.blit(font.render(f"Arm : {arm_status}",1,(255,255,0)),(10,60))

    if block:
        txt = big_font.render("BLOCK", True, (255,0,0))
        rect = txt.get_rect(center=(W//2, H//2))
        screen.blit(txt, rect)

    pygame.display.flip()

# ---------- MOVE ----------
def move(c):
    global x,y,last_move_time
    if block and c not in ["b","B"]:  
        return
    if time.time() - last_move_time < 0.15:  # step cooldown
        return
    last_move_time = time.time()
    trail.append((x,y))
    if c.lower()=="f": y=max(0,y-1)
    if c.lower()=="b": y=min(rows-1,y+1)
    if c.lower()=="l": x=max(0,x-1)
    if c.lower()=="r": x=min(cols-1,x+1)

# ---------- MAIN LOOP ----------
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if e.type == pygame.KEYDOWN:
            cmd = "S"
            if e.key == pygame.K_UP: cmd = "F"
            if e.key == pygame.K_DOWN: cmd = "B"
            if e.key == pygame.K_LEFT: cmd = "L"
            if e.key == pygame.K_RIGHT: cmd = "R"

            if cmd != "S":
                last_cmd = cmd
                move(last_cmd)

            # Arm control with spacebar
            if e.key == pygame.K_SPACE:
                arm_status = "pressed"

            # Fake block trigger with "B"
            if e.key == pygame.K_b:
                block = True
                block_until = time.time() + 2.0  # 2 seconds

        if e.type == pygame.KEYUP:
            if e.key == pygame.K_SPACE:
                arm_status = "Not pressed"

    if block and time.time() > block_until:
        block = False

    draw()
    clock.tick(30)
