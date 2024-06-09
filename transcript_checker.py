import argparse
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import json

def get_youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript])
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def check_content_with_ollama(transcript_text):
    url = "http://localhost:11434/api/generate"  # Replace with your Ollama server URL
    headers = {
        "Content-Type": "application/json",
    }
    prompt = """
You are an AI designed to evaluate text for appropriateness for a 10-year-old child. Your task is to scan the following input text and determine if it contains any curse words, sexually suggestive language, or other inappropriate content.

1. If the text contains inappropriate content for a 10 year old, curse words, or sexually suggestive language respond with the JSON object: {"result": false}.
2. Otherwise, respond with the JSON object: {"result": true}.

Respond only with the JSON object and no other output text.

Text to evaluate:
"""
    prompt = prompt + transcript_text

    payload = {
        "prompt": prompt,
        "model": "llama3:8b-instruct-q4_0",
        "format": "json",
        "stream": False,
        "options": {
            "num_ctx": 4096
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        #print("response.text.response:", response.text.response)  # Print the raw response for debugging
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking content: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return None

def split_text_into_chunks(text, max_length):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def main():
    #video_id = "7__r4FVj-EI"  # Replace with the actual video ID
    #video_id = "IxGvm6btP1A"  # Not approriate
    parser = argparse.ArgumentParser(description="Check YouTube transcript for inappropriate content.")
    parser.add_argument('video_id', type=str, help='The YouTube video ID')
    args = parser.parse_args()

    video_id = args.video_id
    transcript_text = get_youtube_transcript(video_id)
    if transcript_text:
        #print("Transcript fetched successfully. ", transcript_text)
        chunks = split_text_into_chunks(transcript_text, 2000)
        all_chunks_appropriate = True

        for i, chunk in enumerate(chunks, start=1):
            print(f"Checking chunk {i}/{len(chunks)}... - len: ", len(chunk))
            result = check_content_with_ollama(chunk)
            if result:
                try:
                    response_data = json.loads(result.get('response', '{}'))
                    print("Raw result response:", response_data)  # Print the raw result for debugging
                    if response_data.get('result') != True:
                        all_chunks_appropriate = False
                        break
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    all_chunks_appropriate = False
                    break
            else:
                print("Failed to check content with Ollama.")
                all_chunks_appropriate = False
                break

        if all_chunks_appropriate:
            print("The transcript is appropriate for a 10-year-old.")
        else:
            print("The transcript contains inappropriate content.")
    else:
        print("Failed to fetch the transcript.")

if __name__ == "__main__":
    main()
