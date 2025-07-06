# core/voice_local.py
import sounddevice as sd
import numpy as np
import tempfile
import wave
import speech_recognition as sr

class LocalVoiceRecognizer:
    def __init__(self):
        # Inicializa o reconhecedor de voz da biblioteca speech_recognition
        self.recognizer = sr.Recognizer()

    def capture_audio(self, duration=5, fs=44100):
        # Captura áudio do microfone local por 'duration' segundos e taxa de amostragem 'fs'
        # sd.rec grava o áudio e retorna um array numpy com os dados do som
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Espera até terminar a gravação
        return fs, recording

    def recognize(self, audio_data, fs):
        import os

        # Salva os dados de áudio em um arquivo WAV temporário para ser usado pelo recognizer
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            temp_filename = f.name
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(1)           # Mono
                wf.setsampwidth(2)           # 16 bits (2 bytes)
                wf.setframerate(fs)          # Frequência de amostragem
                wf.writeframes(audio_data.tobytes())  # Escreve os frames do áudio

        try:
            # Usa a API Google Speech Recognition para transcrever o áudio (em português)
            with sr.AudioFile(temp_filename) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio, language="pt-BR").lower()
        except sr.UnknownValueError:
            # Não entendeu o áudio
            return None
        except sr.RequestError:
            # Erro na requisição à API externa
            return None
        finally:
            # Remove o arquivo temporário para não deixar lixo no sistema
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def start_background_listening(self, callback, duration=5, fs=44100):
        import threading
        import time

        def listen(duration_local, fs_local):
            t = threading.currentThread()
            while getattr(t, "do_run", True):
                # Captura e reconhece áudio repetidamente
                fs_captura, audio_data = self.capture_audio(duration_local, fs_local)
                command = self.recognize(audio_data, fs_captura)
                if command:
                    # Executa a função de callback passada com o comando reconhecido
                    callback(command)
                time.sleep(0.5)  # Pequena pausa para evitar uso excessivo de CPU

        # Cria e inicia a thread daemon que ficará rodando em background
        thread = threading.Thread(target=listen, args=(duration, fs))
        thread.daemon = True
        thread.start()
        return thread

    def stop_background_listening(self, thread):
        # Para a thread de reconhecimento de voz se ela estiver ativa
        if thread and thread.is_alive():
            thread.do_run = False  # Sinal para a thread parar
            thread.join()          # Espera a thread terminar
            print("🛑 Reconhecimento de voz desativado.")
        else:
            print("⚠️ O reconhecimento de voz não está ativo ou já foi parado.")
