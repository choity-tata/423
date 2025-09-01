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
