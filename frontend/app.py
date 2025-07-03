import streamlit as st, requests, os, json
import matplotlib.pyplot as plt
import matplotlib as mpl  # added imports for theming

# Dark theme palette inspired by AHU simulator
COLORS = {
    'primary': '#ff9500',
    'background': '#1f1f1f',
    'secondary_bg': '#2e2e2e',
    'text': '#ffffff',
    'accent': '#ff5400'
}
# Apply dark background to any matplotlib figure that might be rendered
plt.style.use('dark_background')
mpl.rcParams['axes.facecolor'] = COLORS['secondary_bg']
mpl.rcParams['figure.facecolor'] = COLORS['background']
mpl.rcParams['text.color'] = COLORS['text']
mpl.rcParams['axes.labelcolor'] = COLORS['text']
mpl.rcParams['xtick.color'] = COLORS['text']
mpl.rcParams['ytick.color'] = COLORS['text']
mpl.rcParams['grid.color'] = '#555555'

st.set_page_config(page_title="Smart Building Assistant", page_icon="🏢", layout="wide")

# Inject custom CSS so core Streamlit elements follow the same dark palette
st.markdown(
    f"""
    <style>
    html, body, [data-testid="stApp"] {{
        background-color: {COLORS['background']};
        color: {COLORS['text']};
    }}
    /* Progress bar color */
    .stProgress > div > div > div > div {{
        background-color: {COLORS['accent']} !important;
    }}
    /* Increase base font size without touching the main h1 title */
    /* Paragraphs, list items, labels, sidebars */
    p, li, label, div[data-testid="stMarkdownContainer"] {{
        font-size: 1.2rem !important;
    }}
    /* Subheaders */
    h2 {{ font-size: 1.9rem !important; }}
    h3, h4, h5, h6 {{ font-size: 1.55rem !important; }}
    </style>
    """,
    unsafe_allow_html=True
)

# Fallback to environment variables when Streamlit secrets not configured
LOCAL = os.getenv("LOCAL_MODE", "true").lower() == "true"
API_TOKEN = os.getenv("API_TOKEN", "demo-token")

API_URL = "http://localhost:8000" if LOCAL else "/api"

# ---- Layout: Tabs ----
st.title("🏢 Smart Building Assistant")

tab_chat, tab_upload, tab_health = st.tabs(["💬 Chat", "📄 Upload", "🩺 Health"])


# ---------------- Chat tab ----------------
with tab_chat:
    st.subheader("Assistant")
    mode = st.radio("Mode", ["RAG", "Agent"], horizontal=True)

    # Pre-loaded example prompts
    examples = [
        "How many documents are currently ingested?",
        "Which floor had the highest occupancy on 1 July 2025?",
        "Average kWh consumed by CHILLER-02 between midnight and 2 am?",
        "When was the last filter change for HVAC-01?",
        "Predict failure probability for HVAC-01."
    ]

    st.caption("Try an example question:")
    cols = st.columns(len(examples))
    selected_example: str | None = None
    for i, (col, ex) in enumerate(zip(cols, examples)):
        if col.button(ex, key=f"ex_btn_{i}"):
            selected_example = ex

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("Ask a question…", key="chat_input")
    if selected_example:
        prompt_to_send = selected_example
    else:
        prompt_to_send = prompt

    if prompt_to_send:
        # Reset chat_input if used
        if prompt:
            st.session_state["chat_input"] = ""

        st.session_state.chat.append({"role": "user", "content": prompt_to_send})
        with st.chat_message("user"):
            st.markdown(prompt_to_send)

        endpoint = "/ask" if mode == "RAG" else "/agent"
        payload = {"query": prompt_to_send} if mode == "RAG" else {"question": prompt_to_send}

        with st.spinner("Thinking…"):
            r = requests.post(
                f"{API_URL}{endpoint}",
                json=payload,
                headers={"Authorization": f"Bearer {API_TOKEN}"},
                timeout=60,
            )
        answer = r.json().get("answer", "(error)") if r.ok else r.text
        st.session_state.chat.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
            if r.ok and r.json().get("citations"):
                with st.expander("Citations"):
                    for c in r.json()["citations"]:
                        st.write(f"{c['source']} (page {c['page']}) — {c['snippet']} …")


# ---------------- Upload tab ----------------
with tab_upload:
    st.subheader("Upload building PDF or CSV")
    uploaded = st.file_uploader("Select a PDF or CSV", type=["pdf", "csv"], key="uploader")
    if uploaded is not None:
        files = {"file": (uploaded.name, uploaded.getvalue())}
        with st.spinner("Uploading & ingesting…"):
            r = requests.post(
                f"{API_URL}/upload-document",
                files=files,
                headers={"Authorization": f"Bearer {API_TOKEN}"},
                timeout=60,
            )
        if r.ok:
            st.success(
                f"Ingested {r.json().get('chunks')} chunks from {r.json().get('file_type', '')} ✔"
            )
        else:
            st.error(r.text)


# ---------------- Health tab ----------------
with tab_health:
    st.subheader("Equipment health prediction")
    equip = st.selectbox("Equipment", ["HVAC-01", "CHILLER-02"], key="equip_select")
    col1, col2 = st.columns(2)
    if col1.button("Predict", key="predict_btn"):
        with st.spinner("Fetching sensors & predicting…"):
            r = requests.get(f"{API_URL}/health/{equip}", headers={"Authorization": f"Bearer {API_TOKEN}"}, timeout=30)
        if r.ok:
            p = r.json().get("failure_probability", 0.0)
            col1.metric("Failure prob.", f"{p:.0%}")
            col2.progress(p)
        else:
            st.error(r.text) 