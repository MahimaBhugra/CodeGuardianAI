
import streamlit as st

from src.reviewer import review_code





# =====================================================

# PAGE CONFIGURATION

# =====================================================



st.set_page_config(

    page_title="CodeGuardian AI",

    page_icon="🛡️",

    layout="wide",

    initial_sidebar_state="collapsed",

)


# =====================================================
# SUPABASE AUTHENTICATION
# =====================================================

from supabase import create_client


def get_supabase_client():
    """Create a fresh client so one user's auth session is never shared with another."""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_PUBLISHABLE_KEY"],
    )


def remember_auth_session(auth_response):
    """Keep the current user's Supabase tokens in this Streamlit session."""
    session = auth_response.session
    user = auth_response.user
    if not session or not user:
        return False
    st.session_state.authenticated = True
    st.session_state.user_email = user.email or ""
    st.session_state.user_id = str(user.id)
    st.session_state.supabase_access_token = session.access_token
    st.session_state.supabase_refresh_token = session.refresh_token
    st.session_state.page = "home"
    return True


# Keep authentication separate from the code-review backend.
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "supabase_access_token" not in st.session_state:
    st.session_state.supabase_access_token = ""
if "supabase_refresh_token" not in st.session_state:
    st.session_state.supabase_refresh_token = ""


# A login screen is shown until Supabase successfully authenticates a user.
if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .stApp { background: #050505; color: #ffffff; }
        header[data-testid="stHeader"] { background: #050505; }
        .auth-brand { color: #4ade80; text-align: center; font-size: 2.2rem;
                      font-weight: 800; margin-top: 1.2rem; }
        .auth-subtitle { color: #a3a3a3; text-align: center; margin-bottom: 1.5rem; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-brand">🛡️ CodeGuardian AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">Sign in or create an account to review your code securely.</div>', unsafe_allow_html=True)

    try:
        supabase = get_supabase_client()
    except Exception:
        st.error(
            "Supabase is not configured yet. Add SUPABASE_URL and "
            "SUPABASE_PUBLISHABLE_KEY to .streamlit/secrets.toml, then restart the app."
        )
        st.stop()

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("Email address", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_submitted = st.form_submit_button("Login", use_container_width=True)

        if login_submitted:
            if not login_email.strip() or not login_password:
                st.warning("Enter both your email address and password.")
            else:
                try:
                    auth_response = supabase.auth.sign_in_with_password({
                        "email": login_email.strip(),
                        "password": login_password,
                    })
                    if remember_auth_session(auth_response):
                        st.rerun()
                    else:
                        st.error("Login was not completed. Check your email confirmation and try again.")
                except Exception as e:
                    # Show Supabase's error message to help diagnose configuration issues.
                    # Never display the submitted password or API keys.
                    error_detail = str(e).strip() or type(e).__name__
                    st.error("Login failed. Supabase returned this error:")
                    st.code(f"{type(e).__name__}: {error_detail}")
                    st.caption(
                        "If the message mentions email confirmation, confirm your email in your inbox. "
                        "If it mentions invalid credentials, verify the email and password."
                    )

    with register_tab:
        with st.form("register_form"):
            register_email = st.text_input("Email address", key="register_email")
            register_password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm password", type="password", key="confirm_password")
            register_submitted = st.form_submit_button("Create account", use_container_width=True)

        if register_submitted:
            if not register_email.strip() or not register_password or not confirm_password:
                st.warning("Complete all fields to create your account.")
            elif register_password != confirm_password:
                st.warning("The passwords do not match.")
            elif len(register_password) < 8:
                st.warning("Use a password with at least 8 characters.")
            else:
                try:
                    auth_response = supabase.auth.sign_up({
                        "email": register_email.strip(),
                        "password": register_password,
                    })
                    if remember_auth_session(auth_response):
                        st.success("Your account was created successfully.")
                        st.rerun()
                    else:
                        st.success(
                            "Registration request received. Check your inbox for the "
                            "Supabase confirmation email, then return here to log in."
                        )
                except Exception as e:
                    # Display the actual Supabase response instead of masking the cause.
                    # Do not print submitted passwords or API keys.
                    error_detail = str(e).strip() or type(e).__name__
                    st.error("Registration failed. Supabase returned this error:")
                    st.code(f"{type(e).__name__}: {error_detail}")
                    st.caption(
                        "Check whether the email is already registered, the password meets "
                        "your Supabase password requirements, and the Email provider is enabled."
                    )

    st.caption("Never submit real passwords, API keys, or other secrets in code-review requests.")
    st.stop()






# Rebuild a client for this signed-in Streamlit session and attach that user's JWT.
# RLS in Supabase then enforces access to only this user's rows.
try:
    supabase = get_supabase_client()
    if st.session_state.get("supabase_access_token") and st.session_state.get("supabase_refresh_token"):
        auth_state = supabase.auth.set_session(
            st.session_state.supabase_access_token,
            st.session_state.supabase_refresh_token,
        )
        active_session = getattr(auth_state, "session", None)
        if active_session:
            st.session_state.supabase_access_token = active_session.access_token
            st.session_state.supabase_refresh_token = active_session.refresh_token
except Exception:
    st.session_state.authenticated = False
    st.session_state.supabase_access_token = ""
    st.session_state.supabase_refresh_token = ""
    st.error("Your login session has expired. Please log in again.")
    st.stop()


def save_review(language, source_code, review_result):
    """Save one review using the authenticated user's Supabase session."""
    payload = {
        "user_id": st.session_state.user_id,
        "language": language,
        "source_code": source_code,
        "review_result": review_result,
    }
    return supabase.table("code_reviews").insert(payload).execute()


def fetch_review_history():
    """RLS limits these results to the signed-in user."""
    return (
        supabase.table("code_reviews")
        .select("id, language, source_code, review_result, created_at")
        .order("created_at", desc=True)
        .execute()
        .data
    )


def delete_review(review_id):
    """Delete a review; the database RLS policy checks ownership."""
    return supabase.table("code_reviews").delete().eq("id", review_id).execute()


# =====================================================

# SESSION STATE

# =====================================================



if "page" not in st.session_state:

    st.session_state.page = "home"



if "review_result" not in st.session_state:

    st.session_state.review_result = None





# =====================================================

# CUSTOM CSS

# =====================================================



st.markdown("""

<style>



/* ---------- Global layout ---------- */



.stApp {

    background: #050505;

    color: #ffffff;

}



header[data-testid="stHeader"] {

    background: #050505;

    height: 3.5rem;

}



.stAppViewContainer .main .block-container {

    max-width: 1250px;

    padding: 3rem 2rem;

    overflow-x: hidden;

}



hr {

    border-color: #292929;

}





/* ---------- Navbar ---------- */



.brand-name {

    color: #4ade80;

    font-size: 1.35rem;

    font-weight: 800;

    overflow-wrap: anywhere;

}





/* ---------- Headings ---------- */



.main-title {

    color: #4ade80;

    font-size: clamp(2.4rem, 6vw, 4.5rem);

    font-weight: 800;

    letter-spacing: -2px;

    line-height: 1.15;

    text-align: center;

    overflow-wrap: anywhere;

}



.subtitle {

    max-width: 750px;

    margin: 0 auto 1.5rem;

    color: #a3a3a3;

    font-size: 1.1rem;

    line-height: 1.7;

    text-align: center;

}



.section-title {

    margin: 2rem 0 1rem;

    color: #ffffff;

    font-size: 1.8rem;

    font-weight: 700;

}





/* ---------- Hero section ---------- */



.hero {

    box-sizing: border-box;

    width: 100%;

    margin: 1rem 0 1.5rem;

    padding: 3rem 2rem;

    background: linear-gradient(145deg, #101713, #080808);

    border: 1px solid #244332;

    border-radius: 20px;

    text-align: center;

    overflow-wrap: anywhere;

}



.hero .eyebrow {

    margin-bottom: 1rem;

    color: #4ade80;

    font-size: 0.85rem;

    font-weight: 700;

    letter-spacing: 2px;

    text-transform: uppercase;

}



.hero h2 {

    margin: 0 0 1rem;

    color: #ffffff;

    font-size: clamp(2rem, 4vw, 3rem);

    line-height: 1.25;

}



.hero p {

    max-width: 760px;

    margin: 0 auto;

    color: #b8c4bc;

    font-size: 1.05rem;

    line-height: 1.8;

}





/* ---------- Sliding card animation ---------- */



@keyframes cardSlideIn {

    0% {

        opacity: 0;

        transform: translateX(-120px) scale(0.90);

        filter: blur(5px);

    }



    70% {

        opacity: 1;

        filter: blur(0);

    }



    100% {

        opacity: 1;

        transform: translateX(0) scale(1);

        filter: blur(0);

    }

}





/* ---------- Neon glow ---------- */



@keyframes neonPulse {

    0%, 100% {

        box-shadow: 0 0 8px rgba(168, 85, 247, 0.12);

        border-color: #392747;

    }



    50% {

        box-shadow: 0 0 25px rgba(168, 85, 247, 0.45);

        border-color: #c084fc;

    }

}





/* ---------- Feature cards ---------- */



.feature-card {

    box-sizing: border-box;

    position: relative;

    width: 100%;

    height: 220px;

    padding: 1.3rem;

    margin-bottom: 1rem;



    display: flex;

    flex-direction: column;



    background: linear-gradient(135deg, #111111, #17111d);

    border: 1px solid #392747;

    border-radius: 15px;



    overflow: hidden;

    overflow-wrap: anywhere;



    opacity: 0;



    animation:

        cardSlideIn 1s cubic-bezier(0.16, 1, 0.3, 1) both,

        neonPulse 2.5s ease-in-out infinite;

}



.feature-card:hover {

    border-color: #c084fc;

    box-shadow: 0 0 28px rgba(192, 132, 252, 0.5);

}



.feature-icon {

    flex-shrink: 0;

    margin-bottom: 0.5rem;

    font-size: 1.8rem;

}



.feature-card h3 {

    flex-shrink: 0;

    margin: 0.3rem 0 0.7rem;

    color: #c084fc;

    font-size: 1.1rem;

    line-height: 1.4;

}



.feature-card p {

    margin: 0;

    color: #c4c4ce;

    font-size: 0.93rem;

    line-height: 1.6;

    overflow-wrap: anywhere;

}





/* ---------- Buttons ---------- */



.stButton > button {

    min-height: 48px;

    background: #16a34a;

    color: #ffffff;

    border: 1px solid #16a34a;

    border-radius: 9px;

    font-weight: 600;

    transition: background 0.2s ease, border-color 0.2s ease;

}



.stButton > button:hover {

    background: #15803d;

    color: #ffffff;

    border-color: #15803d;

}





/* ---------- Code editor ---------- */



.stTextArea textarea {

    background: #101010 !important;

    color: #e5e7eb !important;

    border: 1px solid #353535 !important;

    border-radius: 10px !important;

    font-family: Consolas, monospace !important;

    font-size: 15px !important;

}



.stTextArea label,

.stSelectbox label {

    color: #e5e7eb !important;

}





/* ---------- Footer ---------- */



.footer {

    padding: 2rem 0 0.5rem;

    color: #737373;

    font-size: 0.85rem;

    text-align: center;

}





/* ---------- Responsive layout ---------- */



@media (max-width: 768px) {

    .stAppViewContainer .main .block-container {

        padding: 2rem 1rem;

    }



    .hero {

        padding: 2rem 1rem;

    }



    .main-title {

        letter-spacing: -1px;

    }



    .feature-card {

        height: auto;

        min-height: 190px;

        padding: 1.1rem;

        overflow: visible;

    }



    .brand-name {

        font-size: 1.1rem;

    }

}





/* ---------- Reduced motion preference ---------- */



@media (prefers-reduced-motion: reduce) {

    .feature-card {

        opacity: 1;

        animation: none;

    }

}



</style>

""", unsafe_allow_html=True)





# =====================================================

# NAVBAR

# =====================================================



left_nav, user_nav, action_nav = st.columns(

    [3.5, 1.5, 1],

    vertical_alignment="center",

)


with left_nav:

    st.markdown(

        '<div class="brand-name">🛡️ CodeGuardian AI</div>',

        unsafe_allow_html=True,

    )


with user_nav:
    st.caption(f"Signed in: {st.session_state.user_email}")


with action_nav:
    if st.session_state.page != "home":
        if st.button("← Home", use_container_width=True, key="home_nav"):
            st.session_state.page = "home"
            st.rerun()
    if st.button("🕘 History", use_container_width=True, key="history_nav"):
        st.session_state.page = "history"
        st.rerun()
    if st.button("Logout", use_container_width=True, key="logout_nav"):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        for key in (
            "authenticated", "user_email", "user_id", "review_result",
            "supabase_access_token", "supabase_refresh_token",
        ):
            st.session_state.pop(key, None)
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.session_state.user_id = ""
        st.session_state.page = "home"
        st.rerun()



st.divider()





# =====================================================

# HOME PAGE

# =====================================================



if st.session_state.page == "home":



    st.markdown(

        '<div class="main-title">CodeGuardian AI</div>',

        unsafe_allow_html=True,

    )



    st.markdown(

        '<div class="subtitle">'

        'AI-Powered Code Review &amp; Security Analysis'

        '</div>',

        unsafe_allow_html=True,

    )



    # Keep the HTML elements together so Streamlit

    # renders them instead of displaying literal tags.



    st.markdown(

        """

        <div class="hero"><div class="eyebrow">INTELLIGENT CODE ANALYSIS</div><h2>Write better code.<br>Build more securely.</h2><p>Code that works is not always code that is secure. Identify potential bugs, uncover security risks, and improve coding practices with AI-powered code reviews.</p></div>

        """,

        unsafe_allow_html=True,

    )



    _, start_col, _ = st.columns([1, 1.5, 1])



    with start_col:

        if st.button(

            "🚀 Get Started",

            use_container_width=True,

            key="get_started",

        ):

            st.session_state.page = "reviewer"

            st.rerun()



    st.markdown(

        '<div class="section-title">What CodeGuardian AI Offers</div>',

        unsafe_allow_html=True,

    )



    features = [

        (

            "🔍",

            "Bug Detection",

            "Identify potential logic errors and coding problems "

            "that may affect the correctness of your program.",

        ),

        (

            "🛡️",

            "Security Analysis",

            "Check submitted code for potential security "

            "vulnerabilities and insecure coding practices.",

        ),

        (

            "📚",

            "Context-Aware Reviews",

            "Use Retrieval-Augmented Generation (RAG) with "

            "ChromaDB to provide relevant coding guidelines "

            "to the AI model.",

        ),

        (

            "💡",

            "Suggested Fixes",

            "Receive practical suggestions and corrected code "

            "for the issues identified by the reviewer.",

        ),

        (

            "⚙️",

            "Coding Standards",

            "Compare code against relevant coding standards "

            "and security guidelines stored in the knowledge base.",

        ),

        (

            "🤖",

            "AI-Powered Analysis",

            "Use Groq-hosted language models to analyze code "

            "and generate a readable review report.",

        ),

    ]



    # Render three cards per row.

    # Each card receives a unique delay, so they slide in

    # sequentially from left to right.



    for row_start in range(0, len(features), 3):



        columns = st.columns(3, gap="medium")



        for column_index, column in enumerate(columns):



            feature_index = row_start + column_index



            if feature_index >= len(features):

                break



            icon, title, description = features[feature_index]



            delay = row_start * 0.20 + column_index * 0.35

            glow_delay = delay + 1



            with column:

                # Keep the HTML tags at the start of the string so Markdown
                # doesn't interpret the indentation as a code block.
                st.markdown(
                    f'<div class="feature-card" style="animation-delay: {delay}s, {glow_delay}s;">'
                    f'<div class="feature-icon">{icon}</div>'
                    f'<h3>{title}</h3>'
                    f'<p>{description}</p>'
                    '</div>',
                    unsafe_allow_html=True,
                )



    # How it works



    st.markdown(

        '<div class="section-title">How It Works</div>',

        unsafe_allow_html=True,

    )



    step1, step2, step3 = st.columns(3, gap="medium")



    with step1:

        st.markdown("### 01 · Submit")

        st.write("Paste your source code into the review workspace.")



    with step2:

        st.markdown("### 02 · Analyze")

        st.write(

            "Relevant guidelines are retrieved from ChromaDB "

            "and provided to the Groq language model."

        )



    with step3:

        st.markdown("### 03 · Improve")

        st.write(

            "Review the findings, understand their impact, "

            "and examine the suggested corrections."

        )



    st.divider()



    _, bottom_col, _ = st.columns([1, 1.5, 1])



    with bottom_col:

        if st.button(

            "Start Reviewing Your Code →",

            use_container_width=True,

            key="bottom_get_started",

        ):

            st.session_state.page = "reviewer"

            st.rerun()



    st.markdown(

        '<div class="footer">'

        'CodeGuardian AI · AI-assisted code quality and security'

        '</div>',

        unsafe_allow_html=True,

    )





# =====================================================
# REVIEW HISTORY PAGE
# =====================================================

elif st.session_state.page == "history":
    st.markdown('<div class="main-title" style="font-size:3rem;">My Review History</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your previously saved code reviews.</div>', unsafe_allow_html=True)

    try:
        history_rows = fetch_review_history()
    except Exception as history_error:
        st.error("Could not load your review history.")
        st.caption(f"{type(history_error).__name__}: {history_error}")
        history_rows = []

    if not history_rows:
        st.info("No saved reviews yet. Analyze some code and your reviews will appear here.")
    else:
        st.caption(f"{len(history_rows)} saved review(s)")
        for row in history_rows:
            created_at = row.get("created_at", "")
            title = f"{row.get('language', 'Code')} review · {created_at} · #{row['id']}"
            with st.expander(title):
                st.markdown("**Submitted code**")
                st.code(row.get("source_code", ""), language=None)
                st.markdown("**Review report**")
                review_text = row.get("review_result", "")
                marker = "CORRECTED_CODE:"
                if marker in review_text:
                    review_part, fixed_part = review_text.split(marker, 1)
                    st.markdown(review_part.strip())
                    st.markdown("**Suggested corrected code**")
                    st.code(fixed_part.strip())
                else:
                    st.markdown(review_text)
                if st.button("Delete this review", key=f"delete_review_{row['id']}"):
                    try:
                        delete_review(row["id"])
                        st.success("Review deleted.")
                        st.rerun()
                    except Exception as delete_error:
                        st.error("Could not delete this review.")
                        st.caption(f"{type(delete_error).__name__}: {delete_error}")

    st.markdown('<div class="footer">Your saved reviews are protected by Supabase row-level security.</div>', unsafe_allow_html=True)


# =====================================================

# CODE REVIEWER PAGE

# =====================================================



elif st.session_state.page == "reviewer":



    st.markdown(

        '<div class="main-title" style="font-size:3rem;">'

        'Code Review Workspace'

        '</div>',

        unsafe_allow_html=True,

    )



    st.markdown(

        '<div class="subtitle">'

        'Submit your code to identify potential bugs, '

        'security vulnerabilities, and coding issues.'

        '</div>',

        unsafe_allow_html=True,

    )



    language = st.selectbox(

        "Programming Language",

        ["Python", "Java", "JavaScript", "C++", "C", "C#", "Other"],

    )



    code = st.text_area(

        "Source Code",

        height=350,

        placeholder=(

            "Paste your code here...\n\n"

            'Example:\npassword = "admin123"\n'

            'print("Login successful")'

        ),

        key="source_code",

    )



    st.caption(

        "Remove real passwords, API keys, and other sensitive "

        "information before submitting code."

    )



    if st.button(

        "🔍 Analyze Code",

        use_container_width=True,

        key="analyze_code",

    ):



        if not code.strip():

            st.warning("Please paste some code before starting the review.")



        else:

            try:

                with st.spinner(

                    "Analyzing code and retrieving relevant guidelines..."

                ):

                    result = review_code(code)

                st.session_state.review_result = result
                st.session_state.last_review_code = code
                st.session_state.last_review_language = language
                try:
                    save_review(language, code, result)
                    st.success("Review completed and saved to your history.")
                except Exception as save_error:
                    st.warning(
                        "The review completed, but it could not be saved to history. "
                        "Check the Supabase table permissions and your login session."
                    )
                    st.caption(f"Save error: {type(save_error).__name__}: {save_error}")

            except Exception:

                st.error(

                    "The review could not be completed. "

                    "Please check the application logs."

                )



    # Display review results



    if st.session_state.review_result:



        result = st.session_state.review_result



        st.divider()

        st.markdown("## 📋 Review Report")



        marker = "CORRECTED_CODE:"



        if marker in result:



            review_text, fixed_code = result.split(marker, 1)



            st.markdown(review_text.strip())

            st.markdown("## ✅ Corrected Code")



            fixed_code = fixed_code.strip()



            if fixed_code.startswith("```"):



                lines = fixed_code.splitlines()



                if lines and lines[0].startswith("```"):

                    lines = lines[1:]



                if lines and lines[-1].strip() == "```":

                    lines = lines[:-1]



                fixed_code = "\n".join(lines).strip()



            st.code(fixed_code)



            st.download_button(

                "📥 Download Corrected Code",

                data=fixed_code,

                file_name="corrected_code.txt",

                mime="text/plain",

                use_container_width=True,

            )



        else:

            st.markdown(result)



        if st.button("🗑️ Clear Review", key="clear_review"):

            st.session_state.review_result = None

            st.rerun()



    st.markdown(

        '<div class="footer">'

        'AI-generated findings should be verified before applying fixes.'

        '</div>',

        unsafe_allow_html=True,

    )
