from openai import OpenAI
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
from tkinter import messagebox
import re
import helpers.notion_api as api
from helpers.constants import *

class SpeakingAssistant(Frame):
  def __init__(self, root):
    super().__init__(root)

    style = Style()
    style.configure('Alert.TLabel', foreground='red')

    self.root = root
    self.root.title = 'Speaking Assistant'
    self.filepath = None
    self.original_answer = None
    self.revised_answer = None
    self.test_part = ''
    self.question = ''

    self.main_frame = Frame(self.root)
    self.main_frame.grid(padx=20, pady=20, sticky='we')

    # select widgets group
    self.select_frame = Frame(self.main_frame)
    self.select_frame.grid(row=0, column=0, sticky='we')
    self.select_frame.columnconfigure(0, minsize=100, weight=1)
    self.select_frame.columnconfigure(1, minsize=100, weight=1)
    self.select_frame.columnconfigure(2, minsize=100, weight=1)
    self.select_frame.columnconfigure(3, minsize=100, weight=1)

    Label(self.select_frame, text='Select test part:').grid(row=0, column=0, sticky=W, padx=5)

    self.select = Combobox(self.select_frame, values=list(PARTS.keys()))
    self.select.grid(row=1, column=0, columnspan=4, sticky='we', padx=5)
    self.select.bind('<<ComboboxSelected>>', self._on_select)

    self.alert_msg_test_part = Label(self.select_frame, text='You must choose a part.', style='Alert.TLabel')

    # question entry widgets group
    self.question_frame = Frame(self.main_frame)
    self.question_frame.grid(row=1, column=0, sticky='we')
    self.question_frame.columnconfigure(0, minsize=100, weight=1)
    self.question_frame.columnconfigure(1, minsize=100, weight=1)
    self.question_frame.columnconfigure(2, minsize=100, weight=1)
    self.question_frame.columnconfigure(3, minsize=100, weight=1)

    Label(self.question_frame, text='Question:').grid(row=0, column=0, sticky=W, padx=5)

    self.question_entry = Entry(self.question_frame)
    self.question_entry.grid(row=1, column=0, columnspan=4, sticky='we', padx=5)
    self.question_entry.bind('<KeyPress>', self._on_key_press)

    self.alert_msg_question = Label(self.question_frame, text='You must enter a question.', style='Alert.TLabel')

    # file select widgets group
    self.file_select_frame = Frame(self.main_frame)
    self.file_select_frame.grid(row=2, column=0, sticky='we')
    self.file_select_frame.columnconfigure(0, minsize=100, weight=1)
    self.file_select_frame.columnconfigure(1, minsize=100, weight=1)
    self.file_select_frame.columnconfigure(2, minsize=100, weight=1)
    self.file_select_frame.columnconfigure(3, minsize=100, weight=1)

    self.filepath_btn = Button(self.file_select_frame, text='Select Audio File', command=self.open_file_browser)
    self.filepath_btn.grid(row=0, column=0, columnspan=4, sticky='we', padx=5)

    self.filepath_label = Label(self.file_select_frame, text='')
    self.filepath_label.grid(row=1, column=0, columnspan=4, padx=5)

    self.alert_msg_file = Label(self.file_select_frame, text='You must choose a audio file.', style='Alert.TLabel')

    # button widgets group
    self.buttons_frame = Frame(self.main_frame)
    self.buttons_frame.grid(row=3, column=0, sticky='we')
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

  def _on_select(self, event):
    self.alert_msg_test_part.grid_forget()

  def _on_key_press(self, event):
    self.alert_msg_question.grid_forget()

  def open_file_browser(self):
    self.alert_msg_file.grid_forget()

    self.filepath = filedialog.askopenfilename()
    if not self.filepath:
      self._show_alert_msg(self.alert_msg_file, 2, 0)
      return
    self.filepath_label.configure(text=self.filepath)

  def generate_text(self):
    self.test_part = self.select.get()
    if not self.test_part:
      self._show_alert_msg(self.alert_msg_test_part, 2, 0)
      return

    self.question = self.question_entry.get().strip()
    if not self.question:
      self._show_alert_msg(self.alert_msg_question, 2, 0)
      return

    try:
      # Transcribe speech to text
      client = OpenAI()
      audio_file = open(self.filepath, 'rb')
      transcript = client.audio.transcriptions.create(
        model='whisper-1',
        file=audio_file,
        language='en'
      )
      self.original_answer = transcript.text

      # Pass the text to completion API for revision
      completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
          {
            'role': 'system',
            'content': f'You are a highly skilled AI that is trained in English speaking and eductaion. I would like you to read the following transcript which is my answer to this practice speaking test question of IELTS: {self.question}. Please give me a revised and enhanced version of similar length that sounds natural from a test taker. Also, please do not provide any other text in your response than the revised and enhanced answer.'
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
