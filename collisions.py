import math

def elastic_bounce(m1, m2, x1, y1, vx1, vy1, x2, y2, vx2, vy2, e=1.0):
    dx = x2 - x1
    dy = y2 - y1
    dist = math.sqrt(dx*dx + dy*dy) + 1e-12
    nx = dx/dist
    ny = dy/dist
    vx_rel = vx2 - vx1
    vy_rel = vy2 - vy1
    vn = vx_rel*nx + vy_rel*ny
    if vn > 0:
        return vx1, vy1, vx2, vy2  # already separating, no bounce needed
    imp = -(1 + e) * vn / (1/m1 + 1/m2)
    impx = imp * nx
    impy = imp * ny
    return (
        vx1 - impx/m1,
        vy1 - impy/m1,
        vx2 + impx/m2,
        vy2 + impy/m2
    )

def handle_collision(objA, objB, game_state):
    dx = objB['x'] - objA['x']
    dy = objB['y'] - objA['y']
    r_sum = objA['radius'] + objB['radius']
    if dx*dx + dy*dy <= r_sum*r_sum:
        # Example rocket logic: if rocket is not shielded => game over
        if objA.get('type') == 'rocket' and not objA.get('shield_on', False):
            game_state['game_over'] = True
            return
        if objB.get('type') == 'rocket' and not objB.get('shield_on', False):
            game_state['game_over'] = True
            return

        # Otherwise do an elastic bounce
        mA = objA.get('mass', 1.0)
        mB = objB.get('mass', 1.0)
        vx1, vy1, vx2, vy2 = elastic_bounce(
            mA, mB,
            objA['x'], objA['y'], objA['vx'], objA['vy'],
            objB['x'], objB['y'], objB['vx'], objB['vy']
        )
        objA['vx'], objA['vy'] = vx1, vy1
        objB['vx'], objB['vy'] = vx2, vy2
