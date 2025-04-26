import os
import wave
import time
import threading
import tkinter as tk
import pyaudio
import numpy as np
from vosk import Model, KaldiRecognizer
import queue
import json


class VoiceRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.title("Voice Recorder")
        self.root.geometry("400x500")
        self.root.configure(bg="black")

        # Button & Label
        self.button = tk.Button(self.root, text="🎤︎︎", font=('arial', 60, "bold"),
                                command=self.click_handler, padx=10, pady=10)
        self.button.pack()

        self.label = tk.Label(self.root, text="Press the button to start recording",
                              font=('arial', 14), bg="black", fg="white")
        self.label.pack(pady=10)

        # Canvas for waveform
        self.canvas = tk.Canvas(self.root, width=400, height=150, bg="black", highlightthickness=0)
        self.canvas.pack()

        # Transcript box
        self.transcript_box = tk.Text(self.root, height=6, width=48, bg="black", fg="white",
                                      font=('arial', 12, "bold"))
        self.transcript_box.insert(tk.END, "Transcript:\n")
        self.transcript_box.config(state=tk.DISABLED)
        self.transcript_box.pack(pady=10)

        self.recording = False

    def transcribe_live(self):
        try:
            model = Model("vosk-model-small-en-us-0.15")
            recognizer = KaldiRecognizer(model, 16000)
            p = pyaudio.PyAudio()

            stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=16000,
                            input=True,
                            frames_per_buffer=8000)

            while self.recording:
                data = stream.read(8000, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    result = recognizer.Result()
                    result_json = json.loads(result)
                    if 'text' in result_json:
                        text = result_json['text']
                        if text.strip():  # only show non-empty text
                            def update_transcript(t=text):
                                self.transcript_box.config(state=tk.NORMAL)
                                self.transcript_box.insert(tk.END, t + "\n")
                                self.transcript_box.config(state=tk.DISABLED)
                                self.transcript_box.see(tk.END)
                            self.root.after(0, update_transcript)

            stream.stop_stream()
            stream.close()
            p.terminate()

        except Exception as e:
            print("❌ Error in transcribe_live():", e)

    def click_handler(self):
        if self.recording:
            self.recording = False
            self.label.config(text="Recording stopped")
        else:
            self.recording = True
            self.label.config(text="Recording...")
            threading.Thread(target=self.record).start()
            threading.Thread(target=self.transcribe_live).start()

    def record(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        frames = []
        self.visual_peaks = []
        start = time.time()

        while self.recording:
            data = stream.read(1024)
            amplitude = np.frombuffer(data, dtype=np.int16)
            peak = np.abs(amplitude).max()

            self.visual_peaks.append(peak)
            if len(self.visual_peaks) > 100:
                self.visual_peaks.pop(0)

            self.canvas.delete("all")
            height = 100
            center = height // 2
            for i, p in enumerate(self.visual_peaks):
                scaled = int((p / 30000) * (height // 2))
                x = i * 3
                y1 = center - scaled
                y2 = center + scaled
                self.canvas.create_line(x, y1, x, y2, fill="green", width=2)

            self.root.update()

            frames.append(data)

            passed = time.time() - start
            secs = passed % 60
            mins = passed // 60
            hours = mins // 60
            mins = mins % 60

            self.label.config(text=f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}")

        stream.stop_stream()
        stream.close()
        audio.terminate()
        self.save(frames, audio)

    def save(self, frames, audio):
        filename = f"recording_{int(time.time())}.wav"
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
        wf.close()
        self.label.config(text=f"Saved as {filename}")


if __name__ == "__main__":
    app = VoiceRecorder()
    app.root.mainloop()
