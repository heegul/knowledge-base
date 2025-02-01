from PyPDF2 import PdfReader
import openai
from config import OPENAI_API_KEY
from config import DEEPSEEK_API_KEY
from dotenv import load_dotenv

from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser

from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from openai import OpenAI
import os

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('CLAUDE_API_KEY')


openai.api_key = OPENAI_API_KEY

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ''
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
        return text

def split_text_into_chunks(text, max_tokens=3000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word)
        if current_length + word_length + 1 > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length + 1

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def get_summary_chatgpt(text, model="gpt-4o"):
    response = openai.ChatCompletion.create(
        model=model,
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

import time

def get_pdf_summary(text):
    chunks = split_text_into_chunks(text, max_tokens=30000)
    summaries = []
    for chunk in chunks:
        summary = get_summary_chatgpt(chunk)
        summaries.append(summary)
        time.sleep(1)  # Add delay to manage TPM limit
    combined_summary = ' '.join(summaries)
    return combined_summary

def get_pdf_summary_deepseek(text):


    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

    try:

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role":"system","content":"You are an expert in the technical domain relevant to the topic being discussed in the provided content. Don't start with saying Unfortunately, no Apploggies. Just do your best"},
                {
                        "role": "user",
                        "content": f"""Content to be summarized: {text}

                            Assume the audience is also made up of domain experts. Summarize this text to:
                            1. Deliver the main ideas
                            2. Highlight key technical insights
                            3. Elaborate on important points
                                Ensure the summary is comprehensive and detailed, capturing the essence of the discussion.
                                Make sure the amount of content is over 1 page.
                            4. Provide deep, nuanced analysis. 
                            """
                }
            ]
        )
        
        summary = response.choices[0].message.content

        return summary

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
        
    


# def get_pdf_summary_claude(text):
#     client = Anthropic(api_key=ANTHROPIC_API_KEY)
#     message = client.messages.create(
#         model= "claude-2.1",
#         max_tokens=1000,
#         messages=[
#             {
#                 "role": "user",
                                
#                 "content": 
#                         f"You are an expert in the technical domain relevant to the topic being discussed in the PDF. content of PDF: {text} ." + 
#                         "Assume the audience is also made up of domain experts. Summarize this text to deliver the main ideas, " +
#                         "highlight key technical insights, elaborate on important points, and provide deep, nuanced analysis. " +
#                         "Ensure the summary is comprehensive and detailed, capturing the essence of the discussion."

#             }
#         ]
#     )

#     summary = message.content[0].text

#     return summary

def get_pdf_summary_claude(text):
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            temperature=0,
            system = "You are an expert in the technical domain relevant to the topic being discussed in the PDF. Don't start with saying Unfortunately, no Apploggies. Just do your best",
            messages=[
                {
                    "role": "user",
                    "content": f"""Content to be summarized: {text}

                        Assume the audience is also made up of domain experts. Summarize this text to:
                        1. Deliver the main ideas
                        2. Highlight key technical insights
                        3. Elaborate on important points
                        Ensure the summary is comprehensive and detailed, capturing the essence of the discussion.
                        Make sure the amount of content is over 1 page."""
                }
            ]
        )

        summary = message.content[0].text

        return summary

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None







def get_pdf_summary_lama3(description):
    # Define the role-specific instructions
    role = 'researcher'
    role_instructions = {
        'researcher': """
        You are a distinguished researcher and subject matter expert in the field relevant to the topic being discussed. Your role is to analyze, synthesize, and communicate complex information effectively to your peers. Approach this task with the following guidelines:

        1. Expertise Assumption: Presume your audience consists of fellow domain experts who possess a deep understanding of the field. Avoid explaining basic concepts unless they are pivotal to a new insight.

        2. Critical Analysis: Employ your analytical skills to dissect the content, identifying key theories, methodologies, and findings. Evaluate the strengths and potential limitations of the presented information.

        3. Contextual Integration: Place the main ideas within the broader context of the field. Draw connections to relevant theories, recent advancements, or ongoing debates in the academic community.

        4. Precision and Clarity: Utilize domain-specific terminology accurately and precisely. Ensure that your summary is concise yet comprehensive, capturing the nuances of the original text.

        5. Implications and Future Directions: Discuss the potential implications of the main ideas for both theory and practice. Suggest possible avenues for future research or areas that warrant further investigation.

        6. Methodological Focus: If applicable, pay special attention to the research methodologies employed, assessing their appropriateness and potential impact on the findings.

        7. Interdisciplinary Perspective: Where relevant, highlight connections to other related fields or disciplines, fostering a holistic understanding of the topic.

        8. Evidence-Based Approach: Emphasize the empirical evidence or theoretical foundations supporting the main ideas. Critically evaluate the strength and validity of these supports.

        9. Scholarly Tone: Maintain a formal, academic tone throughout your summary, befitting communication among experts in the field.

        10. Innovative Insights: Don't hesitate to propose novel interpretations or hypotheses based on your expert analysis of the content, contributing to the ongoing scholarly discourse.

        Synthesize and summarize the given text, adhering to these guidelines, to deliver a comprehensive yet focused overview of the main ideas that would be valuable and insightful to your peers in the research community.
        """
    }

    # Get the role-specific instruction or use a default
    role_string = role_instructions.get(role, "Summarize this text")


    # Create the Ollama instance with llama3 model
    llm = Ollama(model="llama3:latest")

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", role_string),
        ("human", "{description}")
    ])

    # Create the chain
    chain = prompt | llm | StrOutputParser()

    try:
        # Invoke the chain
        result = chain.invoke({"description": description})
        return result.strip()
    except Exception as e:
        print(f"Error enhancing description: {e}")
        return description
    


# Function to generate a response from the fine-tuned model
def get_response_finetuned(text):


    response = openai.ChatCompletion.create(
        model='ft:gpt-3.5-turbo-1106:personal:wireless-ai:9iaNHfrS',
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
