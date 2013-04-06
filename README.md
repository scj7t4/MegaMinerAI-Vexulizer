Vexulizer
=========

An Asynchronus Curses Debugger/Visualizer For  S&amp;T Sig-Game's Megaminer

What is this?
=========

The intends to provide a generic (along with game specific adapters) framework for presenting a
visualization of grid based games in a console for the purpose of debugging. Some of the features
include:

* An asynchronous interface for presenting the debug. By decoupling the debugger from the actual AI, you can pause and resume the stream of states coming from the AI to examine units or stdout at a specific moment
* Drop in: The vexulizer does fancy stdout and stderr redirection so you don't have fuss with loggers, and you can pull out vexulizer simply by removing the calls you make to it.
* Unit viewer: displays a view of the map which you can define, with a cursor to examine objects you've selected to draw.


Limitations
==========

I wrote this as my first curses program. Curses is not easy to do and there are probably weird things that can happen.
For example, resizing the terminal is not supported. I don't have a definition for the newest megaminer (Reef) and won't
have one until the competition starts since I am a competitor, although I will share it here.

Planned Features
==========

* Breakpoints : Allow the AI to send pause events to the vexulizer so you can specifically observe certain states.

Overview
=========

Still a little up in the air. You'll instatiate a <GameName>Vexulizer class which launches the screen in the 
init function for your AI. From time to time, you'll call a draw function on a list of mappable function to update
the map and and unit viewer. In the shutdown / cleanup function you'll make a call to stop the vexulizer.
