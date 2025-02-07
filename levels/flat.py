import random
import pygame
from .base import LevelBase
from constants import WORLD_WIDTH, WORLD_HEIGHT

class LevelFlat(LevelBase):
    """
    A simple 'flat' level with star parallax, no gravity.
    """
    def __init__(self):
        super().__init__()
        self.star_layers = self._create_star_layers()
        # self.asteroids = self._create_asteroids() # if needed

    def _create_star_layers(self):
        layers = []
        for (count, px) in [(700,0.1), (600,0.2), (500,0.6), (500,0.9)]:
            stars = []
            for _ in range(count):
                sx = random.uniform(0, self.WORLD_WIDTH)
                sy = random.uniform(0, self.WORLD_HEIGHT)
                bri = random.randint(100,220)
                stars.append({'x': sx, 'y': sy, 'color': (bri,bri,bri)})
            layers.append({'stars': stars, 'parallax': px})
        return layers

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))
        for layer in self.star_layers:
            px = layer['parallax']
            for st in layer['stars']:
                sx = (st['x'] - px*cam_x) % self.WORLD_WIDTH
                sy = (st['y'] - px*cam_y) % self.WORLD_HEIGHT
                pygame.draw.circle(screen, st['color'], (int(sx), int(sy)), 1)
