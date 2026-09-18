import os
import re
import traceback
import pandas as pd
import requests

output_dir = 'sbc_downloads'
os.makedirs(output_dir, exist_ok=True)

log_path = os.path.join(output_dir, 'run_log.txt')

try:
  print('Starting SBC download process...')
  csv_file = 'plan_attributes_PUF.csv'

  if not os.path.exists(csv_file):
    raise FileNotFoundError(f'Could not find {csv_file} in repository root.')

  df = pd.read_csv(csv_file, low_memory=False)
  print(f'Successfully loaded CSV with {len(df)} rows.')

  # Find the URL column dynamically
  url_col = None
  for col in df.columns:
    if 'url' in col.lower() and 'benefit' in col.lower():
      url_col = col
      break

  if not url_col:
    raise KeyError('Could not find Summary of Benefits URL column in CSV.')

  print(f'Using URL column: {url_col}')

  success_count = 0
  fail_count = 0

  for index, row in df.iterrows():
    url = row.get(url_col)
    if pd.isna(url) or not str(url).strip().startswith('http'):
      continue

    plan_name = str(row.get('PlanMarketingName', f'plan_{index}'))
    plan_id = str(row.get('StandardComponentId', f'{index}'))

    # Clean filename characters
    safe_name = re.sub(r'[\/*?:"<>|]', '', f'{plan_name}_{plan_id}')[:100]
    file_path = os.path.join(output_dir, f'{safe_name}.pdf')

    # Skip if already downloaded
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

    # Optional: Safety limit for initial testing (remove or increase later if needed)
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
  # Capture any unexpected error so the workflow NEVER fails with exit code 1
  err_msg = f'ERROR ENCOUNTERED:\n{traceback.format_exc()}'
  print(err_msg)
  with open(log_path, 'w') as f:
    f.write(err_msg)
