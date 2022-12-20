#!/usr/bin/env bash

lang=en
original_ds=/gpfsssd/scratch/rech/cfs/commun/prosodic_evaluation/prosodic_$lang/syntactic/dev
building_root=/gpfsssd/scratch/rech/cfs/commun/prosodic_evaluation/build_ds
out_ds=/gpfsssd/scratch/rech/cfs/commun/prosodic_evaluation/prosodic_${lang}_augmented/syntactic/dev

#First create new

DATASET_DIR=$building_root/prosodic_$lang

mkdir -p $DATASET_DIR/audio_16k

#ln -s $original_ds/*wav $DATASET_DIR/audio_16k/
for FILE in $original_ds/*wav; do
    out_file="${out_file##*/}"
    ln -s ${FILE} $DATASET_DIR/audio_16k/"${out_file%%.*}" ;
done


#HOME=/gpfsdswork/projects/rech/ank/ucv88ce/
#export PYTHONPATH=$HOME/repos/brouhaha-maker:$HOME/projects/MultilingualCPC/WavAugment:$PYTHONPATH


conda activate pyannote_datamaker

python launch_vad_pynote.py ${DATASET_DIR}/audio_16k --file_extension .wav -o ${DATASET_DIR}/rttm_files


# TODO FIX WHY NOT ALWAYS CREATE SNR FILES. 
if [[ -n $(find  ${DATASET_DIR}/rttm_files -type f -empty) ]]; then
    echo "There are some empty rttm files. Need to be fixed. For now, replacing by dummies"

    for x in $(find ${DATASET_DIR}/rttm_files -type f -empty); do
        fname=$(echo "${x##*/}" | cut -d'_' -f1);
        echo "SPEAKER ${fname}_vad 1 0.0 1.981124997138977 <NA> <NA> A <NA> <NA>" > $x;
    done
    
fi


# Create white noise and add it to WHITENOISE_DIR

DIR_NOISE=$building_root/whitenoise

# TARGET_SNR=30 # should be between 1 and 30


conda activate datamaker
module load libsndfile

#list between 25 and 30 of 9 values.
SNR_list="25 25.625 26.25 26.875 27.5 28.125 28.75 29.375 30"
DATASET_NAME="standard"
OUTPUT_DIR_VAD_DATASET=$DATASET_DIR

for TARGET_SNR in $SNR_list; do
    
    round_snr=$(echo $TARGET_SNR | sed 's/\./-/')
    OUTPUT_DIR_TRANSFORM=$DATASET_DIR/audio_wn${round_snr}_16k;
    
    echo "Adding white noise with SNR ${TARGET_SNR} to ${DATASET_DIR}"
    python build_vad_datasets.py transform $DATASET_NAME $OUTPUT_DIR_VAD_DATASET \
           --name noise --transforms noise --dir-noise $DIR_NOISE --ext-noise .wav \
           --snr-min $TARGET_SNR --snr-max $TARGET_SNR -o $OUTPUT_DIR_TRANSFORM

done



# -------------------


#TODO
python utils_prosody/update_gold.py $DATASET_DIR  $original_ds/gold.csv --snr_name_list "25 25-625 26-25 26-875 27-5 28-125 28-75 29-375 30"


DATASET_DIR=$building_root/prosodic_$lang

mkdir -p $out_ds
cp $DATASET_DIR/gold.csv $out_ds/gold.csv
ln -s $original_ds/*wav $out_ds/

for TARGET_SNR in $SNR_list; do
    s=$(echo $TARGET_SNR | sed 's/\./-/')
    echo "Copying data from SNR $s"
    for FILE in $DATASET_DIR/audio_wn${s}_16k/audio_16k/*wav; do
        out_file="${FILE%%.*}"
        out_file="${out_file##*/}"
        ln -s ${FILE} $out_ds/"${out_file%%.*}"_wn${s}.wav ;
    done
done


