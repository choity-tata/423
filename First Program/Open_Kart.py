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
