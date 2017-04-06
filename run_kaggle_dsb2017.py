"""Process, detect, train and predict"""

import kaggle.classifier
import kaggle.util
import subprocess
import csv
import os
import keras.optimizers

#import ptvsd
#ptvsd.enable_attach(None, address = ('0.0.0.0', 3000))
#print("Waiting for attach.")
#ptvsd.wait_for_attach()

# paths to raw data
PATH_TRAIN_DATA = "/path/to/training_data"
PATH_TEST_DATA = "/path/to/test/data"
PATH_TRAIN_LABELS = "/razberry/datasets/kaggle-dsb2017/stage1_labels.csv"

# paths to processed data
PATH_TRAIN_PROCESSED = "/path/to/train_proc"
PATH_TEST_PROCESSED = "/path/to/test_proc"

# other paths
PATH_DATASETS = "/razberry/datasets/kaggle-dsb2017"
PATH_WORKSPACE = "/razberry/workspace"

# parameters
N_CROSS_VAL = 2

# session header
version = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
version = version.strip().decode("ascii")
path_session = os.path.join(PATH_WORKSPACE, "dsb2017.{}".format(version))
if not os.path.exists(path_session):
    os.mkdir(path_session)

# TODO: process (both train and test)


"""
# TODO: detection (both train and test)
train_csv = os.path.join(PATH_DATASETS, "detections_train.csv")
test_csv = os.path.join(PATH_DATASETS, "detections_test.csv")

# extract crops around detections (both train and test)
kaggle.util.extract_detections(PATH_TRAIN_DATA, train_csv,
                               os.path.join(PATH_DATASETS,
                                            "detections_train.hdf5"))
kaggle.util.extract_detections(PATH_TEST_DATA, test_csv,
                               os.path.join(PATH_DATASETS,
                                            "detections_test.hdf5"))
"""

# train an ensemble of classifiers
hyper_param = {
    # optimization
    "epochs" : 1,
    "batch_sz": [4],
    "optimizers": [keras.optimizers.Adam(1e-4)],
    "lr_scheduler_param": [(1e-4, 5, 10), (1e-4, 10, 20)],
    # architecture
    "dropout_rate": [0.5],
    "batch_norm": [True],
    "pool_type" : ["both"]
    }

models =[]
session_id = os.path.basename(path_session)
for i in range(0, N_CROSS_VAL):

    print("*** Training and cross validation {}/{}".format(i + 1, N_CROSS_VAL))

    # split to training and validation sets
    train, val = kaggle.classifier.split_train_val(PATH_TRAIN_LABELS,
                                                   seed=int(version, 16) + i)

    path_session_i = os.path.join(path_session, "{}_".format(i) + session_id)
    if not os.path.exists(path_session_i):
        os.mkdir(path_session_i)

    models.append(kaggle.classifier.train_ensemble(
        train,
        val,
        os.path.join(PATH_DATASETS, "stage1_detections_mock.hdf5"),
        path_session_i,
        hyper_param))


# predict on test dir (stage-1 holdout and stage-2)
test_ids = [os.path.splitext(id)[0] for id in os.listdir(PATH_TEST_PROCESSED)]
kaggle.classifier.predict_ensemble(
    models,
    os.path.join(PATH_DATASETS, "stage1_detections_mock.hdf5"),
    test_ids,
    os.path.join(path_session))

