# My Finance Pal

**Accurate personal finance insights that factor in reimbursements and group expenses.**

[Live App →](#) *(coming soon)*

---

## 🧠 Why This Exists

Most personal finance tools **overstate expenses and income** especially for students or roommates because they don't account for **group spending and reimbursements**.

**Example:**  
If you paid for groceries for your house and friends reimbursed you later, your dashboard still shows the **full grocery bill as your own spend** and the repayment as **extra income**.  
That’s misleading.

**My Finance Pal** fixes this by:
- Letting you **tag group expenses**
- Automatically **detecting and reconciling reimbursements**
- Giving you a **true view of your actual spending, income, and net flow**

---

## 🚀 What It Can Do

✅ Upload your **bank transaction CSV** (currently supports **Bank of America** format)  
✅ **AI auto-categorizes** each transaction  
✅ You can **flag group purchases** manually  
✅ It will **detect reimbursements** that match  
✅ Let you **reconcile ambiguous cases**  
✅ Provide a **corrected breakdown** of your true income, expenses, and categories  

---

## 🧭 How to Use It

1. **Upload** your transaction CSV file  
2. **Review & edit** categories, toggle group expenses  
3. Click **Run Analysis** to detect reimbursement matches  
4. **Resolve** any ambiguous cases manually  
5. **View your clean dashboard** with real spending, income, and net income  

No signup. No bank connection. Just clarity.

---

## 🖥️ Backend Setup (FastAPI)

To run the backend locally alongside the frontend:

### 1. Clone this repo
```bash
git clone https://github.com/your-username/myfinancepal.git
cd myfinancepal/backend
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your Hugging Face API token

Create a `.env` file in the `backend/` directory:

```
HF_API_TOKEN=your_huggingface_api_key
```

> Get your token here: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### 5. Run the backend server
```bash
uvicorn backend.main:app --reload
```

Server will be running at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---