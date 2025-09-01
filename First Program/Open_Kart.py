from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, random, time

#checking 2


camera_view = 'chase'
fovY = 60
fovY_map_select = 100
menu_cam_height = 2500.0
SCREEN_W = 1280
SCREEN_H = 720


STATE_MENU = 0
STATE_PLAY_MAP_SELECT = 1  
STATE_PLAY_DRIVE = 2
STATE_EXPLORE = 3
STATE_COMPETE = 4

game_state = STATE_MENU
menu_options = ["Play", "Explore", "Compete", "Exit"]
menu_index = 0
camera_pos = (0, 500, 500)
current_map = 1
map_select_target = 'play'  
app_should_exit = False
last_error_message = ""


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, rgb=(1,1,1)):
    r,g,b = rgb
    glColor3f(r,g,b)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, SCREEN_W, 0, SCREEN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def quad(v0, v1, v2, v3, col):
    glColor3f(*col)
    glBegin(GL_QUADS)
    glVertex3f(*v0); glVertex3f(*v1); glVertex3f(*v2); glVertex3f(*v3)
    glEnd()

def set_clear_color_for_map():
    if current_map == 1:
        glClearColor(0.50, 0.70, 0.90, 1.0)
    elif current_map == 2:
        glClearColor(0.80, 0.85, 0.95, 1.0)
    else:
        glClearColor(0.10, 0.12, 0.15, 1.0)




def draw_base(color):
    s = 6000
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex3f(-s, -s, -1); glVertex3f(s, -s, -1); glVertex3f(s, s, -1); glVertex3f(-s, s, -1)
    glEnd()


def gen_oval(cx, cy, rx, ry, n):
    pts = []
    for k in range(n):
        a = 2*math.pi*k/n
        pts.append((cx + rx*math.cos(a), cy + ry*math.sin(a)))
    return pts

def gen_regular_polygon(cx, cy, r, n, rot_deg=0.0, sx=1.0, sy=1.0):
    rot = math.radians(rot_deg)
    pts = []
    for k in range(n):
        a = 2*math.pi*k/n + rot
        pts.append((cx + sx*r*math.cos(a), cy + sy*r*math.sin(a)))
    return pts

def offset_inner_from_center(outer_pts, inset):
    cx = sum(p[0] for p in outer_pts)/len(outer_pts)
    cy = sum(p[1] for p in outer_pts)/len(outer_pts)
    inner = []
    for x,y in outer_pts:
        vx, vy = x-cx, y-cy
        d = math.hypot(vx, vy)
        scale = max((d - inset) / d, 0.05) if d != 0 else 0.95
        inner.append((cx + vx*scale, cy + vy*scale))
    return inner

def ring_from_polylines(outer_pts, inner_pts, color):
    n = len(outer_pts)
    for i in range(n):
        j = (i + 1) % n
        v0 = (outer_pts[i][0], outer_pts[i][1], 0)
        v1 = (outer_pts[j][0], outer_pts[j][1], 0)
        v2 = (inner_pts[j][0], inner_pts[j][1], 0)
        v3 = (inner_pts[i][0], inner_pts[i][1], 0)
        quad(v0, v1, v2, v3, color)

def draw_checker_finish_line_from_ring(outer_pts, inner_pts, idx, seg_frac,
                                       tiles_along=10, tiles_across=8):
    n = len(outer_pts)
    i0 = idx % n; i1 = (i0 + 1) % n
    def mix(a, b, t):
        return (a[0]*(1-t)+b[0]*t, a[1]*(1-t)+b[1]*t)
    
    oA = mix(outer_pts[i0], outer_pts[i1], seg_frac)
    iA = mix(inner_pts[i0], inner_pts[i1], seg_frac)
    cx, cy = 0.5*(oA[0] + iA[0]), 0.5*(oA[1] + iA[1])
    
    tx, ty = outer_pts[i1][0] - outer_pts[i0][0], outer_pts[i1][1] - outer_pts[i0][1]
    L = math.hypot(tx, ty) or 1.0
    ux, uy = tx/L, ty/L
    nx, ny = -uy, ux
    
    width_vec_x, width_vec_y = (oA[0] - iA[0], oA[1] - iA[1])
    track_w = math.hypot(width_vec_x, width_vec_y)
    total_across = min(track_w, track_w)  
    tile_size = total_across / max(1, tiles_across)
    line_length = tile_size * tiles_along
    
    start_ax = -0.5 * total_across
    start_l = -0.5 * line_length
    
    glPushAttrib(GL_ENABLE_BIT)
    glDisable(GL_DEPTH_TEST)
    z = 0.2
    for a in range(tiles_along):
        for c in range(tiles_across):
            ax0 = start_ax + c * tile_size; ax1 = ax0 + tile_size
            l0 = start_l + a * tile_size;  l1 = l0 + tile_size
            
            v0x = cx + nx*ax0 + ux*l0; v0y = cy + ny*ax0 + uy*l0
            v1x = cx + nx*ax1 + ux*l0; v1y = cy + ny*ax1 + uy*l0
            v2x = cx + nx*ax1 + ux*l1; v2y = cy + ny*ax1 + uy*l1
            v3x = cx + nx*ax0 + ux*l1; v3y = cy + ny*ax0 + uy*l1
            if (a + c) % 2 == 0:
                glColor3f(0.05, 0.05, 0.05)
            else:
                glColor3f(0.95, 0.95, 0.95)
            glBegin(GL_QUADS)
            glVertex3f(v0x, v0y, z)
            glVertex3f(v1x, v1y, z)
            glVertex3f(v2x, v2y, z)
            glVertex3f(v3x, v3y, z)
            glEnd()
    glPopAttrib()

def get_track_polylines_for_map(m):
    if m == 1:
        outer = gen_oval(0, 0, 3000, 1600, 72); inner = offset_inner_from_center(outer, 360); return outer, inner
    if m == 2:
        
        outer = gen_regular_polygon(0, 0, 2300, 5, rot_deg=90.0, sx=1.0, sy=1.0); inner = offset_inner_from_center(outer, 360); return outer, inner
    outer = gen_regular_polygon(0, 0, 2300, 4, rot_deg=45.0, sx=1.35, sy=1.0); inner = offset_inner_from_center(outer, 240); return outer, inner

def get_finish_marker(m):
    # The finish marker indicates the centerline segment index and fractional
    # position (t) along that segment used for both drawing the checker line
    # and anchoring lap progress normalization. On maps 2 and 3, using segment
    # index 2 caused inconsistent wrap detection near corners. Anchor the
    # finish to a straighter segment (index 0) for robust lap detection.
    if m == 1: return 12, 0.5
    if m == 2: return 0, 0.5
    return 0, 0.5




def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        xi, yi = poly[i]; xj, yj = poly[j]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) if (yj - yi) != 0 else 1e-9) + xi)
        if intersect: inside = not inside
    return inside

def point_in_ring(x, y, outer, inner):
    return point_in_poly(x, y, outer) and (not point_in_poly(x, y, inner))

def poly_centroid(poly):
    n = len(poly);  sx = sum(p[0] for p in poly)/max(n,1); sy = sum(p[1] for p in poly)/max(n,1)
    return sx, sy


q_sph = None
q_cyl = None
decor_cache = {1: None, 2: None, 3: None}

def draw_tree(x, y, s=1.0):
    glPushMatrix(); glTranslatef(x, y, 0); glScalef(s, s, s)
    glColor3f(0.35, 0.20, 0.05); gluCylinder(q_cyl, 6, 6, 32, 10, 1)
    glTranslatef(0, 0, 32); glColor3f(0.10, 0.55, 0.20); gluSphere(q_sph, 16, 12, 10)
    glTranslatef(0, 0, 12); gluSphere(q_sph, 12, 12, 10)
    glPopMatrix()

def draw_ice(x, y, s=1.0):
    glPushMatrix(); glTranslatef(x, y, 0); glScalef(s, s, s)
    glColor3f(0.80, 0.90, 0.98); glutSolidCube(22)
    glTranslatef(0, 0, 16); gluSphere(q_sph, 12, 12, 10)
    glTranslatef(0, 0, 10); gluSphere(q_sph, 8, 12, 10)
    glPopMatrix()

def draw_rock(x, y, s=1.0):
    glPushMatrix(); glTranslatef(x, y, 0); glScalef(s, s, s)
    glColor3f(0.30, 0.30, 0.33); gluSphere(q_sph, 14, 12, 10)
    glTranslatef(10, 6, 2); gluSphere(q_sph, 9, 12, 10)
    glTranslatef(-12, -8, 4); gluSphere(q_sph, 7, 12, 10)
    glPopMatrix()

def _lerp2(a, b, t): return (a[0]*(1-t)+b[0]*t, a[1]*(1-t)+b[1]*t)
def _seg_normal(p0, p1):
    dx, dy = (p1[0]-p0[0], p1[1]-p0[1]); L = math.hypot(dx, dy) or 1.0
    return (-dy/L, dx/L)

def _find_off_road(px, py, nx, ny, outer, inner, prefer, base_offset, step=25.0, max_iter=8):
    best = None
    for sign in (+1, -1):
        off = base_offset
        for _ in range(max_iter):
            cx = px + sign*nx*off; cy = py + sign*ny*off
            if not point_in_ring(cx, cy, outer, inner):
                if prefer == 'outside' and not point_in_poly(cx, cy, outer): return (cx, cy)
                if prefer == 'inside'  and point_in_poly(cx, cy, inner):    return (cx, cy)
                if best is None: best = (cx, cy)
            off += step
    return best if best is not None else (px, py)

def _points_outside_outer(outer, inner, base_offset, points_per_segment):
    pts = []; n = len(outer); ts = [(k+1)/(points_per_segment+1) for k in range(points_per_segment)]
    for i in range(n):
        j = (i + 1) % n; p0, p1 = outer[i], outer[j]; nx, ny = _seg_normal(p0, p1)
        for t in ts:
            px, py = _lerp2(p0, p1, t); pts.append(_find_off_road(px, py, nx, ny, outer, inner, 'outside', base_offset))
    return pts

def _points_inside_inner(outer, inner, base_offset, points_per_segment):
    pts = []; n = len(inner); ts = [(k+1)/(points_per_segment+1) for k in range(points_per_segment)]
    for i in range(n):
        j = (i + 1) % n; p0, p1 = inner[i], inner[j]; nx, ny = _seg_normal(p0, p1)
        for t in ts:
            px, py = _lerp2(p0, p1, t); pts.append(_find_off_road(px, py, nx, ny, outer, inner, 'inside', base_offset))
    return pts

def build_decor_for_map(m):
    outer, inner = get_track_polylines_for_map(m)
    if m == 1:
        a = _points_outside_outer(outer, inner, base_offset=70.0, points_per_segment=1)
        b = _points_inside_inner(outer, inner, base_offset=70.0, points_per_segment=1)
        decor_cache[m] = {"trees": a + b}
    elif m == 2:
        a = _points_outside_outer(outer, inner, base_offset=60.0, points_per_segment=10)
        b = _points_inside_inner(outer, inner, base_offset=60.0, points_per_segment=10)
        decor_cache[m] = {"ice": a + b}
    else:
        a = _points_outside_outer(outer, inner, base_offset=65.0, points_per_segment=10)
        b = _points_inside_inner(outer, inner, base_offset=65.0, points_per_segment=10)
        decor_cache[m] = {"rocks": a + b}


def draw_track_map1():
    road = (0.18, 0.18, 0.18); base = (0.35, 0.48, 0.38)
    draw_base(base)
    outer = gen_oval(0, 0, 3000, 1600, 72); inner = offset_inner_from_center(outer, 360)
    ring_from_polylines(outer, inner, road)
    fi, ft = get_finish_marker(1)
    draw_checker_finish_line_from_ring(outer, inner, fi, ft, tiles_along=10, tiles_across=6)
    if decor_cache[1] is None: build_decor_for_map(1)
    for (x, y) in decor_cache[1]["trees"]: draw_tree(x, y, s=2.2)

def draw_track_map2():
    road = (0.20, 0.20, 0.22); base = (0.80, 0.85, 0.95)
    draw_base(base)
    outer, inner = get_track_polylines_for_map(2)
    ring_from_polylines(outer, inner, road)
    fi, ft = get_finish_marker(2)
    draw_checker_finish_line_from_ring(outer, inner, fi, ft, tiles_along=10, tiles_across=6)
    if decor_cache[2] is None: build_decor_for_map(2)
    for (x, y) in decor_cache[2]["ice"]: draw_ice(x, y, s=2.4)

def draw_track_map3():
    road = (0.20, 0.20, 0.22); base = (0.15, 0.18, 0.22)
    draw_base(base)
    outer = gen_regular_polygon(0, 0, 2300, 4, rot_deg=45.0, sx=1.35, sy=1.0); inner = offset_inner_from_center(outer, 240)
    ring_from_polylines(outer, inner, road)
    fi, ft = get_finish_marker(3)
    draw_checker_finish_line_from_ring(outer, inner, fi, ft, tiles_along=10, tiles_across=6)
    if decor_cache[3] is None: build_decor_for_map(3)
    for (x, y) in decor_cache[3]["rocks"]: draw_rock(x, y, s=2.1)

def draw_track():
    if current_map == 1: draw_track_map1()
    elif current_map == 2: draw_track_map2()
    else: draw_track_map3()




def draw_menu():
    glClearColor(0.07, 0.09, 0.12, 1.0)
    draw_text(SCREEN_W//2 - 140, SCREEN_H - 70, "Open Kart Racers")
    y = SCREEN_H - 120
    for i, label in enumerate(menu_options):
        prefix = "> " if i == menu_index else "  "
        draw_text(40, y, f"{prefix}{label}")
        y -= 60

def draw_hud_play():
    y = SCREEN_H - 50
    draw_text(10, y, f"Lives: {lives}"); y -= 30
    draw_text(10, y, f"Collisions: {collision_count}" if race_started else "Press Space to start"); y -= 30
    draw_text(10, y, f"Coins: {coins_collected}"); y -= 30
    draw_text(10, y, "1:Boost(-5c)  2:Autopilot(-10c)  Q:Rifle  E:Missile  R:Reset  M:Menu  F:1st-Person")
    try:
        total_racers = max(1, 1 + (len(ais) if ai_enabled else 0))
        draw_text(SCREEN_W - 160, SCREEN_H - 70, f"Pos: {player_position}/{total_racers}")
        draw_text(SCREEN_W - 160, SCREEN_H - 40, f"Lap: {player_lap}/2")
    except Exception:
        pass

def draw_play_map_select():
    set_clear_color_for_map()
    draw_track()
    target_label = {
        'play': 'Play', 'explore': 'Explore', 'compete': 'Compete'
    }.get(map_select_target, 'Play')
    y = SCREEN_H - 50
    draw_text(10, y, f"{target_label}: Select Map ({current_map})"); y -= 30
    draw_text(10, y, "Press 1/2/3 to change map | Enter/Space to start | M to menu")
    
    desc = {
        1: "Map 1: Sunny Oval - wide turns, forgiving.",
        2: "Map 2: Frozen Square - sharper corners, icy vibe.",
        3: "Map 3: Night Circuit - tighter inner lane, dark."}
    y -= 30
    draw_text(10, y, desc.get(current_map, ""))




def draw_wheel():
    
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.08, 0.08, 0.08)
    radius = 6.0
    length = 4.0
    gluCylinder(q_cyl, radius, radius, length, 24, 1)
    glPopMatrix()

def draw_driver_headarms():
    glPushMatrix(); glTranslatef(0, 0, 8); glColor3f(0.90, 0.75, 0.55)
    gluSphere(q_sph, 3.6, 12, 10); glTranslatef(0, 0, 6); gluSphere(q_sph, 3.0, 12, 10)
    glPopMatrix()
    glPushMatrix(); glTranslatef(-2.2, 2.6, 6); glRotatef(90, 1, 0, 0); glColor3f(0.90, 0.75, 0.55); gluCylinder(q_cyl, 1.2, 1.2, 6.0, 10, 1); glPopMatrix()
    glPushMatrix(); glTranslatef( 2.2, 2.6, 6); glRotatef(90, 1, 0, 0); glColor3f(0.90, 0.75, 0.55); gluCylinder(q_cyl, 1.2, 1.2, 6.0, 10, 1); glPopMatrix()

def draw_kart_at(pos_xy, dir_deg, body_color=(0.85, 0.10, 0.10), with_driver=True):
    glPushMatrix()
    glTranslatef(pos_xy[0], pos_xy[1], 0)
    glRotatef(dir_deg, 0, 0, 1)
    glPushMatrix(); glScalef(0.8, 0.52, 0.34); glColor3f(*body_color); glutSolidCube(40); glPopMatrix()
    glPushMatrix(); glTranslatef(0, 0, 7); glScalef(0.62, 0.48, 0.16); glColor3f(0.10,0.10,0.12); glutSolidCube(40); glPopMatrix()
    for dx, dy in [(-14,-12.5),(14,-12.5),(-14,12.5),(14,12.5)]:
        
        glPushMatrix(); glTranslatef(dx, dy-2, 6.2); draw_wheel(); glPopMatrix()
    if with_driver: draw_driver_headarms()
    glPopMatrix()

kart_pos = [0.0, -300.0, 0.0]
kart_dir = 0.0
kart_speed = 0.0
kart_max_speed = 640.0
kart_accel = 480.0
kart_brake = 320.0


ai_enabled = True
ais = []  
ai_play_speed = 780.0

lives = 5
collision_count = 0
max_collisions_before_life_loss = 5
race_started = False
game_over = False
player_lap = 0
start_seg_play = 0
start_t_play = 0.0
prev_prog_player = 0.0
play_winner = ""
lap_guard_player = 0.0  
ignore_first_wrap_player = False  
player_position = 1  


boost_timer = 0.0           
autopilot_timer = 0.0       
autopilot_side = 1.0        


rifle_ammo = 10             
rifle_regen = 0.0
missile_ammo = 3            
missile_regen = 0.0
player_slow_timer = 0.0     
ai_next_missile = 10.0      
ai_next_rifle = 3.0         
orb_boost_timer_play = 0.0  


bullets = []   
missiles = []  


obstacles = []  
blue_orbs = []  


kart_collision_radius = 22.0
stun_duration_on_bump = 0.6
stun_timer = 0.0
boundary_hit_cooldown = 0.0
lap_guard_player = 0.0  




explore_pos   = [0.0, 0.0, 0.0]
explore_speed = 180.0
explore_dir = 0.0
explore_turn_rate = 140.0
explore_cam_dist = 190.0
explore_cam_height = 120.0
explore_cam_look_ahead = 40.0
explore_model_yaw_offset = -90.0
walk_phase = 0.0
walk_blend = 0.0
walk_swing_deg = 28.0
first_person = False

coins = []
coins_collected = 0
coin_count_min, coin_count_max = 10, 15
coin_collect_radius = 24.0
coin_respawn_min, coin_respawn_max = 3.0, 7.0
coin_spin = 0.0
coin_bob_t = 0.0
explore_timer_active = False
explore_timer = 0.0
explore_game_over = False
explore_ai = []  

explore_boost_active = 0.0
explore_boost_cooldown = 0.0   
explore_boost_charges = 2
explore_boost_mult = 2.8




compete_started = False
comp_start_seg = 0  
comp_start_t = 0.0
compete_over = False
compete_winner = ""


p1_pos = [0.0, 0.0, 0.0]
p1_dir = 0.0
p1_speed = 0.0
p1_stun = 0.0


p2_pos = [0.0, 0.0, 0.0]
p2_dir = 0.0
p2_speed = 0.0
p2_stun = 0.0


p1_rifle_ammo = 10; p1_rifle_regen = 0.0
p1_missile_ammo = 3; p1_missile_regen = 0.0
p2_rifle_ammo = 10; p2_rifle_regen = 0.0
p2_missile_ammo = 3; p2_missile_regen = 0.0
p1_slow_timer = 0.0; p2_slow_timer = 0.0

p1_lives = 5; p2_lives = 5
p1_collision_count = 0; p2_collision_count = 0
p1_hit_cd = 0.0; p2_hit_cd = 0.0
p1_lap = 0; p2_lap = 0
prev_prog_p1 = 0.0; prev_prog_p2 = 0.0
ignore_first_wrap_p1 = False
ignore_first_wrap_p2 = False
# Signed distance to the finish gate along the track tangent at the finish
# (used to detect crossing the finish line robustly on polygonal tracks).
finish_dot_player_prev = None
finish_dot_ais_prev = []
finish_dot_p1_prev = None
finish_dot_p2_prev = None

p1_boost_active = 0.0
p1_boost_cooldown = 0.0
p1_boost_charges = 2
p2_boost_active = 0.0
p2_boost_cooldown = 0.0
p2_boost_charges = 2
p1_orb_boost_timer = 0.0; p2_orb_boost_timer = 0.0




keys_down = set()        
p2_keys = set()          

def get_dt():
    if not hasattr(get_dt, "prev"):
        get_dt.prev = time.time()
        return 0.016
    now = time.time()
    dt = now - get_dt.prev
    get_dt.prev = now
    return max(0.0, min(dt, 0.05))
#---------------------------------------------------------------
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(SCREEN_W, SCREEN_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Open Kart Racers")

    global q_sph, q_cyl
    q_sph = gluNewQuadric()
    q_cyl = gluNewQuadric()

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.05, 0.07, 0.10, 1.0)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutSpecialUpFunc(specialUpListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()
