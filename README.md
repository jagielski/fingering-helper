# fingering-helper
Play an mp3 file and display fingerings for the recorder alongside the music. Great for learning a new song or getting accustomed to a new instrument!

## Usage

1. Identify an mp3 file of interest! It should be pretty noise-free, and cannot contain any slurred notes. This youtube channel produces excellent videos for this purpose: https://www.youtube.com/channel/UCjRO1LHScDOXa-hR8u0ZO2A.

2. Choose your key! Only a couple are supported right now, and C Major is assumed. Changing the key will decrease the quality of the sound.

3. Navigate to your mp3 file within the app. This will load the file and parse it, identifying all notes in the file and changing the key if specified. This is where the hard signal processing work happens, so this might take some time depending on the length of your video and the length of the notes being played.

4. Press Play! Your key-adjusted mp3 will play, and the fingerings for your instrument will be displayed while they are being played in the mp3. Enjoy!


## Limitations/Plans for Future Work
1. Robustness of pitch detection. This would expand the range of mp3 files that could be used. Currently, each note must be separated by some silence in the video (so no slurs!), and the environment should be fairly noise-free (so no arbitrary videos, mainly just synthesized music for now). Fortunately, this is a result of the simple pitch detection algorithm currently in use, and could be fixed by leveraging more robust algorithms from the literature (such as YAAPT http://ws2.binghamton.edu/zahorian/yaapt.htm or YIN http://audition.ens.fr/adc/pdf/2002_JASA_YIN.pdf).

2. Prettiness/more instruments. The fingering diagrams could be implemented directly in the app, which would prevent them from jittering and would take up less space in the assets. More instruments would be very easy to add, too. It currently only supports the Soprano Recorder.

3. User experience could be improved. Pause doesn't work very well, navigating within the file would be nice.
