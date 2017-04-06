import csv
import h5py
from collections import defaultdict
import numpy as np
import os


def extract_detections(path_data, path_csv, path_output):

    CUBE_SZ = 54

    # parse the detections csv
    with open(path_csv, "r") as f:
        reader = csv.reader(f)
        list_detections = list(reader)
    list_detections.pop(0)
    detections = defaultdict(lambda: [])
    for entry in list_detections:
        detections[entry[0]].append((int(float(entry[1])),
                                     int(float(entry[2])),
                                     int(float(entry[3]))))

    log_filename = "{}.log".format(os.path.splitext(path_output)[0])

    # crop detected ROIs and write to hdf5 file
    i_counter = 0
    n_counter = len(detections.keys())
    with open(log_filename, "w") as log_file:
        with h5py.File(path_output, "w") as f_h5:
            for id, coords in detections.items():

                # load CT scan (ct_scan is [z, x, y])
                try:

                    ct_scan = np.load(os.path.join(path_data, 
                                                   "{}.npy".format(id)))
                    crops = np.zeros((CUBE_SZ, CUBE_SZ, CUBE_SZ, len(coords)))

                    # pad ct_scan and crop
                    i_counter += 1
                    if i_counter % 10 == 0:
                        print("*** extracting {}/{}" \
                            .format(i_counter, n_counter))
                    ct_scan_shape = ct_scan.shape
                    ct_scan = np.pad(ct_scan, CUBE_SZ, "constant")
                    for i, xyz in enumerate(coords):
                        try:
                            crops[:, :, :, i] = ct_scan[
                                xyz[2] + CUBE_SZ : xyz[2] + 2 * CUBE_SZ,
                                xyz[0] + CUBE_SZ : xyz[0] + 2 * CUBE_SZ,
                                xyz[1] + CUBE_SZ : xyz[1] + 2 * CUBE_SZ]

                        
                        except ValueError:
                            print("*** ERROR in {}".format(i_counter))
                            log_file.write("Error in {}, shape: {}, xyz: {}\n" \
                                .format(id, ct_scan_shape, xyz))

                    # write
                    f_h5.create_dataset(id,
                                        shape=crops.shape,
                                        dtype=np.int16,
                                        data=crops)

                except IOError:

                    print("*** ERROR in {}".format(i_counter))
                    log_file.write("File {}.npy not found!\n" \
                        .format(id, ct_scan_shape, xyz))