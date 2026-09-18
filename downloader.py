import os
import re
import traceback
import pandas as pd
import requests

output_dir = 'sbc_downloads'
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, 'run_log.txt')

try:
  print('Starting robust CSV parsing...')
  csv_file = 'plan_attributes_PUF.csv'

  if not os.path.exists(csv_file):
    raise FileNotFoundError(f'Could not find {csv_file} in repository root.')

  # Try reading with standard comma first, but fallback if it collapses into one column
  df = pd.read_csv(csv_file, low_memory=False, on_bad_lines='skip')

  if len(df.columns) <= 1:
    # Try semicolon delimiter if comma failed
    df = pd.read_csv(
        csv_file, low_memory=False, delimiter=';', on_bad_lines='skip'
    )

  # Clean column names
  df.columns = [
      str(col).strip().replace('\ufeff', '').replace('\r', '')
      for col in df.columns
  ]
  print(f'Successfully loaded CSV. Total columns found: {len(df.columns)}')

  # If it still only has 1 column, print the first few rows to the log so we can see what it looks like
  if len(df.columns) <= 1:
    sample_data = df.head(5).to_string()
    raise ValueError(
        'CSV is still loading as a single column. Sample content:\n'
        + sample_data
    )

  # Flexible URL column finder
  url_col = None
  for col in df.columns:
    if 'url' in col.lower() and ('benefit' in col.lower() or 'sbc' in col.lower()):
      url_col = col
      break

  if not url_col:
    raise KeyError(
        f'Could not find URL column. Available columns: {list(df.columns)}'
    )

  print(f'Using URL column: {url_col}')

  success_count = 0
  fail_count = 0

  for index, row in df.iterrows():
    url = row.get(url_col)
    if pd.isna(url) or not str(url).strip().startswith('http'):
      continue

    plan_name = f'plan_{index}'
    for col in df.columns:
      if 'planmarketingname' in col.lower() or 'planname' in col.lower():
        val = row.get(col)
        if pd.notna(val):
          plan_name = str(val)
        break

    plan_id = str(index)
    for col in df.columns:
      if 'componentid' in col.lower() or 'planid' in col.lower():
        val = row.get(col)
        if pd.notna(val):
          plan_id = str(val)
        break

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
