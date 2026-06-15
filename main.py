from flask import Flask, request, jsonify
import yt_dlp
import os
import tempfile

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'status': 'Clipio YT API is running!'})

def get_cookies_file():
    """Write cookies from env variable to a temp file"""
    cookies_content = os.environ.get('YT_COOKIES', '')
    if not cookies_content:
        return None
    
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp.write(cookies_content)
    tmp.close()
    return tmp.name

@app.route('/youtube', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400

    cookies_file = get_cookies_file()

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }

    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file

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
    
    finally:
        # Clean up temp cookies file
        if cookies_file and os.path.exists(cookies_file):
            os.unlink(cookies_file)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)