# finance_ai.py

import pandas as pd
import numpy as np
from datetime import timedelta
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

class TransactionCategorizer:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', n_neighbors: int = 5):
        """
        AI-based transaction categorizer using embeddings + k-NN.
        """
        self.embedder = SentenceTransformer(model_name)
        self.n_neighbors = n_neighbors
        self.knn = None
        self.labeled_df = None

    def fit(self, labeled_df: pd.DataFrame):
        """
        Train k-NN index on a labeled DataFrame with columns ['description', 'category'].
        """
        self.labeled_df = labeled_df.copy().reset_index(drop=True)
        # Compute embeddings for descriptions
        embeddings = self.embedder.encode(
            self.labeled_df['description'].tolist(),
            convert_to_numpy=True
        )
        # Fit k-NN on embeddings
        self.knn = NearestNeighbors(
            n_neighbors=self.n_neighbors,
            metric='cosine'
        ).fit(embeddings)
        self.labeled_df['embedding'] = list(embeddings)

    def categorize(self, description: str):
        """
        Categorize a single transaction description.
        Returns: (predicted_category, confidence, neighbor_categories, distances)
        """
        emb = self.embedder.encode(description, convert_to_numpy=True).reshape(1, -1)
        dists, idxs = self.knn.kneighbors(emb)
        neighbor_cats = self.labeled_df.iloc[idxs[0]]['category'].tolist()
        best_cat = neighbor_cats[0]
        confidence = 1.0 - dists[0][0]
        return best_cat, confidence, neighbor_cats, dists[0].tolist()

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

# # Example usage:
# if __name__ == "__main__":
#     # Load labeled data
#     labeled = pd.read_csv("labeled_transactions.csv")  # columns: description,category
#     categorizer = TransactionCategorizer()
#     categorizer.fit(labeled)

#     # Categorize new transactions
#     new_txns = ["Starbucks #123", "Walmart Grocery", "Uber Trip"]
#     for desc in new_txns:
#         cat, conf, neigh, dists = categorizer.categorize(desc)
#         print(f"{desc} -> {cat} (conf {conf:.2f}) neighbors: {neigh}")

#     # Detect group expenses
#     stm = pd.read_csv("transactions.csv", parse_dates=['date'])
#     stm['is_group'] = stm['description'].str.contains('split|shared|group|walmart', case=False)
#     stm['amount'] = stm['amount'].astype(float)
#     stm['date'] = pd.to_datetime(stm['date'])
#     group_df = detect_group_expenses(stm)
#     print(group_df)
