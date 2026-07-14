import numpy as np

try:
    import av
except ImportError:
    av = None

from scipy.signal import correlate

TARGET_SAMPLE_RATE = 16000


def _extract_audio_samples(video_path, window_seconds):
    if av is None:
        raise ImportError("PyAV est requis pour la synchronisation audio : pip install av")

    container = av.open(str(video_path))
    try:
        if not container.streams.audio:
            raise RuntimeError(
                f"Aucune piste audio dans {video_path} : la synchronisation par clap "
                "nécessite une piste audio sur les deux vidéos GoPro."
            )
        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=TARGET_SAMPLE_RATE)
        target_samples = int(window_seconds * TARGET_SAMPLE_RATE)

        chunks = []
        total = 0
        for frame in container.decode(stream):
            for resampled in resampler.resample(frame):
                array = resampled.to_ndarray().reshape(-1).astype(np.float32)
                chunks.append(array)
                total += array.size
            if total >= target_samples:
                break
    finally:
        container.close()

    if not chunks:
        raise RuntimeError(f"Impossible de décoder l'audio de {video_path}.")

    samples = np.concatenate(chunks)[:target_samples]
    if samples.size == 0:
        raise RuntimeError(f"Piste audio vide dans {video_path}.")
    return samples


def _normalize(samples):
    centered = samples - samples.mean()
    std = centered.std()
    if std > 1e-9:
        centered = centered / std
    return centered


def estimate_offset_frames(video_a, video_b, fps, window_seconds=20.0):
    """
    Estime le décalage entier de frames entre deux vidéos GoPro synchronisées
    par un clap sonore en tout début de prise, via corrélation croisée des
    pistes audio (fps garanti identique entre les deux GoPro, cf. discussion
    projet).

    Convention : la frame `j` de `video_b` correspond à la frame
    `j + offset` de `video_a` (offset > 0 signifie que video_b a démarré
    l'enregistrement après video_a).
    """
    samples_a = _normalize(_extract_audio_samples(video_a, window_seconds))
    samples_b = _normalize(_extract_audio_samples(video_b, window_seconds))

    correlation = correlate(samples_a, samples_b, mode="full", method="fft")
    lag_samples = int(np.argmax(correlation)) - (len(samples_b) - 1)
    offset_seconds = lag_samples / TARGET_SAMPLE_RATE
    return round(offset_seconds * fps)
