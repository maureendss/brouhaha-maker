# Installation

## Environment for SNR - C50 prediction

```
conda env create -f env_datamaker.yml
conda activate datamaker
```

## Environment for VAD

```
conda env create -f env_pyannote.yml
conda activate pyannote_datamaker
```

## Build the environment
```
CC=gcc python setup.py build_ext --inplace
python setup.py
```

### Building the data

To have the data in the correct format, you simply have to have one audio dir, within which there is an audio_16k dir, which contains all the audio. 
When asked, DATASET_DIR is the parent "audio".


# Launching pyannote on a dataset

## Inference

The VAD rttm file is needed to calculate the energy of the auio files (we don't want to take into account the pauses)

To run a pyannote inference on a dataset, you can use the script `vad_pyannote/launch_vad_pyannote.py`:

```
python vad_pyannote/launch_vad_pyannote.py ${DATASET_DIR}/audio_16k \
                                            --file_extension .flac
                                            -o ${DATASET_DIR}/rttm_files
```

This script takes advantage of all available GPUs. You can launch it on scrum to deal efficiently with large dataset.


# Apply white noise augmentation to the dataset

To transform your dataset, you will need to use `build_vad_datasets.py` as follow:

## Noise Augmentation


Set dir noise to a dataset which contains one long white noise segment. Careful, it is important that there is only one audio in the dataset, which is also longer than the longest audio.

You can create this white noise using for example audacity (make sure to save it with a 16k sample rate). It should be longer than any segments in the evaluation set (eg 30s)
Set SNR_MIN and MAX to the required value (max 30, min 1)
In decibels (the decibel ratio difference between the 2)

#For example, if you want an equally spaced range of 9 numbers between 1 and 30 you can use : 
[ 1.   ,  4.625,  8.25 , 11.875, 15.5  , 19.125, 22.75 , 26.375, 30.   ])

```
python build_vad_datasets.py transform $DATASET_NAME \
                             $OUTPUT_DIR_VAD_DATASET \
                             --name noise \
                             --transforms noise \
                             --dir-noise $DIR_NOISE \
                             --ext-noise .wav \
                             --snr-min $TARGET_SNR \
                             --snr-max $TARGET_SNR \
                             -o $OUTPUT_DIR_TRANSFORM \
```


# Additional ressources:

Google drive: https://drive.google.com/drive/folders/1XXc8526sIsfg6w8h7oOUF9fWC-9ap2Uu?usp=sharing
