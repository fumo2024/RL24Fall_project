import openai
import re
import json
import os
import random

# 定义文件名
apikey_file = 'apikey.json'

# 检查文件是否存在
if not os.path.exists(apikey_file):
    # 提示用户创建文件并提供示例内容
    print(f"文件 {apikey_file} 不存在，请创建该文件并添加以下内容：")
    example_content = [
        {
            "API_KEY": "YOUR_API_KEY",
            "BASE_URL": "YOUR_BASE_URL",
            "MODEL": "MODEL_NAME"
        }
    ]
    print(json.dumps(example_content, indent=4))
    # 退出程序
    exit(1)

# 从 apikey.json 文件中读取 API_KEY 和 BASE_URL
with open(apikey_file, 'r') as f:
    data = json.load(f)
    api_info = data[0]  # 假设只需要第一个对象的信息

API_KEY = api_info['API_KEY']   # Your API key
BASE_URL = api_info['BASE_URL']  # Your base URL
MODEL = api_info['MODEL']        # Your model name

def main():
    prompt = f"You are an excellent Gomoku chess player. Later, \
            I will need you to help me evaluate one board state. \
            Here are detailed instructions on how to score a Gomoku board:\
            1.**Evaluate Winning Conditions**: \
            - Check if either player has achieved five consecutive stones horizontally, vertically, or diagonally.\
             If so, the game is over, and that player wins. Assign a high positive score (+∞) for the winning player \
            and a high negative score (-∞) for the losing player. \
            2.**Assess Potential Winning Lines**:\
            - Identify any potential lines where a player can achieve five consecutive stones in the next few moves. \
                Score these lines based on their proximity to completion. For example:\
            - Four consecutive stones with an open end (4-in-a-row): Very high positive score for the player.\
            - Three consecutive stones with two open ends (3-in-a-row): High positive score for the player.\
            - Two consecutive stones with two open ends (2-in-a-row): Moderate positive score for the player.\
            3. **Consider Defensive Moves**:
            - Evaluate the opponent's potential to win in the next move. \
                Prioritize blocking any immediate threats by assigning higher scores \
                to positions that prevent the opponent from achieving a winning line. \
            4. **Balance Offensive and Defensive Strategies**:\
            - Combine offensive opportunities with defensive necessities. \
            A balanced evaluation should favor moves that both advance your position and \
            block the opponent's progress.\
            5. **Evaluate Board Control**:\
             - Assess the overall control of the board. Positions that offer more flexibility\
            and future opportunities should be scored higher. Central positions often provide better control over the board.\
            6. **Penalize Vulnerable Positions**:\
            - Positions that leave the player vulnerable to being blocked or that limit future moves \
            should receive lower scores.\
            7. **Use Heuristics for Complex Situations**:\
             - In complex situations where direct scoring is difficult, \
            use heuristic rules based on experience and patterns observed in expert games.\
            8. **Provide a Numerical Score**:\
            - Summarize the evaluation into a numerical score. \
            Positive values indicate an advantage for one player, \
            while negative values indicate an advantage for the other.\
            The magnitude of the score reflects the strength of the advantage.\
            Please evaluate the given board state using these guidelines and \
            provide a detailed explanation of your scoring process. "
    print(f"DEBUG: LLM 输入: {prompt}")
    content = ""

    openai.api_key = API_KEY
    openai.api_base = BASE_URL
    response = openai.ChatCompletion.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": content}
                        ],
                        temperature=0,  # Set temperature to 0 for deterministic output
                        # top_p = 0,   # gpt-4.o
                        stream=False,
                    )
    llm_response = response['choices'][0]['message']['content']
    print(f"DEBUG: LLM 响应: {llm_response}")
    
if __name__ == '__main__':
    main()  