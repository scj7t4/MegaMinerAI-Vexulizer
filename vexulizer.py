from game import MAP_HEIGHT, MAP_WIDTH
from screen import *
import sys

from multiprocessing import Process, Queue, Value
import curses
from time import sleep
from datetime import datetime, timedelta
from StringIO import StringIO
from Queue import Empty
import traceback

import random


class Vexulizer(object):
    rstdout = sys.stdout
    rstderr = sys.stderr
    def __init__(self):
        self.locq = Queue()
        self.running = Value('b',True)
        screen = AsyncCursesScreen()
        self.proc = Process(target=screen.start, args=(self.locq,self.running))
        self.buff = DebugBuffer(self.locq,self.running,sys.stdout)
        self.errbuff = DebugBuffer(self.locq,self.running,sys.stderr)
        self.proc.start()
        sys.stdout = self.buff
        sys.stderr = self.errbuff
    
    def stop_debugger(self):
        print "stopping debugger"
        self.locq.put(('halt',''),False)
        if not self.running.value:
            self.proc.terminate()
        self.proc.join()
        sys.stdout = self.rstdout
        sys.stderr = self.rstderr
        sys.stdout.flush()
        sys.stderr.flush()   
 
    def update_units(self, units):
        self.locq.put(('units',units))

    def print_debug(self, string):
        self.locq.put(('debug',string))
        
    def __del__(self):
        # Restore the stdout on destruction
        self.rstdout.write(self.buff.getvalue())
        self.rstdout.flush() 
        self.rstderr.write(self.errbuff.getvalue())
        self.rstderr.flush() 
        #return super(Vexulizer,self).__del__()


class DebugBuffer(StringIO):
    def __init__(self,locq,running, replaces=None):
        self.locq = locq
        self.running = running
        self.replaces = replaces
        StringIO.__init__(self)
    
    def write(self,s):
        StringIO.write(self,s)
        if not self.running.value and self.replaces:
            self.replaces.write(s)
            self.replaces.flush()
        else:
            self.locq.put(('debug',s))
    
    def writelines(self,sequence):
        StringIO.writelines(self,sequence)
        if not self.running.value and self.replaces:
            self.replaces.writelines(sequence)
            self.replaces.flush()
        else:
            for line in sequence:
                self.locq.put(('debug',line))


if __name__ == "__main__":
    print "HAI"
    v = Vexulizer()

    print "Goodbye"
    print "You Say Hello"
    print "I say goodbye"

    WALL_COLOR = 2
    ENEMY_COLOR = 3
    FRIENDLY_COLOR = 4

    print "This is a particularly long string: it is interesting because magically, it will make" \
        "me cry out to thor and summon him forth"

    for i in range(10):
        print "Turn {}".format(i)
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