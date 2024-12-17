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

class LLMAgent(object):
    
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

    def is_legal(self, move, state):
        """
        Judge whether a stone can be placed at given coordinate.
        """
        i, j = move
        is_inside = i >= 0 and i < self.board_size and j >= 0 and j < self.board_size
        is_vacancy = state[i][j] == 0
        return is_inside and is_vacancy

    def play_stone(self, move, state):
        """
        Play a stone at the given coordinate.
        """
        if not self.is_legal(move, state):
            pass
        else:
            state_ = [row.copy() for row in state]
            state_[move[0]][move[1]] = self.player_id
        return state_  

    def display_board(self, state):
        '''
        Print all placed stone.
        '''
        board_str = ""
        i_ticks = '  0 1 2 3 4 5 6 7 8 9 A B C D E'
        i_ticks = i_ticks[0:1+2*self.board_size]
        board_str += i_ticks + '\n'
        for j in range(self.board_size):
            if j < 10:
                board_str += str(j)
            else:
                board_str += chr(55 + j)
            for i in range(self.board_size):
                board_str += ' '
                if state[i][j] == self.player_id:
                    board_str += 'o'
                elif state[i][j] == -self.player_id:
                    board_str += 'x'
                else:
                    board_str += ' '
                if i == self.board_size - 1:
                    board_str += '\n'
        return board_str

    def plan(self, state):
        cnt=0
        """
        give a plan(a set of recommendations) for the next step
            
        """
        accessible_positions = [(i,j) for i in range(self.board_size) for j in range(self.board_size) if state[i][j]==0]
        inaccessable_positions = [(i,j) for i in range(self.board_size) for j in range(self.board_size) if state[i][j]!=0]
        print(f"[DEBUG] function plan: assessible_positions: \n{accessible_positions}")

        prompt = f"""You are a excellent Gomoku chess player. And later I will need you to help me play Gomoku.
                Here are some important strategies and techniques to improve your Gomoku skills: 
                1. When you find you have already formed a line of four, you must continue to form aLine of five to win the game!
                2.Center Control:Start yourplacement in or near the center of the chessboard.
                3.Blocking:Always be aware of your opponent's moves. If they are close to forming a line of five,prioritize
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
                $The give 5 positions in descending order of recommendation as follows, 
                after making any recommendation, give a reason to convice me that it is good.
                The recommended positions are:
                '1. (x, y).
                2. (x, y).
                3. (x, y).
                4. (x, y).
                5. (x, y).'"""
        print(f"[DEBUG]: LLM plan prompt: \n{prompt}")

        content = self.display_board(state)
        print(f'[DEBUG] llm  player {self.player_id} input state:\n {content}')

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
        print(f"[DEBUG] function plan: LLM 响应: \n{'-'*100}\n{llm_response}\n{'-'*100}\n")
        while cnt<3:
            recommended_positions = re.findall(r'\d+[,.:]\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', llm_response)
            recommended_positions = [(int(x), int(y)) for x, y in recommended_positions]
            print(f"[DEBUG] function plan re_ask: LLM recommended_positions: \n{recommended_positions}")
            if any(pos in accessible_positions for pos in recommended_positions):
                valid_positions = [pos for pos in recommended_positions if pos in accessible_positions]
                print(f"[DEBUG] function plan re_ask complete: LLM valid_positions: \n{valid_positions}")
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
                                    Exactly output 5 recommended positions in accessible empty positions in the following format:
                                    '1. (x, y).
                                    2. (x, y).
                                    3. (x, y).
                                    4. (x, y).
                                    5. (x, y).' 
                                    """}])
                response = openai.ChatCompletion.create(
                    model=self.llm_model,
                    messages=messages,
                    temperature=0.4,  # Set temperature to 0 for deterministic output
                    # top_p = 0,   # gpt-4.o
                    stream=False,
                )
                llm_response = response['choices'][0]['message']['content']
                print(f"[DEBUG] function plan: input messages in re_ask(retry times {cnt}): \n{'-'*100}\n{messages}\n{'-'*100}\n")
                print(f"[DEBUG] function plan: LLM 响应 in re_ask(retry times {cnt}): \n{'-'*100}\n{llm_response}\n{'-'*100}\n")
            else:
                return valid_positions
        print("[DEBUG] plan failed: LLM have given me invalid positions for 3 times, so lead to a single random position.\n")
        return [random.choice(accessible_positions)]

    def evaluate(self, state):
        """
        Evaluate the state and return the best move.
        """
        prompt = f"""You are an excellent Gomoku chess player. 
                    Later, I will need you to evaluate chessboard states.
                    You'll receive a chessboard state and need to give me a score ranging from 0 to 100, where 0 indicates a strong disadvantage for the current player and 100 indicates a strong advantage or imminent win.
                    in the board, o represents the current player's stones, x represents the opponent's stones, and 0 represents empty spaces.
                    Here are some important tips on how to be a good evaluator:
                    1. **Evaluate Winning Conditions**:
                    - Check if either player has achieved five consecutive stones horizontally, vertically, or diagonally. If so, assign a score of 100 for the winning player and 0 for the losing player.(5o for 100, 5x for 0, note this is the highest priority)
                    2. **Assess Potential Winning Lines**:
                   - Identify any potential lines where a player can achieve five consecutive stones in the next few moves. Score these lines based on their proximity to completion:
                     - Four consecutive stones with an open end (4-in-a-row): Score 90-95.
                     - Three consecutive stones with two open ends (3-in-a-row): Score 70-85.
                   - Two consecutive stones with two open ends (2-in-a-row): Score 50-65.
                    3. **Consider Defensive Moves**:
                   - Evaluate the opponent's potential to win in the next move. Prioritize blocking any immediate threats by assigning higher scores to positions that prevent the opponent from achieving a winning line. A successful block should increase the score by 10-20 points.
                    4. **Balance Offensive and Defensive Strategies**:
                     - Combine offensive opportunities with defensive necessities. Favor moves that both advance your position and block the opponent's progress. Balance these factors to adjust the score accordingly.
                    5. **Evaluate Board Control**:
                      - Assess the overall control of the board. Positions that offer more flexibility and future opportunities should receive higher scores. Central positions often provide better control over the board and can add 5-10 points to the score.
                    6. **Penalize Vulnerable Positions**:
                       - Positions that leave the player vulnerable to being blocked or that limit future moves should receive lower scores. Subtract 5-15 points for such positions.
                    7. **Use Heuristics for Complex Situations**:
                       - In complex situations where direct scoring is difficult, use heuristic rules based on experience and patterns observed in expert games. Adjust the score based on these heuristics.
                    8. **Provide Contextual Explanation**:
                       - Along with the numerical score, provide a brief explanation of key factors influencing the score. Highlight critical lines, potential threats, and strategic advantages.
                Please evaluate the given chessboard state using these guidelines and provide both a score and a detailed explanation of your evaluation process.
                please first give me a brief analysis of the current situation.
                and then give me a score ranging from 0 to 100 in the following format:
                '[Score: (your score here)]'
                for example, if you think the score is 80, you should give me '[Score: (80)]'"""
        print(f"[DEBUG] function evaluate: LLM  prompt: \n{prompt}\n")

        content = self.display_board(state)
        print(f'[DEBUG] function evaluate: LLM  evaluate player(id {self.player_id}) in state: \n{content}\n')

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
        response = openai.ChatCompletion.create(
                        model=self.llm_model,
                        messages=messages,
                        temperature=0.3,  # Set temperature to 0 for deterministic output
                        # top_p = 0,   # gpt-4.o
                        stream=False,
                    )
        
        llm_response = response['choices'][0]['message']['content']
        print(f"[DEBUG] function evaluate: LLM 响应: \n{'-'*100}\n{llm_response}\n{'-'*100}\n")

        score = re.findall(r'\(\s*(\d+)\s*\)', llm_response)
        print(f"[DEBUG] function evaluate: LLM score find in LLM response: {score}")
        return int(score[0])
    
    def select(self, recommended_positions, scores):
        max_score_index = scores.index(max(scores))
        return recommended_positions[max_score_index]

    def query_llm(self, state):
        recommended_positions = self.plan(state)
        scores = []
        for move in recommended_positions:
            scores.append(self.evaluate(self.play_stone(move, state)))
        best_move =self.select(recommended_positions,scores)
        print(f"[DEBUG] function query_llm: recommended_positions: \n{recommended_positions} with scores: {scores}\n")
        print(f"[DEBUG] function query_llm: move made by player{self.player_id}: {best_move}\n")
        return best_move