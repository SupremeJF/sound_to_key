import time
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import cv2
import os
import cv2
import ffmpeg
from queue import Queue
import io
from PIL import Image
import tensorflow as tf
from torchaudio import transforms

def extract_audio(input_file):
    try:
        output_audio = 'temp_audio.wav'
        (
            ffmpeg
            .input(input_file)
            .output(output_audio, vn=True, acodec="pcm_s16le", ar=44100, ac=1, format='wav')
            .run()
        )
        audio_data, sample_rate = librosa.load(output_audio, sr=None, mono=True)
        os.remove(output_audio)
        return audio_data, sample_rate
    except Exception as e:
        print(f"Erreur lors de la séparation de l'audio : {e}")
        return None

def display_frames_and_spectrograms(key_n_frames, key_n_sounds, sample_rate=44100, columns=4):
    plt.figure(figsize=(15, 15))

    for i, key_frame in enumerate(key_n_frames, start=1):
        plt.subplot(2 * (len(key_n_frames) // columns + 1), columns, 2 * i - 1)
        plt.imshow(cv2.threshold(cv2.cvtColor(key_frame["frame"], cv2.COLOR_BGR2GRAY), 127, 255, cv2.THRESH_BINARY)[1])
        plt.title(f"Key: {key_frame['key']}")
        plt.axis('off')

        # Trouver le son associé
        for key_n_sound in key_n_sounds:
            if key_n_sound["key"] == key_frame["key"]:
                audio_segment = key_n_sound["sound"]
                break

        # Générer le spectrogramme
        spectrogram = np.abs(librosa.stft(audio_segment))

        # Afficher le spectrogramme
        plt.subplot(2 * (len(key_n_frames) // columns + 1), columns, 2 * i)
        librosa.display.specshow(librosa.amplitude_to_db(spectrogram, ref=np.max), sr=sample_rate, x_axis='time', y_axis='log')
        plt.colorbar(format='%+2.0f dB')
        plt.tight_layout()

    plt.show()
    
def save_spectro(queue):
    while True:
        print('Ecriture en cours')
        data = queue.get()
        print("on a recu un truc")
        # check for stop
        if data is None:
            break
        spec = spectro_gen(data[0])
        write_data(spec,data[1])     
    # all done
    print('Ecriture finie')
    
def spectro_gen(audio_segment, sample_rate=44100):
    top_db = 80

    # calculer le spectrogramme
    spectrogram = np.abs(librosa.stft(y=audio_segment, n_fft=1024, hop_length=160,win_length=400))

    # convertir en décibels
    spectrogram_db = librosa.amplitude_to_db(spectrogram, ref=np.max, top_db=top_db)
    
    # Normaliser les valeurs entre 0 et 1
    spectrogram_db = (spectrogram_db + top_db) / top_db
    
    # retourner le spectrogramme
    return spectrogram_db

    


def write_data(spectrogram, key):
    # Créer un dossier avec le nom de la clé s'il n'existe pas
    output_directory = f"{key}"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Générer un nom de fichier unique en se basant sur l'heure actuelle
    filename = f"{key}_{str(time.time()).replace('.', '_')}.png"

    # Créer le chemin du fichier de sortie
    output_path = os.path.join(output_directory, filename)
    
    gray_image = (spectrogram * 255).astype(np.uint8)

    # Enregistrer le spectrogramme dans un fichier image
    cv2.imwrite(output_path, gray_image)
    
def load_yamnet_model(model_path):
    model = tf.keras.models.load_model(model_path)
    return model

def process_audio(audio_data, sample_rate):
    if sample_rate != 16000:
        audio_data = librosa.resample(audio_data, sample_rate, 16000)
    return audio_data
