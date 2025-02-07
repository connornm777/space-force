import math

def limit_speed(vx, vy, cmax):
    spd = math.hypot(vx, vy)
    if spd > cmax:
        factor = cmax / spd
        vx *= factor
        vy *= factor
    return vx, vy

def wrap_pos(x, y, w, h):
    return (x % w, y % h)
