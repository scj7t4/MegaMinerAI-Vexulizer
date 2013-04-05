from game import MAP_HEIGHT, MAP_WIDTH
import sys

from multiprocessing import Process, Queue
import curses
from time import sleep
from datetime import datetime, timedelta
from StringIO import StringIO
from Queue import Empty

import random

UNIT_KEY_BLACKLIST = ['v']
MAP_CURSOR_BLINK_RATE = timedelta(milliseconds=500)



class AsyncCursesScreen(object):
    def __init__(self):
        self.paused = False
        self.halting = False
    def start(self,q):
        self.queue = q
        try:
            curses.wrapper(self.handler)
        except KeyboardInterrupt:
            pass
    def handler(self,stdscr):
        curses.init_pair(2,curses.COLOR_BLUE,curses.COLOR_BLACK)
        curses.init_pair(3,curses.COLOR_RED,curses.COLOR_BLACK)
        curses.init_pair(4,curses.COLOR_GREEN,curses.COLOR_BLACK)
        # First, draw the initial window.
        stdscr.border()
        stdscr.touchwin()
        stdscr.refresh()
        stdscr.nodelay(1)
        curses.use_default_colors()
        curses.curs_set(0)
        (ty,tx) = stdscr.getmaxyx()
        #MOVE TO COLORS.PY
        curses.init_pair(3,curses.COLOR_RED,curses.COLOR_BLACK)
        curses.init_pair(4,curses.COLOR_GREEN,curses.COLOR_BLACK)
        curses.init_pair(5,curses.COLOR_BLUE,curses.COLOR_BLACK)
        curses.init_pair(2,curses.COLOR_YELLOW,curses.COLOR_BLACK)
        self.game = MapWindow(MAP_HEIGHT+5, MAP_WIDTH*2+5, 0, 0,MAP_WIDTH,MAP_HEIGHT)
        self.unit = UnitWindow(MAP_HEIGHT+5, tx-(MAP_WIDTH*2+5), 0, MAP_WIDTH*2+5)
        self.debug = DebugWindow(ty-(MAP_HEIGHT+5), tx, MAP_HEIGHT+5, 0)
        self.unit.view({'x':5,'y':6,'health':7,'attacks_left':8})
        while 1:
            # Accept key events from the terminal
            key = stdscr.getch()
            if key != -1:
                self.debug.write("Got key {}".format(key))
            if key == curses.KEY_UP:
                #self.debug.write("Got key up")
                self.game.cursor_up()
            elif key == curses.KEY_DOWN:
                #self.debug.write("Got key down")
                self.game.cursor_down()
            elif key == curses.KEY_LEFT:
                #self.debug.write("Got key left")
                self.game.cursor_left()
            elif key == curses.KEY_RIGHT:
                #self.debug.write("Got key right")
                self.game.cursor_right()
            elif key == 9: #Tab
                #self.debug.write("Got key tab")
                self.game.cursor_hide()
            elif key == 113:
                self.unit.cursor_next()
            elif key == 119:
                self.unit.cursor_previous()
            elif key == 32:
                if self.halting:
                    break
                self.paused = not self.paused
                if self.paused:
                    self.debug.write("-- Paused")
                else:
                    self.debug.write("-- Unpaused")
            # Pull items from the pipe if not paused
            if not self.paused:
                try:
                    (t, contents) = self.queue.get(False)
                    if t == 'units':
                        self.game.update(contents)
                    elif t == 'debug':
                        self.debug.write(contents)            
                    elif t == 'halt':
                        self.halting = True
                        self.debug.write("-- End of queue, press space to close")
                except Empty:
                    pass
                
            #Update the unit view
            self.unit.view(self.game.objects_at_cursor())
            self.debug.blit()
            self.unit.blit()
            self.game.blit()
            sleep(.01)
    

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
        self.blinkcursor = False
        self.lastblink = datetime.today()
        self.cwindow = self.window.derwin(1,self.usable_width(),1,self.usablex[0])
        self.describe_cursor()
        self.window.refresh()
        self.map_width = map_width
        self.map_height = map_height
        self.objects = []
        return x

    def objects_at_cursor(self):
        return [ x for x in self.objects if x['x'] == self.cursor[1] and x['y'] == self.cursor[0] ]

    def update(self,objs):
        # expects a list of dicts, each of which need and x,y pair
        self.objects = objs

    def blit(self):
        self.describe_cursor()
        self.dwindow.erase()  
        # Draw dots in for all the celles
        for i in range(self.map_width):
            for j in range(self.map_height):
                self.dwindow.addch(j,i*2,'.')
        for o in self.objects:
            self.dwindow.addch(o['y'], o['x']*2, o['v'][0],curses.color_pair(o['v'][1]))
        if datetime.today()-self.lastblink > MAP_CURSOR_BLINK_RATE:
            self.lastblink = datetime.today()
            self.blinkcursor = not self.blinkcursor
        if self.showcursor and self.blinkcursor:
            self.dwindow.addch(self.cursor[0],self.cursor[1]*2,'*', curses.color_pair(2))
        self.dwindow.refresh()
 
    def describe_cursor(self):
        self.cwindow.erase()
        self.cwindow.addstr("Cursor Position {},{}".format(self.cursor[1],self.cursor[0]))
        self.cwindow.refresh()
 
    def fix_cursor(self):
        if self.cursor[1] >= self.map_width:
            x = 0
        elif self.cursor[1] < 0:
            x = self.map_width-1
        else:
            x = self.cursor[1]
        if self.cursor[0] >= self.map_height:
            y = 0
        elif self.cursor[0] < 0:
            y = self.map_height-1
        else:
            y = self.cursor[0]
        self.cursor = (y,x)
        self.showcursor = True

    def cursor_left(self):
        self.cursor = (self.cursor[0],self.cursor[1]-1)
        self.fix_cursor()
        return self.cursor
    def cursor_right(self):
        self.cursor = (self.cursor[0],self.cursor[1]+1)
        self.fix_cursor()
        return self.cursor
    def cursor_up(self):
        self.cursor = (self.cursor[0]-1,self.cursor[1])
        self.fix_cursor()
        return self.cursor
    def cursor_down(self):
        self.cursor = (self.cursor[0]+1,self.cursor[1])
        self.fix_cursor()
        return self.cursor
    def cursor_hide(self):
        self.showcursor = False


class UnitWindow(CursesWindow):
    def __init__(self, height, width, yoffset, xoffset):
        x = super(UnitWindow, self).__init__(height,width,yoffset,xoffset,window_title="Unit Viewer")
        self.window.addstr(1,1,"Press arrow keys to move cursor. Space to pause/unpause output.")
        self.window.addstr(2,1,"Tab will hide the cursor, Q/W cycles through units under the cursor.")
        self.usabley = (3,self.usabley[1])
        self.dwindow = self.window.derwin(self.usable_height(),self.usable_width(),3,1)
        self.window.refresh()
        self.dwindow.refresh()
        self.cursor = 0
        self.cursorid = None
        self.viewing = []
        return x

    def view(self,objs):
        # for simplicity, and pickles, expects a dict
        if self.viewing != objs:
            self.viewing = objs
            self.cursor = 0
            ocid = self.cursorid
            self.cursorid = None
            #We'll try and restore the cursor based on the last object id
            #We looked at, if we can't its no big deal.
            #If the ocid hasn't been set, try to set it to the first obj
            if ocid == None and len(objs) > 0:
                try:
                    self.cursorid = objs[0]['id']
                except KeyError:
                    pass
            #If there are objects and the ocid is set try to restore the cursor
            elif len(objs) > 0:
                c = 0
                for o in objs:
                    try:
                        if o['id'] == ocid:
                            self.cursor = c
                            self.cursorid = o['id']
                    except KeyError:
                        pass
                    c += 1
            #if no matches were found, the cursor will be reset to 0 and the
            #cursorid will be set to the first object, if it has an id:
            if self.cursorid == None and len(objs) > 0:
                try:
                    self.cursorid = objs[0]['id']
                except KeyError:
                    pass
            #All else fails,cursor id returns to the first object
                 
    def cursor_next(self):
        self.cursor += 1
        if self.cursor >= len(self.viewing):
            self.cursor = 0
            try:
                self.cursorid = self.viewing[self.cursor]['id']
            except KeyError:
                pass
            except IndexError:
                pass

    def cursor_previous(self):
        self.cursor -= 1
        if self.cursor < 0:
            self.cursor = max(0,len(self.viewing)-1)
            try:
                self.cursorid = self.viewing[self.cursor]['id']
            except KeyError:
                pass
            except IndexError:
                pass
    
    def blit(self):
        self.dwindow.erase()
        if len(self.viewing) > 0:
            self.dwindow.addstr(0,0,"Viewing unit {}/{}".format(self.cursor+1,len(self.viewing)))
        if len(self.viewing) == 0:
            self.dwindow.refresh()
            return
        c = 1
        for (k,v) in self.viewing[self.cursor].iteritems():
            if c > self.usable_height():
                break
            if k in UNIT_KEY_BLACKLIST:
                continue
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

class Vexulizer(object):
    def __init__(self):
        self.locq = Queue()
        self.rstdout = sys.stdout
        self.buff = DebugBuffer(self.locq)
        sys.stdout = self.buff
        self.proc = self.start_debugger()
    
    def start_debugger(self):
        screen = AsyncCursesScreen()
        p = Process(target=screen.start, args=(self.locq,))
        p.start()
        return p
    
    def stop_debugger(self):
        self.locq.put(('halt',''),False)
        self.proc.join()
    
    def update_units(self, units):
        self.locq.put(('units',units))

    def print_debug(self, string):
        self.locq.put(('debug',string))
        
    def __del__(self):
        # Restore the stdout on destruction
        print >>self.rstdout, self.buff.getvalue()
        #return super(Vexulizer,self).__del__()


class DebugBuffer(StringIO):
    def __init__(self,locq):
        self.locq = locq
        StringIO.__init__(self)
    
    def write(self,s):
        self.locq.put(('debug',s))
        StringIO.write(self,s)
    
    def writelines(self,sequence):
        for line in sequence:
            self.locq.put(('debug',line))
        StringIO.writelines(self,sequence)


if __name__ == "__main__":
    v = Vexulizer()

    print "Goodbye"
    print "You Say Hello"
    print "I say goodbye"

    WALL_COLOR = 2
    ENEMY_COLOR = 3
    FRIENDLY_COLOR = 4

    for i in range(15):
        #v.print_debug(locq,"Hello world!!") 
        mapjunk = []
        for j in range(200): 
            mapjunk.append({'x':random.randint(0,MAP_WIDTH-1),
                            'y':random.randint(0,MAP_HEIGHT-1),
                            'v':random.choice([('X',WALL_COLOR),
                                               ('W',ENEMY_COLOR),
                                               ('W',FRIENDLY_COLOR),
                                               ('S',ENEMY_COLOR),
                                               ('S',FRIENDLY_COLOR)]),
                            'health': random.randint(1,100),
                            'id': j,
                            'attacks': random.randint(0,3)
                            })
        #Convert the string IO to print debug
        print "Test!"
        v.update_units(mapjunk) 
        sleep(.5)
    
    v.stop_debugger()
