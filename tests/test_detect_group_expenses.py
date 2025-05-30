import pandas as pd
from datetime import datetime

def detect_group_expenses(
    df: pd.DataFrame,
    is_reimbursement_col: str = 'is_reimbursement',
    is_group_col: str         = 'is_group',
    date_col: str             = 'date',
    amount_col: str           = 'amount',
    window_hours: int         = 48
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Matches reimbursements to their specific tagged group expense,
    with manual‐review buckets for ambiguous cases.
    
    Returns:
      matched: DataFrame of reimbursements successfully applied
               with columns [reimb_date, reimb_amt, expense_date,
               expense_desc, original_amt, applied_amt, remaining_amt]
      ambiguous: DataFrame of reimbursements needing manual review,
                 with columns [reimb_date, reimb_amt, candidate_expenses]
    """
    # 1) Split out only reimbursements vs. only group expenses
    reimbs = df[df[is_reimbursement_col] & (df[amount_col] > 0)].copy()
    exps   = df[df[is_group_col]      & (df[amount_col] < 0)].copy()
    
    # 2) Track “remaining” on each expense as positive dollars owed
    exps['remaining'] = -exps[amount_col]
    
    # 3) Prepare records for in‐place matching
    reimb_list = reimbs.sort_values(date_col).to_dict('records')
    exp_list   = exps.sort_values(date_col).to_dict('records')
    
    matched_rows   = []
    ambiguous_rows = []
    
    # 4) For each reimbursement, find its candidate expenses
    for r in reimb_list:
        # build candidate list: within window AND enough remaining balance
        candidates = [
            e for e in exp_list
            if 0 <= (r[date_col] - e[date_col]).total_seconds() <= window_hours*3600
               and e['remaining'] >= r[amount_col]
        ]
        
        if len(candidates) == 1:
            # single unambiguous match → apply it
            e = candidates[0]
            applied = r[amount_col]
            e['remaining'] -= applied
            matched_rows.append({
                'reimb_date':       r[date_col].date(),
                'reimb_amt':        r[amount_col],
                'expense_date':     e[date_col].date(),
                'expense_desc':     e['description'],
                'original_amt':     -e[amount_col],
                'applied_amt':      applied,
                'remaining_amt':    e['remaining']
            })
        else:
            # ambiguous or no match → collect for manual review
            ambiguous_rows.append({
                'reimb_date':        r[date_col].date(),
                'reimb_amt':         r[amount_col],
                'candidate_expenses': [
                    {
                        'date':         e[date_col].date(),
                        'description':  e['description'],
                        'remaining':    e['remaining']
                    } for e in candidates
                ]
            })
    
    matched   = pd.DataFrame(matched_rows)
    ambiguous = pd.DataFrame(ambiguous_rows)
    return matched, ambiguous

def test_group_expense_detection():
    # Load your real BOA data
    df = pd.read_csv(
        'stmt.csv',
        skiprows=6,
        usecols=[0, 1, 2],
        names=['date', 'description', 'amount'],
        header=0,
        engine='python',
        on_bad_lines='skip'
    ).dropna()

    # Clean + parse
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df = df.dropna(subset=['date', 'amount'])

    # Flag reimbursements (you should have category from classification first)
    # For now we'll simulate it:
    df['is_reimbursement'] = (
        df['description'].str.contains('zelle', case=False) &
        df['description'].str.contains('from', case=False)
    )
    # Simulate user-tagged group expenses (you'll replace this with real user input or UI flag)
    df['is_group'] = df['description'].str.contains('walmart', case=False)

    # Run detection logic
    matched, ambiguous = detect_group_expenses(df)

    print("\n✅ Matched Reimbursements:")
    print(matched.to_string(index=False))

    print("\n⚠️ Ambiguous Cases (Need Manual Review):")
    print(ambiguous.to_string(index=False))

    # Optionally save to CSVs
    matched.to_csv('group_matched.csv', index=False)
    ambiguous.to_csv('group_ambiguous.csv', index=False)
    print("\n💾 Results saved: group_matched.csv and group_ambiguous.csv")

if __name__ == "__main__":
    test_group_expense_detection()
