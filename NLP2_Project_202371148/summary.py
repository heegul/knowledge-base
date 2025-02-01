import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def get_summary(text, content_type='default'):

    prompts = {
        'default': (
            "You are an expert in the technical domain relevant to the topic being discussed in the video. "
            "Assume the audience is also made up of domain experts. Summarize this text to deliver the main ideas, "
            "highlight key technical insights, elaborate on important points, and provide deep, nuanced analysis. "
            "Ensure the summary is comprehensive and detailed, capturing the essence of the discussion."
        ),
        'news': (
            "You are a journalist with expertise in breaking down complex news stories for a general audience. "
            "Summarize the following news article, highlighting the key events, important figures, and any significant implications. "
            "Ensure the summary is clear, concise, and easily understandable for the general public."
        ),
        'research': (
            "You are a researcher summarizing a scientific paper for an audience of fellow scientists. "
            "Summarize this text by outlining the main hypothesis, methodology, key findings, and the significance of the results. "
            "Ensure the summary includes enough detail to give a clear understanding of the study's contributions to its field."
        ),
        'business': (
            "You are a business analyst summarizing a business report for senior executives. "
            "Summarize the following report, highlighting key financial metrics, strategic insights, market trends, and actionable recommendations. "
            "Ensure the summary is clear, concise, and focused on the most relevant points for decision-making."
        ),
        'educational': (
            "You are an educator summarizing content for students. "
            "Summarize this text by explaining the main concepts, important details, and any practical applications. "
            "Ensure the summary is accessible and understandable for students, using clear and straightforward language."
        ),
    }

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": prompts[content_type]
            },
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()

