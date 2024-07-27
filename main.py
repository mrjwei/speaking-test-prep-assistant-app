from openai import OpenAI
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
from tkinter import messagebox
import os
from dotenv import load_dotenv
import re
import helpers.notion_api as api

load_dotenv()

NOTION_API_TOKEN = os.getenv('NOTION_API_TOKEN')
PAGE_ID = os.getenv('PAGE_ID')
URL = f'https://api.notion.com/v1/blocks/{PAGE_ID}/children'

class SpeakingAssistant(Frame):
  def __init__(self, root):
    super().__init__(root)
    self.root = root
    self.root.title = 'Speaking Assistant'
    self.filepath = None
    self.original_answer = None
    self.revised_answer = None
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

      data = {
        "children": [
          api.create_block_object("heading_2", ("text", self.question.capitalize())),
          api.create_block_object("heading_3", ("text", "My answer:")),
          api.create_block_object("paragraph", ("text", self.original_answer)),
          api.create_block_object("heading_3", ("text", "ChatGPT answer:")),
          api.create_block_object("paragraph", ("text", self.revised_answer)),
        ]
      }

      api.send_patch_request(URL, NOTION_API_TOKEN, data)
      messagebox.showinfo(title="Done", message="Task succeeded.")
    except Exception as e:
      messagebox.showerror(title='Error', message=f'{e}')

if __name__ == "__main__":
  root = Tk()
  app = SpeakingAssistant(root)
  app.mainloop()
