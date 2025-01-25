"""
A simple "flat space" level.

 - No external forces: rocket experiences no gravitational or curved-space acceleration.
 - Random asteroids are scattered across the large world region.
"""

import random

WORLD_WIDTH  = 5000
WORLD_HEIGHT = 5000

def load_level():
    """
    Return a tuple: (force_func, asteroids_list, stars_list)
      - force_func: a function (x,y,vx,vy)->(ax,ay)
      - asteroids_list: initial asteroids in the world
      - stars_list: for background rendering
    """

    def force_func(x, y, vx, vy):
        # Flat space => no external acceleration
        return (0.0, 0.0)

    # scatter some asteroids
    asteroids = []
    num_asteroids = 20
    for _ in range(num_asteroids):
        ax = random.uniform(0, WORLD_WIDTH)
        ay = random.uniform(0, WORLD_HEIGHT)
        # mass ~ size
        radius = random.uniform(10,30)
        mass   = radius
        vx     = random.uniform(-20,20)
        vy     = random.uniform(-20,20)
        color  = (200,200,200)
        asteroids.append({
            'x': ax,
            'y': ay,
            'vx': vx,
            'vy': vy,
            'radius': radius,
            'mass': mass,
            'color': color
        })

    # random "stars" for background
    stars = []
    num_stars = 200
    for _ in range(num_stars):
        sx = random.uniform(0, WORLD_WIDTH)
        sy = random.uniform(0, WORLD_HEIGHT)
        brightness = random.randint(80,200)
        stars.append({
            'x': sx,
            'y': sy,
            'color': (brightness,brightness,brightness),
            'size': 1
        })

    return (force_func, asteroids, stars)
