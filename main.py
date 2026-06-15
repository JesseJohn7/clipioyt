from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

# Root route so Railway knows app is alive
@app.route('/')
def home():
    return jsonify({'status': 'Clipio YT API is running!'})

@app.route('/youtube', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            best = None
            for f in reversed(formats):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                    best = f
                    break
            
            if not best:
                best = next((f for f in formats if f.get('url')), None)

            if not best:
                return jsonify({'error': 'No downloadable format found'}), 422

            return jsonify({
                'downloadUrl': best['url'],
                'title': info.get('title', 'video'),
                'platform': 'YouTube'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)