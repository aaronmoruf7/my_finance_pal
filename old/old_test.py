# test.py

import pandas as pd
from old.old_main import TransactionCategorizer, detect_group_expenses

# 1) Load real data (skip BOA header rows)
df = pd.read_csv(
    'stmt.csv',
    skiprows=6,
    usecols=[0,1,2],
    names=['date','description','amount'],
    header=0,
    engine='python',
    on_bad_lines='skip'
).dropna(subset=['amount'])
df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
df = df.dropna(subset=['date'])
print(df.head())

# 2) Create sample for manual labeling
sample = df.sample(n=min(100, len(df)), random_state=42).reset_index(drop=True)
# Add blank category column, then save for you to fill
sample['category'] = ''
sample.to_csv('labeled_real_transactions.csv', index=False)
print("🚀 Sample written to labeled_real_transactions.csv — please open and fill 'category' for each row.")

# Pause here: once you've labeled and saved, rerun from #3 onward.

# # COMMENT OUT FROM HERE
# # 3) After labeling, load your labels
# labeled = pd.read_csv('labeled_real_transactions.csv')
# cat = TransactionCategorizer()
# cat.fit(labeled[['description','category']])

# # 4) Flag each txn
# df['category'], df['confidence'] = zip(*df['description'].map(
#     lambda d: cat.categorize(d)[:2]
# ))
# df['is_reimbursement'] = df['category'] == 'Reimbursement'
# df['is_group']         = df['description'].str.contains('Walmart', case=False)

# print("\n=== Transaction Flags ===")
# print(df[['date','description','amount','category','confidence','is_reimbursement','is_group']].to_string(index=False))

# # 5) Detect
# matched, ambiguous = detect_group_expenses(df)

# print("\n=== Matched Reimbursements ===")
# print(matched.to_string(index=False))

# print("\n=== Ambiguous (manual review) ===")
# print(ambiguous.to_string(index=False))
