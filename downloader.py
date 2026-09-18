import os
import re
import pandas as pd
import requests

csv_file = 'plan_attributes_PUF.csv'
output_dir = 'sbc_downloads'

print("Initializing download script...")
os.makedirs(output_dir, exist_ok=True)

if not os.path.exists(csv_file):
  raise FileNotFoundError(f"Could not find {csv_file} in repository root.")

df = pd.read_csv(csv_file, low_memory=False)
print(f"Loaded {len(df)} rows from CSV.")

url_col = 'URLForSummaryofBenefitsCoverage'
if url_col not in df.columns:
  raise KeyError(f"Column '{url_col}' not found in CSV columns.")

downloaded_count = 0
failed_count = 0

for index, row in df.iterrows():
  url = row.get(url_col)
  if pd.isna(url) or not str(url).strip().startswith('http'):
    continue

  plan_name = str(row.get('PlanMarketingName', f'plan_{index}'))
  plan_id = str(row.get('StandardComponentId', f'{index}'))

  # Clean invalid filename characters
  safe_name = re.sub(r'[\/*?:"<>|]', '', f'{plan_name}_{plan_id}')[:100]
  file_path = os.path.join(output_dir, f'{safe_name}.pdf')

  # Skip if already downloaded
  if os.path.exists(file_path):
    downloaded_count += 1
    continue

  try:
    response = requests.get(
        url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}
    )
    if response.status_code == 200:
      with open(file_path, 'wb') as f:
        f.write(response.content)
      downloaded_count += 1
      print(f"[{downloaded_count}] Successfully downloaded: {safe_name}.pdf")
    else:
      failed_count += 1
      if failed_count <= 5:  # Limit log spam
        print(
            f"Failed to download {url} (Status code: {response.status_code})"
        )
  except Exception as e:
    failed_count += 1
    if failed_count <= 5:
      print(f"Error downloading {url}: {e}")

  # Optional safety break for testing if you want to verify artifact creation quickly:
  # Remove this break once you confirm it works!
  if downloaded_count >= 10:
    print("Reached test batch of 10 files.")
    break

print(
    f"Done! Total files ready in '{output_dir}':"
    f" {len(os.listdir(output_dir))}"
)
