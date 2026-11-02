# -*- coding: utf-8 -*-
"""
SLENDERMAN: ESCAPE DEL BOSQUE
Adaptación Kivy para Android. No necesita imágenes ni archivos externos.
Controles: joystick táctil izquierdo; CORRER, LUZ y ESCAPAR a la derecha.
"""
import math
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.core.window import Window


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class ForestGame(Widget):
    WORLD_W, WORLD_H = 2200, 2400
    LAKE = (1510, 1570, 620, 560)
    DOCK = (1430, 1760, 300, 78)
    BOAT = (1650, 1773, 78, 40)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = "menu"
        self.volume = 0.55
        self.options = False
        self.touch_roles = {}
        self.joy_uid = None
        self.joy_origin = None
        self.move_vector = [0.0, 0.0]
        self.running_touch = False
        self.last_size = (0, 0)
        random.seed(18)
        self.trees, self.rocks, self.bushes, self.fog = [], [], [], []
        self.make_world()
        self.new_game()
        self.bind(size=self.redraw, pos=self.redraw)
        Clock.schedule_interval(self.update, 1 / 60)

    def make_world(self):
        for _ in range(210):
            x, y = random.randint(50, self.WORLD_W - 50), random.randint(50, self.WORLD_H - 50)
            if self.in_rect(x, y, self.LAKE, 60) or self.in_rect(x, y, self.DOCK, 40):
                continue
            self.trees.append((x, y, random.randint(20, 34)))
        for _ in range(60):
            x, y = random.randint(40, self.WORLD_W - 40), random.randint(40, self.WORLD_H - 40)
            if not self.in_rect(x, y, self.LAKE, 30):
                self.rocks.append((x, y, random.randint(10, 20)))
        for _ in range(100):
            self.bushes.append((random.randint(30, self.WORLD_W - 30),
                                random.randint(30, self.WORLD_H - 30), random.randint(8, 16)))
        for _ in range(22):
            self.fog.append((random.randint(0, self.WORLD_W), random.randint(0, self.WORLD_H),
                             random.randint(90, 190)))

    @staticmethod
    def in_rect(x, y, rect, pad=0):
        rx, ry, rw, rh = rect
        return rx - pad <= x <= rx + rw + pad and ry - pad <= y <= ry + rh + pad

    def new_game(self):
        self.player = [280.0, 260.0]
        self.stamina = self.battery = 1.0
        self.flashlight = True
        self.slender = [1000.0, 950.0]
        self.slender_state = "hidden"
        self.state_timer = random.uniform(7, 12)
        self.visible_timer = 0
        self.message = "Encuentra el muelle. No dejes que te encuentre."
        self.message_timer = 5
        self.dock_found = False
        self.scare = 0
        self.game_state = "playing"
        self.escape_timer = 0
        self.near_sound_timer = 0
        self.move_vector = [0.0, 0.0]
        self.running_touch = False
        self.joy_uid = None
        self.joy_origin = None
        self.touch_roles.clear()

    def blocked(self, x, y):
        if x < 13 or y < 13 or x > self.WORLD_W - 13 or y > self.WORLD_H - 13:
            return True
        if self.in_rect(x, y, self.LAKE) and not self.in_rect(x, y, self.DOCK, 12) and not self.in_rect(x, y, self.BOAT, 18):
            return True
        for tx, ty, r in self.trees:
            if (x-tx)**2 + (y-ty)**2 < (r*.78+13)**2:
                return True
        for rx, ry, r in self.rocks:
            if (x-rx)**2 + (y-ry)**2 < (r+9)**2:
                return True
        return False

    def move_player(self, dx, dy):
        nx = self.player[0] + dx
        if not self.blocked(nx, self.player[1]):
            self.player[0] = nx
        ny = self.player[1] + dy
        if not self.blocked(self.player[0], ny):
            self.player[1] = ny

    def update(self, dt):
        dt = min(dt, .04)
        if self.state != "playing":
            self.redraw()
            return
        p, s = self.player, self.slender
        mx, my = self.move_vector
        if distance((0, 0), (mx, my)) > 1:
            ln = math.hypot(mx, my)
            mx, my = mx/ln, my/ln
        moving = abs(mx) + abs(my) > .05
        running = self.running_touch and moving and self.stamina > .03
        speed = 225 if running else 130
        if running:
            self.stamina = max(0, self.stamina - dt*.23)
        else:
            self.stamina = min(1, self.stamina + dt*.13)
        if moving:
            self.move_player(mx*speed*dt, my*speed*dt)
        if self.flashlight and self.battery > 0:
            self.battery = max(0, self.battery - dt*.006)
        if self.battery <= 0:
            self.flashlight = False

        if not self.dock_found and distance(p, (self.DOCK[0]+self.DOCK[2]/2, self.DOCK[1]+self.DOCK[3]/2)) < 190:
            self.dock_found = True
            self.message = "Has encontrado el muelle... algo te ha seguido"
            self.message_timer = 5
            self.state_timer = 1.5
        if self.message_timer > 0:
            self.message_timer -= dt
        else:
            self.message = ""

        d = distance(p, s)
        self.state_timer -= dt
        if self.slender_state == "hidden":
            if self.state_timer <= 0:
                for _ in range(30):
                    angle = random.uniform(0, math.tau)
                    radius = random.uniform(280, 470)
                    nx, ny = p[0]+math.cos(angle)*radius, p[1]+math.sin(angle)*radius
                    if 50 < nx < self.WORLD_W-50 and 50 < ny < self.WORLD_H-50 and not self.blocked(nx, ny):
                        s[0], s[1] = nx, ny
                        break
                self.slender_state = "watching"
                self.visible_timer = self.state_timer = random.uniform(2, 4)
                self.scare = .45
        elif self.slender_state == "watching":
            self.visible_timer -= dt
            if d < 360:
                self.slender_state = "stalking"
                self.state_timer = 0
            elif self.visible_timer <= 0:
                self.slender_state = "vanishing"
                self.state_timer = .7
        elif self.slender_state == "vanishing":
            if self.state_timer <= 0:
                self.slender_state = "hidden"
                self.state_timer = random.uniform(5, 9)
        elif self.slender_state in ("stalking", "chasing"):
            aggressive = self.dock_found
            if d < 245 or (aggressive and d < 390):
                self.slender_state = "chasing"
            elif d > 510 and not aggressive:
                self.slender_state = "stalking"
            ln = max(1, d)
            enemy_speed = 105 + (35 if running else 0) + (45 if aggressive else 0)
            if self.slender_state == "chasing":
                s[0] += (p[0]-s[0])/ln*enemy_speed*dt
                s[1] += (p[1]-s[1])/ln*enemy_speed*dt
                self.scare = max(self.scare, .12)
            else:
                s[0] += (p[0]-s[0])/ln*38*dt
                s[1] += (p[1]-s[1])/ln*38*dt
            if d < 33:
                self.state = "gameover"
        self.scare = max(0, self.scare-dt)
        if self.game_state == "escaping":
            self.escape_timer += dt
            if self.escape_timer > 3.8:
                self.state = "win"
        self.redraw()

    def screen_point(self, x, y, camx, camy):
        return x-camx, self.height-(y-camy)

    def draw_text(self, text, x, y, size=18, color=(.9, .9, .86, 1), center=True):
        label = CoreLabel(text=text, font_size=dp(size), color=color)
        label.refresh()
        tex = label.texture
        if center:
            x -= tex.size[0]/2
        Rectangle(texture=tex, pos=(x, y-tex.size[1]/2), size=tex.size)

    def rect_top(self, x, y, w, h, camx, camy):
        return (x-camx, self.height-(y-camy)-h, w, h)

    def rounded_button(self, x, y, w, h, text):
        # x,y are top-left coordinates
        Rectangle  # keep Kivy graphics imports available
        with self.canvas:
            pass
        self.draw_button(x, y, w, h, text)

    def draw_button(self, x, y, w, h, text):
        pos = (x, self.height-y-h)
        with self.canvas:
            Color(.12, .17, .18, .88)
            RoundedRectangle(pos=pos, size=(w, h), radius=[dp(12)])
            Color(.55, .62, .61, .85)
            Line(rounded_rectangle=(pos[0], pos[1], w, h, dp(12)), width=1.2)
        self.draw_text(text, x+w/2, self.height-y-h/2, 15)

    def redraw(self, *args):
        if self.width <= 1 or self.height <= 1:
            return
        self.canvas.clear()
        w, h = self.width, self.height
        with self.canvas:
            Color(.015, .035, .035, 1)
            Rectangle(pos=self.pos, size=self.size)
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "gameover":
            self.draw_end(False)
        elif self.state == "win":
            self.draw_end(True)

    def draw_menu(self):
        w, h = self.width, self.height
        with self.canvas:
            Color(.015, .03, .045, 1)
            Rectangle(pos=self.pos, size=self.size)
            for i in range(12):
                x = i*w/11
                Color(.025, .075, .065, 1)
                Ellipse(pos=(x-dp(35), h*.36), size=(dp(90), dp(150)))
                Color(.035, .06, .055, 1)
                Rectangle(pos=(x-dp(8), h*.16), size=(dp(20), h*.32))
        self.draw_text("SLENDERMAN:", w/2, h*.88, 30, (.86,.88,.84,1))
        self.draw_text("ESCAPE DEL BOSQUE", w/2, h*.81, 20, (.65,.72,.68,1))
        bw, bh = w*.62, max(dp(48), h*.075)
        x, y = (w-bw)/2, h*.52
        for i, title in enumerate(("JUGAR", "OPCIONES", "VOLUMEN: "+("MUDO" if self.volume == 0 else "ACTIVO"), "SALIR")):
            self.draw_button(x, y-i*(bh+dp(12)), bw, bh, title)
        self.draw_text("Muévete • Corre • Encuentra el barco", w/2, h*.06, 13, (.6,.66,.62,1))
        if self.options:
            self.draw_text("Volumen activado o silenciado desde el menú", w/2, h*.12, 12)

    def draw_slender(self, sx, sy, scale=1):
        # Coordenadas ya convertidas a pantalla (origen superior)
        with self.canvas:
            Color(.015, .015, .02, 1)
            Ellipse(pos=(sx-dp(15*scale), self.height-sy-dp(56*scale)), size=(dp(30*scale), dp(7*scale)))
            Color(.025, .025, .035, 1)
            Line(points=[sx, self.height-sy, sx, self.height-sy-dp(48*scale)], width=dp(8*scale))
            Color(.04, .04, .05, 1)
            Ellipse(pos=(sx-dp(7*scale), self.height-sy-dp(8*scale)), size=(dp(14*scale), dp(14*scale)))
            Color(.8, .81, .79, 1)
            Ellipse(pos=(sx-dp(7*scale), self.height-sy-dp(7*scale)), size=(dp(14*scale), dp(14*scale)))

    def draw_game(self):
        w, h = self.width, self.height
        p, s = self.player, self.slender
        camx = clamp(p[0]-w/2, 0, self.WORLD_W-w)
        camy = clamp(p[1]-h/2, 0, self.WORLD_H-h)
        with self.canvas:
            Color(.035, .075, .07, 1)
            Rectangle(pos=self.pos, size=self.size)
            # suelo
            Color(.055, .105, .095, 1)
            for x in range(0, self.WORLD_W, 130):
                for y in range(0, self.WORLD_H, 130):
                    sx, sy = self.screen_point(x, y, camx, camy)
                    if -10 < sx < w+10 and -10 < sy < h+10:
                        Ellipse(pos=(sx, sy-dp(2)), size=(dp(3), dp(3)))
            # lago
            lx, ly = self.screen_point(self.LAKE[0], self.LAKE[1], camx, camy)
            Color(.015, .06, .10, 1)
            Ellipse(pos=(lx, ly-dp(self.LAKE[3])), size=(self.LAKE[2], self.LAKE[3]))
            Color(.05, .13, .17, 1)
            Line(ellipse=(lx, ly-dp(self.LAKE[3]), self.LAKE[2], self.LAKE[3]), width=dp(2))
            # muelle
            dx, dy = self.screen_point(self.DOCK[0], self.DOCK[1], camx, camy)
            Color(.25, .16, .11, 1)
            Rectangle(pos=(dx, dy-dp(self.DOCK[3])), size=(self.DOCK[2], self.DOCK[3]))
            Color(.08, .07, .06, 1)
            for xx in range(int(dx+8), int(dx+self.DOCK[2]), 22):
                Line(points=[xx, dy-dp(self.DOCK[3]), xx, dy], width=dp(2))
            # barco
            bx, by = self.screen_point(self.BOAT[0]+self.BOAT[2]/2, self.BOAT[1]+self.BOAT[3]/2, camx, camy)
            Color(.03, .03, .035, 1)
            Ellipse(pos=(bx-dp(39), by-dp(15)), size=(dp(78), dp(31)))
            Color(.30, .23, .16, 1)
            Ellipse(pos=(bx-dp(34), by-dp(11)), size=(dp(68), dp(22)))
            # vegetación
            for x, y, r in self.bushes:
                sx, sy = self.screen_point(x, y, camx, camy)
                if -40 < sx < w+40 and -40 < sy < h+40:
                    Color(.035,.095,.055,1)
                    Ellipse(pos=(sx-r, sy-r), size=(r*2,r*2))
            for x, y, r in self.rocks:
                sx, sy = self.screen_point(x, y, camx, camy)
                if -40 < sx < w+40 and -40 < sy < h+40:
                    Color(.17,.19,.18,1)
                    Ellipse(pos=(sx-r, sy-r*.7), size=(r*2,r*1.4))
            for x, y, r in self.trees:
                sx, sy = self.screen_point(x, y, camx, camy)
                if -55 < sx < w+55 and -70 < sy < h+70:
                    Color(.08,.065,.055,1)
                    Rectangle(pos=(sx-r*.2, sy-r), size=(r*.4,r))
                    Color(.025,.075,.06,1)
                    Ellipse(pos=(sx-r,sy-r),size=(r*2,r*2))
            # Slenderman
            visible = self.slender_state in ("watching","stalking","chasing","vanishing")
            if self.slender_state == "vanishing" and self.state_timer < .3:
                visible = False
            if visible:
                sx, sy = self.screen_point(s[0], s[1], camx, camy)
                self.draw_slender(sx, sy, 1.15)
            # jugador
            px, py = self.screen_point(p[0], p[1], camx, camy)
            Color(.01,.01,.015,1)
            Ellipse(pos=(px-dp(13),py-dp(5)),size=(dp(26),dp(12)))
            Color(.12,.16,.18,1)
            Ellipse(pos=(px-dp(13),py-dp(13)),size=(dp(26),dp(26)))
            Color(.42,.45,.44,1)
            Ellipse(pos=(px-dp(5),py-dp(8)),size=(dp(10),dp(10)))
            # oscuridad y círculo de linterna
            Color(0,0,0,.72 if self.flashlight and self.battery>0 else .91)
            Rectangle(pos=self.pos,size=self.size)
            if self.flashlight and self.battery>0:
                Color(0,0,0,0)
                Ellipse(pos=(px-dp(105),py-dp(105)),size=(dp(210),dp(210)))
            # HUD
            Color(.03,.04,.045,.95)
            RoundedRectangle(pos=(dp(12),h-dp(66)),size=(dp(160),dp(52)),radius=[dp(6)])
            Color(.45,.60,.42,1)
            Rectangle(pos=(dp(18),h-dp(32)),size=(dp(146*self.stamina),dp(8)))
            Color(.75,.64,.34,1)
            Rectangle(pos=(dp(18),h-dp(52)),size=(dp(146*self.battery),dp(7)))
        self.draw_text("RESISTENCIA", dp(85), h-dp(17), 10)
        self.draw_text("BATERÍA", dp(85), h-dp(39), 10)
        if self.message:
            self.draw_text(self.message, w/2, h*.88, 13)
        if self.battery <= 0:
            self.draw_text("BATERÍA AGOTADA", w/2, h*.80, 13, (1,.72,.4,1))
        # controles táctiles
        joyx, joyy = w*.16, h*.20
        with self.canvas:
            Color(.18,.23,.24,.8)
            Line(circle=(joyx,joyy,dp(48)),width=dp(3))
            Color(.45,.50,.50,.7)
            Ellipse(pos=(joyx-dp(19),joyy-dp(19)),size=(dp(38),dp(38)))
        self.draw_button(w*.78,h*.24,w*.18,h*.09,"CORRER")
        self.draw_button(w*.78,h*.12,w*.18,h*.09,"LUZ: "+("ON" if self.flashlight else "OFF"))
        if self.dock_found and distance(p,(self.BOAT[0]+39,self.BOAT[1]+20)) < 105:
            self.draw_button(w*.39,h*.12,w*.28,h*.09,"ESCAPAR")
            self.draw_text("Pulsa ESCAPAR para subir al barco",w/2,h*.32,12)
        if self.game_state == "escaping":
            self.draw_text("EL BARCO SE ALEJA...",w/2,h/2,22)

    def draw_end(self, won):
        w,h=self.width,self.height
        with self.canvas:
            Color(.01,.015,.025,1)
            Rectangle(pos=self.pos,size=self.size)
        self.draw_text("HAS SOBREVIVIDO..." if won else "GAME OVER",w/2,h*.55,32,
                       (.82,.86,.82,1) if won else (.85,.15,.18,1))
        self.draw_text("El bosque queda atrás. Por ahora." if won else "Slenderman te ha encontrado.",w/2,h*.46,16)
        self.draw_button(w*.25,h*.28,w*.50,dp(58),"JUGAR DE NUEVO")

    def on_touch_down(self, touch):
        x,y=touch.x, self.height-touch.y
        w,h=self.width,self.height
        if self.state == "menu":
            bw,bh=w*.62,max(dp(48),h*.075)
            left=(w-bw)/2
            top=h*.52
            for i,key in enumerate(("play","options","volume","exit")):
                yy=top-i*(bh+dp(12))
                if left <= x <= left+bw and yy-bh <= y <= yy:
                    if key=="play":
                        self.new_game(); self.state="playing"
                    elif key=="options":
                        self.options=not self.options
                    elif key=="volume":
                        self.volume=0 if self.volume else .55
                    else:
                        App.get_running_app().stop()
                    self.redraw()
                    return True
        elif self.state in ("gameover","win"):
            if w*.25 <= x <= w*.75 and h*.28-dp(58) <= y <= h*.28:
                self.new_game(); self.state="playing"; self.redraw()
                return True
        elif self.state=="playing":
            if x>w*.76 and h*.24-dp(5) <= y <= h*.33:
                self.running_touch=True; self.touch_roles[touch.uid]="run"; return True
            if x>w*.76 and h*.12-dp(5) <= y <= h*.21:
                self.flashlight=not self.flashlight; self.touch_roles[touch.uid]="light"; self.redraw(); return True
            if self.dock_found and distance(self.player,(self.BOAT[0]+39,self.BOAT[1]+20))<105:
                if w*.39 <= x <= w*.67 and h*.12-dp(5) <= y <= h*.21:
                    self.game_state="escaping"; self.touch_roles[touch.uid]="escape"; return True
            if x < w*.48:
                self.joy_uid=touch.uid
                self.joy_origin=(x,y)
                self.move_vector=[0,0]
                self.touch_roles[touch.uid]="joy"
                return True
        return True

    def on_touch_move(self, touch):
        if self.state=="playing" and self.joy_uid==touch.uid and self.joy_origin:
            x,y=touch.x,self.height-touch.y
            dx,dy=x-self.joy_origin[0],y-self.joy_origin[1]
            ln=max(1,math.hypot(dx,dy))
            self.move_vector=[clamp(dx/ln,-1,1)*min(1,ln/70),
                              clamp(-dy/ln,-1,1)*min(1,ln/70)]
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        role=self.touch_roles.pop(touch.uid,None)
        if role=="run":
            self.running_touch=False
        if role=="joy" and self.joy_uid==touch.uid:
            self.joy_uid=None; self.joy_origin=None; self.move_vector=[0,0]
        return True


class SlendermanApp(App):
    def build(self):
        self.title = "Slenderman: Escape del Bosque"
        Window.clearcolor = (0.01,0.02,0.025,1)
        return ForestGame()


if __name__ == "__main__":
    SlendermanApp().run()
