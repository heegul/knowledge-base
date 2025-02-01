import json

def convert_to_chat_format(input_jsonl, output_jsonl):
    """
    Convert prompt-completion pairs in JSONL format to chat format required by chat models.

    :param input_jsonl: Path to the input JSONL file with prompt-completion format.
    :param output_jsonl: Path to the output JSONL file with chat format.
    """
    with open(input_jsonl, 'r') as infile, open(output_jsonl, 'w') as outfile:
        for line in infile:
            data = json.loads(line)
            prompt = data.get('prompt', '')
            completion = data.get('completion', '')
            chat_entry = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": completion.strip()}
                ]
            }
            outfile.write(json.dumps(chat_entry) + '\n')

    print(f"Conversion complete. Output saved to {output_jsonl}")

# Example usage:
input_jsonl = r'C:\Users\dankook\source\repos\YouTube\output_data_pdf.jsonl'
output_jsonl = r'C:\Users\dankook\source\repos\YouTube\output_data_pdf_new.jsonl'
convert_to_chat_format(input_jsonl, output_jsonl)