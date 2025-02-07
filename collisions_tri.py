#!/usr/bin/env python3

"""
Asteroid Breakage Engine (Organized Version)
--------------------------------------------

This code demonstrates:
 - A small 'TriangleAtom' class for tiny equilateral triangles.
 - A 'CompositeAsteroid' class that groups them together.
 - A 'Spaceship' class with basic controls and shooting.
 - A 'Projectile' class for bullets.

The collision/breakage logic is kept modular:
 - 'distribute_impulse' can be overridden to change how impulses
   are distributed among atoms in the asteroid.
 - 'check_breakage' can be overridden or extended to define how
   the asteroid breaks up when one or more atoms exceed their
   strength threshold.

You may split these classes into separate files if you prefer.
See placeholders for "physics logic" that you can adapt yourself.
"""

import math
import random
import pygame
from typing import List, Optional, Tuple

########################################
# GLOBAL SETTINGS
########################################
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60

# Atom/triangle defaults
ATOM_SIDE              = 4.0    # Very small triangle side length (few pixels)
ATOM_MASS              = 0.1
ATOM_MATERIAL_STRENGTH = 200.0  # Impulse threshold for breakage

# Spaceship config
SHIP_SIZE         = 15
SHIP_THRUST       = 200.0
SHIP_TURN_SPEED   = 3.0

# Projectile config
PROJECTILE_RADIUS   = 2
PROJECTILE_MASS     = 0.05
PROJECTILE_SPEED    = 400
PROJECTILE_LIFETIME = 2.0

########################################
# Triangle Atom
########################################

class TriangleAtom:
    """
    Represents a tiny equilateral triangle "atom".
    Each one has:
     - side length 'side'
     - mass 'mass'
     - material strength 'mat_strength' (impulse threshold)
     - position 'pos'
     - orientation 'angle'
     - velocity 'vel'
     - angular velocity 'ang_vel'
     - tracked 'last_impulse' for breakage logic
    """
    def __init__(self,
                 pos: pygame.math.Vector2,
                 angle: float,
                 side: float = ATOM_SIDE,
                 mass: float = ATOM_MASS,
                 mat_strength: float = ATOM_MATERIAL_STRENGTH):
        self.position = pos
        self.angle = angle
        self.side = side
        self.mass = mass
        self.mat_strength = mat_strength

        # Moment of inertia for an equilateral triangle about centroid:
        # I = m * a^2 / 12
        self.inertia = self.mass * (self.side ** 2) / 12.0

        self.velocity = pygame.math.Vector2(0, 0)
        self.ang_vel  = 0.0

        # Track the maximum impulse delivered in the current collision step
        self.last_impulse = 0.0

    def apply_impulse(self, impulse: pygame.math.Vector2, contact_point: pygame.math.Vector2):
        """
        Applies an impulse J at 'contact_point' in world coords.
        This updates both linear and angular velocities.
        """
        self.velocity += impulse / self.mass

        r = contact_point - self.position
        # In 2D, the scalar "cross" of (r x J):
        angular_impulse = r.cross(impulse)
        self.ang_vel += angular_impulse / self.inertia

        # Record the largest impulse so we can decide if we break.
        self.last_impulse = max(self.last_impulse, impulse.length())

    def reset_impulse(self):
        self.last_impulse = 0.0

    def exceeds_strength(self) -> bool:
        """Return True if the largest impulse exceeded the material threshold."""
        return self.last_impulse >= self.mat_strength

    def update(self, dt: float):
        """Simple Euler integration of position and angle."""
        self.position += self.velocity * dt
        self.angle += self.ang_vel * dt

    def draw(self, surface: pygame.Surface):
        """
        Render the tiny equilateral triangle at (position, angle).
        We'll color them grey to distinguish from projectiles or ship.
        """
        # For an equilateral triangle, side = a, height = sqrt(3)/2 * a
        h = (math.sqrt(3) / 2) * self.side
        # The centroid is ~1/3 of the height from the base,
        # but let's define local coords so that the centroid is at (0,0).
        # We'll place the top vertex at (0, -2h/3), left at (-a/2, h/3), right at (a/2, h/3).
        local_vertices = [
            pygame.math.Vector2(0,   -2*h/3),
            pygame.math.Vector2(-self.side/2, h/3),
            pygame.math.Vector2( self.side/2, h/3)
        ]
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        screen_pts = []
        for lv in local_vertices:
            rx = lv.x*cos_a - lv.y*sin_a
            ry = lv.x*sin_a + lv.y*cos_a
            sx = self.position.x + rx
            sy = self.position.y + ry
            screen_pts.append((sx, sy))
        pygame.draw.polygon(surface, (128,128,128), screen_pts)
        pygame.draw.polygon(surface, (200,200,200), screen_pts, 1)

########################################
# CompositeAsteroid
########################################

class CompositeAsteroid:
    """
    A group of small TriangleAtom objects. A collision impulse is
    distributed among them. If any atom's impulse exceeds strength,
    that atom "breaks off" as a separate piece.
    """
    def __init__(self, atoms: List[TriangleAtom]):
        self.atoms = atoms

    def total_mass(self) -> float:
        return sum(a.mass for a in self.atoms)

    def center_of_mass(self) -> pygame.math.Vector2:
        if not self.atoms:
            return pygame.math.Vector2(0,0)
        cm = pygame.math.Vector2(0,0)
        for a in self.atoms:
            cm += a.position
        return cm / len(self.atoms)

    def distribute_impulse(self,
                           impulse: pygame.math.Vector2,
                           contact_point: pygame.math.Vector2):
        """
        How to distribute impulse among multiple atoms?
        By default: equally among all atoms.
        You can override this to do something more advanced
        (e.g. distance-based weighting).
        """
        n = len(self.atoms)
        if n < 1:
            return
        per_atom = impulse / float(n)
        for atom in self.atoms:
            atom.apply_impulse(per_atom, contact_point)

    def apply_collision(self,
                        impulse: pygame.math.Vector2,
                        contact_point: pygame.math.Vector2):
        """
        Called by your collision logic to impart an impulse
        on this asteroid. We'll then check for breakage afterwards.
        """
        self.distribute_impulse(impulse, contact_point)

    def breakage_logic(self) -> Optional[List['CompositeAsteroid']]:
        """
        If an atom has last_impulse >= mat_strength,
        remove it from self, return as a new fragment.
        You might want more advanced contour-based breakage.
        """
        new_frags = []
        keep = []
        for atom in self.atoms:
            if atom.exceeds_strength():
                # That single atom breaks off as a new piece
                new_frags.append(CompositeAsteroid([atom]))
            else:
                keep.append(atom)
        if new_frags:
            self.atoms = keep
            return new_frags
        return None

    def update(self, dt: float):
        for a in self.atoms:
            a.update(dt)
            a.reset_impulse()

    def draw(self, surface: pygame.Surface):
        for a in self.atoms:
            a.draw(surface)

########################################
# Projectile
########################################

class Projectile:
    """
    A simple bullet. We define radius, mass, velocity, lifetime, etc.
    """
    def __init__(self, pos: pygame.math.Vector2, vel: pygame.math.Vector2):
        self.position = pos.copy()
        self.velocity = vel.copy()
        self.radius = PROJECTILE_RADIUS
        self.mass = PROJECTILE_MASS
        self.lifetime = PROJECTILE_LIFETIME

    def update(self, dt: float):
        self.position += self.velocity * dt
        self.lifetime -= dt
        # Optionally wrap around screen edges:
        self.position.x %= SCREEN_WIDTH
        self.position.y %= SCREEN_HEIGHT

    def expired(self) -> bool:
        return (self.lifetime <= 0)

    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(surface, (255,255,0),
                           (int(self.position.x), int(self.position.y)),
                           self.radius)

########################################
# Spaceship
########################################

class Spaceship:
    """
    A minimal "Asteroids-style" ship:
     - arrow keys for turning (left/right) and thrust up/down
     - shoot with space
    """
    def __init__(self, pos: pygame.math.Vector2):
        self.position = pos.copy()
        self.velocity = pygame.math.Vector2(0, 0)
        self.angle = 0.0  # facing "up"
        # You might store mass, inertia, etc. if you want more advanced logic.

    def update(self, dt: float, keys):
        # Turn left/right
        if keys[pygame.K_LEFT]:
            self.angle -= SHIP_TURN_SPEED * dt
        if keys[pygame.K_RIGHT]:
            self.angle += SHIP_TURN_SPEED * dt

        # Thrust forward/back
        if keys[pygame.K_UP]:
            fwd = pygame.math.Vector2(math.cos(self.angle), math.sin(self.angle))
            self.velocity += fwd * SHIP_THRUST * dt
        if keys[pygame.K_DOWN]:
            rev = pygame.math.Vector2(math.cos(self.angle), math.sin(self.angle))
            self.velocity -= rev * SHIP_THRUST * dt

        # Move
        self.position += self.velocity * dt

        # Wrap screen
        self.position.x %= SCREEN_WIDTH
        self.position.y %= SCREEN_HEIGHT

    def shoot(self) -> Projectile:
        """
        Create a projectile starting at the "tip" of the ship,
        with a velocity relative to the ship plus some bullet speed.
        """
        tip_offset = pygame.math.Vector2(0, -SHIP_SIZE)
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        tip_world = pygame.math.Vector2(
            self.position.x + tip_offset.x*cos_a - tip_offset.y*sin_a,
            self.position.y + tip_offset.x*sin_a + tip_offset.y*cos_a
        )
        bullet_dir = pygame.math.Vector2(math.cos(self.angle), math.sin(self.angle))
        bullet_vel = self.velocity + bullet_dir * PROJECTILE_SPEED
        return Projectile(tip_world, bullet_vel)

    def draw(self, surface: pygame.Surface):
        """
        Draw a simple triangle for the ship.
        """
        a = SHIP_SIZE
        local_points = [
            pygame.math.Vector2(0, -a),
            pygame.math.Vector2(-a/2, a/2),
            pygame.math.Vector2(a/2, a/2)
        ]
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        scr_points = []
        for lp in local_points:
            rx = lp.x*cos_a - lp.y*sin_a
            ry = lp.x*sin_a + lp.y*cos_a
            sx = self.position.x + rx
            sy = self.position.y + ry
            scr_points.append((sx, sy))
        # Fill color + outline
        pygame.draw.polygon(surface, (0,200,200), scr_points)
        pygame.draw.polygon(surface, (255,255,255), scr_points, 2)

########################################
# Simple collision logic placeholders
########################################

def projectile_hits_asteroid(proj: Projectile,
                             ast: CompositeAsteroid) -> Optional[Tuple[pygame.math.Vector2, pygame.math.Vector2]]:
    """
    A placeholder collision test between a bullet and the asteroid.
    For more advanced logic, you'd do per-atom bounding,
    or any shape-based detection you prefer.

    Here, we do a simple bounding-circle test:
      - We compute the composite's bounding center & radius
      - If distance < (asteroid_radius + projectile_radius) => collision
    We then compute a "normal" from center to projectile for an impulse direction.
    """
    if not ast.atoms:
        return None
    center = ast.center_of_mass()
    # naive bounding radius
    radius = 0.0
    for atom in ast.atoms:
        dist = (atom.position - center).length()
        radius = max(radius, dist + atom.side)
    # check distance
    dist_c = (proj.position - center).length()
    if dist_c <= (radius + proj.radius):
        n = (proj.position - center)
        if n.length_squared() < 1e-12:
            n = pygame.math.Vector2(0, -1)
        else:
            n = n.normalize()
        contact_pt = center + n * radius
        return (n, contact_pt)
    return None

def resolve_elastic_collision(proj: Projectile,
                              ast: CompositeAsteroid,
                              normal: pygame.math.Vector2,
                              contact_point: pygame.math.Vector2,
                              restitution: float = 1.0):
    """
    Another placeholder for elastic collision impulse.  You can refine
    how you compute relative velocity, mass, etc. For demonstration:
    - projectile mass = proj.mass
    - asteroid mass = ast.total_mass()
    - assume asteroid velocity ~ 0, or average of atoms, or a custom method
    """
    m1 = proj.mass
    m2 = ast.total_mass()

    # We'll approximate the asteroid velocity as zero or some average.
    # For demonstration, let's treat it as zero:
    v_ast = pygame.math.Vector2(0, 0)

    v_rel = proj.velocity - v_ast
    proj_speed_normal = v_rel.dot(normal)
    if proj_speed_normal >= 0:
        return  # they're separating

    # Standard formula: J = -(1+e)*(v_rel·n)/(1/m1 + 1/m2)
    J_scalar = -(1+restitution)*proj_speed_normal / (1/m1 + 1/m2)
    impulse = normal * J_scalar

    # update projectile
    proj.velocity += impulse / m1

    # apply collision impulse to asteroid
    ast.apply_collision(impulse, contact_point)

########################################
# MAIN DEMO
########################################

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock  = pygame.time.Clock()

    # Create a random "asteroid" made of many small TriangleAtoms
    # at around some center
    ast_center = pygame.math.Vector2(500, 300)
    atoms = []
    for _ in range(40):
        r = random.uniform(0, 40)
        ang = random.uniform(0, 2*math.pi)
        x = ast_center.x + r*math.cos(ang)
        y = ast_center.y + r*math.sin(ang)
        tri = TriangleAtom(pygame.math.Vector2(x,y),
                           angle=random.uniform(0,2*math.pi))
        # small random velocities
        tri.velocity = pygame.math.Vector2(random.uniform(-20,20),
                                           random.uniform(-20,20))
        atoms.append(tri)
    asteroid = CompositeAsteroid(atoms)

    # Spaceship
    ship = Spaceship(pygame.math.Vector2(100,100))

    # Projectiles list
    bullets: List[Projectile] = []

    running = True
    while running:
        dt = clock.tick(FPS)/1000.0

        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_SPACE:
                    # shoot
                    bullets.append(ship.shoot())

        # Update logic
        keys = pygame.key.get_pressed()
        ship.update(dt, keys)

        # update bullets
        for b in bullets:
            b.update(dt)
        bullets = [b for b in bullets if not b.expired()]

        # collisions: projectile vs. asteroid
        for b in bullets[:]:
            collision = projectile_hits_asteroid(b, asteroid)
            if collision is not None:
                n, contact_pt = collision
                # resolve collision
                resolve_elastic_collision(b, asteroid, n, contact_pt)
                # remove bullet after collision
                bullets.remove(b)

        # update asteroid
        asteroid.update(dt)
        # check breakage
        frags = asteroid.breakage_logic()
        if frags:
            print("Asteroid broke into", len(frags)+1, "pieces.")
            # for a real game, you'd keep them as separate asteroids
            # for demo, let's just keep the "main chunk" if any
            # or the first fragment
            if asteroid.atoms:
                # remain with the smaller chunk
                pass
            else:
                # if the original is empty, take the first fragment
                asteroid = frags[0]

        # draw
        screen.fill((0,0,0))
        asteroid.draw(screen)
        ship.draw(screen)
        for b in bullets:
            b.draw(screen)

        pygame.display.flip()

    pygame.quit()

if __name__=="__main__":
    main()
