import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Basic rule-based boost (not foolproof, but helps)
def rule_based_check(text):
    keywords = {
        "Contract": ["agreement", "service agreement", "signed", "termination", "provider", "client"],
        "Invoice": ["invoice", "amount due", "total due", "bill to", "payment due", "invoice number"],
        "Report": ["summary", "findings", "analysis", "report"],
        "Purchase Order": ["purchase order", "PO", "order date", "item", "supplier"],
        "Email": ["from:", "to:", "subject:", "regards", "best,"],
    }

    scores = {k: 0 for k in keywords}
    text_lower = text.lower()

    for label, words in keywords.items():
        for word in words:
            if word in text_lower:
                scores[label] += 1

    # Return the best label if confident
    best_match = max(scores, key=scores.get)
    if scores[best_match] >= 2:
        return best_match
    return None

def classify_document(text):
    # Step 1: Try rule-based boost
    rule_label = rule_based_check(text)
    if rule_label:
        return rule_label

    # Step 2: Use LLM
    prompt = f"""
You are a highly reliable document classifier. 

You must choose one category from the following:
- Invoice
- Contract
- Report
- Purchase Order
- Email
- Others

Guidelines:
- If the document defines terms, services, duration, payment, parties, and contains signatures — it's a **Contract**.
- If it contains an invoice number, due date, amounts payable — it's an **Invoice**.
- If it contains summaries, findings, charts, KPIs — it's a **Report**.
- If it includes a purchase order or itemized request — it's a **Purchase Order**.
- If it's a message or correspondence — it's an **Email**.
- Otherwise — classify as **Others**.

Return just one word from the list: Invoice, Contract, Report, Purchase Order, Email, Others.

Document:
\"\"\"
{text[:3000]}
\"\"\"
"""
    try:
        response = openai.ChatCompletion.create(
            base_url="https:/genailab.tcs.in"
            model="azure_ai/genailab-maas-DeepSeek-V3-0324",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1  # More deterministic
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"LLM classification failed: {e}")
        return "Others"
