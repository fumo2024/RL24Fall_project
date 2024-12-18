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

class Agent(object):

    def __init__(self, player_id=1, board_size=15):
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
        for i in range(self.board_size):
            if i < 10:
                board_str += str(i)
            else:
                board_str += chr(55 + i)
            for j in range(self.board_size):
                board_str += ' '
                if state[i][j] == self.player_id:
                    board_str += 'o'
                elif state[i][j] == -self.player_id:
                    board_str += 'x'
                else:
                    board_str += ' '
                if j == self.board_size - 1:
                    board_str += '\n'
        return board_str
    
    def is_game_over(self, state):
        """
        检查游戏是否结束。
        如果有玩家赢了或者棋盘已满，则游戏结束。
        """
        def check_winner(player):
            # 检查行
            for i in range(self.board_size):
                for j in range(self.board_size - 4):
                    if all(state[i][j + k] == player for k in range(5)):
                        return True
            # 检查列
            for i in range(self.board_size - 4):
                for j in range(self.board_size):
                    if all(state[i + k][j] == player for k in range(5)):
                        return True
            # 检查主对角线
            for i in range(self.board_size - 4):
                for j in range(self.board_size - 4):
                    if all(state[i + k][j + k] == player for k in range(5)):
                        return True
            # 检查副对角线
            for i in range(4, self.board_size):
                for j in range(self.board_size - 4):
                    if all(state[i - k][j + k] == player for k in range(5)):
                        return True
            return False

        # 检查是否有玩家赢了
        if check_winner(1) or check_winner(-1):
            return True

        # 检查棋盘是否已满
        if all(state[i][j] != 0 for i in range(self.board_size) for j in range(self.board_size)):
            return True

        return False
        
    def accessible_positions(self, state):
        return [(i,j) for i in range(self.board_size) for j in range(self.board_size) if state[i][j]==0]
    
    def inaccessable_positions(self, state):
        return [(i,j) for i in range(self.board_size) for j in range(self.board_size) if state[i][j]!=0]

    def act(self, state):
        """
        Return the next move given the current state.
        """
        pass


class LLMAgent(Agent):
    
    def __init__(self, player_id=1, board_size=15, re_ask=0, loop_ask=1, 
                 model=MODEL, 
                 api_key=API_KEY, 
                 base_url=BASE_URL):
        
        super().__init__(player_id, board_size)
        self.re_ask = re_ask
        self.llm_model = model
        self.loop_ask = loop_ask
        # API key and base URL
        openai.api_key = api_key
        openai.api_base = base_url

    def encode(self, state):
        """
        Encode the content to be fed into the model.
        """
        encoded_state = []
        for row in state:
            encoded_row = ""
            count = 0
            for cell in row:
                if cell == 1:
                    if count > 0:
                        encoded_row += str(count)
                        count = 0
                    encoded_row += "w"
                elif cell == -1:
                    if count > 0:
                        encoded_row += str(count)
                        count = 0
                    encoded_row += "b"
                else:
                    count += 1
            if count > 0:
                encoded_row += str(count)
            encoded_state.append(encoded_row)
        return "\n".join(encoded_state)

    def plan_prompt1(self,state):
        return f"""You are a excellent Gomoku chess player. And later I will need you to help me play Gomoku.
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
                and 0 indicating empty spaces. The moves you can make are as follows: {self.accessible_positions(state)}. 
                pleasw give me position inside the above set.
                The moves which are not empty are as follows: {self.inaccessable_positions(state)}.
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
    
    def plan_prompt2(self,state):
        return f"""You are a excellent Gomoku chess player. And later I will need you to help me play Gomoku.
                Here are some important strategies and techniques to improve your Gomoku skills: 
                1. When you find you have already formed a line of four, you must continue to form aLine of five to win the game!
                2.Center Control:Start yourplacement in or near the center of the chessboard.
                3.Blocking:Always be aware of your opponent's moves. If they are close to forming a line of five,prioritize
                blocking them.Usually when your opponent formsa line of three, you need to block your opponent's plays!
                4.When you find you have already formed a line of three, you are suggested to form a lineof four!
                5.You can only set a piece(play)on empty
                Now I play on a {self.board_size}*{self.board_size} chessboard, 
                I will give you an array indicating board state line by line from left to right with 
                'o' indicating the current player's play, 'x' indicating opponent's plays, 
                and ' ' indicating empty spaces, there are two axis around the board indicating the position of the board, 
                it uses '0' to '9' representing 0-9, and 'A' to 'E' representing 10-14. 
                The moves you can make are as follows: {self.accessible_positions(state)}. 
                pleasw give me position inside the above set.
                The moves which are not empty are as follows: {self.inaccessable_positions(state)}.
                Please do not give me the positions which are not empty.
                note the index starts at 0, So all of the components of your suggestion 
                index must be less than {self.board_size}.
                For each move you generate, also give a short reason.
                Please first give the pieces's positions and their color on the board, then make your recommendation.
                your recommendation should first Generate 3 defensive moves that blocks the opponent's threats,  
                then generate 3 offensive moves that may form combo with your previous or future stones to gain advantage. 
                Your response should follow the format: 
                '<read pieces's positions and colors>
                <analysis of the current situation>
                Defensive moves:
                <one-sentence reason> 1. (<row>,<col>)
                <one-sentence reason> 2. (<row>,<col>)
                <one-sentence reason> 3. (<row>,<col>)
                Offensive moves:
                <one-sentence reason> 4. (<row>,<col>)
                <one-sentence reason> 5. (<row>,<col>)
                <one-sentence reason> 6. (<row>,<col>)'
                """

    def plan_prompt2_encoded(self,state):
        return f"""You are a excellent Gomoku chess player. And later I will need you to help me play Gomoku.
                Here are some important strategies and techniques to improve your Gomoku skills: 
                1. When you find you have already formed a line of four, you must continue to form aLine of five to win the game!
                2.Center Control:Start yourplacement in or near the center of the chessboard.
                3.Blocking:Always be aware of your opponent's moves. If they are close to forming a line of five,prioritize
                blocking them.Usually when your opponent formsa line of three, you need to block your opponent's plays!
                4.When you find you have already formed a line of three, you are suggested to form a lineof four!
                5.You can only set a piece(play)on empty
                Now I play on a {self.board_size}*{self.board_size} chessboard, 
                I will give you an array indicating board state later,
                in which w represent white, b represent black,
                the current player uses {'black' if self.player_id == 1 else 'white'},
                and one row in the array indicates one row in the board,
                the number between two letter indicates the empty positions between two pieces.
                The moves you can make are as follows: {self.accessible_positions(state)}. 
                pleasw give me position inside the above set.
                The moves which are not empty are as follows: {self.inaccessable_positions(state)}.
                Please do not give me the positions which are not empty.
                note the index starts at 0, So all of the components of your suggestion 
                index must be less than {self.board_size}.
                Now, Generate 3 defensive moves that blocks the opponent's threats. 
                Then, generate 3 offensive moves that may form combo with your previous or future stones to gain advantage. 
                For each move you generate, also give a short reason. 
                Your response should follow the format: 
                'Defensive moves:
                <one-sentence reason> 1. (<row>,<col>)
                <one-sentence reason> 2. (<row>,<col>)
                <one-sentence reason> 3. (<row>,<col>)
                Offensive moves:
                <one-sentence reason> 4. (<row>,<col>)
                <one-sentence reason> 5. (<row>,<col>)
                <one-sentence reason> 6. (<row>,<col>)'
                """
    def evaluate_prompt(self,state):
        return f"""You are an excellent Gomoku chess player. 
                    Later, I will need you to evaluate chessboard states.
                    You'll receive a chessboard state and need to give me a score ranging from 0 to 100, where 0 indicates a strong disadvantage for the current player and 100 indicates a strong advantage or imminent win.
                    in the board, 'o' represents the current player's stones, 'x' represents the opponent's stones, and ' ' represents empty spaces, there are two axis around the board indicating the position of the board, 
                    it uses '0' to '9' representing 0-9, and 'A' to 'E' representing 10-14. 
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
                please first give me a brief analysis of the current situation,
                telling me where exactly the pieces's position are and what's color is it, 
                your anasis should be clear, not just repeat what I have given you.
                and then give me a score ranging from 0 to 100 in the following format:
                '[Score: (#your score here)]'
                for example, if you think the score is 80, you should give me '[Score: (#80)]'"""

    def evaluate_prompt_encoded(self,state):
        return f"""You are an excellent Gomoku chess player. 
                    Later, I will need you to evaluate chessboard states.
                    I will give you an array indicating board state later,
                    in which w represent white, b represent black,
                    the current player uses {'black' if self.player_id == 1 else 'white'},
                    and one row in the array indicates one row in the board,
                    the number between two letter indicates the empty positions between two pieces.
                    Here are some important tips on how to be a good evaluator:
                    1. **Evaluate Winning Conditions**:
                    - Check if either player has achieved five consecutive stones horizontally, vertically, or diagonally. If so, assign a score of 100 for the winning player and 0 for the losing player.
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
                '[Score: (#your score here)]'
                for example, if you think the score is 80, you should give me '[Score: (#80)]'"""

    def plan(self, state):
        cnt=0
        """
        give a plan(a set of recommendations) for the next step
            
        """
        accessible_positions = self.accessible_positions(state)
        inaccessable_positions = self.inaccessable_positions(state)
        print(f"[DEBUG] function plan: assessible_positions: \n{accessible_positions}")

        prompt = self.plan_prompt2(state)
        print(f"[DEBUG]: LLM plan prompt: \n{prompt}")

        content = self.display_board(state)
        print(f'[DEBUG] llm  player {self.player_id} board state:\n{content}')
        #content = self.encode(state)
        #print(f'[DEBUG] llm  player {self.player_id} input encoded state:\n{content}')

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
        if self.re_ask == 0:
            recommended_positions = re.findall(r'\d+[,.:]\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', llm_response)
            recommended_positions =list(set([(int(x), int(y)) for x, y in recommended_positions]))
            print(f"[DEBUG] function plan: LLM recommended_positions: \n{recommended_positions}")
            if any(pos in accessible_positions for pos in recommended_positions):
                valid_positions = [pos for pos in recommended_positions if pos in accessible_positions]
                print(f"[DEBUG] function plan: LLM valid_positions: \n{valid_positions}")
                return valid_positions
            elif self.loop_ask == 1:
                while cnt<3:
                    cnt+=1
                    response = openai.ChatCompletion.create(
                        model=self.llm_model,
                        messages=messages,
                        temperature=0.2*cnt,  # Set temperature up to get various output
                        # top_p = 0,   # gpt-4.o
                        stream=False,
                    )
                    llm_response = response['choices'][0]['message']['content']
                    print(f"[DEBUG] function plan: LLM 响应 in loop_ask mode retry times{cnt}: \n{'-'*100}\n{llm_response}\n{'-'*100}\n")
                    recommended_positions = re.findall(r'\d+[,.:]\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', llm_response)
                    recommended_positions =list(set([(int(x), int(y)) for x, y in recommended_positions]))
                    print(f"[DEBUG] function plan: LLM recommended_positions in loop_ask mode retry times{cnt}: \n{recommended_positions}")
                    if any(pos in accessible_positions for pos in recommended_positions):
                        valid_positions = [pos for pos in recommended_positions if pos in accessible_positions]
                        print(f"[DEBUG] function plan: LLM valid_positions in loop_ask mode retry times{cnt}: \n{valid_positions}")
                        return valid_positions
                print("[DEBUG] plan failed in loop_ask mode: LLM have given me invalid positions for 3 times, so lead to a single random position.\n")
                return [random.choice(accessible_positions)]
            print("[DEBUG] plan failed: LLM have given me no invalid positions. with no re_ask option on, it lead to a single random position.\n")
            return [random.choice(accessible_positions)]
        re_ask = self.re_ask
        while cnt<3:
            recommended_positions = re.findall(r'\d+[,.:]\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', llm_response)
            recommended_positions =list(set([(int(x), int(y)) for x, y in recommended_positions]))
            print(f"[DEBUG] function plan re_ask: LLM recommended_positions: \n{recommended_positions}")
            if any(pos in accessible_positions for pos in recommended_positions):
                valid_positions = [pos for pos in recommended_positions if pos in accessible_positions]
                print(f"[DEBUG] function plan re_ask complete: LLM valid_positions: \n{valid_positions}")
                re_ask = 0
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
                    temperature=0.4,  # Set temperature here
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
        prompt = self.evaluate_prompt(state)
        print(f"[DEBUG] function evaluate: LLM  prompt: \n{prompt}\n")

        content = self.display_board(state)
        print(f'[DEBUG] function evaluate: LLM  evaluate player(id {self.player_id}) in state: \n{content}\n')
        #content = self.encode(state)
        #print(f'[DEBUG] function evaluate: LLM  evaluate player(id {self.player_id}) in encoded state: \n{content}\n')

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
        print(f"[DEBUG] function evaluate: LLM 响应: \n{'-'*100}\n{llm_response}\n{'-'*100}\n")

        score = re.findall(r'\(\s*\#\s*(\d+)\s*\)', llm_response)
        print(f"[DEBUG] function evaluate: LLM score find in LLM response: {score}")
        if score:
            return int(score[0])
        else:
            return 0
    
    def select(self, recommended_positions, scores):
        max_score_index = scores.index(max(scores))
        return recommended_positions[max_score_index]

    def act(self, state):
        recommended_positions = self.plan(state)
        scores = []
        for move in recommended_positions:
            scores.append(self.evaluate(self.play_stone(move, state)))
        best_move =self.select(recommended_positions,scores)
        print(f"[DEBUG] function query_llm: recommended_positions: \n{recommended_positions} with scores: {scores}\n")
        print(f"[DEBUG] function query_llm: move made by player{self.player_id}: {best_move}\n")
        return best_move
    
class AIAgent(Agent):
    def __init__(self, player_id=1, board_size=15, depth_limit=2):
        super().__init__(player_id, board_size)
        self.depth_limit = depth_limit  # 搜索深度限制

    def act(self, state):
        """
        Return the next move given the current state.
        """
        print(f"[DEBUG] AIAgent in act: Starting alpha-beta search")
        _, best_move = self.alpha_beta(state, depth=self.depth_limit, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)
        print(f"[DEBUG] AIAgent in act: Best move found: {best_move}")
        return best_move if best_move else (random.randint(0, self.board_size-1), random.randint(0, self.board_size-1))

    def alpha_beta(self, state, depth, alpha, beta, maximizing_player):
        print(f"[DEBUG] AIAgent in alpha_beta: depth={depth}, alpha={alpha}, beta={beta}, maximizing_player={maximizing_player}")
        if depth == 0 or self.is_game_over(state):
            eval_score = self.evaluate(state)
            print(f"[DEBUG] AIAgent in alpha_beta: Reached depth 0 or game over, eval_score={eval_score}")
            return eval_score, None

        legal_moves = [(x, y) for x in range(self.board_size) for y in range(self.board_size) if self.is_legal((x, y), state)]
        if not legal_moves:
            eval_score = self.evaluate(state)
            print(f"[DEBUG] AIAgent in alpha_beta: No legal moves, eval_score={eval_score}")
            return eval_score, None

        best_move = None
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                new_state = self.play_stone(move, state)
                eval, _ = self.alpha_beta(new_state, depth - 1, alpha, beta, False)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    print(f"[DEBUG] AIAgent in alpha_beta: Pruning with alpha={alpha}, beta={beta}")
                    break  # 剪枝
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_state = self.play_stone(move, state)
                eval, _ = self.alpha_beta(new_state, depth - 1, alpha, beta, True)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    print(f"[DEBUG] AIAgent in alpha_beta: Pruning with alpha={alpha}, beta={beta}")
                    break  # 剪枝
            return min_eval, best_move

    def evaluate(self, state):
        """
        Evaluate the current state of the game for the current player.
        Positive values are good for the current player, negative values are bad.
        """
        print(f"[DEBUG] AIAgent in evaluate: Evaluating state")
        scores = {self.player_id: 0, -self.player_id: 0}
        
        # Directions to check for consecutive stones (horizontal, vertical, and two diagonals)
        directions = [(1, 0), (0, 1), (1, 1), (-1, 1)]

        for x in range(self.board_size):
            for y in range(self.board_size):
                if state[x][y] != 0:
                    player = state[x][y]
                    for dx, dy in directions:
                        score = self.evaluate_position(state, x, y, dx, dy, player)
                        scores[player] += score
                        print(f"[DEBUG] AIAgent in evaluate: Evaluated position ({x}, {y}) with direction ({dx}, {dy}), score={score}")

        total_score = scores[self.player_id] - scores[-self.player_id]
        print(f"[DEBUG] AIAgent in evaluate: Total score={total_score}")
        return total_score
    
    def evaluate_position(self, state, x, y, dx, dy, player):
        """
        Evaluate the position at (x, y) in direction (dx, dy) for a given player.
        """
        count = 0  # Number of consecutive stones
        empty_at_end = [False, False]  # Whether there's an empty space at both ends

        # Check forward
        i, j = x, y
        while 0 <= i < self.board_size and 0 <= j < self.board_size and state[i][j] == player:
            count += 1
            i += dx
            j += dy
        empty_at_end[0] = 0 <= i < self.board_size and 0 <= j < self.board_size and state[i][j] == 0

        # Reset coordinates and check backward
        i, j = x - dx, y - dy
        while 0 <= i < self.board_size and 0 <= j < self.board_size and state[i][j] == player:
            count += 1
            i -= dx
            j -= dy
        empty_at_end[1] = 0 <= i < self.board_size and 0 <= j < self.board_size and state[i][j] == 0

        if count >= 5:
            return 10000 if player == self.player_id else -10000  # Five in a row wins

        if count == 4:
            if any(empty_at_end):  # Live four
                return 100 if player == self.player_id else -100
            else:  # Chong four
                return 50 if player == self.player_id else -50

        if count == 3:
            if all(empty_at_end):  # Live three
                return 10 if player == self.player_id else -10
            elif any(empty_at_end):  # Chong three
                return 5 if player == self.player_id else -5

        if count == 2:
            if all(empty_at_end):  # Live two
                return 1 if player == self.player_id else -1

        return 0  # No significant pattern found