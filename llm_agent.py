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

    def plan(self, state):
        cnt=0
        """
        give a plan(a set of recommendations) for the next step
            
        """
        accessible_positions = [(i,j) for i in range(self.board_size) for j in range(self.board_size) if state[i][j]==0]
        inaccessable_positions = [(i,j) for i in range(self.board_size) for j in range(self.board_size) if state[i][j]!=0]
        print(f"DEBUG plan: assessible_positions: {accessible_positions}")

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
                and 0 indicating empty spaces. The moves you can make are as follows: {accessible_positions}. 
                pleasw give me position inside the above set.
                The moves which are not empty are as follows: {inaccessable_positions}.
                Please do not give me the positions which are not empty.
                note the index starts at 0, So all of the components of your suggestion 
                index must be less than {self.board_size}.
                give your advise as the following format: 
                $Give your analysis of the current situation here. 
                $The give 3 positions in descending order of recommendation as follows.
                The recommended positions are:
                '1, (x, y).
                2, (x, y).
                3, (x, y).'"""
        print(f"DEBUG: LLM plan prompt: {prompt}")

        content = self.state_2_token(state)
        print(f'DEBUG llm  {self.player_id} input state: {content}')

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
        response = openai.ChatCompletion.create(
                        model=self.llm_model,
                        messages=messages,
                        temperature=0,  # Set temperature to 0 for deterministic output
                        # top_p = 0,   # gpt-4.o
                        stream=False,
                    )
        
        llm_response = response['choices'][0]['message']['content']
        print(f"DEBUG plan: LLM 响应: {llm_response}")
        while cnt<3:
            recommended_positions = re.findall(r'\d+[,.]\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', llm_response)
            recommended_positions = [(int(x), int(y)) for x, y in recommended_positions]
            print(f"DEBUG plan: LLM recommended_positions: {recommended_positions}")
            if any(pos in accessible_positions for pos in recommended_positions):
                valid_positions = [pos for pos in recommended_positions if pos in accessible_positions]
                print(f"DEBUG plan: LLM valid_positions: {valid_positions}")
                re_ask = 0
            else:
                re_ask = 1
            if re_ask == 1:
                cnt+=1
                messages.append(response.choices[0].message)
                messages.extend([
                    {"role": "user", "content": f"""
                                    The spaces(positions) {recommended_positions} you have given is non-empty, 
                                    please re-give the positions where you want to set your pices(play), 
                                    not {recommended_positions} again! do not give me the positions which are in 
                                    inassessible_positions:{inaccessable_positions}.
                                    Exactly output 3 recommended positions in accessible empty positions in the following format:
                                    '1, (x, y).
                                    2, (x, y).
                                    3, (x, y).'
                                    """}])
                response = openai.ChatCompletion.create(
                    model=self.llm_model,
                    messages=messages,
                    temperature=0,  # Set temperature to 0 for deterministic output
                    # top_p = 0,   # gpt-4.o
                    stream=False,
                )
                llm_response = response['choices'][0]['message']['content']
                print(f"My messages to LLM: {messages}")
                print(f"DEBUG: LLM 响应: {llm_response}")
            else:
                llm_response = response['choices'][0]['message']['content']
                print(f"My messages to LLM: {messages}")
                print(f"DEBUG: LLM 响应: {llm_response}")
                return valid_positions
        print("LLM have given me invalid positions for 3 times, so lead to a random position.")
        return [random.choice(accessible_positions)]

    def query_llm(self, state, moves):
        """
        Query for next step
        [TODO] Design your only strategy 
            Including directly calling LLM or taking LLM's output to build RL based strategies
            
        """
        recommended_positions = self.plan(state)
        print(f"DEBUG query_llm: recommended_positions: {recommended_positions}")
        print(f"DEBUG query_llm: move made by player{self.player_id}: {recommended_positions[0]}")
        return recommended_positions[0]