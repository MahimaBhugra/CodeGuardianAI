# import streamlit as st
# from src.reviewer import review_code

# st.title("AI Code Reviewer")

# code = st.text_area(
#     "Paste your code here",
#     height=300
# )

# if st.button("Review Code"):

#     with st.spinner("Reviewing..."):

#         result = review_code(code)

#     st.subheader("Review Result")

#     st.write(result)




import streamlit as st
from src.reviewer import review_code

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="CodeGuardian AI",
    page_icon="💻",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

/* Main App */
.stApp{
    background-color:#000000;
    color:white;
}

/* Title */
.main-title{
    text-align:center;
    font-size:70px;
    font-weight:800;
    color:#00ff88;
    letter-spacing:2px;
    margin-bottom:5px;
}

/* Subtitle */
.subtitle{
    text-align:center;
    color:#9ca3af;
    font-size:18px;
    margin-bottom:25px;
}

/* Section Headers */
h1, h2, h3{
    color:#00ff88;
}

/* Text Area */
textarea{
    background-color:#111111 !important;
    color:#00ff88 !important;
    font-family:Consolas !important;
    font-size:16px !important;
}

/* Review Box */
.review-box{
    background:#121212;
    padding:20px;
    border-radius:12px;
    border:1px solid #2d2d2d;
    color:white;
}

/* Main Button */
.stButton > button{
    width:100%;
    background-color:#16a34a;
    color:white;
    font-weight:600;
    font-size:18px;
    border-radius:8px;
    border:none;
    height:50px;
}

/* Download Button */
.stDownloadButton > button{
    width:100%;
    background-color:#16a34a;
    color:white;
    font-weight:600;
    border-radius:8px;
    border:none;
}

/* Divider */
hr{
    border:1px solid #2d2d2d;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="main-title">
        CodeGuardian AI
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
        RAG + ChromaDB + Ollama + LLM Powered Code Review System
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# --------------------------------------------------
# INPUT
# --------------------------------------------------

st.subheader("📝 Source Code")

user_code = st.text_area(
    "",
    height=400,
    placeholder="Paste your Python, Java, JavaScript or C++ code here..."
)

# --------------------------------------------------
# REVIEW BUTTON
# --------------------------------------------------

if st.button("🚀 Analyze Code"):

    if not user_code.strip():
        st.warning("Please paste some code first.")
        st.stop()

    with st.spinner("Analyzing Code..."):

        result = review_code(user_code)

    st.divider()

    # --------------------------------------------------
    # SPLIT REVIEW AND FIXED CODE
    # --------------------------------------------------

    if "CORRECTED_CODE:" in result:

        review_text, fixed_code = result.split(
            "CORRECTED_CODE:",
            maxsplit=1
        )

        col1, col2 = st.columns([1, 1])

        # --------------------------
        # REVIEW PANEL
        # --------------------------

        with col1:

            st.subheader("📋 Review Report")

            st.markdown(
                f"""
                <div class="review-box">
                <pre>{review_text}</pre>
                </div>
                """,
                unsafe_allow_html=True
            )

        # --------------------------
        # CORRECTED CODE PANEL
        # --------------------------

        with col2:

            st.subheader("✅ Corrected Code")

            st.code(
                fixed_code.strip(),
                language="python"
            )

            st.caption(
                "Use the copy icon in the top-right corner of the code block."
            )

            st.download_button(
                "📥 Download Corrected Code",
                fixed_code,
                file_name="corrected_code.py",
                mime="text/plain"
            )

    else:

        st.subheader("📋 Review Result")

        st.markdown(
            f"""
            <div class="review-box">
            <pre>{result}</pre>
            </div>
            """,
            unsafe_allow_html=True
        )

