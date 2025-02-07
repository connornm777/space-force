import pygame
import math
import random
import numpy as np

# -------------------------------------
# Read-Only Constants
# -------------------------------------
WIDTH  = 1800
HEIGHT = 1000
FPS    = 60

BASE_DT     = 0.01        # base coordinate step
C_LIGHT     = 300.0        # "speed of light" for bullets
C_MAX       = 300.0        # rocket max speed
BH_RS_INIT  = 100.0        # initial Schwarzschild radius
CX, CY      = WIDTH/2, HEIGHT/2   # black hole center

# -------------------------------------
# Metric & Time-Dilation
# -------------------------------------
def r_coord(x, y):
    return math.sqrt((x - CX)**2 + (y - CY)**2)

def g_tt(bh_radius, x, y):
    r = r_coord(x,y)
    if r <= bh_radius+1:
        # inside horizon
        return -1e-9
    return -(1.0 - bh_radius / r)

def time_dilation_factor(bh_radius, x, y):
    val = g_tt(bh_radius, x, y)
    if val >= 0:
        return 1.0
    fac = -val
    if fac < 1e-12:
        fac = 1e-12
    return math.sqrt(fac)

def metric_spatial(bh_radius, x, y):
    if True:
        r = r_coord(x,y)
        if r <= bh_radius:
            val = 999999.0
            return np.array([[val,0],[0,val]], dtype=float)
        factor = bh_radius / ((r**2) * (bh_radius - r + 1e-9))
        dx, dy = (x - CX), (y - CY)
        return np.array([
            [1 - factor*(dx**2),    -factor*dx*dy],
            [-factor*dx*dy,          1 - factor*(dy**2)]
        ], dtype=float)


    elif False:
        r = r_coord(x,y)
        dx, dy = (x - CX), (y - CY)
        R = max(WIDTH, HEIGHT)/2
        if r <= bh_radius:
            val = 999999.0
            return np.array([[val,0],[0,val]], dtype=float)
        factor = bh_radius / ((r**2) * (bh_radius - r + 1e-9))
        f2 = (1e-12+(dx-100)**2+(dy-5)**2-R**2)
        dx, dy = (x - CX), (y - CY)
        return np.array([
            [(1.0/f2 - factor*(dx**2)),    -factor*dx*dy],
            [-factor*dx*dy,          (1.0/f2 - factor*(dy**2))]
        ], dtype=float)



    elif True:
        r = r_coord(x,y)
        dx, dy = (x - CX), (y - CY)
        R = 1000.0
        if r <= bh_radius:
            val = 999999.0
            return np.array([[val,0],[0,val]], dtype=float)
        factor = bh_radius / ((r**2) * (bh_radius - r + 1e-9))
        f2 = (1e-12+R**2)
        dx, dy = (x - CX), (y - CY)
        return np.array([
            [(1.0 - factor*(dx**2)) + dx**2/f2,    -factor*dx*dy - dx*dy/f2],
            [-factor*dx*dy - dx*dy/f2,          (1.0/f2 - factor*(dy**2)) + dy**2/f2]
        ], dtype=float)

    elif False:
        r = r_coord(x,y)
        dx, dy = (x - CX), (y - CY)
        return np.array([
            [1.0/(y**2+1e-9),    0],
            [0,    1.0/(y**2+1e-9)]
        ], dtype=float)


    elif False:
        r = r_coord(x,y)
        dx, dy = (x - CX), (y - CY)
        ep, K = 0.01, 10
        return np.array([
            [1.0+ep*math.cos(math.pi*x*K/WIDTH)*math.cos(math.pi*y*K/HEIGHT),    0],
            [0,    1.0+ep**math.cos(math.pi*x*K/WIDTH)*math.cos(math.pi*y*K/HEIGHT)]
        ], dtype=float)

    elif True:
        r = r_coord(x,y)
        dx, dy = (x - CX), (y - CY)
        return np.array([
            [1.0/(dx**2+dy**2+1e-9)**0.5,    0],
            [0,    1.0/(dx**2+dy**2+1e-9)**0.5]
        ], dtype=float)


EPS = 1e-4
def partial_derivative_g_spatial(bh_radius, x, y):
    g0   = metric_spatial(bh_radius, x, y)
    gp_x = metric_spatial(bh_radius, x+EPS, y)
    gm_x = metric_spatial(bh_radius, x-EPS, y)
    gp_y = metric_spatial(bh_radius, x, y+EPS)
    gm_y = metric_spatial(bh_radius, x, y-EPS)

    dg_dx = (gp_x - gm_x)/(2*EPS)
    dg_dy = (gp_y - gm_y)/(2*EPS)
    return dg_dx, dg_dy

def christoffel_2d(bh_radius, x, y):
    g_ij = metric_spatial(bh_radius, x, y)
    inv_g= np.linalg.inv(g_ij)
    dg_dx, dg_dy = partial_derivative_g_spatial(bh_radius, x, y)

    def partial_g(alpha, i, j):
        if alpha == 0:
            return dg_dx[i,j]
        else:
            return dg_dy[i,j]

    Gamma = np.zeros((2,2,2), dtype=float)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                val=0.0
                for m in range(2):
                    val+= inv_g[i,m]*(
                      partial_g(j,m,k)+partial_g(k,m,j)-partial_g(m,j,k)
                    )
                Gamma[i,j,k]= 0.5*val
    return Gamma

def geodesic_accel(bh_radius, x,y,vx,vy):
    Gamma= christoffel_2d(bh_radius, x, y)
    ax= -(
     Gamma[0,0,0]*vx*vx + Gamma[0,0,1]*vx*vy
    +Gamma[0,1,0]*vy*vx + Gamma[0,1,1]*vy*vy
    )
    ay= -(
     Gamma[1,0,0]*vx*vx + Gamma[1,0,1]*vx*vy
    +Gamma[1,1,0]*vy*vx + Gamma[1,1,1]*vy*vy
    )
    return ax, ay

def update_geodesic(bh_radius, x,y,vx,vy):
    dt_local= BASE_DT/ time_dilation_factor(bh_radius, x, y)
    ax1, ay1= geodesic_accel(bh_radius, x,y,vx,vy)
    x_mid= x+ 0.5*dt_local*vx
    y_mid= y+ 0.5*dt_local*vy
    vx_mid= vx+ 0.5*dt_local*ax1
    vy_mid= vy+ 0.5*dt_local*ay1
    ax2, ay2= geodesic_accel(bh_radius,x_mid,y_mid,vx_mid,vy_mid)
    x_new= x+ dt_local*vx_mid
    y_new= y+ dt_local*vy_mid
    vx_new= vx+ dt_local*ax2
    vy_new= vy+ dt_local*ay2
    return x_new,y_new,vx_new,vy_new

# -------------------------------------
# Collisions
# -------------------------------------
def circles_collide(x1,y1,r1, x2,y2,r2):
    dx= x2- x1
    dy= y2- y1
    dist_sq= dx*dx + dy*dy
    rad_sum= (r1+r2)
    return dist_sq <= rad_sum*rad_sum

def elastic_bounce(m1,m2, x1,y1,vx1,vy1, x2,y2,vx2,vy2):
    dx= x2-x1
    dy= y2-y1
    dist= math.sqrt(dx*dx+ dy*dy)+1e-10
    nx= dx/dist
    ny= dy/dist
    vx_rel= vx2- vx1
    vy_rel= vy2- vy1
    vn= vx_rel*nx + vy_rel*ny
    if vn>0:
        # separating
        return vx1,vy1,vx2,vy2
    e=1.0
    imp= -(1+ e)* vn / (1/m1 + 1/m2)
    impx= imp* nx
    impy= imp* ny
    vx1_n= vx1 - impx/m1
    vy1_n= vy1 - impy/m1
    vx2_n= vx2 + impx/m2
    vy2_n= vy2 + impy/m2
    return vx1_n, vy1_n, vx2_n, vy2_n

# -------------------------------------
# Rocket
# -------------------------------------
def limit_speed(vx,vy, cmax=C_MAX):
    spd= math.hypot(vx,vy)
    if spd> cmax:
        sc= cmax/spd
        vx*= sc
        vy*= sc
    return vx,vy

def update_rocket(bh_radius, rocket):
    """
    rocket= [x,y, vx,vy, heading_deg, angvel_deg]
    partial geodesic + user rotation + periodic boundary
    """
    x,y,vx,vy,hd,angv= rocket
    dt_local= BASE_DT/ time_dilation_factor(bh_radius, x,y)

    # geodesic
    axG, ayG= geodesic_accel(bh_radius, x,y,vx,vy)
    vx_n= vx+ axG*dt_local
    vy_n= vy+ ayG*dt_local
    x_n= x + vx_n* dt_local
    y_n= y + vy_n* dt_local

    # heading
    hd_n= hd + angv* dt_local

    # periodic boundary
    if x_n<0:     x_n+= WIDTH
    if x_n>WIDTH: x_n-= WIDTH
    if y_n<0:     y_n+= HEIGHT
    if y_n>HEIGHT:y_n-= HEIGHT

    vx_n, vy_n= limit_speed(vx_n, vy_n, C_MAX)
    return [x_n,y_n,vx_n,vy_n, hd_n, angv]

def draw_rocket(surf, rocket, thrust_on, turn_left, turn_right):
    x,y,vx,vy,hd,angv= rocket

    # length
    length= 18.0
    rad= math.radians(hd)

    # front tip
    nose_x= x + length*math.cos(rad)
    nose_y= y + length*math.sin(rad)
    # mid-back
    back_x= x - 0.6*length*math.cos(rad)
    back_y= y - 0.6*length*math.sin(rad)
    # left corner
    left_x= x + (-0.3*length)*math.cos(rad+ math.radians(130))
    left_y= y + (-0.3*length)*math.sin(rad+ math.radians(130))
    # right corner
    right_x= x + (-0.3*length)*math.cos(rad- math.radians(130))
    right_y= y + (-0.3*length)*math.sin(rad- math.radians(130))

    # We can split the rocket into two polygons: front tri & back tri
    # front tri: (nose) -> left corner -> right corner
    # back tri: left corner-> (back) -> right corner
    color_front= (255,0,0)
    color_back = (180,0,0)

    front_tri = [(nose_x,nose_y),(left_x,left_y),(right_x,right_y)]
    pygame.draw.polygon(surf, color_front, front_tri)

    back_tri  = [(left_x,left_y),(back_x,back_y),(right_x,right_y)]
    pygame.draw.polygon(surf, color_back, back_tri)

    # main thruster flame
    if thrust_on:
        flame_len= 25.0
        flame_rad= rad+ math.pi
        fx= back_x + random.uniform(0.8,1.2)* flame_len* math.cos(flame_rad)
        fy= back_y + random.uniform(0.8,1.2)* flame_len* math.sin(flame_rad)
        color_flame= (255,165,0)
        pygame.draw.line(surf, color_flame, (back_x, back_y),(fx, fy),3)

    # side thrusters
    if turn_left:
        flame_len=15
        side_ang= rad- math.radians(90)
        sx= right_x; sy= right_y
        fx= sx+ flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        fy= sy+ flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(surf, (0,255,0), (sx,sy),(fx,fy),2)
    if turn_right:
        flame_len=15
        side_ang= rad+ math.radians(90)
        sx= left_x; sy= left_y
        fx= sx+ flame_len* math.cos(side_ang)* random.uniform(0.8,1.2)
        fy= sy+ flame_len* math.sin(side_ang)* random.uniform(0.8,1.2)
        pygame.draw.line(surf, (0,255,0), (sx,sy),(fx,fy),2)

# -------------------------------------
# Bullets
# -------------------------------------
def create_bullet(bullets, x, y, heading_deg):
    heading_rad= math.radians(heading_deg)
    vx= C_LIGHT* math.cos(heading_rad)
    vy= C_LIGHT* math.sin(heading_rad)
    color=(255,255,100)  # bright yellow
    radius=1.0
    mass=0.0
    bullets.append([x,y,vx,vy, radius,mass,color])

def update_bullet(bh_radius, bullet):
    x,y,vx,vy, rb, mb, col = bullet
    x_n,y_n,vx_n,vy_n= update_geodesic(bh_radius, x,y,vx,vy)
    return [x_n,y_n,vx_n,vy_n, rb, mb, col]

# -------------------------------------
# Asteroids
# -------------------------------------
def spawn_asteroid(asteroids):
    edge= random.choice(['top','bottom','left','right', 'none'])
    return None
    if edge=='none':
        return None
    elif edge=='top':
        x= random.uniform(0,WIDTH)
        y= 0
        vx= random.uniform(-15,15)
        vy= random.uniform(1,10)
    elif edge=='bottom':
        x= random.uniform(0,WIDTH)
        y= HEIGHT
        vx= random.uniform(-15,15)
        vy= random.uniform(-10,-1)
    elif edge=='left':
        x=0
        y= random.uniform(0,HEIGHT)
        vx= random.uniform(1,10)
        vy= random.uniform(-15,15)
    else:
        x=WIDTH
        y= random.uniform(0,HEIGHT)
        vx= random.uniform(-10,-1)
        vy= random.uniform(-15,15)


    ast_type = random.choice(['blue', 'white', 'black'])
    if ast_type == "blue":
        color = (100, 100, 200)
        radius = random.uniform(5, 10)
        mass = radius
    elif ast_type == "white":
        color = (200, 200, 200)
        radius = random.uniform(20, 30)
        mass = 0.1*radius
    elif ast_type == "black":
        color = (1, 1, 1)
        radius = random.uniform(4, 5)
        mass = 100

    asteroids.append([x,y,vx,vy, radius, mass, color])

def update_asteroid(bh_radius, asteroid):
    x,y,vx,vy, rad,mass,col= asteroid
    x_n,y_n,vx_n,vy_n= update_geodesic(bh_radius,x,y,vx,vy)
    return [x_n,y_n,vx_n,vy_n, rad,mass,col]

# -------------------------------------
# Collisions
# -------------------------------------
def handle_collisions(rocket, asteroids, bullets, bh_radius):
    """
    bullet <-> asteroid => bounce
    asteroid <-> asteroid => bounce
    rocket <-> asteroid => game restart
    bullet => vanish if out of domain
    """
    crashed= False

    # bullet <-> asteroid
    for i in range(len(bullets)):
        bx,by,bvx,bvy,br,bm,bcol= bullets[i]
        for j in range(len(asteroids)):
            ax,ay,avx,avy,ar,am,acol= asteroids[j]
            if circles_collide(bx,by,br, ax,ay,ar):
                # bounce
                bvx_n,bvy_n,avx_n,avy_n= elastic_bounce(
                  bm, am, bx,by,bvx,bvy, ax,ay,avx,avy
                )
                bullets[i][2]= bvx_n
                bullets[i][3]= bvy_n
                asteroids[j][2]= avx_n
                asteroids[j][3]= avy_n

    # asteroid <-> asteroid
    for i in range(len(asteroids)):
        x1,y1,vx1,vy1,r1,m1,c1= asteroids[i]
        for j in range(i+1, len(asteroids)):
            x2,y2,vx2,vy2,r2,m2,c2= asteroids[j]
            if circles_collide(x1,y1,r1, x2,y2,r2):
                vx1_n,vy1_n, vx2_n,vy2_n= elastic_bounce(
                  m1,m2, x1,y1,vx1,vy1, x2,y2,vx2,vy2
                )
                asteroids[i][2]= vx1_n
                asteroids[i][3]= vy1_n
                asteroids[j][2]= vx2_n
                asteroids[j][3]= vy2_n

    # rocket <-> asteroid => crash => reset
    rx,ry,rvx,rvy,rhd,rangv= rocket
    rocket_rad= 10
    for (ax,ay,avx,avy,ar,am,acol) in asteroids:
        if circles_collide(rx,ry,rocket_rad, ax,ay,ar):
            crashed= True
            break

    return crashed, bh_radius

# -------------------------------------
# Main
# -------------------------------------
def main():
    pygame.init()
    screen= pygame.display.set_mode((WIDTH, HEIGHT))
    clock= pygame.time.Clock()
    font= pygame.font.SysFont("Arial", 18)

    running= True
    spawn_timer= 0.0

    # local state
    bh_radius= BH_RS_INIT
    asteroids= []
    bullets= []

    def reset_game():
        nonlocal bh_radius, asteroids, bullets
        bh_radius= BH_RS_INIT
        asteroids.clear()
        bullets.clear()
        # rocket in approx stable orbit
        r_start= random.randint(int(WIDTH/4), int(WIDTH/2))
        rocket_x= CX+ r_start
        rocket_y= CY
        # approximate orbital speed
        orb_speed= math.sqrt(bh_radius/(r_start+1e-9))* 30
        rocket_vx= 0
        rocket_vy= -orb_speed
        rocket_hd= 90
        rocket_angv= 0
        return [rocket_x, rocket_y, rocket_vx, rocket_vy, rocket_hd, rocket_angv]

    rocket= reset_game()

    while running:
        dt_real= clock.tick(FPS)/1000.0

        # input
        turn_left= False
        turn_right=False
        thrust_on= False

        for event in pygame.event.get():
            if event.type== pygame.QUIT:
                running=False
            elif event.type== pygame.KEYDOWN:
                if event.key== pygame.K_ESCAPE:
                    running=False
                elif event.key== pygame.K_r:
                    rocket= reset_game()
            elif event.type== pygame.MOUSEBUTTONDOWN:
                # no wave
                pass

        # keys
        keys= pygame.key.get_pressed()
        torque_strength= 50.0
        if keys[pygame.K_a]:
            rocket[5]-= torque_strength* dt_real
            turn_left= True
        if keys[pygame.K_d]:
            rocket[5]+= torque_strength* dt_real
            turn_right = True
        if keys[pygame.K_s]:
            rocket[5]+= -0.05*torque_strength* dt_real * rocket[5]
            turn_right = True
            turn_left = True
        if keys[pygame.K_w]:
            thrust_on= True
            heading_rad= math.radians(rocket[4])
            thrust= 20.0
            rocket[2]+= thrust* math.cos(heading_rad)* dt_real
            rocket[3]+= thrust* math.sin(heading_rad)* dt_real
            rocket[2],rocket[3]= limit_speed(rocket[2], rocket[3])
        if keys[pygame.K_e]:
            N = 100
            for i in range(N):
                create_bullet(bullets, rocket[0], rocket[1], 360*i/N)
        if keys[pygame.K_q]:
            pass
        if keys[pygame.K_SPACE]:
            # shoot bullet
            heading_rad= math.radians(rocket[4])
            rocket[2]+= -10.0* math.cos(heading_rad)* dt_real
            rocket[3]+= -10.0* math.sin(heading_rad)* dt_real
            nose_x= rocket[0]+ 15*math.cos(heading_rad)
            nose_y= rocket[1]+ 15*math.sin(heading_rad)
            create_bullet(bullets, nose_x, nose_y, rocket[4])

        # update rocket
        rocket= update_rocket(bh_radius, rocket)

        # spawn asteroids
        spawn_timer+= dt_real
        if spawn_timer> 1.0:
            spawn_timer=0.0
            spawn_asteroid(asteroids)

        # update asteroids
        new_ast=[]
        for ast in asteroids:
            x,y,vx,vy,rad,mass,col= update_asteroid(bh_radius, ast)
            r_dist= r_coord(x,y)
            if r_dist< bh_radius:
                # black hole grows
                bh_radius+= mass*0.05
            elif 0<=x<=WIDTH and 0<=y<=HEIGHT:
                new_ast.append([x,y,vx,vy,rad,mass,col])
        asteroids[:]= new_ast

        # update bullets
        new_bul=[]
        for b in bullets:
            x,y,vx,vy,rb,mb,col= update_bullet(bh_radius, b)
            r_dist= r_coord(x,y)
            if r_dist< bh_radius:
                # swallowed
                bh_radius+= mb*0.05
            elif (0<=x<=WIDTH and 0<=y<=HEIGHT):
                new_bul.append([x,y,vx,vy,rb,mb,col])
            # else bullet outside domain => vanish
        bullets[:]= new_bul

        # collisions
        crashed, bh_radius= handle_collisions(rocket, asteroids, bullets, bh_radius)
        if crashed:
            rocket= reset_game()
            continue

        # draw
        screen.fill((40,40,40))

        # black hole
        pygame.draw.circle(screen, (0,0,0), (int(CX), int(CY)), int(bh_radius))

        # rocket
        draw_rocket(screen, rocket, thrust_on, turn_left, turn_right)

        # asteroids
        for (x,y,vx,vy,rad,mass,col) in asteroids:
            pygame.draw.circle(screen, col, (int(x), int(y)), int(rad))

        # bullets
        for (x,y,vx,vy,rb,mb,col) in bullets:
            pygame.draw.circle(screen, col, (int(x), int(y)), rb)

        info= f"[R] reset; BH= {bh_radius:.1f}, #ast= {len(asteroids)}, #bul= {len(bullets)}"
        txt= font.render(info, True, (220,220,220))
        screen.blit(txt, (10,10))

        pygame.display.flip()

    pygame.quit()

if __name__=="__main__":
    main()
