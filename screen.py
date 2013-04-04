from game import MAP_HEIGHT, MAP_WIDTH
import sys

from multiprocessing import Process, Queue
import curses
from cStringIO import StringIO
from time import sleep

import random

class AsyncCursesScreen(object):
    def __init__(self):
        self.queue = Queue()
        self.process = Process(target=lambda: curses.wrapper(self.handler))
        self.process.start()
    def join(self):
        self.queue.put("!!HALT")
        self.process.join()
    def handler(self,stdscr):
        # First, draw the initial window.
        stdscr.border()
        stdscr.touchwin()
        stdscr.refresh()
        curses.use_default_colors()
        (ty,tx) = stdscr.getmaxyx()
        self.game = MapWindow(MAP_HEIGHT+5, MAP_WIDTH*2+5, 0, 0,MAP_WIDTH,MAP_HEIGHT)
        self.unit = UnitWindow(MAP_HEIGHT+5, tx-(MAP_WIDTH*2+5), 0, MAP_WIDTH*2+5)
        self.debug = DebugWindow(ty-(MAP_HEIGHT+5), tx, MAP_HEIGHT+5, 0)
        self.debug.write("Hello World!")
        self.debug.write("Hello World!")
        self.debug.write("Hello World!")
        self.debug.write(curses.has_colors())
        self.debug.blit()
        self.unit.view({'x':5,'y':6,'health':7,'attacks_left':8})
        self.unit.blit()
        self.game.blit()
        mapjunk = []
        curses.init_pair(2,curses.COLOR_BLUE,curses.COLOR_BLACK)
        curses.init_pair(3,curses.COLOR_RED,curses.COLOR_BLACK)
        curses.init_pair(4,curses.COLOR_GREEN,curses.COLOR_BLACK)
        WALL_COLOR = curses.color_pair(2)
        ENEMY_COLOR = curses.color_pair(3)
        FRIENDLY_COLOR = curses.color_pair(4)
        for i in range(300):
            mapjunk = []
            for j in range(200): 
                mapjunk.append({'x':random.randint(0,MAP_WIDTH-1),
                                'y':random.randint(0,MAP_HEIGHT-1),
                                'v':random.choice([('X',WALL_COLOR),
                                                   ('W',ENEMY_COLOR),
                                                   ('W',FRIENDLY_COLOR),
                                                   ('S',ENEMY_COLOR),
                                                   ('S',FRIENDLY_COLOR)])})
            self.game.update(mapjunk)
            self.game.blit()
            self.debug.write(str(i))
            self.debug.blit()
            sleep(.5)
        while 1:
            sleep(.5)
            pass

class CursesWindow(object):
    def __init__(self,height,width,yoffset,xoffset,border=True,window_title=None):
        self.window = curses.newwin(height,width,yoffset,xoffset)
        if border:
            self.window.border()
            self.window.touchwin()
            if window_title:
                self.window.addstr(0,1,window_title)
            self.usablex = (1,width-1)
            self.usabley = (1,height-1)
        else:
            self.usablex = (0,width)
            self.usabley = (0,height)
        self.window.refresh()        
    def blit(self):
        self.window.refresh()
    def usable_width(self):
        return self.usablex[1]-self.usablex[0]
    def usable_height(self):
        return self.usabley[1]-self.usabley[0]

class MapWindow(CursesWindow):
    def __init__(self, height, width, yoffset, xoffset, map_width, map_height):
        x = super(MapWindow, self).__init__(height,width,yoffset,xoffset,window_title="Map")
        for i in range(map_width):
            self.window.addch(2,i*2+4,str(i/10)[0])
            self.window.addch(3,i*2+4,str(i%10)[0])
        for i in range(map_height):
            self.window.addch(i+4,1,str(i/10)[0])
            self.window.addch(i+4,2,str(i%10)[0])
        self.usablex = (4,self.usablex[1])
        self.usabley = (4,self.usabley[1])
        self.dwindow = self.window.derwin(self.usable_height(),self.usable_width(),self.usabley[0],self.usablex[0])
        self.dwindow.refresh()
        self.cursor = (0,0)
        self.showcursor = False
        self.cwindow = self.window.derwin(1,self.usable_width(),1,self.usablex[0])
        self.describe_cursor()
        self.window.refresh()
        self.map_width = map_width
        self.map_height = map_height
        self.objects = []
        return x

    def update(self,objs):
        # expects a list of dicts, each of which need and x,y pair
        self.objects = objs

    def blit(self):
        self.dwindow.erase()  
        # Draw dots in for all the celles
        for i in range(self.map_width):
            for j in range(self.map_height):
                self.dwindow.addch(j,i*2,'.')
        for o in self.objects:
            self.dwindow.addch(o['y'], o['x']*2, o['v'][0],o['v'][1])
        self.dwindow.refresh()
 
    def describe_cursor(self):
        self.cwindow.erase()
        if self.showcursor:
            self.cwindow.addstr("Cursor Position {},{}".format(self.cursor[1],self.cursor[0]))
        else:
            self.cwindow.addstr("Cursor Off")
        self.cwindow.refresh()
 
    def fix_cursor(self):
        if self.cursor[1] > self.map_width:
            y = 0
        elif self.cursor[1] < 0:
            y = self.map_width-1
        else:
            y = self.cursor[1]
        if self.cursor[0] > self.map_height:
            x = 0
        elif self.cursor[0] < 0:
            x = self.map_width-1
        else:
            x = self.cursor[0]
        self.cursor = (y,x)

    def cursor_left(self):
        self.cursor = (self.cursor[0],self.cursor[1]-1)
        self.fix_cursor
        return self.cursor
    def cursor_right(self):
        self.cursor = (self.cursor[0],self.cursor[1]+1)
        self.fix_cursor
        return self.cursor
    def cursor_up(self):
        self.cursor = (self.cursor[0]-1,self.cursor[1])
        self.fix_cursor
        return self.cursor
    def cursor_down(self):
        self.cursor = (self.cursor[0]+1,self.cursor[1])
        self.fix_cursor
        return self.cursor


class UnitWindow(CursesWindow):
    def __init__(self, height, width, yoffset, xoffset):
        x = super(UnitWindow, self).__init__(height,width,yoffset,xoffset,window_title="Unit Viewer")
        self.window.addstr(1,1,"Press arrow keys to move cursor. Space to pause/unpause output.")
        self.window.addstr(2,1,"Esc will stop the cursor")
        self.usabley = (3,self.usabley[1])
        self.dwindow = self.window.derwin(self.usable_height(),self.usable_width(),3,1)
        self.window.refresh()
        self.dwindow.refresh()
        self.dirty = False
        self.cursor = (0,0)
        self.viewing = None
        return x

    def view(self,obj):
        # for simplicity, and pickles, expects a dict
        self.viewing = obj
        self.dirty = True
    
    def blit(self):
        if self.dirty == False:
            print "NOT DIRTY"
            return
        self.dirty = False
        self.dwindow.erase()
        if self.viewing == None:
            return
        c = 0
        for (k,v) in self.viewing.iteritems():
            if c > self.usable_height():
                break
            self.dwindow.addstr(c,0,"{}: {}".format(k,v))
            c += 1
        self.dwindow.refresh()


class DebugWindow(CursesWindow):
    def __init__(self, height, width, yoffset, xoffset, scrollback=2000):
        x = super(DebugWindow, self).__init__(height,width,yoffset,xoffset,window_title="Debug Output")
        self.window.refresh()
        self.scrollback = ["Logger Output Will Appear Here, a/z to scroll up down"]
        self.cursor = 0
        self.dwindow = self.window.derwin(self.usable_height(),self.usable_width(),1,1)
        self.dwindow.refresh()
        self.dirty = False
        return x

    def write(self,string):
        string = str(string)
        #Chunk the string to display nicely:
        self.scrollback += string.split("\n")
        self.cursor = len(self.scrollback)-1
        self.dirty = True
    
    def blit(self):
        if self.dirty == False:
            return
        self.dirty = False
        usedlines = 0
        self.dwindow.erase()
        c = self.cursor
        def numlines(string):
            l = len(string)/self.usable_width()
            if len(string) % self.usable_width() > 0:
                l += 1
            return l
        while usedlines < self.usable_height() and c >= 0:
            usedlines += numlines(self.scrollback[c])
            c -= 1
        c += 1
        bc = 0
        for line in self.scrollback[c+1:self.cursor+1]:
            self.dwindow.addstr(bc,0,line)
            bc += numlines(line)
        self.dwindow.refresh()
    
    def cursor_up(self):
        self.dirty = True
        self.cursor = max(0,self.cursor-1)
    
    def cursor_down(self):
        self.dirty = True
        self.cursor = min(len(self.scrollback)-1,self.cursor+1)

AsyncCursesScreen()
print "Goodbye"
print "You Say Hello"
print "I say goodbye"
sleep(60)
