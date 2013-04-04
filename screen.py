from game import MAP_HEIGHT, MAP_WIDTH
import sys

from multiprocessing import Process, Queue
import curses
from cStringIO import StringIO
from time import sleep

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
        curses.use_default_colors()
        stdscr.border()
        stdscr.touchwin()
        stdscr.refresh()
        (ty,tx) = stdscr.getmaxyx()
        self.game = MapWindow(MAP_HEIGHT+4, MAP_WIDTH*2+5, 0, 0,MAP_WIDTH,MAP_HEIGHT)
        self.unit = UnitWindow(MAP_HEIGHT+4, tx-(MAP_WIDTH*2+5), 0, MAP_WIDTH*2+5)
        self.debug = DebugWindow(ty-(MAP_HEIGHT+4), tx, MAP_HEIGHT+4, 0)
        self.debug.write("Hello World!")
        self.debug.write("Hello World!")
        self.debug.write("Hello World!")
        self.debug.write("Hello World!")
        self.debug.blit()
        for i in range(300):
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
            self.window.addch(1,i*2+4,str(i/10)[0])
            self.window.addch(2,i*2+4,str(i%10)[0])
        for i in range(map_height):
            self.window.addch(i+3,1,str(i/10)[0])
            self.window.addch(i+3,2,str(i%10)[0])
        self.usablex = (4,self.usablex[1])
        self.usabley = (3,self.usabley[1])
        self.dwindow = self.window.derwin(self.usable_height(),self.usable_width(),self.usabley[0],self.usablex[0])
        self.dwindow.addstr(0,0,"AHHUOOOOOOOooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo")
        self.dwindow.refresh()
        self.window.refresh()
        return x
        

class UnitWindow(CursesWindow):
    def __init__(self, height, width, yoffset, xoffset):
        x = super(UnitWindow, self).__init__(height,width,yoffset,xoffset,window_title="Unit Viewer")
        self.window.addstr(1,1,"Press uhkm to move cursor. Space to pause/unpause output.")
        self.window.refresh()
        return x

class DebugWindow(CursesWindow):
    def __init__(self, height, width, yoffset, xoffset, scrollback=2000):
        x = super(DebugWindow, self).__init__(height,width,yoffset,xoffset,window_title="Debug Output")
        self.window.refresh()
        self.scrollback = ["Logger Output Will Appear Here"]
        self.cursor = 0
        self.dwindow = self.window.derwin(self.usable_height(),self.usable_width(),1,1)
        self.dwindow.refresh()
        self.dirty = False
        return x
    def write(self,string):
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
        for line in self.scrollback[c:self.cursor+1]:
            self.dwindow.addstr(bc,0,line)
            bc += numlines(line)
        self.dwindow.refresh()
    def cursor_up(self):
        self.cursor = max(0,self.cursor-1)
    def cursor_down(self):
        self.cursor = min(len(self.scrollback)-1,self.cursor+1)

AsyncCursesScreen()
print "Goodbye"
print "You Say Hello"
print "I say goodbye"
sleep(60)
