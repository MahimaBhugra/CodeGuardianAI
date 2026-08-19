
import os
import chromadb
import streamlit as st
from groq import Groq


# ==========================================================
# GROQ CLIENT
# ==========================================================

client_groq = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)


# ==========================================================
# CHROMADB SETUP
# ==========================================================

chroma_client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = chroma_client.get_or_create_collection(
    name="code_review_knowledge"
)


# ==========================================================
# BUILD KNOWLEDGE BASE IF EMPTY
# ==========================================================

if collection.count() == 0:

    documents = []

    files = [
        "data/coding_standards.txt",
        "data/security_guidelines.txt",
        "data/review_examples.txt"
    ]

    for file_name in files:

        if os.path.exists(file_name):

            with open(
                file_name,
                "r",
                encoding="utf-8"
            ) as file:

                documents.append(file.read())

    if documents:

        collection.add(
            documents=documents,
            ids=[
                "coding_standards",
                "security_guidelines",
                "review_examples"
            ][:len(documents)]
        )


# ==========================================================
# CODE REVIEW FUNCTION
# ==========================================================

def review_code(user_code):

    # ------------------------------------------------------
    # Validate input
    # ------------------------------------------------------

    if not user_code or not user_code.strip():

        return "Please provide some code to review."


    # ------------------------------------------------------
    # RAG RETRIEVAL
    # ------------------------------------------------------

    results = collection.query(
        query_texts=[user_code],
        n_results=3
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    context = "\n\n".join(documents)


    # ------------------------------------------------------
    # PROMPT
    # ------------------------------------------------------

    prompt = f"""
You are CodeGuardian AI, a precise and conservative
software code reviewer.

Your task is to review ONLY the code provided by the user.

The retrieved context contains security guidelines,
coding standards, and previous review examples.

Use the retrieved context as a REFERENCE, not as a list
of problems that must automatically be reported.

========================================================
STRICT REVIEW RULES
========================================================

1. Report ONLY problems that actually exist in the code.

2. NEVER invent bugs, vulnerabilities, errors, or
   security issues.

3. NEVER report hypothetical problems.

4. NEVER report a recommendation merely because a coding
   guideline mentions it.

5. A guideline is NOT automatically a bug.

6. Only report a guideline violation when there is
   clear evidence in the submitted code.

7. Do NOT assume code that is not shown.

8. Do NOT assume hidden functionality.

9. Do NOT report issues from unrelated programming
   languages.

10. Do NOT repeat the same issue.

11. Do NOT mention line numbers.

12. Do NOT provide a long general code-quality report.

13. Do NOT criticize optional stylistic preferences.

14. Focus on:
    - Actual bugs
    - Actual security vulnerabilities
    - Actual coding-practice violations that are
      clearly present
    - Problems that could affect correctness,
      security, or maintainability

15. Report a maximum of 5 genuine issues.

16. Keep every issue concise.

17. If there are no genuine issues, say:

    "No significant issues detected."

18. Do not add additional recommendations after the
    review.

========================================================
SEVERITY RULES
========================================================

Use severity only when appropriate.

Critical:
A severe vulnerability or issue that could cause
major security or system impact.

High:
A serious security vulnerability or important bug.

Medium:
A meaningful bug, security concern, or maintainability
problem that should be fixed.

Low:
A minor but genuine issue.

Do NOT assign severity to personal preferences or
optional improvements.

========================================================
RAG CONTEXT
========================================================

The following information was retrieved from the
CodeGuardian AI knowledge base:

{context}

========================================================
USER CODE
========================================================

{user_code}

========================================================
REVIEW PROCESS
========================================================

First:

1. Examine the actual submitted code.

2. Identify problems that are demonstrably present.

3. Compare those problems with the retrieved guidelines.

4. If a retrieved guideline matches the problem,
   mention it.

5. If no guideline matches, report the problem anyway
   if it is genuinely a bug or security issue.

6. Ignore retrieved guidelines that do not apply.

========================================================
OUTPUT FORMAT
========================================================

For every genuine issue, use this format:

ISSUE:
[Short issue name]

SEVERITY:
[Critical / High / Medium / Low]

WHY IT IS A PROBLEM:
[Brief explanation]

WHY IT MATTERS:
[Brief explanation of the impact]

RELATED GUIDELINE:
[Relevant guideline or "None"]

FIX:
[Brief practical fix]

Do not include line numbers.

Do not create empty issue sections.

========================================================
CORRECTED CODE
========================================================

After the issues, provide ONE corrected version of the
user's original code.

The corrected code MUST:

- Preserve the original functionality.
- Fix only the issues you actually identified.
- Make minimal necessary changes.
- Not introduce unrelated functionality.
- Not invent missing code.
- Not completely rewrite the program.
- Not add unnecessary libraries.
- Not change the programming language.

End the response with EXACTLY:

CORRECTED_CODE:

[corrected code]
"""


    # ======================================================
    # GROQ REQUEST
    # ======================================================

    try:

        response = client_groq.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are CodeGuardian AI. "
                        "You are a precise, conservative "
                        "and evidence-based code reviewer. "
                        "Never hallucinate issues. "
                        "Only report problems that are "
                        "actually present in the submitted code."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.1,

            max_completion_tokens=1800
        )


        # --------------------------------------------------
        # RETURN RESPONSE
        # --------------------------------------------------

        return response.choices[0].message.content


    # ======================================================
    # ERROR HANDLING
    # ======================================================

    except Exception as e:

        return f"""
Unable to complete the code review.

Error:
{str(e)}
"""