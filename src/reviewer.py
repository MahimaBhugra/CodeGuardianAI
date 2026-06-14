
import chromadb
import streamlit as st
from groq import Groq


# Groq Client
client_groq = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)


# ChromaDB Setup
client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_or_create_collection(
    name="code_review_knowledge"
)

# Build database automatically if empty
if collection.count() == 0:

    documents = []

    files = [
        "data/coding_standards.txt",
        "data/security_guidelines.txt",
        "data/review_examples.txt"
    ]

    for file_name in files:

        with open(file_name, "r", encoding="utf-8") as f:
            documents.append(f.read())

    collection.add(
        documents=documents,
        ids=[
            "coding_standards",
            "security_guidelines",
            "review_examples"
        ]
    )


# Helper Function
def add_line_numbers(code):

    lines = code.split("\n")

    return "\n".join(
        f"[LINE {i}] {line}"
        for i, line in enumerate(lines, start=1)
    )


# Main Review Function
def review_code(user_code):

    numbered_code = add_line_numbers(user_code)

    results = collection.query(
        query_texts=[user_code],
        n_results=3
    )

    context = "\n".join(
        results["documents"][0]
    )

    prompt = f"""
You are a senior software engineer.

Context:
{context}

Review the following code.

Tasks:
1. Find bugs
2. Mention line numbers
3. Explain issues
4. Suggest fixes
5. Generate corrected code

IMPORTANT:
1. Do not provide the exact line numbers where the bug occurs.
2. Use coding standards and security guidelines as reference.
3. If the user asks questions such as:
   - What is Python?
   - What is the time complexity of this code?
   - What is the space complexity of this code?
   - What best practices are followed?
   Then answer the question directly instead of performing a code review.

Code:
{numbered_code}
"""

    response = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content