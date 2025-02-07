import random, math
import pygame
from .base import LevelBase

class LevelStar(LevelBase):
    STAR_RADIUS_LETHAL = 200
    GRAVITY_RANGE      = 800
    G_M                = 30000

    def __init__(self):
        super().__init__()
        self.STAR_CX = self.WORLD_WIDTH  / 2
        self.STAR_CY = self.WORLD_HEIGHT / 2
        self.star_list = self._create_far_stars()

    def _create_far_stars(self):
        stars = []
        for _ in range(800):
            sx = random.uniform(0, self.WORLD_WIDTH)
            sy = random.uniform(0, self.WORLD_HEIGHT)
            bri = random.randint(100, 220)
            stars.append({'x': sx, 'y': sy, 'color': (bri,bri,bri)})
        return stars

    def force_func(self, x, y, vx, vy):
        dx = x - self.STAR_CX
        dy = y - self.STAR_CY
        r2 = dx*dx + dy*dy
        if r2 < 1e-6:
            return (0,0)
        r = math.sqrt(r2)
        if r >= self.GRAVITY_RANGE:
            return (0,0)
        a_mag = self.G_M / r2
        ax = -a_mag * (dx/r)
        ay = -a_mag * (dy/r)
        return (ax, ay)

    def lethal_check(self, x, y):
        dx = x - self.STAR_CX
        dy = y - self.STAR_CY
        return (dx*dx + dy*dy) < (self.STAR_RADIUS_LETHAL**2)

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))
        sx = self.STAR_CX - cam_x
        sy = self.STAR_CY - cam_y
        for st in self.star_list:
            star_x = st['x'] - cam_x
            star_y = st['y'] - cam_y
            pygame.draw.circle(screen, st['color'], (int(star_x), int(star_y)), 1)
        max_r=2000
        step=10
        for rr in range(int(max_r), self.STAR_RADIUS_LETHAL, -step):
            frac= (rr- self.STAR_RADIUS_LETHAL)/(max_r- self.STAR_RADIUS_LETHAL)
            frac= max(0,min(1,frac))
            rred= int(255*(1-frac)**2)
            ggrn= int(255*((1-frac)**2))
            bblu= int(255*((1-frac)**2))
            pygame.draw.circle(screen,(rred,ggrn,bblu),(int(sx),int(sy)), rr)
        pygame.draw.circle(screen, (0, 0, 0), (int(sx), int(sy)), self.STAR_RADIUS_LETHAL)

