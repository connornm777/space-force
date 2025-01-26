#!/usr/bin/env python3
import math, random, sys
import pygame

# ----------------------------------
# GLOBAL CONSTANTS
# ----------------------------------
SCREEN_WIDTH  = 1800
SCREEN_HEIGHT = 1000
FPS           = 60

BASE_DT       = 0.01
C_LIGHT       = 50000.0
C_MAX         = 50000.0  # you can raise or remove speed limit if desired

WORLD_WIDTH   = 2000
WORLD_HEIGHT  = 100000

TOOLS         = ["Gun","LightPulse","Bomb","ForceField"]
ROCKET_RAD    = 20    # rocket collision radius

############################################################
# LEVEL BASE CLASSES
############################################################

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

############################################################
# LEVEL FLAT
############################################################

class LevelFlat(LevelBase):
    """
    A simple level with no gravity and multiple star-layers.
    """
    def __init__(self):
        super().__init__()
        self.star_layers = self._create_star_layers()
        self.asteroids   = self._create_asteroids()

    def _create_star_layers(self):
        # Increase star density
        layers = []
        # (num_stars, parallax)
        for (n,px) in [(300,0.01),(300,0.02),(250,0.06),(200,0.1)]:
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
        for _ in range(200):
            r = random.uniform(9,10)
            grey= random.randint(100,200)
            asteroid = {
              'x': random.uniform(7*self.WORLD_WIDTH/10,self.WORLD_WIDTH),
              'y': random.uniform(0,self.WORLD_HEIGHT),
              'vx': random.uniform(-5,5),
              'vy': random.uniform(3480,3500),
              'radius':r,
              'mass':r,
              'color':(grey, grey, grey)
            }
            # add random 'spots' for visual interest
            spots = []
            num_spots = random.randint(2,5)
            for _ in range(num_spots):
                # each spot is offset from center with random small radius
                spot_rad = r*random.uniform(0.1,0.3)
                off_angle = random.random()*2*math.pi
                off_dist = r*0.5*random.random()
                offx = off_dist*math.cos(off_angle)
                offy = off_dist*math.sin(off_angle)
                color_variation = random.randint(50,100)
                c = (color_variation, color_variation, color_variation)
                spots.append({'ox':offx,'oy':offy,'r':spot_rad,'c':c})
            asteroid['spots'] = spots
            asts.append(asteroid)
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

############################################################
# LEVEL STAR (SUN)
############################################################

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
        self.star_layers = self._create_star_layers()
        self.asteroids = self._create_asteroids()

    def _create_star_layers(self):
        # Increase star density
        layers = []
        # (num_stars, parallax)
        for (n,px) in [(5000,0.1),(3000,0.2),(2500,0.6),(2000,1.0)]:
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
            r = random.uniform(10,25)
            grey= random.randint(100,200)
            asteroid = {
              'x': random.uniform(0,self.WORLD_WIDTH),
              'y': random.uniform(0,self.WORLD_HEIGHT),
              'vx': random.uniform(-50,50),
              'vy': random.uniform(-50,50),
              'radius':r,
              'mass':r,
              'color':(grey,grey,grey)
            }
            # add spots
            spots = []
            num_spots = random.randint(2,5)
            for _ in range(num_spots):
                spot_rad = r*random.uniform(0.1,0.3)
                off_angle = random.random()*2*math.pi
                off_dist = r*0.5*random.random()
                offx = off_dist*math.cos(off_angle)
                offy = off_dist*math.sin(off_angle)
                color_variation = random.randint(50,100)
                c = (color_variation, color_variation, color_variation)
                spots.append({'ox':offx,'oy':offy,'r':spot_rad,'c':c})
            asteroid['spots'] = spots
            asts.append(asteroid)
        return asts

    def force_func(self, x, y, vx, vy):
        dx= x- self.STAR_CX
        dy= y- self.STAR_CY
        r2= dx*dx+ dy*dy
        r = math.sqrt(r2)
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
        # star radial gradient with user-specified color scheme
        sx= self.STAR_CX- cam_x
        sy= self.STAR_CY- cam_y
        max_r=600
        step=10
        for r in range(int(max_r), self.STAR_RADIUS_LETHAL, -step):
            frac= (r- self.STAR_RADIUS_LETHAL)/(max_r- self.STAR_RADIUS_LETHAL)
            frac= max(0,min(1,frac))
            rr=int(255*(1-frac))
            gg=int(255*((1-frac)**2))
            bb=int(255*((1-frac)**2))
            pygame.draw.circle(screen,(rr,gg,bb),(int(sx),int(sy)),r)
        # lethal core => white
        pygame.draw.circle(screen,(255,255,255),(int(sx),int(sy)), self.STAR_RADIUS_LETHAL)
        for layer in self.star_layers:
            px= layer['parallax']
            for st in layer['stars']:
                draw_object_tiled(
                    screen, st['x'], st['y'], cam_x*px, cam_y*px,
                    st['color'], obj_type="star", radius=1
                )


############################################################
# LEVEL BLACK HOLE
############################################################

class LevelBlackHole(LevelBase):
    """
    Similar to Star, but extremely strong gravity. Lethal radius is pitch black.
    """
    STAR_RADIUS_LETHAL=200  # same lethal radius
    GRAVITY_RANGE=800
    G_M=150000  # stronger gravity

    def __init__(self):
        super().__init__()
        self.HOLE_CX= self.WORLD_WIDTH/2
        self.HOLE_CY= self.WORLD_HEIGHT/2
        self.star_list = self._create_far_stars()
        self.asteroids = self._create_asteroids()

    def _create_far_stars(self):
        s_list=[]
        # also high density
        for _ in range(800):
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
            asteroid = {
              'x': random.uniform(0,self.WORLD_WIDTH),
              'y': random.uniform(0,self.WORLD_HEIGHT),
              'vx': random.uniform(-50,50),
              'vy': random.uniform(-50,50),
              'radius':r,
              'mass':r,
              'color':(grey,grey,grey)
            }
            # add spots
            spots = []
            num_spots = random.randint(2,5)
            for _ in range(num_spots):
                spot_rad = r*random.uniform(0.1,0.3)
                off_angle = random.random()*2*math.pi
                off_dist = r*0.5*random.random()
                offx = off_dist*math.cos(off_angle)
                offy = off_dist*math.sin(off_angle)
                color_variation = random.randint(50,100)
                c = (color_variation, color_variation, color_variation)
                spots.append({'ox':offx,'oy':offy,'r':spot_rad,'c':c})
            asteroid['spots'] = spots
            asts.append(asteroid)
        return asts

    def force_func(self, x, y, vx, vy):
        dx= x- self.HOLE_CX
        dy= y- self.HOLE_CY
        r2= dx*dx+ dy*dy
        r = math.sqrt(r2)
        if r >= self.GRAVITY_RANGE or r < 1e-3:
            return (0.0,0.0)
        a_mag= self.G_M/ r2
        ax= -a_mag*(dx/r)
        ay= -a_mag*(dy/r)
        return (ax,ay)

    def lethal_check(self, x, y):
        dx= x- self.HOLE_CX
        dy= y- self.HOLE_CY
        return (dx*dx+ dy*dy) < (self.STAR_RADIUS_LETHAL*self.STAR_RADIUS_LETHAL)

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))
        # black hole lethal radius => pitch black circle
        sx= self.HOLE_CX- cam_x
        sy= self.HOLE_CY- cam_y
        pygame.draw.circle(screen,(0,0,0),(int(sx),int(sy)), self.STAR_RADIUS_LETHAL)
        # far stars => no parallax
        for st in self.star_list:
            draw_object_tiled(
                screen, st['x'], st['y'], cam_x*0.0, cam_y*0.0,
                st['color'], obj_type="star", radius=1
            )

############################################################
# UTILITY FUNCTIONS
############################################################

def limit_speed(vx, vy, cmax=C_MAX):
    spd= math.hypot(vx, vy)
    if spd> cmax:
        scl= cmax/spd
        vx*= scl
        vy*= scl
    return vx, vy

def wrap_pos(x, y, w=WORLD_WIDTH, h=WORLD_HEIGHT):
    x%= w
    y%= h
    return x, y

def update_rocket(rocket, dt):
    rocket['x']+= rocket['vx']* dt
    rocket['y']+= rocket['vy']* dt
    rocket['x'], rocket['y']= wrap_pos(rocket['x'], rocket['y'])
    rocket['heading']+= rocket['angvel']* dt

############################################################
# DRAW
############################################################

def draw_rocket(screen, rocket, forward_thrust_on, reverse_thrust_on, turn_left, turn_right):
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
    if forward_thrust_on:
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

   # reverse thruster => show from nose => blue
    if reverse_thrust_on:
        flame_len=25
        flame_rad= rad
        fx= nose_x+ random.uniform(0.8,1.2)* flame_len* math.cos(flame_rad)
        fy= nose_y+ random.uniform(0.8,1.2)* flame_len* math.sin(flame_rad)
        pygame.draw.line(screen,(0,0,255),(nose_x,nose_y),(fx,fy),3)


    # Force field => translucent green fill + bright edge
    if rocket['forcefield_on']:
        shield_rad=80
        srf= pygame.Surface((shield_rad*2, shield_rad*2), pygame.SRCALPHA)
        srf.fill((0,0,0,0))
        pygame.draw.circle(srf,(0,255,0,50),(shield_rad,shield_rad),shield_rad)
        pygame.draw.circle(srf,(0,255,0,150),(shield_rad,shield_rad),shield_rad,2)
        screen.blit(srf,(rx-shield_rad, ry-shield_rad))


def elastic_bounce(m1,m2, x1,y1,vx1,vy1, x2,y2,vx2,vy2):
    dx= x2-x1
    dy= y2-y1
    dist= math.sqrt(dx*dx+ dy*dy)+1e-10
    nx= dx/dist
    ny= dy/dist
    vx_rel= vx2-vx1
    vy_rel= vy2-vy1
    vn= vx_rel*nx + vy_rel*ny
    if vn> 0:
        return vx1,vy1, vx2,vy2
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
    if dist < ast['radius']+bul['radius']:
        bul['vx'], bul['vy'], ast['vx'], ast['vy'] = elastic_bounce(
                bul['mass'], ast['mass'], bul['x'], bul['y'], bul['vx'], bul['vy'], ast['x'], ast['y'], ast['vx'], ast['vy']
                )
        return
        nx= dx/dist
        ny= dy/dist
        mB= bul['mass']
        mA= ast['mass']
        mT = mA + mB
        rcm = [(mA*ast['x']+mB*bul['x'])/mT, (mA*ast['y']+mB*bul['y'])/mT]
        vxB, vyB= bul['vx'], bul['vy']
        vxA, vyA= ast['vx'], ast['vy']
        vx_rel= vxA- vxB
        vy_rel= vyA- vyB
        vn= vx_rel*nx + vy_rel*ny
        factor = vn/(mT*dist)
        bul['vx']+= -2*mA*factor*nx
        bul['vy']+= -2*mA*factor*ny
        ast['vx']+= -2*mB*factor*nx 
        ast['vy']+= -2*mB*factor*ny

def bomb_explode(bomb, bullets):
    N=100
    bx, by= bomb['x'], bomb['y']
    bvx,bvy= bomb['vx'], bomb['vy']
    for i in range(N):
        angle= 2*math.pi*i/N
        vx= bvx+ 500*math.cos(angle)
        vy= bvy+ 500*math.sin(angle)
        bullets.append({
          'x':bx, 'y':by, 'vx':vx,'vy':vy,
          'radius':1.0,'mass':0.1,'life':5.0
        })

def draw_object_tiled(screen, wx, wy, cam_x, cam_y, color, obj_type="star", radius=1):
    # draws a simple circle in all wrap-around positions
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            sx= (wx+ dx*WORLD_WIDTH)- cam_x
            sy= (wy+ dy*WORLD_HEIGHT)- cam_y
            if 0<= sx< screen.get_width() and 0<= sy< screen.get_height():
                pygame.draw.circle(screen,color,(int(sx),int(sy)),radius)


def draw_object_tiled_asteroid(screen, ast, cam_x, cam_y):
    # draw main circle + spots in all wrap offsets
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            sx= (ast['x']+ dx*WORLD_WIDTH) - cam_x
            sy= (ast['y']+ dy*WORLD_HEIGHT) - cam_y
            if 0<= sx< screen.get_width() and 0<= sy< screen.get_height():
                # main asteroid body
                pygame.draw.circle(screen, ast['color'], (int(sx), int(sy)), int(ast['radius']))
                # spots
                for spot in ast['spots']:
                    spot_sx= sx+ spot['ox']
                    spot_sy= sy+ spot['oy']
                    pygame.draw.circle(screen, spot['c'], (int(spot_sx),int(spot_sy)), int(spot['r']))


def draw_object_tiled_ring(screen, wx, wy, cam_x, cam_y, color, ring_radius):
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            sx= (wx + dx*WORLD_WIDTH) - cam_x
            sy= (wy + dy*WORLD_HEIGHT) - cam_y
            if 0<= sx<screen.get_width() and 0<= sy<screen.get_height():
                pygame.draw.circle(screen, color, (int(sx), int(sy)), ring_radius,2)

############################################################
# MAIN GAME LOOP
############################################################
def main():
    pygame.init()
    screen= pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock= pygame.time.Clock()
    font= pygame.font.SysFont("Arial",18)

    # updated menu to include black hole
    level_name= run_level_menu(screen, font)
    if level_name=="star":
        lvl= LevelStar()
        rocket_x= lvl.WORLD_WIDTH/2
        rocket_y= lvl.WORLD_HEIGHT/2 + 2000
    elif level_name=="hole":
        lvl= LevelBlackHole()
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
            rocket['y']= newlvl.WORLD_HEIGHT/2 +2000
        elif level_name=="hole":
            newlvl= LevelBlackHole()
            rocket['x']= newlvl.WORLD_WIDTH/2
            rocket['y']= newlvl.WORLD_HEIGHT/2 +2000
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
                            bvx= rocket['vx']+ C_LIGHT* math.cos(h_rad)
                            bvy= rocket['vy']+ C_LIGHT* math.sin(h_rad)
                            rocket['vx'] -= bvx*0.01
                            rocket['vy'] -= bvy*0.01
                            bullets.append({
                            'x':bx,'y':by,'vx':bvx,'vy':bvy,
                            'radius':1.0,'mass':0.3,'life':4.0
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
        forward_thrust=False
        reverse_thrust=False
        torque=50.0

        if keys[pygame.K_a]:
            rocket['angvel']-= torque*dt_real
            turn_left=True
        if keys[pygame.K_d]:
            rocket['angvel']+= torque*dt_real
            turn_right=True
        if keys[pygame.K_w]:
            h_rad= math.radians(rocket['heading'])
            rocket['vx']+= 100.0*math.cos(h_rad)* dt_real
            rocket['vy']+= 100.0*math.sin(h_rad)* dt_real
            rocket['vx'], rocket['vy']= limit_speed(rocket['vx'], rocket['vy'])
            forward_thrust=True
        if keys[pygame.K_s]:
            h_rad= math.radians(rocket['heading'])
            rocket['vx']-= 100.0* math.cos(h_rad)* dt_real
            rocket['vy']-= 100.0* math.sin(h_rad)* dt_real
            rocket['vx'], rocket['vy']= limit_speed(rocket['vx'], rocket['vy'])
            reverse_thrust=True

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
            lp['color_alpha']-= 3000.0*BASE_DT
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

        # asteroids => update (gravity applies)
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
            shield_mass=100.0
            # bullet bounce
            for bul in bullets:
                dx= bul['x']- rocket['x']
                dy= bul['y']- rocket['y']
                ds= dx*dx+ dy*dy
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
                    # rocket velocity update
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

        draw_rocket(screen, rocket, forward_thrust, reverse_thrust, turn_left, turn_right)

        # draw bullets
        for bul in bullets:
            draw_object_tiled(screen, bul['x'], bul['y'], cam_x, cam_y, (255,255,0), "circle", 2)
        # draw pulses
        for lp in lightpulses:
            alpha= max(0,int(lp['color_alpha']))
            fade_c= (150*alpha//255,150*alpha//255,200*alpha//255)
            draw_object_tiled_ring(screen, lp['cx'], lp['cy'], cam_x, cam_y, fade_c, int(lp['radius']))
        # draw bombs
        for bomb in bombs:
            freq= 1.0+ bomb['flash_timer']*2.0
            val= math.sin(2*math.pi* freq* bomb['flash_timer'])
            color= (255,0,0) if val>0 else (255,255,255)
            draw_object_tiled(screen, bomb['x'], bomb['y'], cam_x, cam_y, color,"circle",10)
        # draw asteroids with spots
        for ast in lvl.asteroids:
            draw_object_tiled_asteroid(screen, ast, cam_x, cam_y)

        # tool icons
        x_icon=10
        y_icon=50
        for i,tname in enumerate(TOOLS):
            rect= pygame.Rect(x_icon, y_icon+ i*(45), 40,40)
            color=(200,200,100) if i== tool_index else (50,50,50)
            pygame.draw.rect(screen,color,rect)
            label= font.render(tname,True,(0,0,0))
            screen.blit(label,(x_icon+5,y_icon+ i*(45)+10))

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
    menu_options= ["Flat","Star","Hole"]  # added black hole level
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
