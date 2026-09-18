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

  # Directly use the exact column name from your dataset
  url_col = 'URLForSummaryofBenefitsCoverage'

  if url_col not in df.columns:
    raise KeyError(f"Column '{url_col}' not found in CSV columns.")

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

    # Keep the 50-file test limit for now so it runs instantly. 
    # Change or remove this number later when you want all ~20,000!
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
