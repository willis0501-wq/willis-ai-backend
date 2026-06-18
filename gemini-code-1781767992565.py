import os
import glob
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
# 允許你的 WordPress 網域跨網域呼叫 API
CORS(app, resources={r"/api/*": {"origins": ["https://willis.engineer", "http://willis.engineer"]}})

# 初始化 OpenAI 客户端（Railway 後台設定環境變數 OPENAI_API_KEY）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_skills():
    """自動讀取 skill 資料夾內所有文字檔作為 AI 的知識庫"""
    skill_content = ""
    skill_dir = os.path.join(os.path.dirname(__file__), 'skill')
    
    if os.path.exists(skill_dir):
        # 讀取 skill 資料夾下所有的 .txt 檔案
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
            
        # 載入你寫的專案內容或簡歷
        my_knowledge = load_skills()
        
        # 設定給 AI 的 System Prompt（大腦人設）
        system_prompt = f"你現在是 Willis 的 AI 智能助理。請根據以下關於 Willis 的專屬知識庫內容來回答使用者的問題。如果問題與知識庫無關，請禮貌地引導使用者詢問關於 Willis 的專案或背景。請一律使用繁體中文回答。\n\n【Willis 專屬知識庫】:\n{my_knowledge}"
        
        # 呼叫 OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 使用高CP值的模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )
        
        ai_reply = response.choices[0].message.content
        return jsonify({'reply': ai_reply})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Railway 會自動分配 PORT，預設 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)