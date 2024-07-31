__version__ = '1.2.0'

from openai import OpenAI
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
from tkinter import messagebox
import re
from tkinter import Toplevel
import helpers.notion_api as api
from helpers.constants import *
from helpers.audio_recording_gui import AudioRecordingGUI
from helpers.audio_transcriber import AudioTranscriber

class SpeakingAssistant(Frame):
  def __init__(self, root, **kwargs):
    super().__init__(root, **kwargs)

    style = Style()
    style.configure('Alert.TLabel', foreground='red')

    self.kwargs = kwargs

    self.root = root
    self.root.title('Speaking Mania')

    self.filepath = None
    self.test_part = ''
    self.question = ''
    self.original_answer = ''
    self.revised_answer = ''

    self.audio_app_window = None
    self.audio_app = None

    self.should_show_alert_msg_answer = False

    self.main_frame = Frame(self.root)
    self.main_frame.grid(padx=20, pady=20, sticky='we')

    # select execution mode
    self.mode_select_frame = Frame(self.main_frame)
    self.mode_select_frame.grid(row=0, column=0, sticky='we')
    self.mode_select_frame.columnconfigure(0, minsize=100, weight=1)
    self.mode_select_frame.columnconfigure(1, minsize=100, weight=1)
    self.mode_select_frame.columnconfigure(2, minsize=100, weight=1)
    self.mode_select_frame.columnconfigure(3, minsize=100, weight=1)

    Label(self.mode_select_frame, text='Select execution mode:').grid(row=0, column=0, sticky=W, padx=5)

    self.mode_select = Combobox(self.mode_select_frame, values=MODES)
    self.mode_select.grid(row=1, column=0, columnspan=4, sticky='we', padx=5)
    self.mode_select.current(0)
    self.mode = self.mode_select.get().strip()

    # select widgets group
    self.test_part_select_frame = Frame(self.main_frame)
    self.test_part_select_frame.grid(row=1, column=0, sticky='we')
    self.test_part_select_frame.columnconfigure(0, minsize=100, weight=1)
    self.test_part_select_frame.columnconfigure(1, minsize=100, weight=1)
    self.test_part_select_frame.columnconfigure(2, minsize=100, weight=1)
    self.test_part_select_frame.columnconfigure(3, minsize=100, weight=1)

    Label(self.test_part_select_frame, text='Select test part:').grid(row=0, column=0, sticky=W, padx=5)

    self.test_part_select = Combobox(self.test_part_select_frame, values=list(PARTS.keys()))
    self.test_part_select.grid(row=1, column=0, columnspan=4, sticky='we', padx=5)
    self.test_part_select.bind('<<ComboboxSelected>>', self._on_select_test_part)

    self.alert_msg_test_part = Label(self.test_part_select_frame, text='You must choose a part.', style='Alert.TLabel')

    # question entry widgets group
    self.question_frame = Frame(self.main_frame)
    self.question_frame.grid(row=2, column=0, sticky='we')
    self.question_frame.columnconfigure(0, minsize=100, weight=1)
    self.question_frame.columnconfigure(1, minsize=100, weight=1)
    self.question_frame.columnconfigure(2, minsize=100, weight=1)
    self.question_frame.columnconfigure(3, minsize=100, weight=1)

    Label(self.question_frame, text='Question:').grid(row=0, column=0, sticky=W, padx=5)

    self.question_entry = Entry(self.question_frame)
    self.question_entry.grid(row=1, column=0, columnspan=3, sticky='we', padx=5)
    self.question_entry.bind('<KeyPress>', self._on_key_press)

    self.question_record_btn = Button(self.question_frame, text='Record', command=self.record_question)
    self.question_record_btn.grid(row=1, column=3, sticky='we', padx=5)

    self.alert_msg_question = Label(self.question_frame, text='Question cannot be empty.', style='Alert.TLabel')

    # answer widgets group
    self.answer_frame = Frame(self.main_frame)
    self.answer_frame.grid(row=3, column=0, sticky='we')
    self.answer_frame.columnconfigure(0, minsize=100, weight=1)
    self.answer_frame.columnconfigure(1, minsize=100, weight=1)
    self.answer_frame.columnconfigure(2, minsize=100, weight=1)
    self.answer_frame.columnconfigure(3, minsize=100, weight=1)

    Label(self.answer_frame, text='Answer:').grid(row=0, column=0, sticky=W, padx=5)

    self.filepath_btn = Button(self.answer_frame, text='Select Audio File', command=self.open_file_browser)
    self.filepath_btn.grid(row=1, column=0, columnspan=3, sticky='we', padx=5)

    self.answer_record_btn = Button(self.answer_frame, text='Record', command=self.record_answer)
    self.answer_record_btn.grid(row=1, column=3, sticky='we', padx=5)

    self.answer_label = Label(self.answer_frame, text='')
    self.answer_label.grid(row=2, column=0, columnspan=4, padx=5)

    self.alert_msg_answer = Label(self.answer_frame, text='Answer cannot be empty.', style='Alert.TLabel')

    # button widgets group
    self.buttons_frame = Frame(self.main_frame)
    self.buttons_frame.grid(row=4, column=0, sticky='we')
    self.buttons_frame.columnconfigure(0, minsize=100, weight=1)
    self.buttons_frame.columnconfigure(1, minsize=100, weight=1)
    self.buttons_frame.columnconfigure(2, minsize=100, weight=1)
    self.buttons_frame.columnconfigure(3, minsize=100, weight=1)

    self.gen_btn = Button(self.buttons_frame, text='Generate Text', command=self.generate_text)
    self.gen_btn.grid(row=0, column=0, columnspan=2, sticky='we', padx=5)

    self.quit_btn = Button(self.buttons_frame, text='Quit', command=lambda: self.root.quit())
    self.quit_btn.grid(row=0, column=2, columnspan=2, sticky='we', padx=5)

  def _show_alert_msg(self, msg_widget, row_index, col_index):
    msg_widget.grid(row=row_index, column=col_index, sticky=W, padx=5)

  def _on_select_test_part(self, event):
    self.alert_msg_test_part.grid_forget()

  def _on_key_press(self, event):
    self.alert_msg_question.grid_forget()

  def _question_callback(self, transcript):
    self.question_entry.delete(0, END)
    self.question_entry.insert(0, transcript)
    self.question = transcript

  def _answer_callback(self, transcript):
    self.answer_label.configure(text=f'{transcript[:10]}...')
    self.original_answer = transcript.strip()

  def _initialize_audio_app(self, title, callback):
    self.audio_app_window = Toplevel(self.root)
    self.audio_app = AudioRecordingGUI(self.audio_app_window, title, callback, mode='local', **self.kwargs)

  def record_question(self):
    if self.audio_app_window:
      self.audio_app_window.destroy()
    self.audio_app = None

    self.alert_msg_question.grid_forget()

    self._initialize_audio_app('Record Question', self._question_callback)

  def record_answer(self):
    if self.audio_app_window:
      self.audio_app_window.destroy()
    self.audio_app = None

    self.alert_msg_answer.grid_forget()

    self._initialize_audio_app('Record Answer', self._answer_callback)

  def open_file_browser(self):
    self.alert_msg_answer.grid_forget()

    self.filepath = filedialog.askopenfilename()
    if self.filepath:
      self.answer_label.configure(text=self.filepath)

  def generate_text(self):
    self.test_part = self.test_part_select.get()
    if not self.test_part:
      self._show_alert_msg(self.alert_msg_test_part, 2, 0)
      return

    self.question = self.question_entry.get().strip()
    if not self.question:
      self._show_alert_msg(self.alert_msg_question, 2, 0)
      return

    try:
      if self.filepath:
        if self.mode == 'Local Whisper':
          transcriber = AudioTranscriber(self.filepath, mode='local')
        else:
          transcriber = AudioTranscriber(self.filepath, mode='remote')
        transcriber.transcribe()
        self.original_answer = transcriber.texts[0].strip()

      if not self.original_answer:
        self._show_alert_msg(self.alert_msg_answer, 2, 0)
        return

      # Pass the text to completion API for revision
      client = OpenAI()
      completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
          {
            'role': 'system',
            'content': f'This is {self.test_part} of a practice IELTS speaking test. The question is: {self.question} And following is my answer. Can you revise it for 8.5-point or higher? Please keep your length similar to mine and please do not provide any other text in your response than the revised answer.'
          },
          {
            'role': 'user',
            'content': self.original_answer
          }
        ]
      )
      self.revised_answer = completion.choices[0].message.content

      data = {
        "children": [
          api.create_block_object("heading_2", ("text", self.question.capitalize())),
          api.create_block_object("heading_3", ("text", "My answer:")),
          api.create_block_object("paragraph", ("text", self.original_answer)),
          api.create_block_object("heading_3", ("text", "ChatGPT answer:")),
          api.create_block_object("paragraph", ("text", self.revised_answer)),
        ]
      }

      url = URL_SEG1 + PARTS[self.test_part] + URL_SEG2
      api.send_patch_request(url, NOTION_API_TOKEN, data)
      messagebox.showinfo(title="Done", message="Task succeeded.")
    except Exception as e:
      messagebox.showerror(title='Error', message=f'{e}')

if __name__ == "__main__":
  root = Tk()
  app = SpeakingAssistant(root)
  app.mainloop()
