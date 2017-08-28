"""
A simple game of life implementation to test GUI programming with Tkinter.
"""
import pprint

import numpy as np
from tkinter import *


def is_alive_wrapping(x, y, state):
    """Compute if cell x,y is alive with wrapping edges.
    """
    neighbors_alive = 0
    if 0 < x < state.shape[0] - 1 and 0 < y < state.shape[1] - 1:
        neighbors_alive = np.sum(state[x - 1:x + 2, y - 1:y + 2]) - state[x, y]
    else:
        for i in range(-1, 2, 1):
            for j in range(-1, 2, 1):
                if i == 0 and j == 0:
                    continue
                cx = x + i
                cy = y + j
                cx = 0 if cx >= state.shape[0] else cx
                cy = 0 if cy >= state.shape[1] else cy
                if state[cx, cy] == 1:
                    neighbors_alive += 1
    if state[x][y] == 1:
        if neighbors_alive < 2 or neighbors_alive > 3:
            return False
        return True
    if neighbors_alive == 3:
        return True
    return False


def is_alive(x, y, state):
    """Compute if cell x,y is alive without wrapping edges.
    """
    neighbors_alive = np.sum(state[x - 1:x + 2, y - 1:y + 2]) - state[x, y]
    if state[x][y] == 1:
        if neighbors_alive < 2 or neighbors_alive > 3:
            return False
        return True
    if neighbors_alive == 3:
        return True
    return False


class GameOfLife(object):
    """Game of Life implementation.

    :param initial_state:
        Initial state of the game as a numpy int array. Alive cells should be
        marked with 1 and dead cells with 0.

    :param wrapping:
        If ``True``, the game's cell matrix is wrapped around the edges. That
        is, the top cells have the bottom cells as their neighbors, etc.
    """
    def __init__(self, initial_state, wrapping=False):
        self.w = initial_state.shape[0]
        self.h = initial_state.shape[1]
        self.last_state = initial_state
        self.cur_state = np.copy(initial_state)
        self.wrapping = wrapping
        if self.wrapping:
            self.alive_func = is_alive_wrapping
        else:
            self.alive_func = is_alive

    def get_next_state(self, check_static=True):
        """Advance game by one step.

        :returns: False. If ``check_static == True``, returns ``True`` if
        the last and the current state of the game are exactly the same.
        """
        self.last_state = self.cur_state
        pending_state = np.zeros(self.last_state.shape, dtype=int)
        it = np.nditer(self.cur_state, flags=['multi_index'])
        while not it.finished:
            x, y = it.multi_index
            alive = self.alive_func(x, y, self.cur_state)
            pending_state[x, y] = 1 if alive else 0
            it.iternext()
        self.cur_state = pending_state
        if check_static:
            return np.array_equal(self.last_state, self.cur_state)
        return False

    def run(self, iters=10, print=False):
        """Run game by advancing it ``iter``iterations.

        :param print: If ``True``, prints game's state after each iteration.
        """
        for i in range(iters):
            self.get_next_state()
            if print:
                self.print()

    def print(self):
        print(self.cur_state)


class GOLGUI(object):
    """Simple GUI for Game of Life.
    """
    def __init__(self, root):
        self.root = root
        # Create base frame
        self.frame = Frame(root, borderwidth=0)
        self.frame.grid(row=0, column=0)
        # Create canvas for game of life cells
        self.canvas_frame = Frame(self.frame, borderwidth=0)
        self.canvas_frame.grid(sticky=N+E+S+W)
        self.canvas = GOLCanvasCells(self.canvas_frame, w=50, h=40)
        # Create other GUI elements.
        self.button_frame = Frame(self.frame,
                                  width=self.canvas.tw,
                                  height=self.canvas.th,
                                  borderwidth=0)
        self.button_frame.grid(row=1, column=0, sticky=E)
        self.run_button = Button(self.button_frame, text="RUN",
                                 command=self.start_run)
        self.run_button.grid(column=0, row=0)
        self.root.bind('<Return>', self.start_run)
        self.stop_button = Button(self.button_frame, text="STOP",
                                  command=self.stop)
        self.stop_button.grid(column=1, row=0)
        self.clear_button = Button(self.button_frame, text="CLEAR",
                                   command=self.clear)
        self.clear_button.grid(column=2, row=0)
        self.quit_button = Button(self.button_frame, text="QUIT",
                                  command=self.close)
        self.quit_button.grid(column=3, row=0)
        self.root.bind('<Escape>', self.close)
        self.scale_frame = Frame(self.button_frame)
        self.scale_frame.grid(column=4, row=0)
        self.scale_label = Label(self.scale_frame, text="Speed:")
        self.scale_label.grid(column=0, row=0, sticky=E)
        self.tick_speed = Scale(self.scale_frame, from_=20, to=1000,
                                orient=HORIZONTAL, resolution=10,
                                width=10, length=200)
        self.tick_speed.grid(column=1, row=0)
        self.tick_speed.set(300)
        self.step = 0
        self.iteration = Label(self.button_frame,
                               text="Step: {:0>7}".format(self.step))
        self.iteration.grid(column=5, row=0, sticky=E)
        # Internal attributes for simulation run.
        self._run_job = None
        self._running = False

    def start_run(self, event=None):
        """Start the simulation run.

        Checks that simulation is not already running.
        """
        if not self._running:
            self._running = True
            self.run()

    def run(self, event=None):
        """Run the simulation."""
        static = self.canvas.draw_next_state()
        self.step += 1
        self.iteration['text'] = "Step: {:0>7}".format(self.step)
        if not static:
            self._run_job = self.frame.after(self.tick_speed.get(), self.run)
        else:
            self.stop()

    def stop(self):
        """Stop the simulation run.
        """
        if self._run_job is not None:
            self.root.after_cancel(self._run_job)
            self._run_job = None
        self._running = False

    def clear(self):
        """Clear game of life cells and stop the simulation run.
        """
        self.canvas.clear()
        self.stop()

    def close(self, event=None):
        """Close GUI and exit."""
        self.stop()
        self.root.withdraw()
        sys.exit()


class GOLCanvasCells(object):
    """2D cell matrix made with Tkinter Canvas for Game of Life.

    Also contains the underlying Game of Life implementation.
    """
    def __init__(self, frame, w=50, h=40):
        self.w = w                  # number of cells in x-axis
        self.h = h                  # number of cells in y-axis
        self.cw = 15                # cell width
        self.ch = 15                # cell height
        self.tw = self.w*self.cw    # total width
        self.th = self.h*self.ch    # total height

        # Underlying game of life implementation which is responsible for
        # computing the next state of the cell automaton.
        self.gol = GameOfLife(np.zeros((self.w, self.h), dtype=int),
                              wrapping=True)

        # Create canvas, its cells and helper lines for it.
        self.frame = frame
        self.canvas = Canvas(frame,
                             bg='#eee',
                             width=self.tw+1,
                             height=self.th+1,
                             borderwidth=0,
                             highlightthickness=0)
        self.canvas.grid(sticky=N+E+W+S, padx=5, pady=5)
        pprint.pprint(self.canvas.configure())
        self.cells = [[None for _ in range(self.h)] for _ in range(self.w)]
        self.canvas.bind("<Button-1>", self.toggle_cell)
        self.draw_lines()

    def draw_lines(self):
        """Draw lines for cells to the canvas for easier manipulation.
        """
        self.canvas.create_line(0, 0, self.tw, 0, fill='#ddd')
        self.canvas.create_line(0, 0, 0, self.th, fill='#ddd')
        for i in range(self.w):
            self.canvas.create_line((i+1)*self.cw, 0, (i+1)*self.cw, self.tw,
                                    fill='#ddd')
        for i in range(self.h):
            self.canvas.create_line(0, (i+1)*self.ch, self.tw, (i+1)*self.ch,
                                    fill='#ddd')

    def toggle_cell(self, event=None):
        """Toggle cell between alive and dead.
        """
        x = event.x // self.cw
        y = event.y // self.ch
        # If the tile is not filled, create a rectangle
        if not self.cells[x][y]:
            self.gol.cur_state[x][y] = 1
            self.cells[x][y] = self.canvas.create_rectangle(x * self.cw,
                                                            y * self.ch,
                                                            (x + 1) * self.cw,
                                                            (y + 1) * self.ch,
                                                            fill="black")
        # If the tile is filled, delete the rectangle and clear the reference
        else:
            self.gol.cur_state[x][y] = 0
            self.canvas.delete(self.cells[x][y])
            self.cells[x][y] = None

    def draw_next_state(self):
        """Proceed Game of Life by one step, and draw the next state of it to
        the canvas.
        """
        static = self.gol.get_next_state(check_static=True)
        self.clear_canvas()
        for x in range(self.w):
            for y in range(self.h):
                if self.gol.cur_state[x][y] == 1:
                    r = self.canvas.create_rectangle(x * self.cw,
                                                     y * self.ch,
                                                     (x + 1) * self.cw,
                                                     (y + 1) * self.ch,
                                                     fill="black")
                    self.cells[x][y] = r
        return static

    def clear_canvas(self):
        """Clear canvas.

        This does not clear the state of underlying game of life matrix.
        """
        for x in range(self.w):
            for y in range(self.h):
                if self.cells[x][y]:
                    self.canvas.delete(self.cells[x][y])
                    self.cells[x][y] = None

    def clear(self):
        """Clear canvas and the state of Game of Life.
        """
        self.clear_canvas()
        for x in range(self.w):
            for y in range(self.h):
                self.gol.cur_state[x][y] = 0


if __name__ == "__main__":
    root = Tk()
    root.resizable(False, False)
    root.title("Game of Life")
    gui = GOLGUI(root)
    root.mainloop()