import os
import glob
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["https://willis.engineer", "http://willis.engineer"]}})

def load_skills():
    """自動讀取 skill 資料夾內所有文字檔作為 AI 的知識庫"""
    skill_content = ""
    skill_dir = os.path.join(os.path.dirname(__file__), 'skill')
    
    if os.path.exists(skill_dir):
        txt_files = glob.glob(os.path.join(skill_dir, "*.txt"))
        for file_path in txt_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    skill_content += f.read() + "\n"
            except Exception as e:
                print(f"讀取檔案 {file_path} 失敗: {e}")
    return skill_content

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
            
        my_knowledge = load_skills()
        system_prompt = f"你現在是 Willis 的 AI 智能助理。請根據以下關於 Willis 的專屬知識庫內容來回答使用者的問題。如果問題與知識庫無關，請禮貌地引導使用者詢問關於 Willis 的專案或背景。請一律使用繁體中文回答。\n\n【Willis 專屬知識庫】:\n{my_knowledge}"
        
        # 取得環境變數中的金鑰
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return jsonify({'error': 'OpenAI API key missing in environment variables'}), 500

        # 直接發送標準 HTTP 請求給 OpenAI，避開官方 SDK 的 proxies 衝突
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code != 200:
            return jsonify({'error': response_data.get('error', {}).get('message', 'OpenAI API error')}), response.status_code
            
        ai_reply = response_data['choices'][0]['message']['content']
        return jsonify({'reply': ai_reply})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
