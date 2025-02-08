import math, random, sys
import pygame

############################################################
# GLOBAL CONSTANTS
############################################################
SCREEN_WIDTH  = 1800
SCREEN_HEIGHT = 1000
FPS           = 60

BASE_DT       = 0.1


WORLD_WIDTH   = 100000
WORLD_HEIGHT  = 100000

TOOLS         = ["Gun","LightPulse","Bomb","ForceField"]
ROCKET_RAD    = 20

############################################################
# LEVEL BASE CLASSES
############################################################

class LevelBase:
    def __init__(self):
        self.WORLD_WIDTH  = 20000
        self.WORLD_HEIGHT = 20000
        self.star_layers = self._create_star_layers()
        self.asteroids    = []

    def _create_star_layers(self):
        layers = []
        for (n,px) in [(7000,0.1),(6000,0.2),(5500,0.6),(5000,0.9)]:
            stars = []
            for _ in range(n):
                sx  = random.uniform(0,self.WORLD_WIDTH)
                sy  = random.uniform(0,self.WORLD_HEIGHT)
                bri = random.randint(100,220)
                stars.append({'x':sx,'y':sy,'color':(bri,bri,bri)})
            layers.append({'stars': stars, 'parallax': px})
        return layers

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))
        for layer in self.star_layers:
            px= layer['parallax']
            for st in layer['stars']:
                draw_object_tiled(
                    screen, st['x'], st['y'], cam_x*px, cam_y*px,
                    st['color'], "star", 1
                )

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
        layers = []
        for (n,px) in [(7000,0.1),(6000,0.2),(5500,0.6),(5000,0.9)]:
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
        for _ in range(0):
            r = random.uniform(15,35)
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
            # add random 'spots'
            spots = []
            num_spots = random.randint(2,5)
            for _s in range(num_spots):
                spot_rad = r*random.uniform(0.1,0.3)
                off_angle = random.random()*2*math.pi
                off_dist = r*0.5*random.random()
                offx = off_dist*math.cos(off_angle)
                offy = off_dist*math.sin(off_angle)
                cvar = random.randint(50,100)
                c = (cvar,cvar,cvar)
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
                    st['color'], "star", 1
                )

############################################################
# LEVEL STAR
############################################################

class LevelStar(LevelBase):
    STAR_RADIUS_LETHAL=200
    GRAVITY_RANGE=50000
    G_M=5000
    def __init__(self):
        super().__init__()
        self.STAR_CX= self.WORLD_WIDTH/2
        self.STAR_CY= self.WORLD_HEIGHT/2
        self.star_list = self._create_far_stars()
        self.asteroids = self._create_asteroids()

    def _create_far_stars(self):
        s_list=[]
        for _ in range(800):
            sx= random.uniform(0,self.WORLD_WIDTH)
            sy= random.uniform(0,self.WORLD_HEIGHT)
            bri= random.randint(100,220)
            s_list.append({'x':sx,'y':sy,'color':(bri,bri,bri)})
        return s_list

    def _create_asteroids(self):
        asts=[]
        for _ in range(0):
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
            spots = []
            num_spots = random.randint(2,5)
            for _s in range(num_spots):
                spot_rad = r*random.uniform(0.1,0.3)
                off_angle = random.random()*2*math.pi
                off_dist = r*0.5*random.random()
                offx = off_dist*math.cos(off_angle)
                offy = off_dist*math.sin(off_angle)
                cvar = random.randint(50,100)
                c = (cvar,cvar,cvar)
                spots.append({'ox':offx,'oy':offy,'r':spot_rad,'c':c})
            asteroid['spots'] = spots
            asts.append(asteroid)
        return asts

    def force_func(self, x, y, vx, vy):
        dx= x- self.STAR_CX
        dy= y- self.STAR_CY
        r2= dx*dx+ dy*dy
        r = math.sqrt(r2)
        if r>= self.GRAVITY_RANGE or r< 1e-3:
            return (0.0,0.0)
        a_mag= self.G_M/r
        ax= -a_mag*(dx/r)
        ay= -a_mag*(dy/r)
        return (ax,ay)

    def lethal_check(self, x, y):
        dx= x- self.STAR_CX
        dy= y- self.STAR_CY
        return (dx*dx+ dy*dy) < (self.STAR_RADIUS_LETHAL*self.STAR_RADIUS_LETHAL)

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))
        sx= self.STAR_CX- cam_x
        sy= self.STAR_CY- cam_y
        max_r=2000
        step=10
        for rr in range(int(max_r), self.STAR_RADIUS_LETHAL, -step):
            frac= (rr- self.STAR_RADIUS_LETHAL)/(max_r- self.STAR_RADIUS_LETHAL)
            frac= max(0,min(1,frac))
            rred= int(255*(1-frac))
            ggrn= int(255*((1-frac)**2))
            bblu= int(255*((1-frac)**2))
            pygame.draw.circle(screen,(rred,ggrn,bblu),(int(sx),int(sy)), rr)
        pygame.draw.circle(screen,(255,255,255),(int(sx),int(sy)), self.STAR_RADIUS_LETHAL)
        for layer in self.star_layers:
            px= layer['parallax']
            for st in layer['stars']:
                draw_object_tiled(
                    screen, st['x'], st['y'], cam_x*px, cam_y*px,
                    st['color'], "star", 1
                )

############################################################
# LEVEL BLACK HOLE
############################################################

class LevelBlackHole(LevelBase):
    STAR_RADIUS_LETHAL=200
    GRAVITY_RANGE=800
    G_M=150000
    def __init__(self):
        super().__init__()
        self.HOLE_CX= self.WORLD_WIDTH/2
        self.HOLE_CY= self.WORLD_HEIGHT/2
        self.star_list= self._create_far_stars()
        self.asteroids= self._create_asteroids()

    def _create_far_stars(self):
        s_list=[]
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
            spots = []
            num_spots = random.randint(2,5)
            for _s in range(num_spots):
                spot_rad = r*random.uniform(0.1,0.3)
                off_angle = random.random()*2*math.pi
                off_dist = r*0.5*random.random()
                offx = off_dist*math.cos(off_angle)
                offy = off_dist*math.sin(off_angle)
                cvar = random.randint(50,100)
                c = (cvar,cvar,cvar)
                spots.append({'ox':offx,'oy':offy,'r':spot_rad,'c':c})
            asteroid['spots'] = spots
            asts.append(asteroid)
        return asts

    def force_func(self, x, y, vx, vy):
        dx= x- self.HOLE_CX
        dy= y- self.HOLE_CY
        r2= dx*dx+ dy*dy
        r = math.sqrt(r2)
        if r>= self.GRAVITY_RANGE or r<1e-3:
            return (0.0,0.0)
        a_mag= self.G_M/r2
        ax= -a_mag*(dx/r)
        ay= -a_mag*(dy/r)
        return (ax,ay)

    def lethal_check(self, x, y):
        dx= x- self.HOLE_CX
        dy= y- self.HOLE_CY
        return (dx*dx+ dy*dy) < (self.STAR_RADIUS_LETHAL*self.STAR_RADIUS_LETHAL)

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))
        sx= self.HOLE_CX- cam_x
        sy= self.HOLE_CY- cam_y
        pygame.draw.circle(screen,(0,0,0),(int(sx),int(sy)), self.STAR_RADIUS_LETHAL)
        for st in self.star_list:
            draw_object_tiled(
                screen, st['x'], st['y'], cam_x*0.0, cam_y*0.0,
                st['color'], "star", 1
            )

############################################################
# UTILITY
############################################################


def wrap_pos(x, y, w=WORLD_WIDTH, h=WORLD_HEIGHT):
    x%= w
    y%= h
    return x, y

############################################################
# SINGLE COLLISION HANDLER
############################################################

def elastic_bounce(m1, m2, x1,y1, vx1,vy1, x2,y2, vx2,vy2, e=1.0):
    dx= x2-x1
    dy= y2-y1
    dist= math.sqrt(dx*dx+ dy*dy)+1e-12
    nx= dx/dist
    ny= dy/dist
    vx_rel= vx2- vx1
    vy_rel= vy2- vy1
    vn= vx_rel*nx + vy_rel*ny
    if vn>0:
        return vx1, vy1, vx2, vy2
    imp= -(1+ e)* vn / (1/m1 + 1/m2)
    impx= imp* nx
    impy= imp* ny
    return (
        vx1 - impx/m1,
        vy1 - impy/m1,
        vx2 + impx/m2,
        vy2 + impy/m2
    )

def handle_collision(objA, objB, rocket_data, game_state):
    # game_state is a dict with 'game_over' and possibly other flags
    dx= objB['x']- objA['x']
    dy= objB['y']- objA['y']
    r_sum= objA['radius']+ objB['radius']
    dist2= dx*dx+ dy*dy
    if dist2<= r_sum*r_sum:
        # they overlap => do bounce if possible
        # but if rocket is involved and not shielded => game_over
        # let's define mass for rocket if shield is ON
        # if rocket is OFF => game_over
        # if bullet & bullet => bounce, bullet & asteroid => bounce, etc.
        # unify approach

        # find masses
        mA= objA.get('mass',1.0)
        mB= objB.get('mass',1.0)

        # is rocket?
        typeA= objA.get('type', '')
        typeB= objB.get('type', '')
        rocketA= (typeA=='rocket')
        rocketB= (typeB=='rocket')
        shield_onA= objA.get('shield_on',False)
        shield_onB= objB.get('shield_on',False)

        # if rocket not shield => game over
        if rocketA and (not shield_onA):
            game_state['game_over']= True
            return
        if rocketB and (not shield_onB):
            game_state['game_over']= True
            return

        # else do bounce => unify
        (vx1,vy1, vx2,vy2)= elastic_bounce(
            mA, mB,
            objA['x'], objA['y'], objA['vx'], objA['vy'],
            objB['x'], objB['y'], objB['vx'], objB['vy'],
            e=1.0
        )
        objA['vx'], objA['vy']= vx1, vy1
        objB['vx'], objB['vy']= vx2, vy2

############################################################
# DRAW
############################################################

def draw_rocket(screen, rocket, forward_thrust_on, reverse_thrust_on, turn_left, turn_right):
    rx= SCREEN_WIDTH/2
    ry= SCREEN_HEIGHT/2
    length= 50.0
    wfact = 0.2
    rad= math.radians(rocket['heading'])

    nose_x= rx + length*math.cos(rad)
    nose_y= ry + length*math.sin(rad)
    left_x= rx + (-wfact*length)*math.cos(rad  + math.radians(90))
    left_y= ry + (-wfact*length)*math.sin(rad + math.radians(90))
    right_x= rx + (-wfact*length)*math.cos(rad - math.radians(90))
    right_y= ry + (-wfact*length)*math.sin(rad - math.radians(90))

    color_front=(113,121,126)
    color_back =(159,163,167)
    pygame.draw.polygon(screen, color_front, [(nose_x,nose_y),(left_x,left_y),(right_x,right_y)])
    back_x= rx - length*math.cos(rad)
    back_y= ry - length*math.sin(rad)
    pygame.draw.polygon(screen, color_back, [(back_x,back_y),(left_x,left_y),(right_x,right_y)])

    if forward_thrust_on and not rocket['forcefield_on']:
        flame_len=25
        flame_rad= rad+ math.pi
        fx= back_x+ random.uniform(0.8,1.2)* flame_len* math.cos(flame_rad)
        fy= back_y+ random.uniform(0.8,1.2)* flame_len* math.sin(flame_rad)
        pygame.draw.line(screen,(255,165,0),(back_x,back_y),(fx,fy),3)

    if reverse_thrust_on and not rocket['forcefield_on']:
        flame_len=25
        flame_rad= rad
        fx= nose_x+ random.uniform(0.8,1.2)* flame_len* math.cos(flame_rad)
        fy= nose_y+ random.uniform(0.8,1.2)* flame_len* math.sin(flame_rad)
        pygame.draw.line(screen,(255,165,0),(nose_x,nose_y),(fx,fy),3)

    if turn_left:
        flame_len=10
        side_ang= rad + math.radians(90)
        fbx= back_x - flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        fby= back_y - flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(screen,(0,165,255),(back_x,back_y),(fbx,fby),2)
        ffx= nose_x+ flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        ffy= nose_y+ flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(screen,(0,165,255),(nose_x,nose_y),(ffx,ffy),2)

    if turn_right:
        flame_len=10
        side_ang= rad - math.radians(90)
        fbx= back_x - flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        fby= back_y - flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(screen,(0,165,255),(back_x,back_y),(fbx,fby),2)
        ffx= nose_x+ flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        ffy= nose_y+ flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(screen,(0,165,255),(nose_x,nose_y),(ffx,ffy),2)


    # Force field
    if rocket['forcefield_on']:
        shield_rad=80
        srf= pygame.Surface((shield_rad*2, shield_rad*2), pygame.SRCALPHA)
        srf.fill((0,0,0,0))
        pygame.draw.circle(srf,(0,255,0,50),(shield_rad,shield_rad),shield_rad)
        pygame.draw.circle(srf,(0,255,0,150),(shield_rad,shield_rad),shield_rad,2)
        screen.blit(srf,(rx-shield_rad, ry-shield_rad))


def draw_object_tiled(screen, wx, wy, cam_x, cam_y, color, obj_type="circle", radius=1):
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            sx= (wx+ dx*WORLD_WIDTH)- cam_x
            sy= (wy+ dy*WORLD_HEIGHT)- cam_y
            if 0<=sx< screen.get_width() and 0<=sy< screen.get_height():
                pygame.draw.circle(screen,color,(int(sx),int(sy)),radius)


def draw_object_tiled_asteroid(screen, ast, cam_x, cam_y):
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            sx= (ast['x']+dx*WORLD_WIDTH)- cam_x
            sy= (ast['y']+dy*WORLD_HEIGHT)- cam_y
            if 0<=sx<screen.get_width() and 0<=sy<screen.get_height():
                pygame.draw.circle(screen,ast['color'],(int(sx),int(sy)),int(ast['radius']))
                for spot in ast['spots']:
                    sxx= sx+ spot['ox']
                    syy= sy+ spot['oy']
                    pygame.draw.circle(screen,spot['c'],(int(sxx),int(syy)),int(spot['r']))


def draw_object_tiled_ring(screen,wx,wy,cam_x,cam_y,color,ring_radius):
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            sx= (wx+dx*WORLD_WIDTH)- cam_x
            sy= (wy+dy*WORLD_HEIGHT)- cam_y
            if 0<=sx<screen.get_width() and 0<=sy<screen.get_height():
                pygame.draw.circle(screen,color,(int(sx),int(sy)),ring_radius,2)

############################################################
# MAIN
############################################################
def main():
    pygame.init()
    screen= pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock= pygame.time.Clock()
    font= pygame.font.SysFont("Arial",18)

    level_name= run_level_menu(screen,font)
    if level_name=="star":
        lvl= LevelStar()
        rocket_x= lvl.WORLD_WIDTH/2
        rocket_y= lvl.WORLD_HEIGHT/2+2000
    elif level_name=="hole":
        lvl= LevelBlackHole()
        rocket_x= lvl.WORLD_WIDTH/2
        rocket_y= lvl.WORLD_HEIGHT/2+2000
    else:
        lvl= LevelFlat()
        rocket_x= lvl.WORLD_WIDTH/2
        rocket_y= lvl.WORLD_HEIGHT/2

    # We'll keep rocket in the same data structure as everything else
    rocket={
        'type':'rocket',
        'x':rocket_x,'y':rocket_y,
        'vx':0,'vy':0,
        'radius':ROCKET_RAD,
        'mass':10.0,  # rocket mass
        'heading':0,
        'angvel':0,
        'forcefield_on':False,  # or shield_on
        'shield_on':False,      # for collision logic
    }

    # Convert asteroids => type 'asteroid'
    for ast in lvl.asteroids:
        ast['type']='asteroid'

    # We'll keep bullets, bombs, pulses in lists
    bullets=[]
    bombs=[]
    lightpulses=[]

    # We'll define a game_state
    game_state={
        'game_over':False
    }

    def reset_game():
        nonlocal rocket, bullets, bombs, lightpulses, game_state
        game_state['game_over']=False
        if level_name=="star":
            newlvl= LevelStar()
            rocket['x']= newlvl.WORLD_WIDTH/2
            rocket['y']= newlvl.WORLD_HEIGHT/2+2000
            lvl.asteroids= newlvl.asteroids
        elif level_name=="hole":
            newlvl= LevelBlackHole()
            rocket['x']= newlvl.WORLD_WIDTH/2
            rocket['y']= newlvl.WORLD_HEIGHT/2+2000
            lvl.asteroids= newlvl.asteroids
        else:
            newlvl= LevelFlat()
            rocket['x']= newlvl.WORLD_WIDTH/2
            rocket['y']= newlvl.WORLD_HEIGHT/2
            lvl.asteroids= newlvl.asteroids
        rocket['vx']=0; rocket['vy']=0; rocket['heading']=0; rocket['angvel']=0
        rocket['forcefield_on']=False
        rocket['shield_on']=False
        bullets.clear()
        bombs.clear()
        lightpulses.clear()

    running=True
    while running:
        dt_real= clock.tick(FPS)/1000.0
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    running=False
                elif event.key==pygame.K_q and not game_state['game_over']:
                    pass # cycle tools if desired
                    # we do indexing but let's do that
                    # (the user can cycle if they want)
                    # we'll do it:
                    pass
                elif event.key==pygame.K_e and not game_state['game_over']:
                    pass
                elif event.key==pygame.K_SPACE:
                    if game_state['game_over']:
                        reset_game()
                    else:
                        # use tool
                        # we can do same logic as before
                        tool_index=0 # hack, or store it somewhere
                        # let's do direct:
                        pass
                elif event.key==pygame.K_r:
                    if game_state['game_over']:
                        reset_game()
                    else:
                        reset_game()
        # handle keys
        keys= pygame.key.get_pressed()
        turn_left=False
        turn_right=False
        forward_thrust=False
        reverse_thrust=False
        torque=20.0
        thrust = 20.0

        if keys[pygame.K_a]:
            rocket['angvel']-= torque*dt_real
            turn_left=True
        if keys[pygame.K_d]:
            rocket['angvel']+= torque*dt_real
            turn_right=True
        if keys[pygame.K_w] and not rocket['forcefield_on']:
            # forward thrust
            h_rad= math.radians(rocket['heading'])
            rocket['vx']+= thrust* math.cos(h_rad)* dt_real
            rocket['vy']+= thrust* math.sin(h_rad)* dt_real
            forward_thrust=True
        # user wants s => backward thrust
        if keys[pygame.K_s] and not rocket['forcefield_on']:
            h_rad= math.radians(rocket['heading'])
            rocket['vx']-= thrust* math.cos(h_rad)* dt_real
            rocket['vy']-= thrust* math.sin(h_rad)* dt_real
            reverse_thrust=True

        rocket['shield_on']= rocket['forcefield_on'] # unify naming

        # update rocket rotation & position
        rocket['vx']+= lvl.force_func(rocket['x'],rocket['y'],rocket['vx'],rocket['vy'])[0]*BASE_DT
        rocket['vy']+= lvl.force_func(rocket['x'],rocket['y'],rocket['vx'],rocket['vy'])[1]*BASE_DT
        rocket['heading']+= rocket['angvel']*BASE_DT
        rocket['x']+= rocket['vx']*BASE_DT
        rocket['y']+= rocket['vy']*BASE_DT
        rocket['x'], rocket['y']= wrap_pos(rocket['x'], rocket['y'])

        # lethal check rocket
        if lvl.lethal_check(rocket['x'], rocket['y']):
            game_state['game_over']=True

        # we don't do bullet update here, but let's do so
        # eventually you'd handle bullets, bombs, pulses
        # or replicate logic from prior code
        # skip for brevity

        # collisions => unify across rocket, bullets, asteroids, bombs
        # let's build a single list of objects for collisions
        # rocket, asteroids, bullets, bombs

        all_objects=[]
        # rocket
        all_objects.append(rocket)
        # asteroids
        for a in lvl.asteroids:
            all_objects.append(a)
        # bullets
        # bombs
        # skip pulses since they're area-based?
        # or we can do if we want them to bounce?? Probably not

        # next, pairwise collisions
        for i in range(len(all_objects)):
            for j in range(i+1,len(all_objects)):
                handle_collision(all_objects[i],all_objects[j],rocket, game_state)
                if game_state['game_over']:
                    break
            if game_state['game_over']:
                break

        # draw
        screen.fill((0,0,0))
        cam_x= rocket['x']- SCREEN_WIDTH/2
        cam_y= rocket['y']- SCREEN_HEIGHT/2
        lvl.draw_background(screen, rocket, cam_x, cam_y)
        # rocket
        draw_rocket(screen, rocket, forward_thrust, reverse_thrust, turn_left, turn_right)

        # handle game_over?
        if game_state['game_over']:
            msg= "GAME OVER! Press SPACE to restart"
            t_s= font.render(msg, True, (255,0,0))
            screen.blit(t_s,(SCREEN_WIDTH/2-100, SCREEN_HEIGHT/2))
        pygame.display.flip()

    pygame.quit()

def run_level_menu(screen, font):
    menu_options= ["Flat","Star","Hole"]
    idx=0
    clock= pygame.time.Clock()
    while True:
        dt= clock.tick(60)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    idx= (idx-1)% len(menu_options)
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    idx= (idx+1)% len(menu_options)
                elif event.key==pygame.K_RETURN:
                    return menu_options[idx].lower()
        screen.fill((20,20,30))
        title= "SPACE-FORCE: SELECT LEVEL"
        t_surf= font.render(title,True,(255,255,255))
        screen.blit(t_surf,(SCREEN_WIDTH//2-100,100))
        for i,opt in enumerate(menu_options):
            color= (200,200,100) if i==idx else (200,200,200)
            txt= font.render(opt,True,color)
            screen.blit(txt,(SCREEN_WIDTH//2-50+ i*150, 300))
        instruct= "Use Left/Right, Enter=confirm, Esc=quit"
        i_s= font.render(instruct,True,(200,200,200))
        screen.blit(i_s,(SCREEN_WIDTH//2-200,SCREEN_HEIGHT-100))
        pygame.display.flip()

if __name__=="__main__":
    main()
