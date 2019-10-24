import math
class FingeringController(object):
    def __init__(self, canvas):
        self.canvas = canvas
        self.all_holes, self.set_holes, self.fingering_table = self.make_fingerings()
        self.draw_holes = self.make_outlines(canvas)

    def make_fingerings(self):
        raise NotImplementedError

    def make_outlines(self, canvas):
        raise NotImplementedError


RECORDER_HOLES = ["back_half", "back_whole", "l1", "l2", "l2_half", "l3", "r1", "r2", "r2_half", "r3", "r4", "r3s", "r4s"]
RECORDER_FINGERINGS = {
    ("C", 4): {True: ["back_whole", "l1", "l2", "l3", "r1", "r2", "r3", "r3s", "r4", "r4s"], False: [], None: ["back_half", "l2_half", "r2_half"]},
    ("C#", 4): {True: ["back_whole", "l1", "l2", "l3", "r1", "r2", "r3", "r3s", "r4"], False: ["r4s"], None: ["back_half", "l2_half", "r2_half"]},
    ("D", 4): {True: ["back_whole", "l1", "l2", "l3", "r1", "r2", "r3", "r3s"], False: ["r4", "r4s"], None: ["back_half", "l2_half", "r2_half"]},
    ("D#", 4): {True: ["back_whole", "l1", "l2", "l3", "r1", "r2", "r3"], False: ["r3s", "r4", "r4s"], None: ["back_half", "l2_half", "r2_half"]},
    ("E", 4): {True: ["back_whole", "l1", "l2", "l3", "r1", "r2"], False: ["r3", "r3s", "r4", "r4s"], None: ["back_half", "l2_half", "r2_half"]},
    ("F", 4): {True: ["back_whole", "l1", "l2", "l3", "r1", "r3", "r3s", "r4", "r4s"], False: ["r2", "r2_half"], None: ["back_half", "l2_half"]},
    ("F#", 4): {True: ["back_whole", "l1", "l2", "l3", "r2", "r3", "r3s"], False: ["r1", "r4", "r4s"], None: ["back_half", "l2_half", "r2_half"]},
    ("G", 4): {True: ["back_whole", "l1", "l2", "l3"], False: ["r1", "r2", "r2_half", "r3", "r4", "r3s", "r4s"], None: ["back_half", "l2_half"]},
    ("A", 5): {True: ["back_whole", "l1", "l2"], False: ["l3", "r1", "r2", "r2_half", "r3", "r4", "r3s", "r4s"], None: ["back_half", "l2_half"]},
    ("B", 5): {True: ["back_whole", "l1"], False: ["l2", "l2_half", "l3", "r1", "r2", "r2_half", "r3", "r4", "r3s", "r4s"], None: ["back_half"]},
    ("C", 5): {True: ["back_whole", "l2"], False: ["l1", "l3", "r1", "r2", "r2_half", "r3", "r4", "r3s", "r4s"], None: ["back_half", "l2_half"]},
    ("C#", 5): {True: ["l1", "l2"], False: ["back_whole", "back_half", "l3", "r1", "r2", "r2_half", "r3", "r4", "r3s", "r4s"], None: ["l2_half"]},
    ("D", 5): {True: ["l2"], False: ["back_whole", "back_half", "l1", "l3", "r1", "r2", "r2_half", "r3", "r4", "r3s", "r4s"], None: ["l2_half"]},
    ("D#", 5): {True: ["l2", "l3", "r1", "r2", "r3", "r3s"], False: ["back_whole", "back_half", "l1", "r4", "r4s"], None: ["l2_half", "r2_half"]},
    ("E", 5): {True: ["back_half", "l1", "l2", "l3", "r1", "r2"], False: ["back_whole", "r3", "r3s", "r4", "r4s"], None: ["l2_half", "r2_half"]},
    ("F", 5): {True: ["back_half", "l1", "l2", "l3", "r1", "r3", "r3s"], False: ["back_whole", "r2", "r2_half", "r4", "r4s"], None: ["l2_half"]},
    ("G", 5): {True: ["back_half", "l1", "l2", "l3"], False: ["back_whole", "r1", "r2", "r2_half", "r3", "r3s", "r4", "r4s"], None: ["l2_half"]},
    ("A", 6): {True: ["back_half", "l1", "l2"], False: ["back_whole", "l3", "r1", "r2", "r2_half", "r3", "r3s", "r4", "r4s"], None: ["l2_half"]},
    ("B", 6): {True: ["back_half", "l1", "l2", "r1", "r2"], False: ["back_whole", "l3", "r3", "r3s", "r4", "r4s"], None: ["l2_half", "r2_half"]},
    ("C", 6): {True: ["back_half", "l1", "r1", "r2"], False: ["back_whole", "l2", "l2_half", "l3", "r3", "r3s", "r4", "r4s"], None: ["r2_half"]},
    ("C#", 6): {True: ["back_half", "l1", "l2_half", "l3", "r1", "r2_half", "r3", "r3s", "r4", "r4s"], False: ["back_whole", "l2", "r2"], None: []},
    ("D", 6): {True: ["back_half", "l1", "l3", "r1", "r3", "r3s"], False: ["back_whole", "l2", "l2_half", "r2", "r2_half", "r4", "r4s"], None: []},
    ("fail", ''): {True: [], None: [], False: RECORDER_HOLES}
}


class RecorderFingeringController(FingeringController):
    @classmethod
    def invert_finger_dict(cls, finger_d):
        """This is a convenience function for the easiest way to hardcode fingerings."""
        inverted_d = {}
        for val in finger_d:
            for hole in finger_d[val]:
                inverted_d[hole] = val
        return inverted_d        

    def make_fingerings(self):
        all_holes = RECORDER_HOLES
        set_holes = {hole: False for hole in all_holes}
        fingering_table = RECORDER_FINGERINGS  # {note: RecorderFingeringController.invert_finger_dict(RECORDER_FINGERINGS[note]) for note in RECORDER_FINGERINGS}
        return all_holes, set_holes, fingering_table

    def make_outlines(self, canvas):
        draw_holes = {}
        left, right, up, down = 0, 200, 0, 600
        dx, dy = right - left, down - up

        # make note label
        draw_holes['label'] = canvas.create_text(left + 3*dx//4, up + 19*down//20, anchor="n", text="None", font="Arial 30 bold")
        
        # make back hole
        big_hole_size = 3*dx//16

        back_x0 = left + 3*dx//8
        back_x1 = back_x0 + big_hole_size

        back_y0 = (up + down) // 2 - big_hole_size
        back_y1 = back_y0 + big_hole_size
        draw_holes['back_whole'] = [canvas.create_oval(back_x0, back_y0, back_x1, back_y1, outline="black", fill="", width=2)]

        # make back half hole
        back_half = []
        r = (back_x1 - back_x0) / 2
        mx, my = (back_x0 + back_x1) / 2, (back_y0 + back_y1) / 2
        x_left, y_left = int(mx - r*math.sqrt(3)/2), my - r//2
        x_right, y_right = int(mx + r*math.sqrt(3)/2), my - r//2
        back_half.append(canvas.create_arc(back_x0, back_y0, back_x1, back_y1, start=150, extent=240, fill="black", outline=""))  # make this to coincide with the back whole
        back_half.append(canvas.create_polygon(mx, my, x_left, y_left, x_right, y_right, fill="black", outline=""))  # make this to fit into the arc
        draw_holes['back_half'] = back_half
       
        # make big holes
        right_row_x0 = left + 3*dx//4
        right_row_x1 = right_row_x0 + big_hole_size
        right_row_top, right_row_gap = up + dy//6, 20

        small_hole_size = big_hole_size//2
        small_x0 = right_row_x1 + right_row_gap//2
        small_x1 = small_x0 + small_hole_size

        for i, hole in enumerate(["l1", "l2", "l3", "r1", "r2", "r3", "r4"]):
            y0 = right_row_top + i*(right_row_gap + big_hole_size)
            y1 = y0 + big_hole_size
            draw_holes[hole] = [canvas.create_oval(right_row_x0, y0, right_row_x1, y1, outline="black", fill="", width=2)]

            if hole in ["l2", "r2"]:
                half_hole = []
                r = (right_row_x1 - right_row_x0) / 2
                mx, my = (right_row_x0 + right_row_x1) / 2, (y0 + y1) / 2
                x_left, y_left = int(mx - r*math.sqrt(3)/2), my - r//2
                x_right, y_right = int(mx + r*math.sqrt(3)/2), my - r//2

                half_hole.append(canvas.create_arc(right_row_x0, y0, right_row_x1, y1, start=150, extent=240, fill="black", outline=""))  # make this to coincide with the hole
                half_hole.append(canvas.create_polygon(mx, my, x_left, y_left, x_right, y_right, fill="black", outline=""))  # make this to fit into the arc
                draw_holes[hole+"_half"] = half_hole

            if hole in ["r3", "r4"]:
                small_hole_name = hole + "s"
                small_y0 = y0 + 0.5*(big_hole_size - small_hole_size)
                small_y1 = small_y0 + small_hole_size
                draw_holes[hole + "s"] = [canvas.create_oval(small_x0, small_y0, small_x1, small_y1, outline="black", fill="", width=2)]

        return draw_holes

    def draw_note(self, note):
        fill_list = []
        drain_list = []

        for hole in self.fingering_table[note][True]:
            if not self.set_holes[hole]:  # if note isn't set, set it
                fill_list += self.draw_holes[hole]

        for hole in self.fingering_table[note][False]:
            if not self.set_holes[hole]:  # if note is set, unset it
                drain_list += self.draw_holes[hole]

        for canvas_hole in fill_list:
            self.canvas.itemconfig(canvas_hole, fill='black')

        for canvas_hole in drain_list:
            self.canvas.itemconfig(canvas_hole, fill='')

        self.canvas.itemconfig(self.draw_holes['label'], text=note[0] + str(note[1]))

