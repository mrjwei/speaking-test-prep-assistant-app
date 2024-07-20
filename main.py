from openai import OpenAI
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
from tkinter import messagebox
from pathlib import Path
import re

class SpeakingAssistant(Frame):
  def __init__(self, root):
    super().__init__(root)
    self.root = root
    self.root.title = 'Speaking Assistant'
    self.filepath = None
    self.original_answer = None
    self.revised_answers = None
    self.question = ''

    self.main_frame = Frame(self.root)
    self.main_frame.grid(padx=20, pady=20, sticky='we')
    self.main_frame.columnconfigure(0, minsize=100, weight=1)
    self.main_frame.columnconfigure(1, minsize=100, weight=1)
    self.main_frame.columnconfigure(2, minsize=100, weight=1)
    self.main_frame.columnconfigure(3, minsize=100, weight=1)

    Label(self.main_frame, text='Question:').grid(row=0, column=0, sticky=W, padx=5)

    self.question_entry = Entry(self.main_frame)
    self.question_entry.grid(row=1, column=0, columnspan=4, sticky='we', padx=5)

    self.filepath_btn = Button(self.main_frame, text='Select Audio File', command=self.open_file_browser)
    self.filepath_btn.grid(row=2, column=0, columnspan=4, sticky='we', padx=5)

    self.filepath_label = Label(self.main_frame, text='')
    self.filepath_label.grid(row=3, column=0, columnspan=4, padx=5)

    self.gen_btn = Button(self.main_frame, text='Generate Text', command=self.generate_text)
    self.gen_btn.grid(row=4, column=0, columnspan=2, sticky='we', padx=5)

    self.quit_btn = Button(self.main_frame, text='Quit', command=lambda: self.root.quit())
    self.quit_btn.grid(row=4, column=2, columnspan=2, sticky='we', padx=5)

    self.result_label = Label(self.main_frame, text='')
    self.result_label.grid(row=5, column=0, columnspan=4)

  def open_file_browser(self):
    self.filepath = filedialog.askopenfilename()
    if not self.filepath:
      return
    self.filepath_label.configure(text=self.filepath)

  def generate_text(self):
    try:
      self.question = self.question_entry.get().strip()
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

      # generate text file containing the two pieces of text
      Path('outputs').mkdir(parents=True, exist_ok=True)
      filepath = f'outputs/{"_".join([w for w in re.split(r'[ ,;.?]', self.question) if w])}.txt'

      formatted_text = f'''
        Q: {self.question.capitalize()}\n\n
        Your answer:\n\n
        {self.original_answer}\n\n
        Revised answer:\n\n
        {self.revised_answer}\n
      '''

      with open(filepath, 'w') as f:
        f.write(formatted_text)

      self._update_result_label()
    except Exception as e:
      messagebox.showerror(title='Error', message=f'{e}')

  def _update_result_label(self):
    self.result_label.configure(text='Done.')

if __name__ == "__main__":
  root = Tk()
  app = SpeakingAssistant(root)
  app.mainloop()
