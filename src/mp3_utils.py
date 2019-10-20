import pydub 
import numpy as np

# downloaded from https://www.youtube.com/watch?v=_Frv85_twbc
FILE = "/home/matthew/Documents/projects/shownotes/fingering-helper/data/hotcrossbuns.mp3"


# this is courtesy of stack overflow:
# https://stackoverflow.com/questions/53633177/how-to-read-a-mp3-audio-file-into-a-numpy-array-save-a-numpy-array-to-mp3

def read(f, normalized=False):
  """MP3 to numpy array"""
  a = pydub.AudioSegment.from_mp3(f)
  y = np.array(a.get_array_of_samples())
  if a.channels == 2:
    y = y.reshape((-1, 2))
  if normalized:
    return a.frame_rate, np.float32(y) / 2**15
  else:
    return a.frame_rate, y

def write(f, sr, x, normalized=False):
  """numpy array to MP3"""
  channels = 2 if (x.ndim == 2 and x.shape[1] == 2) else 1
  if normalized:  # normalized array - each item should be a float in [-1, 1)
    y = np.int16(x * 2 ** 15)
  else:
    y = np.int16(x)
  song = pydub.AudioSegment(y.tobytes(), frame_rate=sr, sample_width=2, channels=channels)
  song.export(f, format="mp3", bitrate="320k")
