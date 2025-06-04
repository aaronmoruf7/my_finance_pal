from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import io
from fastapi import Request


from .classify import classify_transactions
from .group_expenses import detect_group_expenses

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
        df['is_group'] = False
        df['is_reimbursement'] = False

        # Step 1: categorize
        df = classify_transactions(df)

        transaction_data = df

        return {
            "status": "success",
            "rows_loaded": len(df),
            "categorized": df.to_dict(orient="records")
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

@app.post("/run", response_model=RunResult)
async def run_processing(request: Request):
    body = await request.json()
    transactions = pd.DataFrame(body["transactions"])

    if transactions.empty:
        raise HTTPException(status_code=400, detail="No transactions provided.")

    # Step 2: Group Expense Detection
    matched, ambiguous = detect_group_expenses(transactions)

    return {
        "categorized": transactions.to_dict(orient="records"),
        "matched": matched.to_dict(orient="records"),
        "ambiguous": ambiguous
    }



