import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_TOKEN = os.getenv('NOTION_API_TOKEN')
URL_SEG1 = 'https://api.notion.com/v1/blocks/'
URL_SEG2 = '/children'

MODES = [
  'Local Whisper',
  'Remote API',
]

PARTS = {
  'Part 1': os.getenv('PAGE_ID_PART1'),
  'Part 2': os.getenv('PAGE_ID_PART2'),
  'Part 3': os.getenv('PAGE_ID_PART3'),
}
