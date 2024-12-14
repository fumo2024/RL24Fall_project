import openai
import re
import json
import os
# from zhipuai import ZhipuAI

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

class Agent(object):
    
    def __init__(self, player_id=1, board_size=15, 
                 model=MODEL, 
                 api_key=API_KEY, 
                 base_url=BASE_URL):
        
        
        self.llm_model = model
        # API key and base URL
        openai.api_key = api_key
        openai.api_base = base_url
        
        self.player_id = player_id
        self.board_size = board_size
        
    def state_2_token(self, state) -> str:
        """
        Change state to tokens for LLM input.
        [TODO] Design states required and proper parsing methods for the state
        """
        
        token = ' '.join(str(cell) for row in state for cell in row)    # Simply change state into array

        return token
    
    def token_2_state(self, text):
        # 将LLM回复转换为棋盘状态/输出位置
        """
        Parse LLM output texts into move position.
        [TODO]
        1. Parse LLM text
        2. Choose the best move as strategy
        """
        
        coordinates = re.findall(r'\((\d+), (\d+)\)', text)   # Simply keep (a, b)
        
        if not coordinates:
            raise ValueError("No valid coordinates found in the text")

        print(f'DEBUG llm {self.player_id} coordinates: {coordinates}')

        return (int(coordinates[0][0]), int(coordinates[0][1]))
        
    def query_llm(self, state):
        """
        Query for next step
        [TODO] Design your only strategy 
            Including directly calling LLM or taking LLM's output to build RL based strategies
            
        """
        
        # [TODO] Parse state into token
        content = self.state_2_token(state)
        print(f'DEBUG llm  {self.player_id} input: {content}')
        
        # [Reference] Call LLM API
        # [TODO] TWO "content" part both should be modified for your purpose
        response = openai.ChatCompletion.create(
                        model=self.llm_model,
                        messages=[
                            {"role": "system", "content": f"You are a good Gomoku chess player. And later I will need you to help me play Gomoku.  I play on a {self.board_size}*{self.board_size} chessboard, I will give you an array indicating board state line by line from left to right with {self.player_id} indicating my play, {-self.player_id} indicating opponent's plays, and 0 indicating empty spaces. You can give me 3 positions in descending order of recommendation."},
                            {"role": "user", "content": content}
                        ],
                        temperature=0,  # Set temperature to 0 for deterministic output
                        # top_p = 0,   # gpt-4.o
                        stream=False,
                    )
        
        llm_response = response['choices'][0]['message']['content']
        print(f"DEBUG: LLM 响应: {llm_response}")

        # [TODO] Parse response into steps
        step = self.token_2_state(llm_response)
        print(f"DEBUG: 解析的步骤: {step}")

        return step