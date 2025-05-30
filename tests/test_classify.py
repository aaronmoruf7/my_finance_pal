import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.classify import hf_llama_classify

# Minimal test input
description = "VENMO FROM JANE"
amount = 24.00

category, confidence = hf_llama_classify(description, amount)
print(f"📄 \"{description}\" → 🧠 {category} (Confidence: {confidence:.2f})")