import streamlit as st
import time
from openai import OpenAI

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="AccountingGPT", 
    page_icon="🍁",
    layout="wide"
)

# --- 2. THE "BRAIN" (Tax Knowledge Base) ---
class TaxKnowledgeBase:
    def search(self, query):
        # MOCK DATABASE: Simulates searching the Income Tax Act
        knowledge = {
            "tfsa": "The 2024 TFSA contribution limit is **$7,000**. You must be 18+ with a valid SIN. Unused contribution room carries forward indefinitely.",
            "rrsp": "Your RRSP deduction limit is **18%** of your previous year's earned income, up to a maximum of **$31,560** (for 2024). Contributions reduce your taxable income.",
            "home": "The flat rate method ($2/day) for home office expenses ended in 2023. You must now use the **Detailed Method** and obtain a signed T2200 form from your employer.",
            "deadline": "The filing deadline for most individuals is **April 30, 2024**. For self-employed individuals, it is June 15, but any taxes owed are still due by April 30.",
            "meal": "Meal and entertainment expenses are generally limited to **50% deductibility** for business purposes.",
            "cpp": "The maximum pensionable earnings for CPP in 2024 is **$68,500**. The basic exemption remains at $3,500."
        }
        
        query = query.lower()
        results = []
        for key, text in knowledge.items():
            if key in query:
                results.append(text)
        return results

class CRALiveConnector:
    def get_news(self):
        return [
            "⚠️ Interest Rate Update: CRA prescribed interest rates for Q1 2025 have risen to 6%.",
            "✅ Confirmed: The 2024 TFSA Contribution Limit is officially $7,000.",
            "📅 Reminder: RRSP Contribution Deadline is February 29, 2024."
        ]

# Initialize Logic
if 'kb' not in st.session_state:
    st.session_state.kb = TaxKnowledgeBase()
    st.session_state.cra = CRALiveConnector()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. SIDEBAR (API Key & News) ---
with st.sidebar:
    st.title("🍁 TaxGPT")
    st.caption("Canadian Tax Assistant")
    
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.", icon="🗝️")
    
    st.divider()
    
    st.subheader("📢 Live CRA Updates")
    for news in st.session_state.cra.get_news():
        st.info(news)

# --- 4. CHAT INTERFACE ---
st.title("Accounting Assistant")
st.markdown("Ask me about **TFSA limits**, **RRSP deadlines**, or **Home Office expenses**.")

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. CHAT LOGIC ---
if prompt := st.chat_input("How can I help with your taxes?"):
    if not openai_api_key:
        st.stop()

    # A. Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. RAG STEP: Search Knowledge Base
    relevant_info = st.session_state.kb.search(prompt)
    context_str = "\n".join(relevant_info) if relevant_info else "No specific tax act section found."
    
    # C. CREATE PROMPT
    system_instruction = f"""
    You are an expert Canadian Tax Accountant. 
    Answer the user's question using the context below. 
    If the context doesn't have the answer, use your general knowledge but warn the user to verify.
    
    CONTEXT FROM INCOME TAX ACT / CRA:
    {context_str}
    """

    # D. CALL OPENAI
    client = OpenAI(api_key=openai_api_key)
    
    messages_payload = [{"role": "system", "content": system_instruction}] + [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages_payload,
            stream=True,
        )
        response = st.write_stream(stream)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
