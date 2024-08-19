from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
from pathlib import Path
import wavio
import uuid
from datetime import datetime, timedelta
from .audio_transcriber import AudioTranscriber
from .audio_recorder import AudioRecorder

class AudioRecordingGUI:
  def __init__(self, root, title, callback, **kwargs):
    self.callback = callback
    self.recorder = AudioRecorder()
    self.audio_data = None
    self.results = []

    self.isTicking = False
    self.start_time = None
    self.elapsed_time = timedelta()

    self.kwargs = kwargs

    style = Style()
    style.configure('timer.TLabel', foreground='red', font=('Helvetica', 24))

    self.root = root
    self.root.title(title)

    self.main_frame = Frame(self.root)
    self.main_frame.grid(row=0, column=0)
    for i in range(5):
      self.main_frame.columnconfigure(i, minsize=50, weight=1)

    self.timer = Label(self.main_frame, text='00:00', style='timer.TLabel')
    self.timer.grid(row=0, column=0, columnspan=5, padx=5, pady=5)

    self.start_btn = Button(self.main_frame, text='Start', command=self.start)
    self.start_btn.grid(row=1, column=0, sticky=W, padx=10)

    self.toggle_btn = Button(self.main_frame, text='Pause', command=self.toggle, state=DISABLED)
    self.toggle_btn.grid(row=1, column=1, sticky=W, padx=10)

    self.stop_btn = Button(self.main_frame, text='Stop', command=self.stop, state=DISABLED)
    self.stop_btn.grid(row=1, column=2, sticky=W, padx=10)

    self.restart_btn = Button(self.main_frame, text='Restart', command=self.restart, state=DISABLED)
    self.restart_btn.grid(row=1, column=4, sticky=E, padx=10)

    self.quit_btn = Button(self.main_frame, text='Quit', command=self.quit)
    self.quit_btn.grid(row=2, column=0, columnspan=5, sticky='we', padx=10, pady=10)

  def start(self):
    self.reset_timer()
    self.start_timer()
    self.recorder.start_recording()
    self.start_btn.configure(state=DISABLED)
    self.toggle_btn.configure(state=NORMAL)
    self.stop_btn.configure(state=NORMAL)
    self.restart_btn.configure(state=NORMAL)

  def toggle(self):
    if self.isTicking:
      self.stop_timer()
    else:
      self.start_timer()
    self.recorder.toggle_recording()
    if self.toggle_btn.cget('text') == 'Pause':
      self.toggle_btn.configure(text='Resume', state=NORMAL)
    else:
      self.toggle_btn.configure(text='Pause', state=NORMAL)
    self.stop_btn.configure(state=NORMAL)

  def stop(self):
    self.stop_timer()
    self.start_btn.configure(state=NORMAL)
    self.toggle_btn.configure(text='Pause', state=DISABLED)
    self.stop_btn.configure(state=DISABLED)
    self.restart_btn.configure(state=DISABLED)

    self.audio_data = self.recorder.stop_recording()
    if self.audio_data is not None:
      should_save = messagebox.askyesno("Save Recording", "Do you want to save the recording?")
      if should_save:
        self.save()
      else:
        self.restart()
    else:
      self.restart()

  def save(self):
    path = Path('./_recordings')
    if not path.exists():
      path.mkdir(parents=True, exist_ok=True)
    filepath = path / f'{str(uuid.uuid4())}.wav'

    try:
      wavio.write(filepath.as_posix(), self.audio_data, self.recorder.samplerate, sampwidth=2)

      transcriber = AudioTranscriber(filepath, **self.kwargs)
      transcriber.transcribe()
      self.results.append((filepath, transcriber.texts))

      self.callback(transcriber.texts[0])
    except Exception as e:
      messagebox.showerror(title='Error', message=f'{e}')
    finally:
      self.restart()

  def restart(self):
    self.reset_timer()
    self.start_btn.configure(state=NORMAL)
    self.toggle_btn.configure(text='Pause', state=DISABLED)
    self.stop_btn.configure(state=DISABLED)
    self.restart_btn.configure(state=DISABLED)
    self.recorder.recordings = []
    self.audio_data = None

  def start_timer(self):
    if not self.isTicking:
      self.isTicking = True
      if not self.start_time:
        self.start_time = datetime.now() - self.elapsed_time
      self.update_timer()

  def stop_timer(self):
    if self.isTicking:
      self.isTicking = False
      self.start_time = datetime.now()
      self.elapsed_time = datetime.now() - self.start_time

  def reset_timer(self):
    self.isTicking = False
    self.start_time = None
    self.elapsed_time = timedelta()
    self.timer.config(text='00:00')

  def update_timer(self):
    if self.isTicking:
      elapsed_time = datetime.now() - self.start_time
      mins, secs = divmod(elapsed_time.seconds, 60)
      self.timer.config(text=f'{mins:02}:{secs:02}')
      self.root.after(1000, self.update_timer)

  def quit(self):
    self.stop()
    self.reset_timer()
    if self.recorder.audio_thread:
      self.recorder.audio_thread.join()
    self.root.destroy()

