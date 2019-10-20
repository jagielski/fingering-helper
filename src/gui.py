from math import floor
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
import os
import pitch_processing
from pygame import mixer

REDRAW_INTERVAL = 100  # ms


class FingeringHelper(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master
        self.pack()

        self.music_frame = tk.Frame(self, bg='grey')
        self.display_frame = tk.Frame(self, bg='white')

        self.music_frame.grid(row=0, column=0)
        self.display_frame.grid(row=0, column=1)

        all_makers = [self.make_file_picker_button,
                      self.make_play_button,
                      self.make_pause_button,
                      self.make_quit_button,
                      self.make_scroller]
        [make() for make in all_makers]
        self.fname = None
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
                              command=self.master.destroy)
        self.quit_button.grid(column=0, row=3)


    def make_scroller(self):
        self.progress_canvas_width = 200
        self.progress_canvas = tk.Canvas(self.music_frame, width=self.progress_canvas_width, height=200, bg="white")
        self.progress_canvas.grid(column=0, row=4)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 5, 200, fill='orange')
        self.redraw_ct = 0
        self.progress_bar_x = 0

    def pick_file(self):
        self.fname = askopenfilename(filetypes=(("MP3 files", "*.mp3"),
                                                ("All files", "*.*") ))
        if self.fname:
            process_ret = pitch_processing.process_file(self.fname)
            self.frame_rate, self.mp3_arr, self.all_notes = process_ret
            print("got all notes")
            for v in self.all_notes:
                print(v[1], v[0])
            self.song_length = self.mp3_arr.shape[0] / self.frame_rate
            self.total_redraws = self.song_length * 1000 / REDRAW_INTERVAL
            # self.redraw_rate = self.song_length * 1000 / (REDRAW_INTERVAL * self.progress_canvas_width)
            print("song length:", self.song_length)
            #print("redraw rate:", self.redraw_rate)
            mixer.music.load(self.fname)

        fname_end = os.path.split(self.fname)[-1]
        self.file_picker_button["text"] = "File picked: " + fname_end
        self.file_picker_button["command"] = None

    def stop_music(self):
        mixer.music.stop()

    def play_music(self):
        mixer.music.play()
        self.master.after(REDRAW_INTERVAL, self.redraw)

    def redraw(self):
        self.redraw_ct += 1
        new_progress_bar_x = floor((self.redraw_ct * self.progress_canvas_width) / self.total_redraws)

        if new_progress_bar_x > self.progress_bar_x:
            self.progress_canvas.move(self.progress_bar, new_progress_bar_x - self.progress_bar_x, 0)
            self.progress_bar_x = new_progress_bar_x

        if mixer.music.get_busy():
            self.master.after(REDRAW_INTERVAL, self.redraw)


root = tk.Tk()
root.geometry('350x200')
root.title('Fingering Helper!')
app = FingeringHelper(master=root)
root.mainloop()

