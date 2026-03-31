import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

# ---------------- SETUP ----------------
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(layout="wide")

MAX_FOLLOWUPS = 2  # ✅ fixed requirement

# ---------------- UI ----------------
st.markdown("""
<style>
.card {
    background: white;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #eee;
    margin-bottom: 10px;
}
.answer {
    background: #f6f8fb;
    padding: 10px;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("🎤 AI Interview Coach")
st.markdown("""
## 🚀 Mock Practice Interviews

Practice real interviews with:
- 🎯 Role-specific questions
- 🔁 Smart follow-ups
- 📊 Detailed feedback

👉 Select your role, skills, and start the interview.
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    role = st.selectbox("Role", ["Product Manager", "Consulting", "General"])

with col2:
    level = st.selectbox("Level", ["Entry", "Intermediate", "Expert"])

with col3:
    competencies = st.multiselect(
        "Competencies",
        [
            "Product Sense","User Empathy","Analytics","Execution","Strategy",
            "Stakeholders","Leadership","Collaboration","Problem Solving",
            "Communication","Prioritization","Decision Making"
        ]
    )

with col4:
    total_questions = st.selectbox("Questions", [1,2,3,4])

if st.button("🔄 Reset Interview"):
    st.session_state.clear()

st.divider()

# ---------------- STATE ----------------
if "interview" not in st.session_state:
    st.session_state["interview"] = []

if "q_index" not in st.session_state:
    st.session_state["q_index"] = 0

if "followup_count" not in st.session_state:
    st.session_state["followup_count"] = 0

if "active" not in st.session_state:
    st.session_state["active"] = False

if "show_feedback" not in st.session_state:
    st.session_state["show_feedback"] = False

# ---------------- START ----------------
if not st.session_state.get("active") and not st.session_state.get("show_feedback"):
    st.info("👆 Start the interview to begin practicing")
if st.button("🚀 Start Interview"):
    st.session_state["interview"] = []
    st.session_state["q_index"] = 1
    st.session_state["followup_count"] = 0
    st.session_state["active"] = True
    st.session_state["show_feedback"] = False

    prompt = f"""
    You are a strict interviewer for a {role} role.

    Candidate level: {level}
    Focus areas: {', '.join(competencies)}

    Ask ONE interview question.
    Only output the question.
    """

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    question = res.choices[0].message.content.strip()

    st.session_state["current_q"] = question

    st.session_state["interview"].append({
        "main_question": question,
        "main_answer": "",
        "followups": []
    })

# ---------------- DISPLAY HISTORY ----------------
for i, q in enumerate(st.session_state["interview"]):
    st.markdown(f"### Question {i+1}")

    st.markdown(f"<div class='card'>{q['main_question']}</div>", unsafe_allow_html=True)

    if q["main_answer"]:
        st.markdown(f"<div class='answer'><b>Your Answer:</b> {q['main_answer']}</div>", unsafe_allow_html=True)

    for j, f in enumerate(q["followups"]):
        st.markdown(f"- Follow-up {j+1}: {f['question']}")
        st.markdown(f"<div class='answer'>{f['answer']}</div>", unsafe_allow_html=True)

    st.divider()

# ---------------- CURRENT QUESTION ----------------
if st.session_state["active"]:

    st.subheader(f"Current Question {st.session_state['q_index']}")
    st.write(st.session_state["current_q"])

    answer = st.text_area(
        "Your Answer",
        key=f"ans_{st.session_state['q_index']}_{st.session_state['followup_count']}"
    )

    col1, col2, col3 = st.columns(3)

    # -------- SUBMIT --------
    with col1:
        if st.button("Submit Answer", use_container_width=True):

            if not answer.strip():
                st.warning("Enter answer")
                st.stop()

            current = st.session_state["interview"][-1]

            # Save main or followup answer
            if st.session_state["followup_count"] == 0:
                current["main_answer"] = answer
            else:
                current["followups"].append({
                    "question": st.session_state["current_q"],
                    "answer": answer
                })

            # Build context (important)
            context = f"Main Question: {current['main_question']}\n"
            context += f"Answer: {current['main_answer']}\n"

            for f in current["followups"]:
                context += f"Follow-up: {f['question']}\nAnswer: {f['answer']}\n"

            # FOLLOWUPS FLOW
            if st.session_state["followup_count"] < MAX_FOLLOWUPS:
                prompt = f"""
                You are a strict interviewer.

                Context:
                {context}

                Ask ONE sharp follow-up question.
                Only output the question.
                """

                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"user","content":prompt}]
                )

                st.session_state["current_q"] = res.choices[0].message.content.strip()
                st.session_state["followup_count"] += 1

            else:
                # ✅ AUTO END OR NEXT
                if st.session_state["q_index"] >= total_questions:
                    st.success("Interview complete! Generating feedback...")
                    st.session_state["active"] = False
                    st.session_state["show_feedback"] = True
                else:
                    st.session_state["ready_next"] = True

    # -------- NEXT QUESTION --------
    with col2:
        disabled = st.session_state["q_index"] >= total_questions

        if st.button("Next Question", disabled=disabled, use_container_width=True):

            if st.session_state["q_index"] < total_questions:
                st.session_state["q_index"] += 1
                st.session_state["followup_count"] = 0
                st.session_state["ready_next"] = False

                prompt = f"""
                You are an interviewer for a {role} role.

                Ask a NEW interview question.
                Only output the question.
                """

                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"user","content":prompt}]
                )

                question = res.choices[0].message.content.strip()

                st.session_state["current_q"] = question

                st.session_state["interview"].append({
                    "main_question": question,
                    "main_answer": "",
                    "followups": []
                })

    # -------- END INTERVIEW --------
    with col3:
        if st.button("End Interview", use_container_width=True):
            st.session_state["active"] = False
            st.session_state["show_feedback"] = True


# ---------------- FEEDBACK ----------------
if st.session_state.get("show_feedback"):

    st.header("📊 Interview Feedback")

    interview_data = st.session_state["interview"]

    # ✅ Check if ANY valid answers exist
    answered_questions = [
        q for q in interview_data if q.get("main_answer", "").strip()
    ]

    if len(answered_questions) == 0:
        st.warning("⚠️ You did not answer any questions. Please attempt the interview to receive feedback.")
        st.stop()

    # Build transcript ONLY with answered questions
    transcript = ""
    for i, q in enumerate(answered_questions):
        transcript += f"\nQuestion {i+1}: {q['main_question']}\n"
        transcript += f"Answer: {q['main_answer']}\n"

    # 🔥 STRICT PROMPT (no hallucination)
    prompt = f"""
    You are an honest and strict interview evaluator.

    Evaluate ONLY based on the answers provided below.

    If answers are incomplete or weak:
    - Clearly call it out
    - DO NOT assume missing information
    - DO NOT fabricate answers

    Interview data:
    {transcript}

    IMPORTANT RULES:
    - If insufficient data → say "Insufficient data for evaluation"
    - Be critical but constructive
    - Do NOT return JSON

    Structure your response:

    OVERALL FEEDBACK:
    (Mention if limited data)

    STRENGTHS:
    - bullets (only if applicable)

    WEAKNESSES:
    - bullets

    IMPROVEMENTS:
    - bullets

    QUESTION-WISE:

    Question 1:
    Feedback:
    Ideal Answer:

    Question 2:
    Feedback:
    Ideal Answer:
    """

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    st.write(res.choices[0].message.content)
