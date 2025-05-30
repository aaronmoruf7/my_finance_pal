from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import io

from classify import classify_transactions
from group_expenses import detect_group_expenses

app = FastAPI()

# Allow frontend dev environments like localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set specific origin in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global store for uploaded data (dev-only, for demo)
transaction_data: pd.DataFrame = pd.DataFrame()

# --- Models for response ---

class RunResult(BaseModel):
    categorized: list[dict]
    matched: list[dict]
    ambiguous: list[dict]

# --- Routes ---

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global transaction_data
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')), skiprows=7, usecols=[0, 1, 2], names=['date', 'description', 'amount'], header=0)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df = df.dropna(subset=['date', 'amount'])
        transaction_data = df
        return {"status": "success", "rows_loaded": len(df)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


@app.post("/run", response_model=RunResult)
def run_processing():
    global transaction_data
    if transaction_data.empty:
        raise HTTPException(status_code=400, detail="No uploaded CSV. Please upload a file first.")

    # Step 1: Categorize
    categorized_df = classify_transactions(transaction_data.copy())

    # Step 2: Group Expense Detection
    matched, ambiguous = detect_group_expenses(categorized_df)

    return {
        "categorized": categorized_df.to_dict(orient='records'),
        "matched": matched.to_dict(orient='records'),
        "ambiguous": ambiguous.to_dict(orient='records')
    }
