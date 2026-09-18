import os
import re
import pandas as pd
import requests

# We will use your CSV file directly
csv_file_path = 'plan_attributes_PUF.csv'
output_folder = 'sbc_downloads'

os.makedirs(output_folder, exist_ok=True)


def clean_filename(name):
  return re.sub(r'[\/*?:"<>|]', '', str(name))


try:
  df = pd.read_csv(csv_file_path, low_memory=False)
  print(f'Successfully loaded {len(df)} rows from CSV.')
except Exception as e:
  print(f'Error reading CSV: {e}')
  exit()

download_count = 0

for index, row in df.iterrows():
  plan_name = row.get('PlanMarketingName', f'Plan_{index}')
  hios_id = row.get('StandardComponentId', '')
  url = row.get('URLForSummaryofBenefitsCoverage')

  if pd.isna(url) or not str(url).startswith('http'):
    continue

  safe_name = clean_filename(f'{plan_name}_{hios_id}')
  file_name = f'{safe_name}.pdf'
  file_path = os.path.join(output_folder, file_name)

  try:
    response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
      with open(file_path, 'wb') as f:
        f.write(response.content)
      print(f'Downloaded: {file_name}')
      download_count += 1
    else:
      print(f'Failed: {file_name} (Status: {response.status_code})')
  except Exception as e:
    print(f'Error on {file_name}: {e}')

print(f'Total downloaded: {download_count}')
