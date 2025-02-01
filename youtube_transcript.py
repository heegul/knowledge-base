from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import os

def write_transcript_to_html(video_id):
    try:
        # Fetching the transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

        # Format the transcript into plain text
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript_list)

        # Creating HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Transcript for Video {video_id}</title>
        </head>
        <body>
            <h1>Transcript for Video: {video_id}</h1>
            <pre>{transcript_text}</pre>
        </body>
        </html>
        """

        # Writing to HTML file
        filename = f"transcript_{video_id}.html"
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(html_content)
        print(f"Transcript has been written to {filename}")

    except Exception as e:
        print("An error occurred while fetching the transcript:", str(e))

# Example usage
video_id = 'dWZyXRBYQ-Y&t=380s'
write_transcript_to_html(video_id)