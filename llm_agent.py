import openai
import re
import json
import os
import random
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
    
    def token_2_state(self, text, moves):
        # 将LLM回复转换为棋盘状态/输出位置
        """
        Parse LLM output texts into move position.
        [TODO]
        1. Parse LLM text
        2. Choose the best move as strategy
        """
        
        all_coordinates = re.findall(r'\((\d+),\s*(\d+)\)', text)   # Simply keep (a, b)
        recommended_positions = re.findall(r'\d+[,.]\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', text)

        # Convert to list of tuples
        all_coordinates = [(int(x), int(y)) for x, y in all_coordinates]
        recommended_positions = [(int(x), int(y)) for x, y in recommended_positions]
        all_moves = [coord for sublist in moves.values() for coord in sublist]

        print(f"DEBUG token_2_state: All coordinates: {all_coordinates}")
        print(f"DEBUG token_2_state: Recommended positions: {recommended_positions}")
        print(f"DEBUG token_2_state: Moves: {all_moves}")

        # Filter out moves that are already in the moves list
        filtered_all_coordinates = [coord for coord in all_coordinates if coord not in all_moves and coord[0] < self.board_size and coord[1] < self.board_size]
        filtered_recommended_positions = [coord for coord in recommended_positions if coord not in all_moves and coord[0] < self.board_size and coord[1] < self.board_size]

        if not filtered_recommended_positions:
            print("DEBUG token_2_state: No recommended positions found in the LLM response")
        else:
            print(f"DEBUG token_2_state: Recommended positions: {filtered_recommended_positions}")
            return filtered_recommended_positions[0]

        if not filtered_all_coordinates:
            print("DEBUG token_2_state: LLM give no valid coordinates, so chose a random one")
            empty_grid = []
            for x in range(self.board_size):
                for y in range(self.board_size):
                    if (x,y) not in all_moves:
                        empty_grid.append((x, y))
            return random.choice(empty_grid)
        else:
            print(f"DEBUG token_2_state: All coordinates: {filtered_all_coordinates}")
            return filtered_all_coordinates[0]
        
    def query_llm(self, state, moves):
        """
        Query for next step
        [TODO] Design your only strategy 
            Including directly calling LLM or taking LLM's output to build RL based strategies
            
        """
        prompt = f"""You are a excellent Gomoku chess player. And later I will need you to help me play Gomoku.
                Here are some important strategies and techniques to improve your Gomoku skills: 
                1. When you find you have already formed a line of four, you must continue to form aLine of five to win the game!
                2.Center Control:Start yourplacement in or near the center of the chessboard.
                3.Blocking:Always be aware of your opponent's moves. If they are close to forming a line of five,prioritize\
                blocking them.Usually when your opponent formsa line of three, you need to block your opponent's plays!
                4.When you find you have already formed a line of three, you are suggested to form a lineof four!
                5.You can only set a piece(play)on empty
                Now I play on a {self.board_size}*{self.board_size} chessboard, 
                I will give you an array indicating board state line by line from left to right with 
                {self.player_id} indicating my play, {-self.player_id} indicating opponent's plays, 
                and 0 indicating empty spaces. The previous moves are as follows: {moves}. 
                pleasw do not give me the same position as the previous moves.
                note the index starts at 0, So all of the components of your suggestion 
                index must be less than {self.board_size}.
                give your advise as the following format: 
                $Give your analysis of the current situation here. 
                $The give 3 positions in descending order of recommendation as follows.
                The recommended positions are:
                '1, (x, y).
                2, (x, y).
                3, (x, y).'"""
        print(f"DEBUG: LLM 输入: {prompt}")

        # [TODO] Parse state into token
        content = self.state_2_token(state)
        print(f'DEBUG llm  {self.player_id} input state: {content}')

        # [Reference] Call LLM API
        # [TODO] TWO "content" part both should be modified for your purpose
        response = openai.ChatCompletion.create(
                        model=self.llm_model,
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

        # [TODO] Parse response into steps
        step = self.token_2_state(llm_response, moves)
        print(f"DEBUG: 解析的步骤: {step}")

        return step