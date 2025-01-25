import pygame
import math
import random
import numpy as np

# -------------------------------------------------
# Basic Constants
# -------------------------------------------------
SCREEN_WIDTH  = 1800
SCREEN_HEIGHT = 1000
FPS           = 60

BASE_DT       = 0.01
C_LIGHT       = 300.0   # bullet speed
C_MAX         = 300.0   # rocket max speed

WORLD_WIDTH   = 5000
WORLD_HEIGHT  = 5000

TOOLS = ["Gun", "LightPulse", "Bomb"]

# -------------------------------------------------
# Utility
# -------------------------------------------------
def limit_speed(vx, vy, cmax=C_MAX):
    spd = math.hypot(vx, vy)
    if spd > cmax:
        scl = cmax/spd
        vx *= scl
        vy *= scl
    return vx, vy

def distance_sq(x1,y1, x2,y2):
    dx = x2 - x1
    dy = y2 - y1
    return dx*dx + dy*dy

def distance(x1,y1, x2,y2):
    return math.sqrt(distance_sq(x1,y1,x2,y2))

def wrap_position(x, y):
    """
    Periodic boundaries: if out of [0..WORLD_WIDTH/HEIGHT], wrap around.
    """
    if x < 0:         x += WORLD_WIDTH
    elif x >= WORLD_WIDTH:  x -= WORLD_WIDTH
    if y < 0:         y += WORLD_HEIGHT
    elif y >= WORLD_HEIGHT: y -= WORLD_HEIGHT
    return x, y

# -------------------------------------------------
# Rocket
# -------------------------------------------------
def update_rocket(rocket):
    """
    rocket = {'x','y','vx','vy','heading','angvel'}
    No external force. Euler integration. Then wrap in world.
    's' key logic: we reduce angvel => see main loop for torque usage.
    """
    dt = BASE_DT
    # integrate velocity
    rocket['x'] += rocket['vx']*dt
    rocket['y'] += rocket['vy']*dt
    rocket['x'], rocket['y'] = wrap_position(rocket['x'], rocket['y'])

    # rotation
    rocket['heading'] += rocket['angvel']*dt

def draw_rocket(screen, rocket, thrust_on, turn_left, turn_right):
    rx = SCREEN_WIDTH/2
    ry = SCREEN_HEIGHT/2
    length = 30.0
    rad = math.radians(rocket['heading'])

    # front/back corners
    nose_x  = rx + length*math.cos(rad)
    nose_y  = ry + length*math.sin(rad)
    left_x  = rx + (-0.4*length)*math.cos(rad + math.radians(130))
    left_y  = ry + (-0.4*length)*math.sin(rad + math.radians(130))
    right_x = rx + (-0.4*length)*math.cos(rad - math.radians(130))
    right_y = ry + (-0.4*length)*math.sin(rad - math.radians(130))

    color_front = (255,0,0)
    color_back  = (180,0,0)

    front_tri = [(nose_x,nose_y),(left_x,left_y),(right_x,right_y)]
    pygame.draw.polygon(screen, color_front, front_tri)
    back_x = rx - 0.7*length*math.cos(rad)
    back_y = ry - 0.7*length*math.sin(rad)
    back_tri= [(left_x,left_y),(back_x,back_y),(right_x,right_y)]
    pygame.draw.polygon(screen, color_back, back_tri)

    # flames
    if thrust_on:
        flame_len= 25.0
        flame_rad= rad + math.pi
        fx = back_x+ random.uniform(0.8,1.2)* flame_len* math.cos(flame_rad)
        fy = back_y+ random.uniform(0.8,1.2)* flame_len* math.sin(flame_rad)
        pygame.draw.line(screen, (255,165,0), (back_x,back_y),(fx,fy),3)

    if turn_left:
        # thruster on right side
        flame_len=15
        side_ang= rad- math.radians(90)
        sx= right_x; sy= right_y
        fx= sx+ flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        fy= sy+ flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(screen, (0,255,0), (sx,sy),(fx,fy),2)

    if turn_right:
        flame_len=15
        side_ang= rad+ math.radians(90)
        sx= left_x; sy= left_y
        fx= sx+ flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        fy= sy+ flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(screen, (0,255,0), (sx,sy),(fx,fy),2)


# -------------------------------------------------
# Tools
# -------------------------------------------------
def create_bullet(bullets, rocket):
    heading_rad = math.radians(rocket['heading'])
    nose_dx = 30.0*math.cos(heading_rad)
    nose_dy = 30.0*math.sin(heading_rad)
    bx = rocket['x'] + nose_dx
    by = rocket['y'] + nose_dy
    bvx= rocket['vx'] + C_LIGHT*math.cos(heading_rad)
    bvy= rocket['vy'] + C_LIGHT*math.sin(heading_rad)
    bullets.append({
        'x': bx, 'y': by, 'vx':bvx, 'vy':bvy,
        'radius':2.0, 'mass':1.0
    })

def create_lightpulse(lightpulses, rocket):
    lightpulses.append({
        'cx': rocket['x'],
        'cy': rocket['y'],
        'radius': 0.0,
        'speed': C_LIGHT
    })

def create_bomb(bombs, rocket):
    """
    Bomb travels with rocket's velocity at time of creation.
    'flash_timer' controls color flicker,
    'explode_time' => after which it explodes into radial bullets.
    """
    bombs.append({
        'x': rocket['x'],
        'y': rocket['y'],
        'vx': rocket['vx'],
        'vy': rocket['vy'],
        'flash_timer': 0.0,
        'explode_time': 3.0,  # seconds
        'radius': 10.0
    })

# -------------------------------------------------
# Bomb Updating
# -------------------------------------------------
def update_bomb(bomb, dt):
    # move
    bomb['x'] += bomb['vx']*dt
    bomb['y'] += bomb['vy']*dt
    bomb['x'], bomb['y'] = wrap_position(bomb['x'], bomb['y'])

    # flash
    bomb['flash_timer'] += dt

def draw_bomb(screen, bomb, rocket):
    # convert to screen coords
    cam_x = rocket['x'] - SCREEN_WIDTH/2
    cam_y = rocket['y'] - SCREEN_HEIGHT/2
    bx_screen = bomb['x'] - cam_x
    by_screen = bomb['y'] - cam_y

    # flicker color => alternate red/white with increasing frequency
    t = bomb['flash_timer']
    # frequency grows => flicker_period ~ 1/(1+t)
    flicker_freq = 1.0 + t*2.0  # grows over time
    # we can do a quick sin or mod approach
    # if sin(2*pi*flicker_freq * t) > 0 => red else white
    val = math.sin(2*math.pi* flicker_freq * t)
    if val>0:
        color = (255,0,0)
    else:
        color = (255,255,255)

    pygame.draw.circle(screen, color, (int(bx_screen), int(by_screen)), int(bomb['radius']))

def bomb_explode(bomb, bullets):
    """
    Creates a bunch of radial bullets from bomb's position
    in all directions. Then bomb is removed.
    """
    N = 20
    bx, by = bomb['x'], bomb['y']
    bvx, bvy= bomb['vx'], bomb['vy']
    for i in range(N):
        angle = 2*math.pi*i/N
        vx = bvx + C_LIGHT* math.cos(angle)
        vy = bvy + C_LIGHT* math.sin(angle)
        bullets.append({
          'x': bx, 'y': by,
          'vx': vx, 'vy': vy,
          'radius': 2.0,
          'mass': 1.0
        })

# -------------------------------------------------
# Collisions
# -------------------------------------------------
def bullet_asteroid_collision(bullet, ast):
    """
    bullet + asteroid => bullet disappears, asteroid gets momentum
    bullet has mass=1 => inelastic
    """
    # inelastic momentum combination
    mb = bullet['mass']
    vxB, vyB = bullet['vx'], bullet['vy']
    ma = ast['mass']
    vxA, vyA = ast['vx'], ast['vy']

    vx_new = (ma*vxA + mb*vxB)/(ma+ mb)
    vy_new = (ma*vyA + mb*vyB)/(ma+ mb)
    ast['vx'] = vx_new
    ast['vy'] = vy_new

def ring_asteroid_bounce(lp, ast):
    """
    If ring radius + ast['radius'] >= distance => bounce => ring['speed'] *= -1
    """
    dist_c = distance(lp['cx'], lp['cy'], ast['x'], ast['y'])
    if dist_c <= lp['radius'] + ast['radius']:
        # bounce
        lp['speed']*= -1

# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    pygame.init()
    screen= pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock= pygame.time.Clock()
    font= pygame.font.SysFont("Arial", 18)

    # Make stars
    num_stars = 300
    stars = []
    for _ in range(num_stars):
        sx = random.uniform(0, WORLD_WIDTH)
        sy = random.uniform(0, WORLD_HEIGHT)
        brightness = random.randint(100,180)
        stars.append({
            'x': sx, 'y': sy,
            'color': (brightness,brightness,brightness)
        })

    # Make asteroids
    asteroids=[]
    num_aster = 20
    for _ in range(num_aster):
        ax= random.uniform(0, WORLD_WIDTH)
        ay= random.uniform(0, WORLD_HEIGHT)
        vx= random.uniform(-50,50)
        vy= random.uniform(-50,50)
        radius= random.uniform(15,35)
        mass= radius
        # greyer
        grey = random.randint(120,180)
        color= (grey,grey,grey)
        asteroids.append({
          'x':ax, 'y':ay, 'vx':vx, 'vy':vy,
          'radius':radius, 'mass':mass, 'color':color
        })

    # Rocket
    rocket = {
      'x': WORLD_WIDTH/2,
      'y': WORLD_HEIGHT/2,
      'vx': 0.0, 'vy': 0.0,
      'heading':0.0,
      'angvel':0.0
    }

    # lists
    bullets     = []
    lightpulses = []
    bombs       = []

    tool_index  = 0

    running=True
    while running:
        dt_real= clock.tick(FPS)/1000.0

        # Input
        turn_left= False
        turn_right=False
        thrust_on= False

        events= pygame.event.get()
        for event in events:
            if event.type== pygame.QUIT:
                running=False
            elif event.type== pygame.KEYDOWN:
                if event.key== pygame.K_ESCAPE:
                    running=False
                elif event.key== pygame.K_q:
                    tool_index= (tool_index-1)% len(TOOLS)
                elif event.key== pygame.K_e:
                    tool_index= (tool_index+1)% len(TOOLS)
                elif event.key== pygame.K_SPACE:
                    # use tool
                    tname= TOOLS[tool_index]
                    if tname=="Gun":
                        create_bullet(bullets, rocket)
                    elif tname=="LightPulse":
                        create_lightpulse(lightpulses, rocket)
                    elif tname=="Bomb":
                        create_bomb(bombs, rocket)
                elif event.key== pygame.K_r:
                    # reset rocket + random asteroids
                    rocket= {
                      'x': WORLD_WIDTH/2,
                      'y': WORLD_HEIGHT/2,
                      'vx': 0.0,'vy':0.0,
                      'heading': 0.0,
                      'angvel': 0.0
                    }
                    asteroids.clear()
                    for _ in range(num_aster):
                        ax= random.uniform(0, WORLD_WIDTH)
                        ay= random.uniform(0, WORLD_HEIGHT)
                        vx= random.uniform(-50,50)
                        vy= random.uniform(-50,50)
                        radius= random.uniform(15,35)
                        mass= radius
                        grey = random.randint(120,180)
                        color= (grey,grey,grey)
                        asteroids.append({
                          'x':ax,'y':ay,'vx':vx,'vy':vy,
                          'radius':radius,'mass':mass,'color':color
                        })
                    bullets.clear()
                    lightpulses.clear()
                    bombs.clear()

        # keys
        keys= pygame.key.get_pressed()
        torque_strength= 50.0
        if keys[pygame.K_a]:
            rocket['angvel'] -= torque_strength*dt_real
            turn_left=True
        if keys[pygame.K_d]:
            rocket['angvel'] += torque_strength*dt_real
            turn_right=True
        if keys[pygame.K_w]:
            # forward thrust
            thrust_on= True
            heading_rad= math.radians(rocket['heading'])
            rocket['vx']+= 100.0* math.cos(heading_rad)*dt_real
            rocket['vy']+= 100.0* math.sin(heading_rad)*dt_real
            rocket['vx'], rocket['vy']= limit_speed(rocket['vx'], rocket['vy'])
        # 's' => stabilize rotation => apply torque opposite angvel
        if keys[pygame.K_s]:
            # e.g. simple approach => rocket['angvel'] *= 0.9
            # or apply torque T = -some_factor * angvel
            # we'll do a direct damper
            rocket['angvel']-= 3.0* rocket['angvel'] * dt_real
            turn_left=True
            turn_right=True

        # update rocket
        update_rocket(rocket)

        # Periodic boundary for rocket velocity done in limit_speed; for position we did wrap

        # update bullets => each bullet has (x,y,vx,vy,radius,mass)
        new_bul=[]
        for bul in bullets:
            bul['x'] += bul['vx']*BASE_DT
            bul['y'] += bul['vy']*BASE_DT
            # wrap
            bul['x'], bul['y']= wrap_position(bul['x'], bul['y'])
            new_bul.append(bul)
        bullets= new_bul

        # update lightpulses
        # bounce on contact with asteroids
        new_lp=[]
        for lp in lightpulses:
            lp['radius'] += lp['speed']* BASE_DT
            # check collisions with asteroids
            # if ring radius + ast.radius >= dist => bounce => speed *= -1
            for ast in asteroids:
                dist_c= distance(lp['cx'], lp['cy'], ast['x'], ast['y'])
                if dist_c <= lp['radius'] + ast['radius']:
                    lp['speed']*= -1
            # remove if radius<0 => negative => done, or too big => done
            if 0<=lp['radius']<= (WORLD_WIDTH+WORLD_HEIGHT):
                new_lp.append(lp)
        lightpulses= new_lp

        # update bombs => each has x,y,vx,vy,flash_timer,explode_time
        new_bombs=[]
        for bomb in bombs:
            bomb['x']+= bomb['vx']*BASE_DT
            bomb['y']+= bomb['vy']*BASE_DT
            bomb['x'], bomb['y']= wrap_position(bomb['x'], bomb['y'])
            bomb['flash_timer']+= BASE_DT
            if bomb['flash_timer']> bomb['explode_time']:
                # explode
                bomb_explode(bomb, bullets)
            else:
                new_bombs.append(bomb)
        bombs= new_bombs

        # update asteroids
        for ast in asteroids:
            ast['x']+= ast['vx']*BASE_DT
            ast['y']+= ast['vy']*BASE_DT
            ast['x'], ast['y']= wrap_position(ast['x'], ast['y'])

        # bullet <-> asteroid collisions
        new_bul=[]
        for bul in bullets:
            collided=False
            for ast in asteroids:
                if distance_sq(bul['x'],bul['y'], ast['x'],ast['y']) <= (bul['radius']+ ast['radius'])**2:
                    # inelastic => bullet disappears, asteroid gains momentum
                    bullet_asteroid_collision(bul, ast)
                    collided=True
                    break
            if not collided:
                new_bul.append(bul)
        bullets= new_bul

        # Draw
        screen.fill((0,0,0))

        # star background => rocket-based camera
        cam_x= rocket['x'] - SCREEN_WIDTH/2
        cam_y= rocket['y'] - SCREEN_HEIGHT/2
        for st in stars:
            sx_scr= st['x']- cam_x
            sy_scr= st['y']- cam_y
            if 0<=sx_scr< SCREEN_WIDTH and 0<=sy_scr< SCREEN_HEIGHT:
                pygame.draw.circle(screen, st['color'], (int(sx_scr),int(sy_scr)), 1)

        # rocket => center
        draw_rocket(screen, rocket, thrust_on, turn_left, turn_right)

        # bullets => transform
        for bul in bullets:
            bx_scr= bul['x']- cam_x
            by_scr= bul['y']- cam_y
            pygame.draw.circle(screen, (255,255,0), (int(bx_scr), int(by_scr)), 2)

        # light pulses => ring
        for lp in lightpulses:
            cx_scr= lp['cx']- cam_x
            cy_scr= lp['cy']- cam_y
            pygame.draw.circle(screen, (150,150,200), (int(cx_scr), int(cy_scr)), int(lp['radius']), 2)

        # bombs
        for bomb in bombs:
            bx_scr= bomb['x']- cam_x
            by_scr= bomb['y']- cam_y
            # flicker color
            freq= 1.0 + bomb['flash_timer']*2.0
            val= math.sin(2*math.pi*freq* bomb['flash_timer'])
            if val>0: color= (255,0,0)
            else:     color= (255,255,255)
            pygame.draw.circle(screen, color, (int(bx_scr),int(by_scr)), 10)

        # asteroids
        for ast in asteroids:
            ax_scr= ast['x']- cam_x
            ay_scr= ast['y']- cam_y
            pygame.draw.circle(screen, ast['color'], (int(ax_scr), int(ay_scr)), int(ast['radius']))

        # UI
        tool_name= TOOLS[tool_index]
        msg= f"Tool: {tool_name} (Q/E to switch, SPACE=use)  S=stabilize rotation, R=reset rocket/objects"
        text_surf= pygame.font.SysFont("Arial",18).render(msg, True, (200,200,200))
        screen.blit(text_surf, (10,10))

        pygame.display.flip()

    pygame.quit()

def bomb_explode(bomb, bullets):
    """
    Creates radial bullets from bomb location with speed = C_LIGHT,
    in N directions. Then bomb is removed from bombs list in main loop.
    """
    N= 20
    bx, by= bomb['x'], bomb['y']
    bvx, bvy= bomb['vx'], bomb['vy']
    for i in range(N):
        angle= 2*math.pi*i/N
        vx= bvx + C_LIGHT* math.cos(angle)
        vy= bvy + C_LIGHT* math.sin(angle)
        bullets.append({
          'x':bx, 'y':by,
          'vx':vx, 'vy':vy,
          'radius':2.0, 'mass':1.0
        })


if __name__=="__main__":
    main()
