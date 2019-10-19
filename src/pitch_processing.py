import mp3_utils
import matplotlib.pyplot as plt
import numpy as np

MAGNITUDE_CUTOFF = 200  # cutoff for minimum signal amplitude
ZERO_LEN_CUTOFF = 45  # smallest zero run length (44.1kHz)
MIN_RUN_LEN = 150  # minimum run length to get pitch of (44.1kHz)

ALL_NOTE_NAMES = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']


def get_nonzero_blocks(arr):
    zero_entries = (arr == 0)
    consecutive_zero_blocks = np.copy(zero_entries).astype(np.int)
    for i in range(consecutive_zero_blocks.shape[0]):
        if (i > 0) and (consecutive_zero_blocks[i-1] > 0) and (consecutive_zero_blocks[i] > 0):
            consecutive_zero_blocks[i] = consecutive_zero_blocks[i-1] + 1
    return consecutive_zero_blocks


def get_nonzero_block_bounds(arr, len_cutoff):
    nonzero_blocks = get_nonzero_blocks(arr)
    above_cutoff_locs = np.where(nonzero_blocks >= len_cutoff)[0]
    true_locations_followed_by_false = []
    for i, loc in enumerate(above_cutoff_locs):
        if (i + 1) == above_cutoff_locs.shape[0]:
            true_locations_followed_by_false.append((loc, nonzero_blocks[loc]))
        else:
            if above_cutoff_locs[i+1] != (loc + 1):
                true_locations_followed_by_false.append((loc, nonzero_blocks[loc]))
    return true_locations_followed_by_false


def partition_nonzero_blocks(arr, len_cutoff=1):
    true_locations_followed_by_false = get_nonzero_block_bounds(arr, len_cutoff)
    partition_inds = []
    for loc, run_len in true_locations_followed_by_false:
        start, end = loc - run_len + 1, loc
        partition_inds.append(start)
        partition_inds.append(end)
    all_runs = []

    if arr[0] != 0: # need to add the first block
        run_start = 0
        run_end = arr.shape[0] if len(partition_inds) == 0 else partition_inds[0]
        run = (run_start, run_end), arr[run_start:run_end]
        all_runs.append(run)

    for start_ind in range(1, len(partition_inds), 2):  # start at end of first zero block
        if len(partition_inds) <= (start_ind + 1):  # don't go out of bounds
            continue
        run_inds = (partition_inds[start_ind] + 1, partition_inds[start_ind + 1])
        run = run_inds, arr[run_inds[0]:run_inds[1]]
        all_runs.append(run)
    
    if arr[-1] != 0 and len(partition_inds) > 0:  # need to add the last block
        run_inds = (partition_inds[-1] + 1, arr.shape[0])
        run = run_inds, arr[run_inds[0]:run_inds[1]]
        all_runs.append(run)

    return all_runs


def index_into_arr(all_runs, arr):
    other_runs = []
    for run_tup, _ in all_runs:
        run_start, run_end = run_tup
        other_runs.append((run_tup, arr[run_start:run_end]))
    return other_runs


# shitty test infra ayy
def test_fn(name, fn, inp):
    print(name)
    print(inp)
    print(fn(inp))


def test():
    test_fn("normal", partition_nonzero_blocks, np.array([0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0]))

    test_fn("doesn't start with 0", partition_nonzero_blocks, np.array([1, 1, 1, 0, 0, 0, 1, 0]))

    test_fn("doesn't end with zero", partition_nonzero_blocks, np.array([0, 0, 0, 1, 1, 1, 0, 0, 0, 1]))

    test_fn("short gaps", partition_nonzero_blocks, np.array([0, 1, 0, 1, 0, 1, 0]))

    test_fn("all zeros", partition_nonzero_blocks, np.array([0, 0, 0, 0, 0, 0]))

    test_fn("no zeros", partition_nonzero_blocks, np.array([1, 1, 1, 1, 1, 1]))

    print("test indexing")
    tst_arr = np.array([0, 0, 0, 2, 2, 2, 0, 0, 0, 2, 0])
    print(index_into_arr(partition_nonzero_blocks(tst_arr), tst_arr))


def get_hz(partition):
    partition_inds, partition_vals = partition
    ind_range = np.arange(partition_inds[0], partition_inds[1])
    
    spec = np.fft.fft(partition_vals)
    freq = np.fft.fftfreq(ind_range.shape[-1])
    
    #plt.plot(44100*freq, spec.real)
    #plt.xlim(-5000, 5000)
    #plt.plot(freq, spec.imag)
    #plt.show()
    
    top_k = np.argpartition(np.abs(spec.real), -1)[-1:]
    
    hz = np.median(44100 * np.abs(freq[top_k]))
    
    return hz


def hz_to_note(hz):
    # assumes A4 = 440 Hz
    all_note_names = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

    note_diff = int(round(12*np.log2(hz / 440)))
    
    octave = 4 + note_diff // 12
    note_ind = note_diff % 12
    note_name = all_note_names[note_ind]
    return note_name, octave


def get_notes(partition_li):
    all_notes = []
    for i, partition in enumerate(partition_li):
        print("processing partition {}".format(i))
        hz = get_hz(partition)
        note = hz_to_note(hz)
        all_notes.append((partition[0], note))
    return all_notes


def squish_below_cutoff(arr):
    decrease_abs = np.abs(arr) - MAGNITUDE_CUTOFF
    squished = np.maximum(0, decrease_abs)
    return squished


def remove_smalls(p_li):
    return [p for p in p_li if (p[0][1] - p[0][0]) > MIN_RUN_LEN]


def partition_full_mp3_arr(mp3_arr):
    all_mp3_partitions = partition_nonzero_blocks(squish_below_cutoff(mp3_arr[:, 0]), len_cutoff=ZERO_LEN_CUTOFF)
    orig_mp3_partitions = index_into_arr(all_mp3_partitions, mp3_arr[:, 0])
    proc_mp3_partitions = remove_smalls(orig_mp3_partitions)
    return proc_mp3_partitions


def process_file(fname):
    # load
    frame_rate, mp3_arr = mp3_utils.read(fname)
    print("loaded")

    # partition
    proc_mp3_partitions = partition_full_mp3_arr(mp3_arr)
    print("split into {} partitions".format(len(proc_mp3_partitions)))

    # get all notes
    all_notes = get_notes(proc_mp3_partitions)
    print("got all notes")
    for v in all_notes:
        print(v[1], v[0])


def setup_argparse():
    import argparse
    parser = argparse.ArgumentParser(description='read off all the notes in a file')
    parser.add_argument('fname', help='file name to parse')
    return parser


if __name__=='__main__':
    parser = setup_argparse()
    args = parser.parse_args()
    process_file(args.fname)
