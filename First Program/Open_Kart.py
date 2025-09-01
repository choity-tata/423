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

def get_center_and_tangent(outer, inner, idx, t):
    n = len(outer); i = idx % n; j = (i + 1) % n
    def mix(a, b, s): return (a[0]*(1-s)+b[0]*s, a[1]*(1-s)+b[1]*s)
    o = mix(outer[i], outer[j], t)
    inn = mix(inner[i], inner[j], t)
    cx = 0.5*(o[0] + inn[0]); cy = 0.5*(o[1] + inn[1])
    tx = outer[j][0] - outer[i][0]; ty = outer[j][1] - outer[i][1]
    ang = math.degrees(math.atan2(ty, tx))
    return (cx, cy), ang

def _segment_length(pts, i):
    j = (i + 1) % len(pts)
    dx = pts[j][0] - pts[i][0]; dy = pts[j][1] - pts[i][1]
    return math.hypot(dx, dy)

def closest_center_param(outer, inner, px, py):
    """Return (seg_idx, t, center_point). Projects onto the road centerline polyline."""
    best_d2 = 1e30; best = (0, 0.0, (0.0,0.0))
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        c0x = 0.5*(outer[i][0] + inner[i][0]); c0y = 0.5*(outer[i][1] + inner[i][1])
        c1x = 0.5*(outer[j][0] + inner[j][0]); c1y = 0.5*(outer[j][1] + inner[j][1])
        vx, vy = (c1x - c0x, c1y - c0y)
        vv = vx*vx + vy*vy or 1.0
        wx, wy = (px - c0x, py - c0y)
        t = max(0.0, min(1.0, (wx*vx + wy*vy)/vv))
        cx, cy = (c0x + vx*t, c0y + vy*t)
        d2 = (px - cx)**2 + (py - cy)**2
        if d2 < best_d2:
            best_d2 = d2
            best = (i, t, (cx, cy))
    return best

def normalized_progress(seg, t, start_seg, nsegs, start_t=0.0):
    """Return progress in [0, nsegs) relative to (start_seg,start_t).
    Uses continuous parameter (seg + t) so wrap occurs exactly at the start fraction.
    """
    cur = (seg + t)
    start = (start_seg + start_t)
    
    rel = (cur - start) % nsegs
    return rel

def _step_back_center_param(outer, seg, t, back_len):
    """Move backward along the centerline by back_len units; return (seg,t)."""
    n = len(outer)
    cur_seg = seg % n
    cur_t = max(0.0, min(1.0, t))
    remain = max(0.0, back_len)
    while remain > 1e-6:
        seg_len = _segment_length(outer, cur_seg)
        dist_on_seg = cur_t * max(seg_len, 1e-6)
        if remain <= dist_on_seg:
            new_t = (dist_on_seg - remain) / max(seg_len, 1e-6)
            return cur_seg, max(0.0, min(1.0, new_t))
        else:
            remain -= dist_on_seg
            cur_seg = (cur_seg - 1) % n
            cur_t = 1.0
    return cur_seg, cur_t

def _step_forward_center_param(outer, seg, t, fwd_len):
    """Move forward along the centerline by fwd_len units; return (seg,t)."""
    n = len(outer)
    cur_seg = seg % n
    cur_t = max(0.0, min(1.0, t))
    remain = max(0.0, fwd_len)
    while remain > 1e-6:
        seg_len = _segment_length(outer, cur_seg)
        rest_on_seg = (1.0 - cur_t) * max(seg_len, 1e-6)
        if remain <= rest_on_seg:
            new_t = cur_t + remain / max(seg_len, 1e-6)
            return cur_seg, max(0.0, min(1.0, new_t))
        else:
            remain -= rest_on_seg
            cur_seg = (cur_seg + 1) % n
            cur_t = 0.0
    return cur_seg, cur_t

def update_laps_play():
    """Update lap counters for player and AIs; stop race at 2 laps.
    Skips the first wrap detection right after race start so the race doesn't begin at 1/2.
    """
    global prev_prog_player, player_lap, game_over, play_winner, lap_guard_player
    global prev_prog_ais, ai_laps, ignore_first_wrap_player, player_position
    if game_over:
        return
    outer, inner = get_track_polylines_for_map(current_map)
    nsegs = len(outer)

    # Current player progress along centerline
    p_seg, p_t, _ = closest_center_param(outer, inner, kart_pos[0], kart_pos[1])
    prog_p = normalized_progress(p_seg, p_t, start_seg_play, nsegs, start_t=start_t_play)

    # Compute finish gate signed distance along tangent and across-track distance
    fi, ft = get_finish_marker(current_map)
    (fx, fy), fang = get_center_and_tangent(outer, inner, fi, ft)
    urad = math.radians(fang)
    ux, uy = math.cos(urad), math.sin(urad)       # tangent (gate normal)
    nx, ny = -uy, ux                              # across-track axis
    # Track width at finish for gating
    jfi = (fi + 1) % len(outer)
    oA = (outer[fi][0]*(1-ft)+outer[jfi][0]*ft, outer[fi][1]*(1-ft)+outer[jfi][1]*ft)
    iA = (inner[fi][0]*(1-ft)+inner[jfi][0]*ft, inner[fi][1]*(1-ft)+inner[jfi][1]*ft)
    track_w = math.hypot(oA[0]-iA[0], oA[1]-iA[1])
    # Signed distances
    rx, ry = kart_pos[0] - fx, kart_pos[1] - fy
    finish_dot_cur = rx*ux + ry*uy      # along tangent; gate plane is 0
    across = abs(rx*nx + ry*ny)

    # Require a clear sign change with small epsilon and forward motion along the track
    # to avoid false triggers at spawn.
    CROSS_EPS = 5.0
    vel_fwd = math.cos(math.radians(kart_dir)) * ux + math.sin(math.radians(kart_dir)) * uy
    crossed_finish_gate = (
        globals().get('finish_dot_player_prev') is not None and
        vel_fwd > 0.2 and
        globals()['finish_dot_player_prev'] <= -CROSS_EPS and finish_dot_cur >= CROSS_EPS and
        across <= track_w * 0.75
    )

    wrapped = (prog_p + 0.5 < prev_prog_player)
    if lap_guard_player > 0.0:
        # During guard (e.g., after collision/respawn), only count a physical
        # finish gate crossing. Do not advance prev_prog while in guard.
        if crossed_finish_gate:
            if ignore_first_wrap_player:
                ignore_first_wrap_player = False
            else:
                player_lap += 1
    else:
        # First event (either wrap or gate) arms; subsequent events increment.
        if wrapped or crossed_finish_gate:
            if ignore_first_wrap_player:
                ignore_first_wrap_player = False
            else:
                player_lap += 1
    # Only advance prev progress when not in guard
    if lap_guard_player <= 0.0:
        prev_prog_player = prog_p
    globals()['finish_dot_player_prev'] = finish_dot_cur
    
    # AI lap updates (if any AIs are present)
    for idx, A in enumerate(ais):
        a_seg, a_t, _ = closest_center_param(outer, inner, A['pos'][0], A['pos'][1])
        prog_a = normalized_progress(a_seg, a_t, start_seg_play, nsegs, start_t=start_t_play)
        # Finish gate crossing for AI
        rax, ray = A['pos'][0] - fx, A['pos'][1] - fy
        ad = rax*ux + ray*uy
        a_across = abs(rax*nx + ray*ny)
        crossed_ai_gate = (
            idx < len(globals().get('finish_dot_ais_prev', [])) and
            globals()['finish_dot_ais_prev'][idx] is not None and
            globals()['finish_dot_ais_prev'][idx] <= -CROSS_EPS and ad >= CROSS_EPS and
            a_across <= track_w * 0.75
        )

        if A.get('lap_guard', 0.0) > 0.0:
            # Like player, only count physical crossing; don't advance prev prog
            if crossed_ai_gate:
                ai_laps[idx] += 1
        else:
            wrapped_ai = (prog_a + 0.5 < prev_prog_ais[idx])
            if wrapped_ai or crossed_ai_gate:
                ai_laps[idx] += 1
        # Only advance prev when not in guard
        if A.get('lap_guard', 0.0) <= 0.0:
            prev_prog_ais[idx] = prog_a
        # update AI gate cache
        if idx >= len(globals()['finish_dot_ais_prev']):
            globals()['finish_dot_ais_prev'].extend([None] * (idx - len(globals()['finish_dot_ais_prev']) + 1))
        globals()['finish_dot_ais_prev'][idx] = ad
    
    try:
        player_total = player_lap + (prog_p / max(1, nsegs))
        ahead = 0
        for idx, A in enumerate(ais):
            a_seg, a_t, _ = closest_center_param(outer, inner, A['pos'][0], A['pos'][1])
            prog_a2 = normalized_progress(a_seg, a_t, start_seg_play, nsegs, start_t=start_t_play)
            ai_total = ai_laps[idx] + (prog_a2 / max(1, nsegs))
            if ai_total > player_total + 1e-6:
                ahead += 1
        player_position = 1 + ahead
    except Exception:
        pass
    
    if player_lap >= 2 or any(l >= 2 for l in ai_laps):
        game_over = True
        if player_lap >= 2 and any(l >= 2 for l in ai_laps):
            play_winner = "Photo Finish!"
        elif player_lap >= 2:
            play_winner = "You Win!"
        else:
            play_winner = "Opponent Wins!"

def update_laps_compete():
    """Update lap counters and detect winner in compete mode.
    Skips the first wrap detection for both players so laps don't start at 1/2.
    """
    global prev_prog_p1, prev_prog_p2, p1_lap, p2_lap, compete_over, compete_winner
    global ignore_first_wrap_p1, ignore_first_wrap_p2
    if compete_over:
        return
    outer, inner = get_track_polylines_for_map(current_map)
    nsegs = len(outer)
    s1, t1, _ = closest_center_param(outer, inner, p1_pos[0], p1_pos[1])
    s2, t2, _ = closest_center_param(outer, inner, p2_pos[0], p2_pos[1])
    prog1 = normalized_progress(s1, t1, comp_start_seg, nsegs, start_t=comp_start_t)
    prog2 = normalized_progress(s2, t2, comp_start_seg, nsegs, start_t=comp_start_t)
    # Finish gate based detection (robust across polygonal maps)
    fi, ft = get_finish_marker(current_map)
    (fx, fy), fang = get_center_and_tangent(outer, inner, fi, ft)
    urad = math.radians(fang)
    ux, uy = math.cos(urad), math.sin(urad)
    nx, ny = -uy, ux
    jfi = (fi + 1) % len(outer)
    oA = (outer[fi][0]*(1-ft)+outer[jfi][0]*ft, outer[fi][1]*(1-ft)+outer[jfi][1]*ft)
    iA = (inner[fi][0]*(1-ft)+inner[jfi][0]*ft, inner[fi][1]*(1-ft)+inner[jfi][1]*ft)
    track_w = math.hypot(oA[0]-iA[0], oA[1]-iA[1])

    r1x, r1y = p1_pos[0] - fx, p1_pos[1] - fy
    r2x, r2y = p2_pos[0] - fx, p2_pos[1] - fy
    d1 = r1x*ux + r1y*uy
    d2 = r2x*ux + r2y*uy
    a1 = abs(r1x*nx + r1y*ny)
    a2 = abs(r2x*nx + r2y*ny)

    CROSS_EPS = 5.0
    # Require forward crossing along track direction to count
    v1_fwd = math.cos(math.radians(p1_dir)) * ux + math.sin(math.radians(p1_dir)) * uy
    v2_fwd = math.cos(math.radians(p2_dir)) * ux + math.sin(math.radians(p2_dir)) * uy
    crossed1 = (
        globals().get('finish_dot_p1_prev') is not None and v1_fwd > 0.2 and
        globals()['finish_dot_p1_prev'] <= -CROSS_EPS and d1 >= CROSS_EPS and a1 <= track_w * 0.75)
    crossed2 = (
        globals().get('finish_dot_p2_prev') is not None and v2_fwd > 0.2 and
        globals()['finish_dot_p2_prev'] <= -CROSS_EPS and d2 >= CROSS_EPS and a2 <= track_w * 0.75)

    wrapped1 = (prog1 + 0.5 < prev_prog_p1)
    wrapped2 = (prog2 + 0.5 < prev_prog_p2)

    if wrapped1 or crossed1:
        if ignore_first_wrap_p1:
            ignore_first_wrap_p1 = False
        else:
            p1_lap += 1
    if wrapped2 or crossed2:
        if ignore_first_wrap_p2:
            ignore_first_wrap_p2 = False
        else:
            p2_lap += 1
    prev_prog_p1 = prog1
    prev_prog_p2 = prog2
    globals()['finish_dot_p1_prev'] = d1
    globals()['finish_dot_p2_prev'] = d2
    if p1_lap >= 2 or p2_lap >= 2:
        compete_over = True
        if p1_lap >= 2 and p2_lap >= 2:
            compete_winner = "Draw!"
        elif p1_lap >= 2:
            compete_winner = "Player 1 Wins!"
        else:
            compete_winner = "Player 2 Wins!"


def update_kart(dt):
    global kart_speed, kart_dir, stun_timer, boost_timer, autopilot_timer, lap_guard_player
    global ai_enabled, player_slow_timer, boundary_hit_cooldown, collision_count
    
    if stun_timer > 0.0:
        stun_timer = max(0.0, stun_timer - dt)
        kart_speed = 0.0
        return

    

    
    slow_mult = 0.65 if player_slow_timer > 0.0 else 1.0
    if player_slow_timer > 0.0:
        player_slow_timer = max(0.0, player_slow_timer - dt)

    
    boost_mult = 1.0
    if boost_timer > 0.0:
        boost_mult = max(boost_mult, 1.6)
    if autopilot_timer > 0.0:
        boost_mult = max(boost_mult, 1.15)
    
    if 'orb_boost_timer_play' in globals() and orb_boost_timer_play > 0.0:
        boost_mult = max(boost_mult, 2.3)

    a = 0.0
    if autopilot_timer > 0.0:
        
        a += kart_accel
    else:
        if b'w' in keys_down: a += kart_accel
        if b's' in keys_down: a -= kart_brake
    kart_speed += a * dt
    kart_speed = min(kart_speed, kart_max_speed * boost_mult * slow_mult)
    kart_speed = max(kart_speed, -kart_max_speed*0.4)

    
    if kart_speed > 0:
        kart_speed -= 120.0 * dt
        if kart_speed < 0: kart_speed = 0.0
    elif kart_speed < 0:
        kart_speed += 120.0 * dt
        if kart_speed > 0: kart_speed = 0.0

    
    if autopilot_timer > 0.0:
        outer, inner = get_track_polylines_for_map(current_map)
        seg, t, (cx, cy) = closest_center_param(outer, inner, kart_pos[0], kart_pos[1])
        
        (_, cur_ang) = get_center_and_tangent(outer, inner, seg, t)
        
        ahead_len = max(120.0, min(420.0, 180.0 + kart_speed * 0.20))
        if current_map == 3:
            ahead_len *= 0.85
        segA, tA = _step_forward_center_param(outer, seg, t, ahead_len)
        (ax, ay), ang = get_center_and_tangent(outer, inner, segA, tA)
        
        corner = abs(((ang - cur_ang + 540.0) % 360.0) - 180.0)
        if corner > 25.0:
            ahead_len = max(90.0, ahead_len * 0.55)
            segA, tA = _step_forward_center_param(outer, seg, t, ahead_len)
            (ax, ay), ang = get_center_and_tangent(outer, inner, segA, tA)
        
        desired_side = 0.0
        if ai_enabled and ais:
            best = 1e18
            for A in ais:
                dx = ax - A['pos'][0]; dy = ay - A['pos'][1]
                d2 = dx*dx + dy*dy
                if d2 < best:
                    best = d2
            if best < (160.0*160.0):
                desired_side = autopilot_side  
        j = (segA + 1) % len(outer)
        tx = outer[j][0] - outer[segA][0]; ty = outer[j][1] - outer[segA][1]
        L  = math.hypot(tx, ty) or 1.0
        nx, ny = (-ty / L, tx / L)
        
        def _mix(a, b, s):
            return (a[0]*(1-s)+b[0]*s, a[1]*(1-s)+b[1]*s)
        oA = _mix(outer[segA], outer[j], tA)
        iA = _mix(inner[segA], inner[j], tA)
        track_w = math.hypot(oA[0]-iA[0], oA[1]-iA[1])
        half_w = 0.5 * track_w
        safety = 18.0 if current_map != 3 else 22.0
        lane_limit = max(10.0, half_w - safety)
        lane = desired_side * min((12.0 if current_map == 3 else 18.0), lane_limit)  
        target_x = ax + nx * lane
        target_y = ay + ny * lane
        desired = math.degrees(math.atan2(target_y - kart_pos[1], target_x - kart_pos[0]))
        
        speed_factor = max(0.35, kart_speed/max(kart_max_speed,1.0))
        base_turn = 3.6 if current_map != 3 else 3.9
        turn_speed = base_turn * speed_factor * 60.0 * dt
        
        diff = (desired - kart_dir + 540.0) % 360.0 - 180.0
        if diff > 0: kart_dir += min(diff, turn_speed)
        else:        kart_dir += max(diff, -turn_speed)
        
        base_cap = kart_max_speed * boost_mult * slow_mult
        sharp = abs(diff)
        if current_map == 3:
            if corner > 40.0:
                base_cap *= 0.55
            elif corner > 25.0:
                base_cap *= 0.75
        if sharp > 45.0:
            base_cap *= 0.55
        elif sharp > 30.0:
            base_cap *= 0.75
        elif sharp > 20.0:
            base_cap *= 0.90
        if kart_speed > base_cap:
            
            kart_speed = max(base_cap, kart_speed - kart_brake * 0.7 * dt)
    else:
        
        if b'a' in keys_down:
            kart_dir += 3.0 * (kart_speed/max(kart_max_speed,1.0)) * 60.0 * dt
        if b'd' in keys_down:
            kart_dir -= 3.0 * (kart_speed/max(kart_max_speed,1.0)) * 60.0 * dt

    dx = math.cos(math.radians(kart_dir)) * kart_speed * dt
    dy = math.sin(math.radians(kart_dir)) * kart_speed * dt
    oldx, oldy = kart_pos[0], kart_pos[1]
    kart_pos[0] += dx; kart_pos[1] += dy

    outer, inner = get_track_polylines_for_map(current_map)
    if not point_in_ring(kart_pos[0], kart_pos[1], outer, inner):
        if autopilot_timer > 0.0:
            
            segc, tc, (ccx, ccy) = closest_center_param(outer, inner, kart_pos[0], kart_pos[1])
            j = (segc + 1) % len(outer)
            tx = outer[j][0] - outer[segc][0]; ty = outer[j][1] - outer[segc][1]
            L = math.hypot(tx, ty) or 1.0
            nx, ny = (-ty/L, tx/L)
            
            lane = (kart_pos[0]-ccx)*nx + (kart_pos[1]-ccy)*ny
            lane = max(-16.0, min(16.0, lane))
            kart_pos[0], kart_pos[1] = ccx + nx*lane, ccy + ny*lane
            kart_speed *= 0.35
            
            (_, _ang) = get_center_and_tangent(outer, inner, segc, tc)
            kart_dir = _ang
        else:
            kart_pos[0], kart_pos[1] = oldx, oldy
            kart_speed *= 0.2
            if boundary_hit_cooldown <= 0.0:
                collision_count += 1
                boundary_hit_cooldown = 0.5
                
                stun_timer = max(stun_timer, 0.3)
    
    if boost_timer > 0.0: boost_timer = max(0.0, boost_timer - dt)
    if autopilot_timer > 0.0: autopilot_timer = max(0.0, autopilot_timer - dt)
    if 'orb_boost_timer_play' in globals() and orb_boost_timer_play > 0.0:
        globals()['orb_boost_timer_play'] = max(0.0, orb_boost_timer_play - dt)
    if lap_guard_player > 0.0:
        lap_guard_player = max(0.0, lap_guard_player - dt)

def update_ais(dt):
    if not ai_enabled or not ais:
        return
    outer, inner = get_track_polylines_for_map(current_map)
    for A in ais:
        
        if A['pause_timer'] > 0.0:
            A['pause_timer'] = max(0.0, A['pause_timer'] - dt)
        if A.get('stop_timer', 0.0) > 0.0:
            A['stop_timer'] = max(0.0, A['stop_timer'] - dt)
        if A.get('lap_guard', 0.0) > 0.0:
            A['lap_guard'] = max(0.0, A['lap_guard'] - dt)
        seg_len = _segment_length(outer, A['seg'])
        slow_mult = 0.75 if A.get('slow_timer',0.0) > 0.0 else 1.0
        if A.get('slow_timer',0.0) > 0.0:
            A['slow_timer'] = max(0.0, A['slow_timer'] - dt)
        pause_mult = 0.15 if A['pause_timer'] > 0.0 else 1.0
        
        move_mult = 0.0 if A.get('stop_timer', 0.0) > 0.0 else pause_mult
        dt_frac = (A['speed'] * slow_mult * move_mult * dt) / max(seg_len, 1e-6)
        A['t'] += dt_frac
        while A['t'] >= 1.0:
            A['t'] -= 1.0
            A['seg'] = (A['seg'] + 1) % len(outer)
        (cx, cy), ang = get_center_and_tangent(outer, inner, A['seg'], A['t'])
        j = (A['seg'] + 1) % len(outer)
        dx = outer[j][0] - outer[A['seg']][0]; dy = outer[j][1] - outer[A['seg']][1]
        L  = math.hypot(dx, dy) or 1.0
        nx, ny = (-dy / L, dx / L)
        
        look_x, look_y = cx + (outer[j][0]-outer[A['seg']][0])*0.1, cy + (outer[j][1]-outer[A['seg']][1])*0.1
        best = 1e9; sign = 1.0
        for ob in obstacles:
            if not ob.get('active', True): continue
            odx = ob['x'] - look_x; ody = ob['y'] - look_y
            d2 = odx*odx + ody*ody
            if d2 < best:
                best = d2
                side = odx*nx + ody*ny
                sign = -1.0 if side > 0 else 1.0
        
        target_lane = A.get('lane', 26.0) * sign
        A['lane'] += (target_lane - A['lane']) * min(1.0, 2.0 * dt)
        A['pos'][0], A['pos'][1], A['pos'][2] = cx + nx * A['lane'], cy + ny * A['lane'], 0.0
        A['dir'] = ang

def check_player_ai_collisions():
    global stun_timer, collision_count, kart_speed
    
    if autopilot_timer > 0.0:
        return
    if not ai_enabled or not race_started or not ais: return
    outer, inner = get_track_polylines_for_map(current_map)
    for A in ais:
        dx = kart_pos[0] - A['pos'][0]; dy = kart_pos[1] - A['pos'][1]
        sum_r = kart_collision_radius * 2
        if dx*dx + dy*dy <= sum_r*sum_r:
            
            d = math.hypot(dx, dy) or 1.0
            nx, ny = dx/d, dy/d
            push = (sum_r - d) * 0.5
            kart_pos[0] += nx * push; kart_pos[1] += ny * push
            
            p_seg, p_t, _ = closest_center_param(outer, inner, kart_pos[0], kart_pos[1])
            a_seg, a_t, _ = closest_center_param(outer, inner, A['pos'][0], A['pos'][1])
            nsegs = len(outer)
            prog_p = normalized_progress(p_seg, p_t, p_seg, nsegs, start_t=p_t)
            prog_a = normalized_progress(a_seg, a_t, p_seg, nsegs, start_t=p_t)
            if prog_a < prog_p - 1e-6:
                
                fwdx, fwdy = math.cos(math.radians(kart_dir)), math.sin(math.radians(kart_dir))
                vax, vay = A['pos'][0] - kart_pos[0], A['pos'][1] - kart_pos[1]
                if (fwdx * vax + fwdy * vay) < 0.0:
                    A['stop_timer'] = max(A.get('stop_timer', 0.0), stun_duration_on_bump)
                else:
                    A['pause_timer'] = max(A.get('pause_timer', 0.0), stun_duration_on_bump * 0.5)
                
                back = 180.0
                new_seg, new_t = _step_back_center_param(outer, a_seg, a_t, back)
                (cx, cy), ang = get_center_and_tangent(outer, inner, new_seg, new_t)
                j = (new_seg + 1) % len(outer)
                ddx = outer[j][0] - outer[new_seg][0]; ddy = outer[j][1] - outer[new_seg][1]
                LL = math.hypot(ddx, ddy) or 1.0
                nnx, nny = (-ddy/LL, ddx/LL)
                lane = A.get('lane', 0.0)
                A['seg'], A['t'] = new_seg, new_t
                A['pos'][0], A['pos'][1], A['pos'][2] = cx + nnx*lane, cy + nny*lane, 0.0
                A['dir'] = ang
                A['lap_guard'] = 2.0
            elif prog_p < prog_a - 1e-6:
                stun_timer = max(stun_timer, stun_duration_on_bump)
                kart_speed = 0.0
                
                back = 180.0
                
                (ccx, ccy) = closest_center_param(outer, inner, kart_pos[0], kart_pos[1])[2]
                jj = (p_seg + 1) % len(outer)
                ddx = outer[jj][0] - outer[p_seg][0]; ddy = outer[jj][1] - outer[p_seg][1]
                LL = math.hypot(ddx, ddy) or 1.0
                nnx, nny = (-ddy/LL, ddx/LL)
                lane = (kart_pos[0] - ccx)*nnx + (kart_pos[1] - ccy)*nny
                new_seg, new_t = _step_back_center_param(outer, p_seg, p_t, back)
                (cx, cy), ang = get_center_and_tangent(outer, inner, new_seg, new_t)
                kart_pos[0], kart_pos[1] = cx + nnx*lane, cy + nny*lane
                globals()['kart_dir'] = ang
                globals()['kart_speed'] = 0.0
                globals()['lap_guard_player'] = 2.0
            else:
                A['pause_timer'] = max(A.get('pause_timer',0.0), 0.3)
                stun_timer = max(stun_timer, 0.3)
            collision_count += 1

def build_obstacles_for_map(m, count=12):
    global obstacles
    random.seed(42)
    obstacles = []
    outer, inner = get_track_polylines_for_map(m)
    n = len(outer)
    
    fi, ft = get_finish_marker(m)
    (sx, sy), _ = get_center_and_tangent(outer, inner, fi, ft)
    
    avoid_window = min(6, max(1, n // 12))
    
    finish_exclusion_r = 800.0
    r2 = finish_exclusion_r * finish_exclusion_r
    for _ in range(count):
        tries = 0
        while True:
            i = random.randrange(0, n)
            j = (i + 1) % n
            
            close_seg = ((i - fi) % n <= avoid_window) or ((fi - i) % n <= avoid_window)
            
            t = random.uniform(0.2, 0.8)
            cx = 0.5*(outer[i][0]*(1-t)+outer[j][0]*t + inner[i][0]*(1-t)+inner[j][0]*t)
            cy = 0.5*(outer[i][1]*(1-t)+outer[j][1]*t + inner[i][1]*(1-t)+inner[j][1]*t)
            nx, ny = _seg_normal(outer[i], outer[j])
            off = random.uniform(-18.0, 18.0)
            ox, oy = cx + nx*off, cy + ny*off
            close_finish = (ox - sx)*(ox - sx) + (oy - sy)*(oy - sy) < r2
            if not (close_seg or close_finish):
                obstacles.append({"x": ox, "y": oy, "r": 16.0, "active": True, "respawn": 0.0})
                break
            tries += 1
            if tries > 200:
                
                best_d2 = -1.0; best = None
                for _ in range(20):
                    ii = random.randrange(0, n); jj = (ii + 1) % n
                    tt = random.uniform(0.2, 0.8)
                    ccx = 0.5*(outer[ii][0]*(1-tt)+outer[jj][0]*tt + inner[ii][0]*(1-tt)+inner[jj][0]*tt)
                    ccy = 0.5*(outer[ii][1]*(1-tt)+outer[jj][1]*tt + inner[ii][1]*(1-tt)+inner[jj][1]*tt)
                    nnx, nny = _seg_normal(outer[ii], outer[jj])
                    ooff = random.uniform(-18.0, 18.0)
                    px, py = ccx + nnx*ooff, ccy + nny*ooff
                    d2 = (px - sx)*(px - sx) + (py - sy)*(py - sy)
                    if d2 > best_d2 and ((ii - fi) % n > avoid_window and (fi - ii) % n > avoid_window):
                        best_d2 = d2; best = (px, py)
                if best is None:
                    best = (ox, oy)
                obstacles.append({"x": best[0], "y": best[1], "r": 16.0, "active": True, "respawn": 0.0})
                break

def draw_obstacles():
    for ob in obstacles:
        if ob.get('active', True):
            draw_rock(ob['x'], ob['y'], s=0.9)

def build_blue_orbs_for_map(m, count=10):
    global blue_orbs
    blue_orbs = []
    outer, inner = get_track_polylines_for_map(m)
    n = len(outer)
    for _ in range(count):
        i = random.randrange(0, n); j = (i + 1) % n
        t = random.uniform(0.05, 0.95)
        cx = 0.5*(outer[i][0]*(1-t)+outer[j][0]*t + inner[i][0]*(1-t)+inner[j][0]*t)
        cy = 0.5*(outer[i][1]*(1-t)+outer[j][1]*t + inner[i][1]*(1-t)+inner[j][1]*t)
        nx, ny = _seg_normal(outer[i], outer[j])
        lane = random.uniform(-22.0, 22.0)
        blue_orbs.append({"x": cx + nx*lane, "y": cy + ny*lane, "active": True, "respawn": 0.0})

def update_blue_orbs(dt):
    for orb in blue_orbs:
        if not orb['active']:
            orb['respawn'] -= dt
            if orb['respawn'] <= 0.0:
                
                outer, inner = get_track_polylines_for_map(current_map)
                n = len(outer)
                i = random.randrange(0, n); j = (i + 1) % n
                t = random.uniform(0.05, 0.95)
                cx = 0.5*(outer[i][0]*(1-t)+outer[j][0]*t + inner[i][0]*(1-t)+inner[j][0]*t)
                cy = 0.5*(outer[i][1]*(1-t)+outer[j][1]*t + inner[i][1]*(1-t)+inner[j][1]*t)
                nx, ny = _seg_normal(outer[i], outer[j])
                lane = random.uniform(-22.0, 22.0)
                orb['x'], orb['y'] = cx + nx*lane, cy + ny*lane
                orb['active'] = True

def draw_blue_orbs():
    for orb in blue_orbs:
        if orb['active']:
            glPushMatrix()
            glTranslatef(orb['x'], orb['y'], 8.0)
            glColor3f(0.2, 0.5, 1.0)
            gluSphere(q_sph, 6.0, 12, 10)
            glPopMatrix()

def check_orb_pickups_play():
    for orb in blue_orbs:
        if not orb['active']: continue
        dx = kart_pos[0] - orb['x']; dy = kart_pos[1] - orb['y']
        if dx*dx + dy*dy <= (24.0*24.0):
            orb['active'] = False
            orb['respawn'] = random.uniform(4.0, 9.0)
            
            globals()['orb_boost_timer_play'] = max(globals().get('orb_boost_timer_play', 0.0), 4.0)

def check_orb_pickups_compete():
    for orb in blue_orbs:
        if not orb['active']: continue
        
        dx = p1_pos[0] - orb['x']; dy = p1_pos[1] - orb['y']
        if dx*dx + dy*dy <= (24.0*24.0):
            orb['active'] = False; orb['respawn'] = random.uniform(4.0, 9.0)
            globals()['p1_orb_boost_timer'] = max(globals().get('p1_orb_boost_timer', 0.0), 4.0)
            continue
        
        dx = p2_pos[0] - orb['x']; dy = p2_pos[1] - orb['y']
        if dx*dx + dy*dy <= (24.0*24.0):
            orb['active'] = False; orb['respawn'] = random.uniform(4.0, 9.0)
            globals()['p2_orb_boost_timer'] = max(globals().get('p2_orb_boost_timer', 0.0), 4.0)

def check_obstacle_collisions_play():
    global kart_speed, collision_count, boundary_hit_cooldown, stun_timer
    
    
    if autopilot_timer <= 0.0:
        for ob in obstacles:
            if not ob.get('active', True): continue
            dx = kart_pos[0] - ob['x']; dy = kart_pos[1] - ob['y']
            rr = (ob['r'] + kart_collision_radius)
            d2 = dx*dx + dy*dy
            if d2 <= rr*rr:
                
                d = math.hypot(dx, dy) or 1.0
                nx, ny = dx/d, dy/d
                push = (rr + 2.0) - d
                if push > 0:
                    kart_pos[0] += nx * push
                    kart_pos[1] += ny * push
                kart_speed = 0.0
                stun_timer = max(stun_timer, 0.3)
                if boundary_hit_cooldown <= 0.0:
                    collision_count += 1
                    boundary_hit_cooldown = 0.5
                
                ob['active'] = False
                ob['respawn'] = random.uniform(1.0, 3.0)
    
    for A in ais:
        for ob in obstacles:
            if not ob.get('active', True): continue
            dx = A['pos'][0] - ob['x']; dy = A['pos'][1] - ob['y']
            rr = (ob['r'] + kart_collision_radius)
            d2 = dx*dx + dy*dy
            if d2 <= rr*rr:
                d = math.hypot(dx, dy) or 1.0
                nx, ny = dx/d, dy/d
                push = (rr + 2.0) - d
                if push > 0:
                    A['pos'][0] += nx * push
                    A['pos'][1] += ny * push
                A['pause_timer'] = max(A.get('pause_timer',0.0), 0.3)
                
                ob['active'] = False
                ob['respawn'] = random.uniform(1.0, 3.0)

def update_obstacle_respawn(dt):
    for ob in obstacles:
        if not ob['active']:
            ob['respawn'] -= dt
            if ob['respawn'] <= 0.0:
                ob['active'] = True

def enforce_collision_and_lives():
    global collision_count, lives, race_started, game_over
    if game_over: return
    if collision_count >= max_collisions_before_life_loss:
        lives = max(0, lives - 1)
        collision_count = 0
        race_started = False
    if lives <= 0:
        game_over = True

def check_obstacle_collisions_compete():
    """Per-player obstacle collisions for compete mode."""
    global p1_speed, p2_speed, p1_stun, p2_stun, p1_collision_count, p2_collision_count, p1_hit_cd, p2_hit_cd
    for ob in obstacles:
        if not ob.get('active', True):
            continue
        
        dx = p1_pos[0] - ob['x']; dy = p1_pos[1] - ob['y']
        rr = (ob['r'] + kart_collision_radius)
        d2 = dx*dx + dy*dy
        if d2 <= rr*rr:
            d = math.hypot(dx, dy) or 1.0
            nx, ny = dx/d, dy/d
            push = (rr + 2.0) - d
            if push > 0:
                p1_pos[0] += nx * push; p1_pos[1] += ny * push
            p1_speed = 0.0
            p1_stun = max(p1_stun, 0.3)
            if p1_hit_cd <= 0.0:
                p1_collision_count += 1; p1_hit_cd = 0.5
        
        dx2 = p2_pos[0] - ob['x']; dy2 = p2_pos[1] - ob['y']
        d22 = dx2*dx2 + dy2*dy2
        if d22 <= rr*rr:
            d = math.hypot(dx2, dy2) or 1.0
            nx, ny = dx2/d, dy2/d
            push = (rr + 2.0) - d
            if push > 0:
                p2_pos[0] += nx * push; p2_pos[1] += ny * push
            p2_speed = 0.0
            p2_stun = max(p2_stun, 0.3)
            if p2_hit_cd <= 0.0:
                p2_collision_count += 1; p2_hit_cd = 0.5

def enforce_compete_lives():
    """Apply life loss on too many collisions and reset players to track.""" 
    global p1_collision_count, p2_collision_count, p1_lives, p2_lives
    if p1_collision_count >= max_collisions_before_life_loss:
        p1_lives = max(0, p1_lives - 1)
        p1_collision_count = 0
        reset_p1_to_track()
    if p2_collision_count >= max_collisions_before_life_loss:
        p2_lives = max(0, p2_lives - 1)
        p2_collision_count = 0
        reset_p2_to_track()

def reset_p1_to_track():
    outer, inner = get_track_polylines_for_map(current_map)
    seg, t, (cx, cy) = closest_center_param(outer, inner, p1_pos[0], p1_pos[1])
    (tx, ty), ang = get_center_and_tangent(outer, inner, seg, t)
    j = (seg + 1) % len(outer)
    dx = outer[j][0] - outer[seg][0]; dy = outer[j][1] - outer[seg][1]
    L  = math.hypot(dx, dy) or 1.0
    nx, ny = (-dy / L, dx / L)
    lane = 26.0
    p1_pos[0], p1_pos[1], p1_pos[2] = cx + nx*lane, cy + ny*lane, 0.0
    global p1_dir, p1_speed, p1_stun
    p1_dir = ang; p1_speed = 0.0; p1_stun = 0.0

def reset_p2_to_track():
    outer, inner = get_track_polylines_for_map(current_map)
    seg, t, (cx, cy) = closest_center_param(outer, inner, p2_pos[0], p2_pos[1])
    (tx, ty), ang = get_center_and_tangent(outer, inner, seg, t)
    j = (seg + 1) % len(outer)
    dx = outer[j][0] - outer[seg][0]; dy = outer[j][1] - outer[seg][1]
    L  = math.hypot(dx, dy) or 1.0
    nx, ny = (-dy / L, dx / L)
    lane = 26.0
    p2_pos[0], p2_pos[1], p2_pos[2] = cx - nx*lane, cy - ny*lane, 0.0
    global p2_dir, p2_speed, p2_stun
    p2_dir = ang; p2_speed = 0.0; p2_stun = 0.0

def build_coins_for_map(m):
    global coins, coins_collected, coin_spin, coin_bob_t
    coins_collected = 0; coin_spin = 0.0; coin_bob_t = 0.0
    coins = []
    outer, inner = get_track_polylines_for_map(m)
    n = random.randint(10, 15)
    def _poly_bounds(poly):
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        return min(xs), max(xs), min(ys), max(ys)
    def _rand_point_in_poly(poly):
        minx, maxx, miny, maxy = _poly_bounds(poly)
        for _ in range(2000):
            x = random.uniform(minx, maxx); y = random.uniform(miny, maxy)
            if point_in_poly(x, y, poly): return (x, y)
        cx = sum(p[0] for p in poly)/len(poly); cy = sum(p[1] for p in poly)/len(poly); return cx, cy
    for _ in range(n):
        x, y = _rand_point_in_poly(inner)
        coins.append({"x": x, "y": y, "active": True, "timer": 0.0})

def update_coins(dt):
    global coin_spin, coin_bob_t, coins_collected, explore_timer_active, explore_timer
    coin_spin = (coin_spin + 60.0 * dt) % 360.0
    coin_bob_t += dt
    for c in coins:
        if c["active"]:
            dx = explore_pos[0] - c["x"]; dy = explore_pos[1] - c["y"]
            if dx*dx + dy*dy <= (24.0*24.0):
                c["active"] = False
                c["timer"] = random.uniform(3.0, 7.0)
                coins_collected += 1
                
                if not explore_timer_active:
                    explore_timer_active = True
                    explore_timer = 10.0
                else:
                    explore_timer += 5.0
        else:
            c["timer"] -= dt
            if c["timer"] <= 0.0:
                c["active"] = True

def draw_coin_at(x, y):
    h = 6.0 + 2.0 * math.sin(coin_bob_t * 2.0)
    glPushMatrix()
    glTranslatef(x, y, h)
    glRotatef(coin_spin, 0, 0, 1)
    glColor3f(0.95, 0.80, 0.22)  
    gluCylinder(q_cyl, 10.0, 10.0, 2.0, 24, 1)
    glPopMatrix()

def draw_coins():
    for c in coins:
        if c["active"]:
            draw_coin_at(c["x"], c["y"])
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
