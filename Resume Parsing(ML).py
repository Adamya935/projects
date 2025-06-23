# app.py
import streamlit as st
import io
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document
def extract_text_from_pdf(file):
    return extract_pdf_text(file)

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text(file):
    if file.type == "application/pdf":
        return extract_text_from_pdf(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file)
    elif file.type == "text/plain":
        return str(file.read(), "utf-8")
    else:
        return "Unsupported file type."

st.title("Resume Parser & Job Matcher")

uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    resume_text = extract_text(uploaded_file)
    import re


    def extract_email(text):
        match = re.search( r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        return match.group(0) if match else "Not found"


    def extract_phone(text):
        match = re.search(r'(\+?\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{4}', text)
        return match.group(0) if match else "Not found"


    def extract_name(text):
        # Naive method: gets the first two capitalized words
        lines = text.strip().split('\n')
        for line in lines:
            words = line.strip().split()
            if len(words) >= 2 and all(w.istitle() for w in words[:2]):
                return ' '.join(words[:2])
        return "Not found"


    def extract_skills(text, skill_set):
        text_lower = text.lower()
        found_skills = [skill for skill in skill_set if skill.lower() in text_lower]
        return found_skills


    common_skills = ["Python", "Java", "SQL", "Machine Learning", "Deep Learning", "NLP", "TensorFlow", "Excel", "AWS"]

    st.subheader("Extracted Resume Text:")
    st.text_area("Text Output", resume_text, height=300)
    st.subheader("Extracted Information")

    email = extract_email(resume_text)
    phone = extract_phone(resume_text)
    name = extract_name(resume_text)
    skills = extract_skills(resume_text, common_skills)

    st.write(f"**Name:** {name}")
    st.write(f"**Email:** {email}")
    st.write(f"**Phone:** {phone}")
    st.write(f"**Skills:** {', '.join(skills) if skills else 'Not found'}")

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    # Upload Job Description
    st.subheader("Upload Job Description")
    jd_file = st.file_uploader("Upload Job Description File", type=["pdf", "docx", "txt"], key="jd")

    if jd_file is not None:
        jd_text = extract_text(jd_file)
        st.subheader("Extracted JD Text:")
        st.text_area("JD Text Output", jd_text, height=200)

        # Matching
        st.subheader("Resume Match Score")


        def calculate_similarity(resume_text, jd_text):
            documents = [resume_text, jd_text]
            tfidf = TfidfVectorizer().fit_transform(documents)
            score = cosine_similarity(tfidf[0:1], tfidf[1:2])
            return round(float(score[0][0]) * 100, 2)


        match_score = calculate_similarity(resume_text, jd_text)
        st.write(f"**Match Score:** {match_score} / 100")


