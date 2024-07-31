from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
from pathlib import Path
import wavio
import uuid
from .audio_transcriber import AudioTranscriber
from .audio_recorder import AudioRecorder

class AudioRecordingGUI:
  def __init__(self, root, title, callback, **kwargs):
    self.callback = callback
    self.recorder = AudioRecorder()
    self.audio_data = None
    self.results = []

    self.kwargs = kwargs

    self.root = root
    self.root.title(title)

    self.main_frame = Frame(self.root)
    self.main_frame.grid(padx=20, pady=20, sticky='we')
    for i in range(5):
      self.main_frame.columnconfigure(i, minsize=50, weight=1)

    self.start_btn = Button(self.main_frame, text='Start', command=self.start)
    self.start_btn.grid(row=0, column=0, padx=5)

    self.toggle_btn = Button(self.main_frame, text='Pause', command=self.toggle, state=DISABLED)
    self.toggle_btn.grid(row=0, column=1, padx=5)

    self.stop_btn = Button(self.main_frame, text='Stop', command=self.stop, state=DISABLED)
    self.stop_btn.grid(row=0, column=2, padx=5)

    self.restart_btn = Button(self.main_frame, text='Restart', command=self.restart, state=DISABLED)
    self.restart_btn.grid(row=0, column=4, sticky=E, padx=5)

    self.list_btn = Button(self.main_frame, text='List Results', command=self.list_results)
    self.list_btn.grid(row=1, column=0, columnspan=4, sticky='we', padx=5)

    self.quit_btn = Button(self.main_frame, text='Quit', command=self.root.destroy)
    self.quit_btn.grid(row=2, column=0, columnspan=4, sticky='we', padx=5)

  def start(self):
    self.recorder.start_recording()
    self.start_btn.configure(state=DISABLED)
    self.toggle_btn.configure(state=NORMAL)
    self.stop_btn.configure(state=NORMAL)
    self.restart_btn.configure(state=DISABLED)

  def toggle(self):
    self.recorder.toggle_recording()
    if self.toggle_btn.cget('text') == 'Pause':
      self.toggle_btn.configure(text='Resume', state=NORMAL)
    else:
      self.toggle_btn.configure(text='Pause', state=NORMAL)
    self.stop_btn.configure(state=NORMAL)

  def stop(self):
    self.start_btn.configure(state=NORMAL)
    self.toggle_btn.configure(text='Pause', state=DISABLED)
    self.stop_btn.configure(state=DISABLED)
    self.restart_btn.configure(state=NORMAL)

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
    self.start_btn.configure(state=NORMAL)
    self.toggle_btn.configure(text='Pause', state=DISABLED)
    self.stop_btn.configure(state=DISABLED)
    self.restart_btn.configure(state=DISABLED)
    self.recorder.recordings = []
    self.audio_data = None

  def list_results(self):
    info_str = ''
    for filepath, texts in self.results:
      info_str += f'{filepath}:'
      info_str += f'{texts[0]}\n'

    messagebox.showinfo("Results", info_str)

