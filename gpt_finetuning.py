import openai
from config import OPENAI_API_KEY
import json

# Set your OpenAI API key
openai.api_key = OPENAI_API_KEY

# Define your dataset file path
dataset_file_path = r'C:\Users\dankook\source\repos\YouTube\output_data_pdf.jsonl'


def upload():
    # Upload the file
    upload_response = openai.File.create(
        file=open(dataset_file_path),
        purpose='fine-tune'
    )

    file_id = upload_response['id']
    print("File uploaded successfully. File ID:", file_id)
    return file_id

def main():
    file_id = 'file-BpiqrAPMAYLHjFFHUyGbnrCk'
    # Wait for user input to proceed
    input("Press any key to proceed to fine-tuning...")

    try:

        # Fine-tune the model
        response = openai.FineTune.create(
            training_file=file_id,
            model="gpt-4o-2024-05-13",
            n_epochs=3,
            batch_size=1
        )
        print("Fine-tuning job created:", response)

    except openai.error.OpenAIError as e:
        print(f"An error occurred: {e}")



if __name__ == "__main__":
    main()