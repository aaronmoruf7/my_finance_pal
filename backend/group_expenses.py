import pandas as pd

def detect_group_expenses(
    df: pd.DataFrame,
    is_reimbursement_col: str = 'is_reimbursement',
    is_group_col: str         = 'is_group',
    date_col: str             = 'date',
    amount_col: str           = 'amount',
    window_hours: int         = 48
) -> tuple[pd.DataFrame, list[dict]]:
    """
    Matches reimbursements to their specific tagged group expenses.
    
    Returns:
      matched: DataFrame of clear matches
      ambiguous: list of dicts with { transaction, possibleGroups }
    """
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")  # <-- Ensure datetime

    reimbs = df[df[is_reimbursement_col] & (df[amount_col] > 0)].copy()
    exps   = df[df[is_group_col]        & (df[amount_col] < 0)].copy()



    # Make sure each row has a unique ID
    if 'id' not in df.columns:
        df["id"] = df.index.astype(str)
        reimbs["id"] = reimbs.index.astype(str)

    exps['remaining'] = -exps[amount_col]  # Flip to positive remaining

    reimb_list = reimbs.sort_values(date_col).to_dict('records')
    exp_list   = exps.sort_values(date_col).to_dict('records')

    matched_rows = []
    ambiguous_rows = []

    for r in reimb_list:
        candidates = [
            e for e in exp_list
            if 0 <= (r[date_col] - e[date_col]).total_seconds() <= window_hours * 3600
            and e['remaining'] >= r[amount_col]
        ]
        if len(candidates) == 1:
            e = candidates[0]
            applied = r[amount_col]
            e['remaining'] -= applied
            matched_rows.append({
                'id': r['id'],
                'description': r['description'],
                'amount': r[amount_col],
                'category': 'Reimbursement',
                'confidence': 1.0,
                'is_group': False,
                'is_reimbursement': True,
                'reimb_date': r[date_col].date(),
                'expense_date': e[date_col].date(),
                'expense_desc': e['description'],
                'original_amt': -e[amount_col],
                'applied_amt': applied,
                'remaining_amt': e['remaining']
            })
        else:
            ambiguous_rows.append({
                "transaction": {
                    "id": r['id'],
                    "description": r['description'],
                    "amount": r[amount_col],
                    "category": "Reimbursement",
                    "confidence": 1.0,
                    "is_group": False,
                    "is_reimbursement": True,
                },
                "possibleGroups": [e['description'] for e in candidates]
            })

    matched = pd.DataFrame(matched_rows)
    return matched, ambiguous_rows
