
import streamlit as st
import PyPDF2
from docx import Document
import io
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit configuration
st.set_page_config(
    page_title="Resume Critiquer",
    page_icon="📝",
    layout="centered"
)

st.title("AI Resume Critiquer 📝")
st.markdown(
    "Upload your resume and get AI-powered feedback tailored to your needs."
)

# Get Groq API key
groq_api_key = os.getenv("GROQ_API_KEY")

# File uploader
uploaded_file = st.file_uploader(
    "Upload your resume (PDF or TXT or Docx):",
    type=["pdf", "txt", "docx"]
)

job_role = st.text_input(
    "Enter the job role you're targeting (optional):"
)

analyse = st.button("Analyse Resume")


# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    text = ""

    for page in pdf_reader.pages:
        text += (page.extract_text() or "") + "\n"

    return text


# Extract text from uploaded file
def extract_text_from_file(uploaded_file):

    file_extension = uploaded_file.name.lower().split(".")[-1]

    if file_extension == "pdf":
        return extract_text_from_pdf(
            io.BytesIO(uploaded_file.getvalue())
        )

    elif file_extension == "docx":
        document = Document(io.BytesIO(uploaded_file.getvalue()))

        text = []

        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)

        # Extract text from tables
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text.append(cell.text)

        return "\n".join(text)

    elif file_extension == "txt":
        return uploaded_file.getvalue().decode("utf-8")

    return ""


# Analyse resume
if analyse and uploaded_file:

    try:
        # Check API key
        if not groq_api_key:
            st.error("GROQ_API_KEY not found. Please configure your .env file.")
            st.stop()

        # Extract file content
        file_content = extract_text_from_file(uploaded_file)

        if not file_content.strip():
            st.error("File does not have any content...")
            st.stop()

        # Create prompt
        prompt = f"""
        Please analyze this resume and provide constructive feedback.

        Focus on the following aspects:

        1. Content clarity and impact
        2. Skills presentation
        3. Experience descriptions
        4. Specific improvements for {
            job_role if job_role else 'general job applications'
        }
        5. Score the resume out of 10 (Strictly out of 10, no text)
            based on its effectiveness for the targeted role.

        Resume content:
        {file_content}

        Please provide your analysis in a clear, structured format
        with specific recommendations.
        """

        # Initialize Groq client
        client = Groq(api_key=groq_api_key)

        # Generate response
        with st.spinner("Analyzing your resume..."):

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that provides "
                            "detailed resume critiques."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=8192
            )

        # Display results
        st.markdown("### Analysis Results")

        output_text = response.choices[0].message.content

        if output_text:
            st.markdown(output_text)
        else:
            st.warning("No content generated.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
