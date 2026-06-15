from flask import Flask, request, jsonify
import os
import re
import urllib.request
import json

app = Flask(__name__)

# List of public Invidious instances - we try each one
INVIDIOUS_INSTANCES = [
    'https://inv.nadeko.net',
    'https://invidious.privacydev.net',
    'https://vid.puffyan.us',
    'https://invidious.nerdvpn.de',
    'https://invidious.io.lol',
]

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/')
def home():
    return jsonify({'status': 'Clipio YT API is running!'})

@app.route('/youtube', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL required'}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Could not extract video ID'}), 400

    print(f"Trying video ID: {video_id}", flush=True)

    # Try each Invidious instance until one works
    for instance in INVIDIOUS_INSTANCES:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            print(f"Trying instance: {instance}", flush=True)

            req = urllib.request.Request(
                api_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                video_data = json.loads(response.read().decode())

            title = video_data.get('title', 'video')
            formats = video_data.get('adaptiveFormats', []) + video_data.get('formatStreams', [])

            if not formats:
                print(f"No formats from {instance}", flush=True)
                continue

            # Pick best mp4 with video
            mp4_formats = [
                f for f in formats
                if 'video/mp4' in f.get('type', '') and f.get('url')
            ]

            # Sort by quality
            mp4_formats.sort(
                key=lambda f: int(f.get('qualityLabel', '0p').replace('p', '') or 0),
                reverse=True
            )

            # Fallback to formatStreams (combined video+audio)
            if not mp4_formats:
                mp4_formats = [
                    f for f in video_data.get('formatStreams', [])
                    if f.get('url')
                ]

            if not mp4_formats:
                print(f"No mp4 formats from {instance}", flush=True)
                continue

            best = mp4_formats[0]
            print(f"Success from {instance}!", flush=True)

            return jsonify({
                'downloadUrl': best['url'],
                'title': title,
                'platform': 'YouTube'
            })

        except Exception as e:
            print(f"Instance {instance} failed: {e}", flush=True)
            continue

    return jsonify({'error': 'Could not fetch video. Try again later.'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)