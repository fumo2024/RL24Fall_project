import openai
import re

API_KEY = YOUR_API_KEY   # Your API key
BASE_URL = YOUR_NASE_URL  # Your base URL

class Agent(object):
    
    def __init__(self, player_id=1, board_size=15, 
                 model="deepseek-chat", 
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
        
        # print(f'DEBUG llm {self.player_id} coordinates: {coordinates}')

        return (int(coordinates[1][0]), int(coordinates[1][1]))
        
    def query_llm(self, state):
        """
        Query for next step
        [TODO] Design your only strategy 
            Including directly calling LLM or taking LLM's output to build RL based strategies
            
        """
        
        # [TODO] Parse state into token
        content = self.state_2_token(state)
        # print(f'DEBUG llm  {self.player_id} input: {content}')
        
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
        
        # print(f"DEBUG llm response: {response['choices'][0]['message']['content']}")
        
        # [TODO] Parse response into steps
        step = self.token_2_state(response.choices[0].message.content)
        
        return step