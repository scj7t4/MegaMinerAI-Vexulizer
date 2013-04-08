from vexulizer import Vexulizer

class ReefVexulizer(object)
    """
    This is the object you should use to enable the Vexulizer for REEF
    (Megaminer 11). To install, include this object by doing:

    from megaminer11 import ReefVexulizer

    Then, in your init function in AI.py:

    self.vex = ReefVexulizer(self)

    And in your run function, you probably want, at the very list a call to
    snapshot at the beginning and end like so:

    def run(self):
        self.vex.snapshot(self) #To capture what your opponent did
        <!-- Your AI goes here --->
        <!-- Snip --->
        self.vex.snapshot(self) #To capture what you did.

    In addition to what is suggested, you can make calls to 
    self.vex.snapshot(self) as often as you like to update the state more 
    often. In addition, you can use self.vex.breakpoint(self) which also
    updates the visualizer state, but will also pause the visualizer for
    you to inspect.

    Because the vexulizer uses curses (and is asynchronous), it probably will
    automatically shut itself off in the arena. but, in case it doesn't you
    can turn enable off before your submit it and not have to worry!
    """
    def __init__(self,ai,enable=True):
        self.enable = enable
        if not self.enable:
            return
        #: The underlying vexulizer
        self.vex = Vexulizer(ai.getMapWidth(),ai.getMapHeight(),COLOR_PROFILE)
    def update_map(self,ai):
        if not self.enable:
            return
        # Using the AI, convert each type to a dictionary and then push the
        # whole caboodle to the visualizer
        package = []
        package += self.get_typeA(ai)
        package += self.get_typeB(ai)
        self.vex.update_units(package)
    def get_typeA(self,ai):
        # Make a list of dictionaries describing the unit of that type.
        r = []
        return r
    def snapshot(self,ai):
        if not self.enable:
            return
        self.update_map(ai)
        self.vex.mark_turn(ai.getTurnNumber())
    def breakpoint(self,ai)
        if not self.enable:
            return
        self.update_map(ai)
        self.vex.breakpoint(ai.getTurnNumber())
    def end(self,ai)
        if not self.enable:
            return
        self.vex.stop_debugger()
