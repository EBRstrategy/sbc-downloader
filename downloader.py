import os
import re
import traceback
import pandas as pd
import requests

output_dir = 'sbc_downloads'
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, 'run_log.txt')

try:
  print('Starting CSV parsing with dynamic header detection...')
  csv_file = 'plan_attributes_PUF.csv'

  if not os.path.exists(csv_file):
    raise FileNotFoundError(f'Could not find {csv_file} in repository root.')

  # Automatically find the exact line number where the real headers begin
  header_row = 0
  with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f):
      if (
          'StandardComponentId' in line
          or 'URLForSummaryofBenefitsCoverage' in line
      ):
        header_row = idx
        break

  print(f'Detected true header row at line index: {header_row}')

  # Read CSV skipping the extra title/metadata lines at the top
  df = pd.read_csv(csv_file, skiprows=header_row, low_memory=False)

  # Clean column names
  df.columns = [
      str(col).strip().replace('\ufeff', '').replace('\r', '')
      for col in df.columns
  ]
  print(f'Successfully loaded CSV. Total columns found: {len(df.columns)}')

  url_col = 'URLForSummaryofBenefitsCoverage'
  if url_col not in df.columns:
    for col in df.columns:
      if 'url' in col.lower() and 'benefit' in col.lower():
        url_col = col
        break

  if url_col not in df.columns:
    raise KeyError(f"Could not find URL column. Columns found: {list(df.columns)}")

  print(f'Using URL column: {url_col}')

  success_count = 0
  fail_count = 0

  for index, row in df.iterrows():
    url = row.get(url_col)
    if pd.isna(url) or not str(url).strip().startswith('http'):
      continue

    plan_name = str(row.get('PlanMarketingName', f'plan_{index}'))
    plan_id = str(row.get('StandardComponentId', f'{index}'))

    safe_name = re.sub(r'[\/*?:"<>|]', '', f'{plan_name}_{plan_id}')[:100]
    file_path = os.path.join(output_dir, f'{safe_name}.pdf')

    if os.path.exists(file_path):
      success_count += 1
      continue

    try:
      response = requests.get(
          url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}
      )
      if response.status_code == 200:
        with open(file_path, 'wb') as f:
          f.write(response.content)
        success_count += 1
      else:
        fail_count += 1
    except Exception:
      fail_count += 1

    # Test limit set to 50 files so it runs instantly
    if success_count >= 50:
      print('Reached initial batch limit of 50 files.')
      break

  msg = (
      f'Completed! Successfully downloaded {success_count} PDFs. Failed:'
      f' {fail_count}'
  )
  print(msg)
  with open(log_path, 'w') as f:
    f.write(msg)

except Exception as e:
  err_msg = f'ERROR ENCOUNTERED:\n{traceback.format_exc()}'
  print(err_msg)
  with open(log_path, 'w') as f:
    f.write(err_msg)
