"""
Labyrinth maker
"""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103,W1202,E1120,R0913,R0914,E0401,W1203,R1732,W1514,R0912,R0903,R0902,R0911

import copy
import time
import curses
import random


class Cell:
    """Represents a single cell of the maze. It is either a wall or a path.

    is_wall: True if the cell is a wall, False if it is a path.
    is_border: True, if the cell is a border of the area. That way,
            any shape can be used for a maze.
    """

    def __init__(self, border: bool = False):
        """Initially a cell is a wall."""
        self.is_wall = True
        self.is_border = border

    def set_wall(self, flag: bool):
        """Set the status of a wall."""
        self.is_wall = flag


class Maze:
    """Represents a maze. The maze has some height and a width,
    and is surrounded by a 'border' (except entry/exit points).
    """

    # The four possible directions and their meaning
    cmap = {(0, -1): "up", (0, 1): "down", (-1, 0): "left", (1, 0): "right"}

    # The four possible directions
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        entry_point: list = None,
        exit_point: list = None,
        debug: bool = False,
    ):
        """
        Initializes a maze.

        Args:
            width (int): The width of the total maze.
            height (int): The height of the total maze.
            entry_point (int, int): The location of the entry point.
                                    If None, the middle cell on the top is used (negative x).
            exit_point (int, int): The location of the exit point.
                                   If None, the middle cell on the bottom is used (positive x).
            debug (bool): If True, will print debug messages.
        """

        self.width = width
        self.height = height
        if entry_point:
            self.entry = entry_point
        else:
            self.entry = (self.width // 2, 0)
        if exit_point:
            self.exit = exit_point
        else:
            self.exit = (self.width // 2, self.height - 1)

        # Path of the route through the maze (list of 2D coordinates).
        self.path = []

        # List of blocked cells (list of 2D coordinates).
        self.blocked = []

        self.choices = []

        # coordinate of test point probing the maze.
        self.x = 0
        self.y = 0

        # coordinates for a test point stop
        self.stop = None

        # Just a counter to count the steps
        self.counter = 0

        # Flag to indicate if a main path has been found
        self.flag_path = False

        # Flag to indicate if the maze is completed
        self.flag_done = False

        # Indicates the stage of maze creation
        # 1 - Search main path
        # 2 - Creating dead ends
        # 3 - Last check
        # 4 - Finished
        self.stage = 0

        # For debugging
        self.debug = debug
        self.delay = 0.0
        self.dolog = False
        self.fileout = None

        self.init_maze()

        if self.debug:
            # Using 'curses' to print out the maze.
            self.out = curses.initscr()
            curses.noecho()
            curses.cbreak()

    def init_maze(self):
        """Initializes the maze matrix."""
        self.maze = []

        # First and last row are borders.
        upper = [Cell(border=True) for _ in range(self.width)]
        lower = [Cell(border=True) for _ in range(self.width)]

        # Create the maze with the border around it
        self.maze.append(upper)
        for _ in range(self.height - 2):
            row = [Cell(border=True)]
            row.extend([Cell() for _ in range(self.width - 2)])
            row.append(Cell(border=True))
            self.maze.append(row)
        self.maze.append(lower)

        self.set_entry_exit()

    def set_entry_exit(self):
        """Sets the entry ansd exit points."""
        self.unset_border(*self.entry)
        self.unset_border(*self.exit)

    def set_clear(self, x: int, y: int):
        """Sets the cell (x,y) as 'path'"""
        self.set_path(x, y)

    def set_path(self, x: int, y: int):
        """Sets the cell (x,y) as 'path'."""
        self.maze[y][x].set_wall(False)

    def set_wall(self, x: int, y: int):
        """Sets the cell (x,y) as 'wall'."""
        self.maze[y][x].set_wall(True)

    def set_border(self, x: int, y: int):
        """Defines the given position as border."""
        self.maze[y][x].is_border = True

    def unset_border(self, x: int, y: int):
        """Unsets the given position as border."""
        self.maze[y][x].is_border = False

    def possible(self, x: int, y: int, dx: int, dy: int) -> bool:
        """Returns True, if the given location (x+dx, y+dy) is a possibility to continue the path.
        Conditions:
        - the location is inside the maze
        - the location is a wall
        - the next location (like x+2*dx) is a wall
        - the adjacent locations are a wall (to avoid loops)
        - the location is not blocked
        """
        # Check location is part of the maze
        if x + dx < 0 or x + dx >= self.width:
            return False
        if y + dy < 0 or y + dy >= self.height:
            return False

        if self.stage == 1:
            if (x + dx, y + dy) == self.stop:
                return True

        # Check the location and the following location are walls
        if self.is_path(x + dx, y + dy):
            return False
        if self.is_path(x + 2 * dx, y + 2 * dy):
            return False

        # Check if location is not blocked
        if self.is_blocked(x + dx, y + dy):
            return False

        # Check adjacent cells of location are walls.
        if dx == 0:
            if self.is_path(x + 1, y + dy) or self.is_path(x - 1, y + dy):
                return False
        else:
            if self.is_path(x + dx, y + 1) or self.is_path(x + dx, y - 1):
                return False

        return True

    def is_path(self, x: int, y: int) -> bool:
        """Returns True, if the position is a path."""
        if x < 0 or x >= self.width:
            return False
        if y < 0 or y >= self.height:
            return False
        return not self.maze[y][x].is_wall

    def is_blocked(self, x: int, y: int) -> bool:
        """Returns True, if the position is a border cell or blocked."""
        if (x, y) in self.blocked:
            return True
        if self.maze[y][x].is_border:
            return True
        return False

    def pos(self) -> list:
        """Returns the current position of the test point."""
        return (self.x, self.y)

    def printrow(self, txt: str):
        """Print out a row of the maze. For debug only."""
        self.out.addstr(0, 0, txt)
        self.out.refresh()

    def print(self, txt: str = ""):
        """Prints out the maze. For debugging only.

        Using the following characters:
            #  wall
            X  blocked cell
            B  border cell
            o  test point
        """
        if self.dolog:
            self.fileout.write(txt + "\n")
        if self.debug:
            self.out.addstr(0, 0, txt + (100 - len(txt)) * " ")
        else:
            print(txt + (100 - len(txt)) * " ")
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                if self.maze[y][x].is_wall:
                    c = "#"
                else:
                    c = " "
                if (x, y) in self.blocked:
                    c = "X"
                if self.maze[y][x].is_border:
                    c = "B"
                if (x, y) == (self.x, self.y):
                    c = "o"

                row += c
            if self.debug:
                self.out.addstr(y + 1, 0, row)
            else:
                print(row)
        if self.debug:
            self.out.refresh()
        time.sleep(self.delay)

    def forward(self, x: int, y: int):
        """Move the test point to the given location."""
        self.counter += 1

        # Set coordinates
        self.x = x
        self.y = y

        # Add coordinates to the path
        self.path.append((x, y))

        # And mark the cell as 'path'.
        self.set_path(x, y)

    def backward(self):
        """Move the test point back one step."""
        self.counter += 1

        # Remove current cell from path
        x, y = self.path.pop()

        # Set coordinates to last cell
        if len(self.path) > 0:
            self.x, self.y = self.path[-1]
        else:
            # If the test point is back at the first cell, the maze is finished!
            self.x, self.y = x, y
            self.flag_done = True
            return

        if not self.flag_path:
            # Append cell to the blocked list and set it back to 'wall'.
            self.blocked.append((x, y))
            self.set_wall(x, y)

    def get_choices(self) -> list:
        """Returns a list of possible choices for the next step."""
        self.choices = []
        for dx, dy in self.directions:
            if self.possible(self.x, self.y, dx, dy):
                self.choices.append((dx, dy))
        return self.choices

    def choose_next(self):
        """Choose the next step.

        Check the possible choices, and if no choice is possible,
        go back until there are choices possible.
        """
        while not self.get_choices():
            self.backward()
            self.print(f"Step {self.counter} -> Back to Cell {self.x}/{self.y}")
            if self.pos() == self.stop:
                self.flag_done = True
                return
            if self.flag_done:
                return

        # Make a random choice
        dx, dy = random.choice(self.choices)

        # Move forward that choice
        self.forward(self.x + dx, self.y + dy)

        # Debugging/printing
        txt = " ".join([self.cmap[x] for x in self.choices])
        msg = (
            f"Step {self.counter} -> Cell {self.x}/{self.y}  possible directions: {txt}.   "
            f"Chosen direction {self.cmap[(dx, dy)].upper()} to cell {self.x+dx}/{self.y+dy}"
        )
        self.print(msg)

    def create(self):
        """Creates the maze."""
        if self.dolog:
            self.fileout = open("maze.log", "w")
        # Sets the entry and exit points
        self.set_entry_exit()

        ######################################
        # First step: Find main path
        ######################################
        self.stage = 1
        # Set the stop point
        self.stop = self.exit
        # Start at the entry point
        self.forward(*self.entry)

        # Loop until the test point is at the exit point.
        while True:
            self.choose_next()
            if self.pos() == self.exit:
                break

        # Main path has been found. Unblocking all blocked cells, and setting the flag to indicate
        # a random main path has been found
        self.blocked = []
        self.flag_path = True
        self.print("Main path has been found")

        #############################
        # Second step: Find dead ends
        #############################
        self.stage = 2

        # Backup main path
        mainpath = copy.deepcopy(self.path)

        for _ in range(self.width):
            # Get random location along the mainpath and set the test point to that location
            index = random.randint(1, len(mainpath) - 1)
            self.x, self.y = mainpath[index]

            # If there are no choices for this random location, try some other random location
            if not self.get_choices():
                continue

            # Select path up to this position
            self.path = mainpath[:index]
            self.stop = mainpath[index]

            # Choose path from there
            while not self.flag_done:
                self.choose_next()

            # Unset the flag, as we need to find more dead ends
            self.flag_done = False

        #############################################################
        # Third part: Check main path for any undiscovered dead ends.
        #############################################################
        self.stage = 3
        self.print("STAGE 3")
        # Reset point to last cell
        # self.delay = 0.2
        self.path = copy.deepcopy(mainpath)
        self.x, self.y = self.exit
        self.stop = self.entry

        # And go back from here
        self.backward()
        while not self.flag_done:
            self.choose_next()
            self.print("Last check for possible dead ends.")
        self.print("Maze Done!")
        self.stage = 4

        self.finish()

    def finish(self):
        """Stops curses output."""
        if self.dolog:
            self.fileout.close()
        if self.debug:
            self.out.getch()
            curses.echo()
            curses.nocbreak()
            curses.endwin()

    def get_matrix(self) -> list:
        """Returns the final maze matrix with the surrounding wall, to be used elsewhere.

        0 means path
        1 means wall
        """

        matrix = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if self.maze[y][x].is_wall:
                    row.append(1)
                else:
                    row.append(0)
            matrix.append(row)
        return matrix
