import matplotlib.pyplot as plt
import numpy as np
import os
import tkinter as tk

from math import floor

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.backends.tkagg as tkagg

from matplotlib.figure import Figure

from pygame import mixer
import PIL.Image
import PIL.ImageTk


from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror

import pitch_processing



REDRAW_INTERVAL = 100  # ms
ALL_INSTRUMENTS = ["S. Recorder", "8-Xun"]
DIRTY_NAMES = {"S. Recorder": 'recorder', "8-xun": 'xun'}
OUT_OF_RANGE_FILES = {"S. Recorder": "src/assets/failrecorder.gif"}
HARDCODED_PLOT_PATH = "src/assets/waveform.png"


MAJOR_KEYS = {"C Major": 0, "D Major": 2, "E Major": 4, "-2": -2}
MAJOR_LIST = ["C Major", "D Major", "E Major", "-2"]


def make_arr_plot(new_mp3_arr):
    fig = plt.figure(figsize=(6, 2.5))
    plt.axis('off')
    plt.plot(np.arange(new_mp3_arr.shape[0]), new_mp3_arr[:, 0])
    plt.tight_layout()
    plt.savefig(HARDCODED_PLOT_PATH)


def make_filename(instrument, note):
    name = note[0].lower()+str(note[1])+DIRTY_NAMES[instrument]
    fname = "src/assets/" + name + ".gif"
    return fname


def convert_partitions_to_redraw_frame(partitions, frame_rate):
    # change the units from frames to redraws for each partition
    frame_partitions = []
    for partition in partitions:
        (s_start, s_end), note = partition

        redraw_start = (s_start * 1000.) / (REDRAW_INTERVAL * frame_rate)
        redraw_end = (s_end * 1000.) / (REDRAW_INTERVAL * frame_rate)

        frame_partition = (redraw_start, redraw_end), note
        frame_partitions.append(frame_partition)

    return frame_partitions

class FingeringHelper(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master
        self.pack()

        self.music_frame = tk.Frame(self, bg='grey')
        self.display_frame = tk.Frame(self, bg='white')

        self.music_frame.grid(row=0, column=0)
        self.display_frame.grid(row=0, column=1)

        self.instrument = ALL_INSTRUMENTS[0]

        self.make_file_picker_button()
        self.make_play_button()
        self.make_pause_button()
        self.make_major_menu()
        self.make_progress_scroller()
        self.make_quit_button()
        self.make_display_canvas()
        self.fname = None
        self.stop_redrawing = False
        mixer.init()


    def make_file_picker_button(self):
        self.file_picker_button = tk.Button(self.music_frame, text="Pick a file!", command=self.pick_file)
        self.file_picker_button.grid(column=0, row=0)


    def make_play_button(self):
        self.play_button = tk.Button(self.music_frame, text='Play', command=self.play_music)
        self.play_button.grid(column=0, row=1)


    def make_pause_button(self):
        self.pause_button = tk.Button(self.music_frame, text='Pause', command=self.stop_music)
        self.pause_button.grid(column=0, row=2)


    def make_quit_button(self):
        self.quit_button = tk.Button(self.music_frame, text="QUIT", fg="red",
                              command=lambda : (mixer.music.stop() or self.master.destroy()))
        self.quit_button.grid(column=0, row=5)
    

    def make_progress_scroller(self):
        self.progress_canvas_width = 500
        self.progress_canvas_height = 200

        self.progress_canvas = tk.Canvas(self.music_frame, width=self.progress_canvas_width, height=self.progress_canvas_height, bg='white')
        self.progress_canvas.grid(column=0, row=4)

        self.redraw_ct = 0
        self.progress_bar_x = 0

    def draw_progress_scroller(self, mp3_arr):
        make_arr_plot(mp3_arr)
        im = PIL.Image.open(HARDCODED_PLOT_PATH)
        self.waveform_plot = PIL.ImageTk.PhotoImage(im)
        self.progress_canvas.create_image(self.progress_canvas_width/2, self.progress_canvas_height/2, image=self.waveform_plot)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 5, self.progress_canvas_height, fill='orange')

    def make_display_canvas(self):
        self.display_canvas = tk.Canvas(self.display_frame, width=400, height=800, bg='white')
        self.display_canvas.pack(expand=tk.YES, fill=tk.BOTH)
        self.display_image = None

    def make_major_menu(self):
        self.major_variable = tk.StringVar(self.display_frame)

        self.major_variable.set("C Major")
        self.key_offset = 0

        self.major_menu = tk.OptionMenu(self.music_frame, self.major_variable, *MAJOR_LIST, command=self.set_major)
        self.major_menu.grid(column=0, row=3)

    def make_instrument_menu(self):
        self.instrument_listbox = tk.OptionMenu()

    def pick_file(self):
        self.fname = askopenfilename(filetypes=(("MP3 files", "*.mp3"),
                                                ("All files", "*.*") ))
        if self.fname:
            self.reinitialize()
            self.frame_rate, self.mp3_arr, self.all_notes, new_fname, new_mp3_arr = pitch_processing.process_file(self.fname, self.key_offset)
            self.draw_progress_scroller(new_mp3_arr)

            print("got all notes")
            for v in self.all_notes:
                print(v[1], v[0])

            self.song_length = self.mp3_arr.shape[0] / self.frame_rate
            self.total_redraws = self.song_length * 1000 / REDRAW_INTERVAL
            self.all_notes_redraws = convert_partitions_to_redraw_frame(self.all_notes, self.frame_rate)

            # add a sentinel to prevent overstepping array in redraw()
            self.all_notes_redraws.append(((self.total_redraws + 10, self.total_redraws + 10), ("A", 5)))

            print("song length:", self.song_length)
            mixer.music.load(new_fname)
            self.stop_redrawing = True

        fname_end = os.path.split(self.fname)[-1]
        self.file_picker_button["text"] = "File picked: " + fname_end
        #self.file_picker_button["command"] = None


    def reinitialize(self):
        if mixer.music.get_busy():
            self.stop_music()

        self.cur_note_screen = 0
        self.is_displaying_note = False

        self.progress_canvas.delete('all')
        self.display_canvas.delete('all')

        self.redraw_ct = 0
        self.progress_bar_x = 0

    def stop_music(self):
        mixer.music.pause()
        self.stop_redrawing = True


    def play_music(self):
        mixer.music.play()
        self.master.after(REDRAW_INTERVAL, self.redraw)
        self.stop_redrawing = False
    
    def set_major(self, event):
        self.key_offset = MAJOR_KEYS[event]


    def redraw(self):
        self.redraw_ct += 1

        # convince yourself of this math
        new_progress_bar_x = floor((self.redraw_ct * self.progress_canvas_width) / self.total_redraws)

        if new_progress_bar_x > self.progress_bar_x:  # could move by more than one
            self.progress_canvas.move(self.progress_bar, new_progress_bar_x - self.progress_bar_x, 0)
            self.progress_bar_x = new_progress_bar_x
        
        cur_partition_inds, cur_note = self.all_notes_redraws[self.cur_note_screen]
        print(self.redraw_ct, self.cur_note_screen, cur_partition_inds, cur_note)

        # if we aren't displaying a note but we should be
        if not self.is_displaying_note and (self.redraw_ct + 1 >= cur_partition_inds[0]):
            # make the image
            desired_filename = make_filename(self.instrument, cur_note)
            print(make_filename(self.instrument, cur_note))
            if not os.path.exists(desired_filename):
                desired_filename = OUT_OF_RANGE_FILES[self.instrument]
            self.display_image = tk.PhotoImage(file=desired_filename)

            # and put it on
            self.display_canvas.create_image(100, 400, image=self.display_image)
            self.is_displaying_note = True

        # if we are displaying an image but we should stop
        elif self.is_displaying_note and (self.redraw_ct > 1 + cur_partition_inds[1]):
            self.display_canvas.delete('all')
            self.is_displaying_note = False
            self.cur_note_screen += 1

        if not self.stop_redrawing and mixer.music.get_busy():
            self.master.after(REDRAW_INTERVAL, self.redraw)


root = tk.Tk()
root.geometry('800x800')
root.title('Fingering Helper!')
app = FingeringHelper(master=root)
root.mainloop()
