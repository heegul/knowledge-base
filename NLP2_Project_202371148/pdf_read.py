from PyPDF2 import PdfReader
import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ''
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
        return text

def get_pdf_summary(text):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert in the technical domain relevant to the topic being discussed in the PDF. "
                    "Assume the audience is also made up of domain experts. Summarize this text to deliver the main ideas, "
                    "highlight key technical insights, elaborate on important points, and provide deep, nuanced analysis. "
                    "Ensure the summary is comprehensive and detailed, capturing the essence of the discussion."
                )
            },
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()
