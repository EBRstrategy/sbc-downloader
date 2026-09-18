import os
import re
import pandas as pd
import requests

# Configuration
csv_file_path = 'sbc_links.csv'  # Your CSV file with links
output_folder = 'sbc_downloads'  # Where the PDFs will be temporarily saved

os.makedirs(output_folder, exist_ok=True)


def clean_filename(name):
  return re.sub(r'[\/*?:"<>|]', '', str(name))


try:
  df = pd.read_csv(csv_file_path)
  print(f'Loaded {len(df)} rows from {csv_file_path}.')
except FileNotFoundError:
  print(
      f"Error: Could not find '{csv_file_path}'. Make sure it's uploaded to"
      ' your repository.'
  )
  exit()

for index, row in df.iterrows():
  plan_identifier = clean_filename(row.get('PlanName', f'Plan_{index}'))
  url = row.get('URL')

  if pd.isna(url) or not str(url).startswith('http'):
    continue

  file_name = f'{plan_identifier}.pdf'
  file_path = os.path.join(output_folder, file_name)

  try:
    response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
      with open(file_path, 'wb') as f:
        f.write(response.content)
      print(f'Downloaded: {file_name}')
    else:
      print(f'Failed: {file_name} (Status: {response.status_code})')
  except Exception as e:
    print(f'Error on {file_name}: {e}')
