#!/usr/bin/env python3
import math, random, sys
import pygame

# ----------------------------------
# GLOBAL CONSTANTS
# ----------------------------------
# Increased speed limit to a very high value to effectively remove it.
SCREEN_WIDTH  = 1800
SCREEN_HEIGHT = 1000
FPS           = 60

BASE_DT       = 0.01
C_LIGHT       = 300.0
C_MAX         = 999999.0   # effectively no max speed

WORLD_WIDTH   = 5000
WORLD_HEIGHT  = 5000

TOOLS         = ["Gun","LightPulse","Bomb","ForceField"]
ROCKET_RAD    = 20    # rocket collision radius

# ------------------------------------------------------------------
# LEVEL BASE CLASSES
# ------------------------------------------------------------------
class LevelBase:
    def __init__(self):
        self.WORLD_WIDTH  = WORLD_WIDTH
        self.WORLD_HEIGHT = WORLD_HEIGHT
        self.asteroids    = []

    def force_func(self, x, y, vx, vy):
        return (0.0, 0.0)

    def lethal_check(self, x, y):
        return False

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))

class LevelFlat(LevelBase):
    """
    A simple level with no gravity and multiple star-layers.
    """
    def __init__(self):
        super().__init__()
        self.star_layers = self._create_star_layers()
        self.asteroids   = self._create_asteroids()

    def _create_star_layers(self):
        layers = []
        # (num_stars, parallax)
        for (n,px) in [(200,0.0),(200,0.2),(150,0.6),(100,1.0)]:
            stars = []
            for _ in range(n):
                sx  = random.uniform(0,self.WORLD_WIDTH)
                sy  = random.uniform(0,self.WORLD_HEIGHT)
                bri = random.randint(100,220)
                stars.append({'x':sx,'y':sy,'color':(bri,bri,bri)})
            layers.append({'stars': stars, 'parallax': px})
        return layers

    def _create_asteroids(self):
        asts=[]
        for _ in range(20):
            r = random.uniform(15,35)
            grey= random.randint(100,200)
            asts.append({
              'x': random.uniform(0,self.WORLD_WIDTH),
              'y': random.uniform(0,self.WORLD_HEIGHT),
              'vx': random.uniform(-50,50),
              'vy': random.uniform(-50,50),
              'radius':r,
              'mass':r,
              'color':(grey,grey,grey)
            })
        return asts

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))
        for layer in self.star_layers:
            px= layer['parallax']
            for st in layer['stars']:
                draw_object_tiled(
                    screen, st['x'], st['y'], cam_x*px, cam_y*px,
                    st['color'], obj_type="star", radius=1
                )

class LevelStar(LevelBase):
    """
    A star at center with lethal radius=200, gravity range=800 => G=30000.
    Has a radial gradient background, plus some fixed stars.
    """
    STAR_RADIUS_LETHAL=200
    GRAVITY_RANGE=800
    G_M=30000

    def __init__(self):
        super().__init__()
        self.STAR_CX= self.WORLD_WIDTH/2
        self.STAR_CY= self.WORLD_HEIGHT/2
        self.star_list = self._create_far_stars()
        self.asteroids = self._create_asteroids()

    def _create_far_stars(self):
        s_list=[]
        # increased count to 2000 for denser starfield
        for _ in range(2000):
            sx= random.uniform(0,self.WORLD_WIDTH)
            sy= random.uniform(0,self.WORLD_HEIGHT)
            bri= random.randint(100,220)
            s_list.append({'x':sx,'y':sy,'color':(bri,bri,bri)})
        return s_list

    def _create_asteroids(self):
        asts=[]
        for _ in range(20):
            r = random.uniform(10,25)
            grey= random.randint(100,200)
            asts.append({
              'x': random.uniform(0,self.WORLD_WIDTH),
              'y': random.uniform(0,self.WORLD_HEIGHT),
              'vx': random.uniform(-50,50),
              'vy': random.uniform(-50,50),
              'radius':r,
              'mass':r,
              'color':(grey,grey,grey)
            })
        return asts

    def force_func(self, x, y, vx, vy):
        dx= x- self.STAR_CX
        dy= y- self.STAR_CY
        r2= dx*dx+ dy*dy
        r = math.sqrt(r2)
        # only apply gravity if within range
        if r >= self.GRAVITY_RANGE or r < 1e-3:
            return (0.0,0.0)
        a_mag= self.G_M/ r2
        ax= -a_mag*(dx/r)
        ay= -a_mag*(dy/r)
        return (ax,ay)

    def lethal_check(self, x, y):
        dx= x- self.STAR_CX
        dy= y- self.STAR_CY
        return (dx*dx+ dy*dy) < (self.STAR_RADIUS_LETHAL*self.STAR_RADIUS_LETHAL)

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))
        # radial gradient from outer to lethal radius
        sx= self.STAR_CX- cam_x
        sy= self.STAR_CY- cam_y
        max_r=600
        step=10
        for rr in range(int(max_r), self.STAR_RADIUS_LETHAL, -step):
            frac= (rr- self.STAR_RADIUS_LETHAL)/(max_r- self.STAR_RADIUS_LETHAL)
            frac= max(0,min(1,frac))
            # color fade from white to darker reds
            red= int(255*(1-frac))
            g = int(255*(1-frac)**2)
            b = int(255*(1-frac)**2)
            pygame.draw.circle(screen, (red,g,b), (int(sx), int(sy)), rr)
        # lethal core
        pygame.draw.circle(screen,(255,255,255),(int(sx),int(sy)), self.STAR_RADIUS_LETHAL)

        # far stars => no parallax
        for st in self.star_list:
            draw_object_tiled(
                screen, st['x'], st['y'], cam_x*0.0, cam_y*0.0,
                st['color'], obj_type="star", radius=1
            )

# ---------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------

def limit_speed(vx, vy, cmax=C_MAX):
    # If you prefer truly no limit, just return vx, vy.
    # For now, keep cmax very large so it won't hamper normal play.
    spd= math.hypot(vx, vy)
    if spd> cmax:
        scl= cmax/spd
        vx*= scl
        vy*= scl
    return vx, vy


def wrap_pos(x, y, w=WORLD_WIDTH, h=WORLD_HEIGHT):
    # periodic boundary
    x%= w
    y%= h
    return x, y


def update_rocket(rocket, dt):
    rocket['x']+= rocket['vx']* dt
    rocket['y']+= rocket['vy']* dt
    rocket['x'], rocket['y']= wrap_pos(rocket['x'], rocket['y'])
    rocket['heading']+= rocket['angvel']* dt


def draw_rocket(screen, rocket, thrust_on, turn_left, turn_right):
    rx= SCREEN_WIDTH/2
    ry= SCREEN_HEIGHT/2
    length= 30.0
    rad= math.radians(rocket['heading'])

    nose_x= rx + length*math.cos(rad)
    nose_y= ry + length*math.sin(rad)
    left_x= rx + (-0.4*length)*math.cos(rad + math.radians(130))
    left_y= ry + (-0.4*length)*math.sin(rad + math.radians(130))
    right_x= rx + (-0.4*length)*math.cos(rad - math.radians(130))
    right_y= ry + (-0.4*length)*math.sin(rad - math.radians(130))

    color_front=(255,0,0)
    color_back =(180,0,0)
    pygame.draw.polygon(screen, color_front, [(nose_x,nose_y),(left_x,left_y),(right_x,right_y)])
    back_x= rx - 0.7*length*math.cos(rad)
    back_y= ry - 0.7*length*math.sin(rad)
    pygame.draw.polygon(screen, color_back, [(left_x,left_y),(back_x,back_y),(right_x,right_y)])

    # thrusters
    if thrust_on and not rocket['forcefield_on']:
        flame_len=25
        flame_rad= rad+ math.pi
        fx= back_x+ random.uniform(0.8,1.2)* flame_len* math.cos(flame_rad)
        fy= back_y+ random.uniform(0.8,1.2)* flame_len* math.sin(flame_rad)
        pygame.draw.line(screen,(255,165,0),(back_x,back_y),(fx,fy),3)

    if turn_left:
        flame_len=15
        side_ang= rad- math.radians(90)
        sx, sy= right_x, right_y
        fx= sx+ flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        fy= sy+ flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(screen,(0,255,0),(sx,sy),(fx,fy),2)

    if turn_right:
        flame_len=15
        side_ang= rad+ math.radians(90)
        sx, sy= left_x, left_y
        fx= sx+ flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        fy= sy+ flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(screen,(0,255,0),(sx,sy),(fx,fy),2)

    # Force field => translucent green fill + bright edge
    if rocket['forcefield_on']:
        shield_rad=80
        srf= pygame.Surface((shield_rad*2, shield_rad*2), pygame.SRCALPHA)
        srf.fill((0,0,0,0))
        center=(shield_rad, shield_rad)
        # faint fill
        pygame.draw.circle(srf, (0,255,0,50), center, shield_rad)
        # bright edge
        pygame.draw.circle(srf, (0,255,0,150), center, shield_rad, 2)
        screen.blit(srf, (rx-shield_rad, ry-shield_rad))


def elastic_bounce(m1,m2, x1,y1,vx1,vy1, x2,y2,vx2,vy2):
    dx= x2-x1
    dy= y2-y1
    dist= math.sqrt(dx*dx+ dy*dy)+1e-10
    nx= dx/dist
    ny= dy/dist
    vx_rel= vx2-vx1
    vy_rel= vy2-vy1
    vn= vx_rel*nx + vy_rel*ny
    # only bounce if objects are moving closer
    if vn> 0:
        return vx1,vy1, vx2,vy2

    # perfectly elastic
    e= 1.0
    imp= -(1+ e)* vn / (1/m1 + 1/m2)
    impx= imp* nx
    impy= imp* ny

    return (
        vx1- impx/m1,  vy1- impy/m1,
        vx2+ impx/m2,  vy2+ impy/m2
    )

def bullet_asteroid_collision(bul, ast):
    dx= ast['x']- bul['x']
    dy= ast['y']- bul['y']
    dist= math.hypot(dx, dy)
    if dist < 1e-10:
        return

    nx= dx/dist
    ny= dy/dist
    mB= bul['mass']
    mA= ast['mass']
    vxB, vyB= bul['vx'], bul['vy']
    vxA, vyA= ast['vx'], ast['vy']

    # relative velocity
    vx_rel= vxA- vxB
    vy_rel= vyA- vyB
    vn= vx_rel*nx + vy_rel*ny
    # if they're moving apart, no collision
    if vn>0:
        return

    # do an elastic collision
    e= 1.0
    imp= -(1+ e)* vn / (1/mB + 1/mA)
    impx= imp* nx
    impy= imp* ny

    bul['vx']+= impx/mB
    bul['vy']+= impy/mB
    ast['vx']-= impx/mA
    ast['vy']-= impy/mA

    # push them out of overlap if needed
    r_sum= bul['radius']+ ast['radius']
    overlap= (r_sum - dist)
    if overlap>0:
        # proportion to masses
        bul_push= overlap*(mA/(mA+ mB))
        ast_push= overlap*(mB/(mA+ mB))
        bul['x']-= nx* bul_push
        bul['y']-= ny* bul_push
        ast['x']+= nx* ast_push
        ast['y']+= ny* ast_push


def bomb_explode(bomb, bullets):
    N=20
    bx, by= bomb['x'], bomb['y']
    bvx,bvy= bomb['vx'], bomb['vy']
    for i in range(N):
        angle= 2*math.pi*i/N
        vx= bvx+ C_LIGHT*math.cos(angle)
        vy= bvy+ C_LIGHT*math.sin(angle)
        bullets.append({
            'x':bx, 'y':by,
            'vx':vx, 'vy':vy,
            'radius':2.0, 'mass':1.0,
            'life':4.0
        })

def draw_object_tiled(screen, wx, wy, cam_x, cam_y, color, obj_type="star", radius=1):
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            sx= (wx+ dx*WORLD_WIDTH)- cam_x
            sy= (wy+ dy*WORLD_HEIGHT)- cam_y
            if 0<= sx<screen.get_width() and 0<= sy<screen.get_height():
                pygame.draw.circle(screen, color, (int(sx),int(sy)), radius)


def draw_object_tiled_ring(screen, wx, wy, cam_x, cam_y, color, ring_radius):
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            sx= (wx + dx*WORLD_WIDTH) - cam_x
            sy= (wy + dy*WORLD_HEIGHT) - cam_y
            if 0<= sx<screen.get_width() and 0<= sy<screen.get_height():
                pygame.draw.circle(screen, color, (int(sx), int(sy)), ring_radius, 2)

# ---------------------------------------------------------
# MAIN GAME LOOP
# ---------------------------------------------------------
def main():
    pygame.init()
    screen= pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock= pygame.time.Clock()
    font= pygame.font.SysFont("Arial",18)

    level_name= run_level_menu(screen, font)
    if level_name=="star":
        lvl= LevelStar()
        rocket_x= lvl.WORLD_WIDTH/2
        rocket_y= lvl.WORLD_HEIGHT/2 + 2000
    else:
        lvl= LevelFlat()
        rocket_x= lvl.WORLD_WIDTH/2
        rocket_y= lvl.WORLD_HEIGHT/2

    rocket = {
      'x':rocket_x, 'y':rocket_y,
      'vx':0,       'vy':0,
      'heading':0,  'angvel':0,
      'forcefield_on':False
    }

    bullets=[]
    lightpulses=[]
    bombs=[]
    asteroids= lvl.asteroids
    game_over=False
    tool_index=0

    def reset_game():
        nonlocal rocket, bullets, lightpulses, bombs, asteroids, game_over
        if level_name=="star":
            newlvl= LevelStar()
            rocket['x']= newlvl.WORLD_WIDTH/2
            rocket['y']= newlvl.WORLD_HEIGHT/2 + 2000
        else:
            newlvl= LevelFlat()
            rocket['x']= newlvl.WORLD_WIDTH/2
            rocket['y']= newlvl.WORLD_HEIGHT/2
        rocket['vx']=0
        rocket['vy']=0
        rocket['heading']=0
        rocket['angvel']=0
        rocket['forcefield_on']=False
        bullets.clear()
        lightpulses.clear()
        bombs.clear()
        asteroids.clear()
        asteroids.extend(newlvl.asteroids)
        game_over=False

    running=True
    while running:
        dt_real= clock.tick(FPS)/1000.0
        for event in pygame.event.get():
            if event.type== pygame.QUIT:
                running=False
            elif event.type== pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    running=False
                elif event.key==pygame.K_q and not game_over:
                    tool_index= (tool_index-1)% len(TOOLS)
                elif event.key==pygame.K_e and not game_over:
                    tool_index= (tool_index+1)% len(TOOLS)
                elif event.key==pygame.K_SPACE:
                    if game_over:
                        reset_game()
                    else:
                        tname= TOOLS[tool_index]
                        if tname=="Gun":
                            h_rad= math.radians(rocket['heading'])
                            dx=30* math.cos(h_rad)
                            dy=30* math.sin(h_rad)
                            bx= rocket['x']+ dx
                            by= rocket['y']+ dy
                            bvx= rocket['vx']+ C_LIGHT*math.cos(h_rad)
                            bvy= rocket['vy']+ C_LIGHT*math.sin(h_rad)
                            bullets.append({
                              'x':bx,'y':by,'vx':bvx,'vy':bvy,
                              'radius':2.0,'mass':1.0,'life':4.0
                            })
                        elif tname=="LightPulse":
                            lightpulses.append({
                              'cx': rocket['x'],'cy': rocket['y'],
                              'radius':0.0,'speed':C_LIGHT,
                              'max_radius':2000.0,
                              'color_alpha':255
                            })
                        elif tname=="Bomb":
                            bombs.append({
                              'x':rocket['x'],'y':rocket['y'],
                              'vx':rocket['vx'],'vy':rocket['vy'],
                              'flash_timer':0.0,'explode_time':3.0
                            })
                        elif tname=="ForceField":
                            rocket['forcefield_on']= not rocket['forcefield_on']
                elif event.key== pygame.K_r:
                    if game_over:
                        reset_game()
                    else:
                        reset_game()

        if game_over:
            screen.fill((0,0,0))
            msg= "GAME OVER! Press SPACE to restart"
            txt_s= font.render(msg, True,(255,0,0))
            screen.blit(txt_s,(SCREEN_WIDTH/2-100, SCREEN_HEIGHT/2))
            pygame.display.flip()
            continue

        # keys
        keys= pygame.key.get_pressed()
        turn_left=False
        turn_right=False
        thrust_on=False
        torque=50.0

        if keys[pygame.K_a]:
            rocket['angvel']-= torque*dt_real
            turn_left=True
        if keys[pygame.K_d]:
            rocket['angvel']+= torque*dt_real
            turn_right=True
        if keys[pygame.K_w] and not rocket['forcefield_on']:
            h_rad= math.radians(rocket['heading'])
            rocket['vx']+= 100.0*math.cos(h_rad)* dt_real
            rocket['vy']+= 100.0*math.sin(h_rad)* dt_real
            rocket['vx'], rocket['vy']= limit_speed(rocket['vx'], rocket['vy'])
            thrust_on=True
        if keys[pygame.K_s]:
            rocket['angvel']-= 3.0* rocket['angvel']* dt_real
            turn_left=True
            turn_right=True

        # level force => rocket
        ax, ay= lvl.force_func(rocket['x'], rocket['y'], rocket['vx'], rocket['vy'])
        rocket['vx']+= ax*BASE_DT
        rocket['vy']+= ay*BASE_DT
        rocket['vx'], rocket['vy']= limit_speed(rocket['vx'], rocket['vy'])
        update_rocket(rocket, BASE_DT)

        # lethal => rocket
        if lvl.lethal_check(rocket['x'], rocket['y']):
            game_over=True

        # Bullets
        new_bul=[]
        for bul in bullets:
            bul['x']+= bul['vx']*BASE_DT
            bul['y']+= bul['vy']*BASE_DT
            bul['x'], bul['y']= wrap_pos(bul['x'], bul['y'])
            bul['life']-= BASE_DT
            if bul['life']>0 and not lvl.lethal_check(bul['x'], bul['y']):
                new_bul.append(bul)
        bullets= new_bul

        # pulses => expand & fade
        new_lp=[]
        for lp in lightpulses:
            lp['radius']+= lp['speed']*BASE_DT
            lp['color_alpha']-= 60.0*BASE_DT
            if lp['radius']< lp['max_radius'] and lp['color_alpha']>0:
                new_lp.append(lp)
        lightpulses= new_lp

        # bombs
        new_bombs=[]
        for bomb in bombs:
            bomb['x']+= bomb['vx']*BASE_DT
            bomb['y']+= bomb['vy']*BASE_DT
            bomb['x'], bomb['y']= wrap_pos(bomb['x'], bomb['y'])
            bomb['flash_timer']+= BASE_DT
            if bomb['flash_timer']> bomb['explode_time']:
                bomb_explode(bomb, bullets)
            else:
                new_bombs.append(bomb)
        bombs= new_bombs

        # asteroids => update
        new_ast=[]
        for ast in lvl.asteroids:
            fx,fy= lvl.force_func(ast['x'], ast['y'], ast['vx'], ast['vy'])
            ast['vx']+= fx*BASE_DT
            ast['vy']+= fy*BASE_DT
            ast['x']+= ast['vx']*BASE_DT
            ast['y']+= ast['vy']*BASE_DT
            ast['x'], ast['y']= wrap_pos(ast['x'], ast['y'])
            if not lvl.lethal_check(ast['x'], ast['y']):
                new_ast.append(ast)
        lvl.asteroids= new_ast

        # bullet <-> asteroid collisions
        for bul in bullets:
            for ast in lvl.asteroids:
                dx= ast['x']- bul['x']
                dy= ast['y']- bul['y']
                r_sum= ast['radius']+ bul['radius']
                if dx*dx+ dy*dy <= r_sum*r_sum:
                    bullet_asteroid_collision(bul, ast)

        # Forcefield collisions
        if rocket['forcefield_on']:
            shield_rad=80
            shield_mass=1.0
            # bullet bounce
            for bul in bullets:
                dx= bul['x']- rocket['x']
                dy= bul['y']- rocket['y']
                ds= dx*dx+ dy*dy
                # if bullet is inside rocket radius => game over
                if ds<= (ROCKET_RAD+ bul['radius'])**2:
                    game_over=True
                    break
                elif ds<= (shield_rad+ bul['radius'])**2:
                    vx1,vy1,vx2,vy2= elastic_bounce(
                        bul['mass'], shield_mass,
                        bul['x'], bul['y'], bul['vx'], bul['vy'],
                        rocket['x'], rocket['y'], rocket['vx'], rocket['vy']
                    )
                    bul['vx'], bul['vy']= vx1, vy1
                    # If you want rocket to be unaffected, comment out:
                    rocket['vx'], rocket['vy']= vx2, vy2
            # asteroid bounce
            if not game_over:
                for ast in lvl.asteroids:
                    dx= ast['x']- rocket['x']
                    dy= ast['y']- rocket['y']
                    ds= dx*dx+ dy*dy
                    if ds<= (ROCKET_RAD+ ast['radius'])**2:
                        game_over=True
                        break
                    elif ds<= (shield_rad+ ast['radius'])**2:
                        vx1,vy1,vx2,vy2= elastic_bounce(
                            ast['mass'], shield_mass,
                            ast['x'],ast['y'], ast['vx'],ast['vy'],
                            rocket['x'],rocket['y'], rocket['vx'],rocket['vy']
                        )
                        ast['vx'], ast['vy']= vx1, vy1
                        rocket['vx'], rocket['vy']= vx2, vy2
        else:
            # rocket collisions => bullet or asteroid
            for bul in bullets:
                dx= bul['x']- rocket['x']
                dy= bul['y']- rocket['y']
                if dx*dx+ dy*dy <= (ROCKET_RAD+ bul['radius'])**2:
                    game_over=True
                    break
            if not game_over:
                for ast in lvl.asteroids:
                    dx= ast['x']- rocket['x']
                    dy= ast['y']- rocket['y']
                    if dx*dx+ dy*dy <= (ROCKET_RAD+ ast['radius'])**2:
                        game_over=True
                        break

        # draw
        cam_x= rocket['x']- SCREEN_WIDTH/2
        cam_y= rocket['y']- SCREEN_HEIGHT/2
        lvl.draw_background(screen, rocket, cam_x, cam_y)
        draw_rocket(screen, rocket, (keys[pygame.K_w] and not rocket['forcefield_on']), keys[pygame.K_a], keys[pygame.K_d])

        # bullets
        for bul in bullets:
            draw_object_tiled(screen, bul['x'], bul['y'], cam_x, cam_y, (255,255,0), "circle", 2)

        # pulses
        for lp in lightpulses:
            alpha= max(0,int(lp['color_alpha']))
            fade_c= (150*alpha//255,150*alpha//255,200*alpha//255)
            draw_object_tiled_ring(screen, lp['cx'], lp['cy'], cam_x, cam_y, fade_c, int(lp['radius']))

        # bombs
        for bomb in bombs:
            freq= 1.0+ bomb['flash_timer']*2.0
            val= math.sin(2*math.pi* freq* bomb['flash_timer'])
            color= (255,0,0) if val>0 else (255,255,255)
            draw_object_tiled(screen, bomb['x'], bomb['y'], cam_x, cam_y, color, "circle", 10)

        # asteroids
        for ast in lvl.asteroids:
            draw_object_tiled(screen, ast['x'], ast['y'], cam_x, cam_y, ast['color'], "circle", int(ast['radius']))

        # tool icons
        x_icon=10
        y_icon=50
        for i,tname in enumerate(TOOLS):
            rect= pygame.Rect(x_icon, y_icon+ i*(45), 40,40)
            color=(200,200,100) if i== tool_index else (50,50,50)
            pygame.draw.rect(screen,color,rect)
            label= font.render(tname,True,(0,0,0))
            screen.blit(label,(x_icon+5,y_icon+ i*(45)+10))

        # instructions
        msg="Q/E=tools, SPACE=use, W/A/D=move, S=stabilize, R=reset, ESC=quit"
        text_surf= font.render(msg, True,(200,200,200))
        screen.blit(text_surf,(10,10))

        if game_over:
            go_msg= "GAME OVER! Press SPACE to restart"
            txt_s= font.render(go_msg, True,(255,0,0))
            screen.blit(txt_s,(SCREEN_WIDTH/2-100, SCREEN_HEIGHT/2))

        pygame.display.flip()

    pygame.quit()


def run_level_menu(screen, font):
    menu_options= ["Flat","Star"]
    idx=0
    clock= pygame.time.Clock()

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type== pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type== pygame.KEYDOWN:
                if event.key== pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    idx= (idx-1)% len(menu_options)
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    idx= (idx+1)% len(menu_options)
                elif event.key== pygame.K_RETURN:
                    return menu_options[idx].lower()

        screen.fill((20,20,30))
        title= "SPACE-FORCE: SELECT LEVEL"
        t_surf= font.render(title, True,(255,255,255))
        screen.blit(t_surf,(SCREEN_WIDTH//2-100, 100))

        for i,opt in enumerate(menu_options):
            color= (200,200,100) if i==idx else (200,200,200)
            txt= font.render(opt, True,color)
            screen.blit(txt,(SCREEN_WIDTH//2-50+ i*150, 300))

        instruct= "Use Left/Right, Enter to confirm, Esc to quit"
        i_surf= font.render(instruct, True,(200,200,200))
        screen.blit(i_surf,(SCREEN_WIDTH//2-200, SCREEN_HEIGHT-100))
        pygame.display.flip()

# -----------------------------------------
if __name__=="__main__":
    main()
