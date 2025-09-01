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
