"""
Modern Streamlit UI for Email/SMS Spam Detection

Run:
    streamlit run app.py
"""

import streamlit as st

# ---------------- Page Config ---------------- #
st.set_page_config(
    page_title="Email / SMS Spam Detector",
    page_icon="📧",
    layout="wide",
)

# ---------------- Import Model ---------------- #
from predict import predict

# ---------------- Custom CSS ---------------- #
st.markdown("""
<style>

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}

.stApp{
    background: linear-gradient(135deg,#EEF2FF,#F8FAFC);
}

/* Hero Card */
.hero{
    background:rgba(255,255,255,0.82);
    backdrop-filter: blur(18px);
    padding:35px;
    border-radius:20px;
    box-shadow:0 15px 35px rgba(0,0,0,.08);
    margin-bottom:25px;
}

/* Sidebar */
[data-testid="stSidebar"]{
    background:#0F172A;
}

[data-testid="stSidebar"] *{
    color:white;
}

/* Text Area */
textarea{
    border-radius:15px !important;
    font-size:17px !important;
}

/* Button */
.stButton>button{
    width:100%;
    height:55px;
    border:none;
    border-radius:12px;
    color:white;
    font-size:18px;
    font-weight:600;
    background:linear-gradient(90deg,#2563EB,#3B82F6);
    transition:0.3s;
}

.stButton>button:hover{
    transform:translateY(-2px);
    box-shadow:0 12px 25px rgba(37,99,235,.35);
}

/* Result Card */
.result{
    padding:25px;
    border-radius:18px;
    color:white;
    text-align:center;
    font-size:28px;
    font-weight:bold;
    margin-top:20px;
}

.safe{
    background:linear-gradient(135deg,#16A34A,#22C55E);
}

.spam{
    background:linear-gradient(135deg,#DC2626,#EF4444);
}

/* Info Cards */
.metric-card{
    background:white;
    border-radius:18px;
    padding:20px;
    box-shadow:0 5px 15px rgba(0,0,0,.08);
    text-align:center;
    margin-bottom:15px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar ---------------- #

with st.sidebar:

    st.title("🛡 Spam Detector")

    st.markdown("---")

    st.markdown("""
### About

This application detects whether an Email or SMS is **Spam** or **Ham** using a Machine Learning model.

### Technology

- Streamlit
- Scikit-learn
- TF-IDF
- NLTK

### Workflow

1. Clean text
2. TF-IDF Vectorization
3. ML Prediction
4. Confidence Score
""")

    st.markdown("---")

    st.success("Production Ready 🚀")

# ---------------- Hero ---------------- #

st.markdown("""
<div class="hero">
<h1 style="color:#1E3A8A;">📧 Email & SMS Spam Detector</h1>

<p style="font-size:18px;color:#475569;">
Detect spam messages instantly using Machine Learning.
Simply paste your email or SMS and click
<b>Analyze Message</b>.
</p>

</div>
""", unsafe_allow_html=True)

# ---------------- Layout ---------------- #

left, right = st.columns([2.2,1])

with left:

    input_text = st.text_area(
        "Message",
        placeholder="Paste your Email or SMS here...",
        height=260
    )

    predict_btn = st.button("🔍 Analyze Message")

with right:

    st.markdown("""
<div class="metric-card">
<h3>⚡ Fast</h3>
Prediction in milliseconds
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="metric-card">
<h3>🎯 Accurate</h3>
TF-IDF + Machine Learning
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="metric-card">
<h3>🛡 Secure</h3>
No message is stored
</div>
""", unsafe_allow_html=True)

# ---------------- Prediction ---------------- #

if predict_btn:

    if not input_text.strip():

        st.warning("⚠ Please enter an Email or SMS.")

    else:

        with st.spinner("Analyzing message..."):

            try:

                    result = predict(input_text)

                    label = result["label"].lower()

                    confidence = result["confidence"]

                    if label == "spam":

                        st.markdown("""
    <div class="result spam">
    🚨 SPAM MESSAGE
    </div>
    """, unsafe_allow_html=True)

                    else:

                        st.markdown("""
    <div class="result safe">
    ✅ SAFE MESSAGE
    </div>
    """, unsafe_allow_html=True)

                    st.write("")

                    st.write(confidence)
                    

                    st.progress(confidence)

            except ValueError as e:

                st.warning(str(e))

            except Exception as e:

                st.error(f"Unexpected Error: {e}")