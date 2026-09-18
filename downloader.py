import os
import re
import pandas as pd
import requests

# Pointing directly to your uploaded Excel file
excel_file_path = 'plan_attributes_PUF.xlsx'
output_folder = 'sbc_downloads'

os.makedirs(output_folder, exist_ok=True)


def clean_filename(name):
  return re.sub(r'[\/*?:"<>|]', '', str(name))


try:
  # Read the Excel file (automatically grabs the first sheet)
  df = pd.read_excel(excel_file_path)
  print(f'Loaded {len(df)} rows from {excel_file_path}.')
except Exception as e:
  print(f"Error reading Excel file: {e}")
  exit()

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
    response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
      with open(file_path, 'wb') as f:
        f.write(response.content)
      print(f'Downloaded: {file_name}')
    else:
      print(f'Failed: {file_name} (Status: {response.status_code})')
  except Exception as e:
    print(f'Error on {file_name}: {e}')
