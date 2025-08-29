import streamlit as st
import requests
import json
import fitz  # PyMuPDF for PDF

# App setup
st.set_page_config(page_title="📄 Multi-Doc AI Assistant", layout="wide")
st.title("📄 Backoffice Document Classifier & Router")

# Session state init
if "doc_data" not in st.session_state:
    st.session_state.doc_data = []  # List of dicts: {name, text, label, routing, metadata}

# ---------------- Helper Functions ---------------- #

def extract_text(file):
    if file.name.endswith(".txt"):
        return file.read().decode("utf-8")
    elif file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    return ""

def query_ollama(prompt, model="llama3"):
    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ Ollama error: {e}"

def rule_based_classification(text):
    keywords = {
        "Contract": ["agreement", "service agreement", "signed", "termination", "provider", "client"],
        "Invoice": ["invoice", "amount due", "total due", "bill to", "payment due"],
        "Report": ["summary", "findings", "analysis", "report"],
        "Purchase Order": ["purchase order", "PO", "order date", "supplier"],
        "Email": ["from:", "to:", "subject:", "regards", "best,"]
    }
    scores = {k: 0 for k in keywords}
    text_lower = text.lower()
    for label, words in keywords.items():
        for word in words:
            if word in text_lower:
                scores[label] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None

def classify_document(text):
    rule_label = rule_based_classification(text)
    if rule_label:
        return rule_label
    prompt = f"""Classify this document into one of:
- Invoice
- Contract
- Report
- Purchase Order
- Email
- Other

Just respond with the label.

Document:
\"\"\"
{text[:2000]}
\"\"\"
"""
    return query_ollama(prompt)

def route_document(label):
    routing_map = {
        "Invoice": "Finance Department",
        "Contract": "Legal Department",
        "Report": "Analytics",
        "Purchase Order": "Procurement",
        "Email": "Support",
        "Other": "General Admin"
    }
    return routing_map.get(label, "General Admin")

def extract_metadata(text):
    prompt = f"""
Extract the following metadata from this service contract:

- Agreement Title
- Client
- Provider
- Start Date
- End Date
- Monthly Payment
- Termination Terms

Return JSON only.

Document:
\"\"\"
{text}
\"\"\"
"""
    response = query_ollama(prompt)
    try:
        return json.loads(response)
    except:
        return {"raw_response": response}

# ---------------- UI: Metadata Extraction Toggle ---------------- #

extract_meta = st.checkbox("🔎 Extract metadata for contracts?", value=False)

# ---------------- Upload & Analyze ---------------- #

uploaded_files = st.file_uploader("📁 Upload multiple .txt or .pdf documents", type=["txt", "pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("🔍 Analyzing uploaded documents..."):
        st.session_state.doc_data = []  # Reset previous

        for i, file in enumerate(uploaded_files):
            with st.status(f"Processing `{file.name}` ({i+1}/{len(uploaded_files)})...", expanded=False):
                text = extract_text(file)
                label = classify_document(text)
                routing = route_document(label)
                metadata = extract_metadata(text) if label == "Contract" and extract_meta else {}

                st.session_state.doc_data.append({
                    "name": file.name,
                    "text": text,
                    "label": label,
                    "routing": routing,
                    "metadata": metadata
                })

# ---------------- Document Summary ---------------- #

if st.session_state.doc_data:
    st.subheader("📑 Document Analysis Summary")

    for idx, doc in enumerate(st.session_state.doc_data):
        st.markdown(f"### 🗂️ Document {idx + 1}: `{doc['name']}`")

        col1, col2 = st.columns(2)
        with col1:
            new_label = st.selectbox(
                f"Classification (Override for `{doc['name']}`)", 
                ["Invoice", "Contract", "Report", "Purchase Order", "Email", "Other"],
                index=["Invoice", "Contract", "Report", "Purchase Order", "Email", "Other"].index(doc["label"]),
                key=f"label_{idx}"
            )
            st.session_state.doc_data[idx]["label"] = new_label

        with col2:
            new_route = st.selectbox(
                f"Routing (Override for `{doc['name']}`)",
                ["Finance Department", "Legal Department", "Analytics", "Procurement", "Support", "General Admin"],
                index=["Finance Department", "Legal Department", "Analytics", "Procurement", "Support", "General Admin"].index(doc["routing"]),
                key=f"route_{idx}"
            )
            st.session_state.doc_data[idx]["routing"] = new_route

        st.markdown(f"""
- **🧾 Classification**: `{new_label}`
- **📬 Routing Suggestion**: `{new_route}`
""")

        if extract_meta and doc["metadata"]:
            st.markdown("**🔎 Extracted Metadata:**")
            st.json(doc["metadata"])

            # ✅ Download metadata as JSON
            metadata_json = json.dumps(doc["metadata"], indent=2)
            st.download_button(
                label=f"📥 Download Metadata for {doc['name']}",
                data=metadata_json,
                file_name=f"{doc['name']}_metadata.json",
                mime="application/json",
                key=f"download_{idx}"
            )

        st.markdown("---")

# ---------------- Chat Interface ---------------- #

if st.session_state.doc_data:
    st.subheader("💬 Ask a Question About Any Document")

    doc_names = [doc["name"] for doc in st.session_state.doc_data]
    selected_doc_name = st.selectbox("Select a document to chat with", doc_names)

    selected_doc = next(d for d in st.session_state.doc_data if d["name"] == selected_doc_name)
    chat_input = st.chat_input("Ask something about this document...")

    if chat_input:
        with st.chat_message("user"):
            st.markdown(chat_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                full_prompt = f"""
You are a helpful assistant answering questions about this document:

\"\"\"
{selected_doc['text']}
\"\"\"

User Question: {chat_input}
"""
                answer = query_ollama(full_prompt)
                st.markdown(answer)
