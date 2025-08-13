# get_transcript_web.py
import sys
import requests
from urllib.parse import urlparse, parse_qs

# --- IMPORTANT ---
#  INSTALL
# PASTE YOUR FREE API KEY FROM SUPADATA.AI HERE
API_KEY = "YOUR_API_KEY_HERE"
# -----------------

def get_video_id(url: str) -> str:
    """Extracts the YouTube video ID from a URL."""
    if not url:
        return None
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = parse_qs(query.query)
            if 'v' in p:
                return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    return None

def get_transcript_from_web_api(video_id: str) -> str:
    """Fetches the transcript by calling the Supadata web API."""
    if not video_id:
        return "ERROR: Invalid video ID."

    if API_KEY == "YOUR_API_KEY_HERE":
        return "ERROR: Please replace 'YOUR_API_KEY_HERE' with your actual Supadata API key in the script."

    api_url = f"https://api.supadata.ai/v1/youtube/transcript?videoId={video_id}"
    headers = {
        "x-api-key": API_KEY
    }

    print(f"Fetching transcript for video ID: {video_id} using web API...")
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)

        data = response.json()

        # Check if the response contains the transcript content
        if "content" in data and data["content"]:
             # Combine the text from each segment into a single string
            full_transcript = " ".join([segment['text'] for segment in data['content']])
            return full_transcript
        else:
            return f"ERROR: Could not retrieve transcript. The API response was: {data}"

    except requests.exceptions.RequestException as e:
        return f"An error occurred while calling the API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_transcript_web.py <youtube_url>")
        sys.exit(1)

    video_url = sys.argv[1]
    video_id = get_video_id(video_url)

    if not video_id:
        print(f"ERROR: Could not extract a valid video ID from the URL: {video_url}")
        sys.exit(1)

    final_transcript = get_transcript_from_web_api(video_id)

    print("\n--- TRANSCRIPT ---")
    f = open('video_%s.txt' %(video_id),'w')
    print(final_transcript, file = f)
    f.close()
    print("--------------------")
