from numpy import log10, cumsum, arange
from copy import deepcopy
import random
from copy import deepcopy
from pathlib import Path
import torch
import torchaudio
import tqdm
from cpc_dataset_maker.transforms.transform import Transform
from cpc_dataset_maker.transforms.labels import SNR_LABEL, DETAILED_SNR, RMS_LABEL, SPEECH_ACTIVITY_LABEL
from cpc_dataset_maker.transforms.normalization import (
    energy_normalization,
    energy_normalization_on_vad,
    peak_normalization,
)
from typing import Any, Dict, Set, List, Tuple, Union

SNR_NO_NOISE = 30
CROSSFADE_MAX = 50


def compute_detailed_snr(audio_data: torch.Tensor, noise: torch.Tensor, sample_rate, step: float = 0.01, window_size: int = 2) -> List[List[float]]:
    """
    Compute the mean snr every step on a sliding window of size window_size.
    step and window_size are in seconds
    """
    window_frames = int(window_size * sample_rate)
    step_in_frames = int(step * sample_rate)

    detailed_snr = list()

    power_audio = cumsum([x**2 for x in audio_data])
    power_noise = cumsum([x**2 for x in noise])

    start_windows = arange(0, audio_data.size()[0] - window_frames + 1, step_in_frames)
    end_windows = arange(window_frames - 1, audio_data.size()[0], step_in_frames)
 
    signal_to_noise = [(power_audio[end] - power_audio[start]) / (power_noise[end] - power_noise[start]) \
                        for start, end in zip(start_windows, end_windows)]
    # signal_to_noise = (power_audio[end_windows] - power_audio[start_windows]) / (power_noise[end_windows] - power_noise[start_windows])
 
    snr_db = 10 * log10(signal_to_noise)
    detailed_snr = zip(start_windows, end_windows, snr_db)

    return detailed_snr


def save_detailed_snr_labels(values: List[float], file_path: Union[Path, str]) -> None:
    seq_name = Path(file_path).stem
    with open(file_path, "w") as rttm_file:
        for start, end, snr in values:
            rttm_file.write(
                f"{seq_name} {start} {end} {snr}\n"
            )


# add noise to audio files
class AddNoise(Transform):
    def __init__(
        self,
        dir_noise: Union[str, Path],
        ext_noise: str = ".flac",
        snr_min: float = 0.1,
        snr_max: float = 0.9 * SNR_NO_NOISE,
        snr_no_noise: float = SNR_NO_NOISE,
    ):
        self.dir_noise = Path(dir_noise)
        self.noise_files = [
            str(x) for x in self.dir_noise.glob(f"**/*{ext_noise}")
        ]
        self.snr_no_noise = snr_no_noise
        self.ext_noise = ext_noise  # extension of noise sequences

        self.snr_min = snr_min  # minimum value for SNR
        self.snr_max = snr_max  # maximum value for SNR
        print(
            f"Add noise to audio files with a random SNR between {snr_min} and {snr_max}"
        )
        self.load_noise_db()

    def load_noise_db(self) -> None:

        print("Loading the noise dataset")
        noise_data = []
        random.shuffle(self.noise_files)
        for x in tqdm.tqdm(self.noise_files, total=len(self.noise_files)):
            noise_data.append(torchaudio.load(x)[0].mean(dim=0))

        self.noise_data = torch.cat(noise_data, dim=0)
        print("Dataset loaded")

    @property
    def input_labels(self) -> Set[str]:
        return set()

    @property
    def output_labels(self) -> Set[str]:
        return {RMS_LABEL, SNR_LABEL, DETAILED_SNR}

    @property
    def size_noise(self) -> int:
        return len(self.noise_data)

    @property
    def init_params(self) -> Dict[str, Any]:
        return {
            "ext_noise": self.ext_noise,
            "dir_noise": str(self.dir_noise),
            "noise_files": self.noise_files,
            "snr_min": self.snr_min,
            "snr_max": self.snr_max,
            "snr_no_noise": self.snr_no_noise,
        }

    def __call__(
        self, audio_data: torch.tensor, sr: int, label_dict: Dict[str, Any]
    ) -> Tuple[torch.tensor, Dict[str, Any]]:

        audio_nb_frames = audio_data.size(0)

        # set a random SNR
        snr = random.random() * (self.snr_max - self.snr_min) + self.snr_min
        if snr >= self.snr_no_noise:
            snr = self.snr_no_noise
        a = float(snr) / 20
        noise_rms = 1 / (10 ** a)

        # if noise sequences are shorter than the audio file, add different
        # noise sequences one after the other
        frame_start = random.randint(0, self.size_noise - audio_nb_frames)
        noise_seq_torch = self.noise_data[frame_start : frame_start + audio_nb_frames]

        audio_data_normalized = energy_normalization_on_vad(audio_data, label_dict[SPEECH_ACTIVITY_LABEL], sr)
        noise = energy_normalization(noise_seq_torch) * noise_rms

        y = peak_normalization(
            audio_data_normalized
            + noise
        )
        new_labels = deepcopy(label_dict)
        new_labels[RMS_LABEL] = noise_rms
        new_labels[SNR_LABEL] = snr
        new_labels[DETAILED_SNR] = compute_detailed_snr(audio_data_normalized, noise, sr)

        return y, new_labels
