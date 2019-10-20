import mp3_utils
import numpy as np
import os

MAGNITUDE_CUTOFF = 200  # cutoff for minimum signal amplitude
ZERO_LEN_CUTOFF = 45  # smallest zero run length (44.1kHz)
MIN_RUN_LEN = 150  # minimum note length to get pitch of (44.1kHz)

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

    # this is a confusing way to write this function
    
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


def get_hz(partition, shift_key):
    partition_inds, partition_vals = partition
    ind_range = np.arange(partition_inds[0], partition_inds[1])
    
    spec = np.fft.fft(partition_vals)
    freq = np.fft.fftfreq(ind_range.shape[-1])

    sort_map = np.argsort(freq)
    rev_sort_map = np.argsort(sort_map)
    new_spec = np.zeros_like(spec, dtype=np.complex128)
    
    sorted_freq = freq[sort_map]
    
    shifted_freqs = freq * 2**(shift_key/12.)
    for i in range(shifted_freqs.shape[0]):
        freq_val = shifted_freqs[i]
        spec_val = spec[i]
        closest_ind = np.minimum(np.searchsorted(sorted_freq, freq_val), freq.shape[0]-1)
        new_spec[rev_sort_map[closest_ind]] += spec_val
    
    rev_partition = np.fft.ifft(new_spec)

    big_cutoff = np.percentile(np.abs(new_spec.real), 99.9)

    big_freqs = 44100*np.abs(freq[np.where(np.abs(new_spec.real) > big_cutoff)])
    
    freqs_in_range = np.where(big_freqs < np.min(big_freqs) + 15)

    hz = np.mean(big_freqs[freqs_in_range])
    
    if shift_key == 0:
        return hz, partition_vals
    else:
        return hz, rev_partition

def hz_to_note(hz):
    # assumes A4 = 440 Hz
    all_note_names = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

    note_diff = int(round(12*np.log2(hz / 440)))
    
    octave = 4 + note_diff // 12
    note_ind = note_diff % 12
    note_name = all_note_names[note_ind]
    return note_name, octave


def get_notes(partition_li, shift_key=0):
    all_notes = []
    shifted_partitions = []
    for i, partition in enumerate(partition_li):
        print("processing partition {}".format(i))
        hz, shifted_vals = get_hz(partition, shift_key)
        note = hz_to_note(hz)
        all_notes.append((partition[0], note))
        shifted_partition = (partition[0], shifted_vals)
        shifted_partitions.append(shifted_partition)
    return all_notes, shifted_partitions


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


def overwrite_mp3_arr_new_key(mp3_arr, shifted_partitions):
    new_mp3_arr = np.copy(mp3_arr)
    for partition_inds, partition_vals in shifted_partitions:
        part_start, part_end = partition_inds
        new_mp3_arr[part_start:part_end, 0] = partition_vals
    return new_mp3_arr


def make_new_fname(fname, shift_key):
    print(os.path.split(fname))
    split_fname = list(os.path.split(fname))
    split_fname[-1] = str(shift_key) + "_" + split_fname[-1]
    print(split_fname)
    return os.path.join(*split_fname)


def process_file(fname, shift_key=0):
    # load file
    frame_rate, mp3_arr = mp3_utils.read(fname)
    print("loaded")

    # partition np array
    proc_mp3_partitions = partition_full_mp3_arr(mp3_arr)
    print("split into {} partitions".format(len(proc_mp3_partitions)))

    # get all notes
    all_notes, shifted_partitions = get_notes(proc_mp3_partitions, shift_key)

    # overwrite mp3_arr with changed key
    if shift_key == 0:
        return frame_rate, mp3_arr, all_notes, fname, mp3_arr

    new_mp3_arr = overwrite_mp3_arr_new_key(mp3_arr, shifted_partitions)
    # save new mp3 arr in the new key
    new_fname = make_new_fname(fname, shift_key)
    mp3_utils.write(new_fname, frame_rate, new_mp3_arr[:, 0])
    
    return frame_rate, mp3_arr, all_notes, new_fname, new_mp3_arr


def setup_argparse():
    import argparse
    parser = argparse.ArgumentParser(description='read off all the notes in a file')
    parser.add_argument('fname', help='file name to parse')
    return parser


if __name__=='__main__':
    parser = setup_argparse()
    args = parser.parse_args()
    _, _, all_notes, _ = process_file(args.fname)
    print("got all notes")
    for v in all_notes:
        print(v[1], v[0])
