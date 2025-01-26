"""
levels.py

Defines classes for different levels:
 - LevelBase   (abstract parent)
 - LevelFlat   (flat space, no gravity)
 - LevelStar   (star in center with lethal radius + gravity)
All in one file, so 'main.py' can do:

  from levels import LevelFlat, LevelStar

"""

import random, math

WORLD_WIDTH  = 5000
WORLD_HEIGHT = 5000

# ------------------------------------------------------------------
# Base Class
# ------------------------------------------------------------------
class LevelBase:
    """
    Base class for a level. Child classes:
      - define self.asteroids
      - define star or background data
      - override force_func(x, y, vx, vy)->(ax, ay) if needed
      - override lethal_check(x, y)-> bool
      - override draw_background(...) to do custom backgrounds
    """
    def __init__(self):
        self.WORLD_WIDTH  = WORLD_WIDTH
        self.WORLD_HEIGHT = WORLD_HEIGHT
        self.asteroids    = []  # store the random asteroids or objects

    def force_func(self, x, y, vx, vy):
        """
        Return (ax, ay) acceleration from geometry or gravity.
        Default => no force
        """
        return (0.0, 0.0)

    def lethal_check(self, x, y):
        """
        Return True if (x, y) is in lethal zone (like a star interior).
        Default => False
        """
        return False

    def draw_background(self, screen, rocket, cam_x, cam_y):
        """
        Called by main to draw the background (stars, color gradients, etc.).
        By default, fill black.
        """
        import pygame
        screen.fill((0,0,0))

# ------------------------------------------------------------------
# Flat Level
# ------------------------------------------------------------------
class LevelFlat(LevelBase):
    """
    Flat space: no gravity. 
    We'll do multiple parallax star layers for the background.
    We'll store them in self.star_layers, each with (stars[], parallax).
    Also random asteroids in self.asteroids.
    """
    def __init__(self):
        super().__init__()
        self.star_layers = self._create_star_layers()
        self.asteroids   = self._create_asteroids()

    def force_func(self, x, y, vx, vy):
        return (0.0, 0.0)  # no gravity

    def lethal_check(self, x, y):
        return False

    def draw_background(self, screen, rocket, cam_x, cam_y):
        import pygame
        screen.fill((0,0,0))
        # parallax
        for layer in self.star_layers:
            parallax = layer['parallax']
            for st in layer['stars']:
                sx_scr = st['x'] - (cam_x * parallax)
                sy_scr = st['y'] - (cam_y * parallax)
                if 0 <= sx_scr < screen.get_width() and 0<= sy_scr < screen.get_height():
                    pygame.draw.circle(screen, st['color'], (int(sx_scr), int(sy_scr)), 1)

    def _create_star_layers(self):
        layers = []
        # e.g. (num_stars, parallax)
        params = [(150,0.2), (100,0.5), (50,1.0)]  
        for (n, px) in params:
            star_list=[]
            for _ in range(n):
                sx= random.uniform(0, self.WORLD_WIDTH)
                sy= random.uniform(0, self.WORLD_HEIGHT)
                brightness= random.randint(100,200)
                color= (brightness, brightness, brightness)
                star_list.append({'x':sx,'y':sy,'color':color})
            layers.append({'stars': star_list, 'parallax': px})
        return layers

    def _create_asteroids(self):
        asts=[]
        for _ in range(20):
            ax= random.uniform(0, self.WORLD_WIDTH)
            ay= random.uniform(0, self.WORLD_HEIGHT)
            vx= random.uniform(-50,50)
            vy= random.uniform(-50,50)
            radius= random.uniform(15,35)
            mass  = radius
            grey  = random.randint(100,200)
            color = (grey,grey,grey)
            asts.append({
              'x':ax,'y':ay,
              'vx':vx,'vy':vy,
              'radius':radius,'mass':mass,
              'color': color
            })
        return asts

# ------------------------------------------------------------------
# Star Level
# ------------------------------------------------------------------
class LevelStar(LevelBase):
    """
    A star in the center with lethal radius=200, gravity range=800.
    We'll do a radial gradient from white->red->black in draw_background.
    """
    STAR_RADIUS_LETHAL = 100
    GRAVITY_RANGE      = 800
    G_M                = 50000
    STAR_CX            = WORLD_WIDTH/4
    STAR_CY            = WORLD_HEIGHT/4

    def __init__(self):
        super().__init__()
        # minimal random starfield
        self.star_list = self._create_star_list()
        self.asteroids = self._create_asteroids()

    def force_func(self, x, y, vx, vy):
        dx= x- self.STAR_CX
        dy= y- self.STAR_CY
        r2= dx*dx + dy*dy
        r = math.sqrt(r2)
        if r>= self.GRAVITY_RANGE:
            return (0.0,0.0)
        if r<1e-3:
            return (0.0,0.0)
        a_mag= self.G_M / r2
        ax= -a_mag* (dx/r)
        ay= -a_mag* (dy/r)
        return (ax, ay)

    def lethal_check(self, x, y):
        dx= x- self.STAR_CX
        dy= y- self.STAR_CY
        r2= dx*dx + dy*dy
        return (r2< self.STAR_RADIUS_LETHAL*self.STAR_RADIUS_LETHAL)

    def draw_background(self, screen, rocket, cam_x, cam_y):
        import pygame
        # fill black first
        screen.fill((0,0,0))
        # draw radial gradient for star
        sx= self.STAR_CX- cam_x
        sy= self.STAR_CY- cam_y
        step=10
        max_r=600
        for r in range(int(max_r), self.STAR_RADIUS_LETHAL, -step):
            frac= (r- self.STAR_RADIUS_LETHAL)/(max_r- self.STAR_RADIUS_LETHAL)
            if frac<0: frac=0
            if frac>1: frac=1
            # color => white*(1-frac)+ red*(frac)
            rr=255
            gg=int(255*(1-frac))
            bb=int(255*(1-frac))
            c=(rr,gg,bb)
            pygame.draw.circle(screen, c, (int(sx),int(sy)), r,0)
        # lethal interior => white
        pygame.draw.circle(screen, (255,255,255), (int(sx),int(sy)), self.STAR_RADIUS_LETHAL,0)

        # draw minimal star_list
        for st in self.star_list:
            sxx= st['x']- cam_x
            syy= st['y']- cam_y
            if 0<=sxx< screen.get_width() and 0<= syy< screen.get_height():
                pygame.draw.circle(screen, st['color'], (int(sxx),int(syy)), 1)

    def _create_star_list(self):
        st_list=[]
        for _ in range(100):
            sx= random.uniform(0, self.WORLD_WIDTH)
            sy= random.uniform(0, self.WORLD_HEIGHT)
            bright= random.randint(140,220)
            color= (bright,bright,bright)
            st_list.append({'x':sx,'y':sy,'color':color})
        return st_list

    def _create_asteroids(self):
        asts=[]
        for _ in range(20):
            ax= random.uniform(0, self.WORLD_WIDTH)
            ay= random.uniform(0, self.WORLD_HEIGHT)
            vx= random.uniform(-50,50)
            vy= random.uniform(-50,50)
            radius= random.uniform(10,25)
            mass= radius
            grey= random.randint(120,180)
            color=(grey,grey,grey)
            asts.append({
              'x':ax,'y':ay,
              'vx':vx,'vy':vy,
              'radius':radius,'mass':mass,
              'color':color
            })
        return asts
