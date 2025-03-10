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
import requests
import json
from transformers import pipeline
from bs4 import BeautifulSoup

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('CLAUDE_API_KEY')
GROK_API_KEY = os.getenv('GROK_API_KEY')


openai.api_key = OPENAI_API_KEY

# Initialize the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


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

def get_web_summaries(query):
    """
    Fetch and summarize content from the top 5 Google search results for a given query.

    Args:
        query (str): The search query derived from the PDF text.

    Returns:
        str: Combined summaries of the top 5 web pages, or an empty string if an error occurs.
    """
    search_url = f"https://www.google.com/search?q={query}"
    try:
        html_content = requests.get(search_url).text
    except Exception as e:
        print(f"Error fetching search results: {e}")
        return ""

    soup = BeautifulSoup(html_content, "html.parser")
    # Extract URLs from organic search results (links with <h3> tags)
    urls = [a['href'] for a in soup.find_all('a') if
            a.find('h3') and a['href'].startswith('http') and 'google' not in a['href']][:5]

    summaries = []
    for url in urls:
        try:
            html = requests.get(url).text
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts and styles to reduce noise
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            summary = summarizer(text, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
            summaries.append(summary)
        except Exception as e:
            print(f"Error processing {url}: {e}")

    return "\n\n".join(summaries)

def get_summary_grok(text):
    """
    Summarize a research paper using the Grok API, enhanced with summaries from the top 5 related websites.

    Args:
        text (str): The extracted text of the research paper.

    Returns:
        str or None: The LaTeX-formatted summary if successful, None otherwise.
    """
    # API endpoint
    url = "https://api.x.ai/v1/chat/completions"

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }

    # System message content
    system_message_content = (
        "You are a domain expert in the field relevant to the provided research paper. Use this information to provide deep insights in your summary.\n\n"
        "Your task is to summarize the provided research paper, maintaining its section structure. For each section in the original paper, write a brief summary of that section in the summary, using the same section heading.\n\n"
        "The summary should be formatted in LaTeX, with each section starting with the appropriate LaTeX section command (e.g., \\section{}, \\subsection{}, etc.). If the original paper has figures, tables, or equations that are crucial to understanding the section, include references to them or provide simplified versions in the summary.\n\n"
        "The output should be a complete LaTeX document that can be compiled to produce a nicely formatted summary. The LaTeX document should start with:\n\n"
        "\\documentclass[12pt]{article}\n"
        "\\usepackage{amsmath}\n"
        "\\usepackage{amsfonts}\n"
        "\\usepackage{amssymb}\n"
        "\\usepackage[left=1in, right=1in, top=1in, bottom=1in]{geometry}\n"
        "\\usepackage{hyperref}\n"
        "\\usepackage{booktabs}\n"
        "\\begin{document}\n\n"
        "And end with:\n\n"
        "\\end{document}\n\n"
        "Include any necessary \\packages or commands in the preamble to ensure that the document compiles correctly.\n\n"
        "Please ensure that the LaTeX code is correct and that the document is self-contained."
    )

    # Extract query from the first line of text (assumed to be the title)
    query = text.split('\n', 1)[0].strip()

    # Get web summaries
    web_summaries = get_web_summaries(query)

    # Construct user message content with PDF text and web summaries
    if web_summaries:
        additional_content = f"\n\nAdditionally, here are summaries of related web content:\n\n{web_summaries}"
    else:
        additional_content = ""

    user_message_content = f"Here is the text of a research paper:\n\n{text}{additional_content}"

    # User message
    user_message = {
        "role": "user",
        "content": user_message_content
    }

    # System message
    system_message = {
        "role": "system",
        "content": system_message_content
    }

    # Payload (data to send to the API)
    payload = {
        "messages": [system_message, user_message],
        "model": "grok-2-latest",  # Assuming Grok 3 is available
        "stream": False,
        "temperature": 0
    }

    try:
        # Make the API request
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            result = response.json()
            # Extract the assistant's reply
            summary = result["choices"][0]["message"]["content"]
            return summary
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None



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

                {"role": "system", "content": """You are a distinguished technical expert and researcher with deep domain knowledge. 
                    Approach this analysis with academic rigor and provide insights that would be valuable to fellow experts.
                    Focus on technical depth while maintaining clarity and precision in your explanations."""},
                {
                    "role": "user",
                    "content": f"""Content to be summarized: {text}

                        As a domain expert writing for other experts, please provide a comprehensive analysis that:

                        1. Core Analysis:
                           - Synthesize the main theoretical frameworks and concepts
                           - Identify key methodological approaches
                           - Evaluate the significance of major findings

                        2. Technical Deep-Dive:
                           - Analyze technical implementations and architectural decisions
                           - Examine algorithmic complexity and performance considerations
                           - Highlight innovative technical solutions

                        3. Critical Evaluation:
                           - Assess the strengths and limitations of approaches
                           - Compare with existing state-of-the-art methods
                           - Identify potential areas for improvement

                        4. Contextual Integration:
                           - Place findings within broader theoretical frameworks
                           - Connect to recent developments in the field
                           - Discuss implications for future research

                        Please ensure:
                        - Maintain technical precision and academic rigor
                        - Support key points with specific evidence from the text
                        - Provide detailed analysis spanning at least one page
                        - Focus on depth rather than breadth in technical aspects
                        """
                }

            ]
        )
        
        summary = response.choices[0].message.content

        return summary

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
        
    


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
