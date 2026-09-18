import os
import re
import pandas as pd
import requests

csv_file = 'plan_attributes_PUF.csv'
output_dir = 'sbc_downloads'

os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv(csv_file, low_memory=False)
print(f'Loaded {len(df)} rows from CSV.')

count = 0
for index, row in df.iterrows():
  url = row.get('URLForSummaryofBenefitsCoverage')
  if pd.isna(url) or not str(url).startswith('http'):
    continue

  plan_name = str(row.get('PlanMarketingName', f'plan_{index}'))
  plan_id = str(row.get('StandardComponentId', f'{index}'))
  
  # Clean filename characters
  safe_name = re.sub(r'[\/*?:"<>|]', '', f'{plan_name}_{plan_id}')[:150]
  file_path = os.path.join(output_dir, f'{safe_name}.pdf')

  try:
    res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    if res.status_code == 200:
      with open(file_path, 'wb') as f:
        f.write(res.content)
      count += 1
      print(f'Downloaded {count}: {safe_name}.pdf')
      
      # Optional: Remove the # in the next line if you want to test just the first 50 files first
      # if count >= 50: break 
  except Exception as e:
    print(f'Skipped due to error: {e}')

print(f'Total downloaded: {count}')
