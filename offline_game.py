from ChessBoard import ChessBoard
from llm_agent import LLMAgent
import json
import argparse

def start_game(board, players, max_iter=5):
    moves = {"black": [], "white": []}
    curr_player = 0     # players[0]先手
    
    iterations = max_iter     # 此处限制最大回合数，仅作演示，实际对局中游戏分出胜负则终局
    
    while iterations > 0:
        
        print(f"{'#'*100}")
        print(f'[output] iteration: {max_iter - iterations + 1}')
        print(f"{'#'*100}")

        # 调用agent决策落子位置
        state = board.get_state()
        move = players[curr_player].query_llm(state)

        # 记录移动
        if curr_player == 1:
            moves["white"].append(move)
        else:
            moves["black"].append(move)
        
        # 更新棋盘状态
        board.play_stone(move)
        board.display_board()
        curr_player = 1 - curr_player
        
        iterations -= 1

        if board.is_ended():
            winner = "black" if curr_player == 1 else "white"
            print(f"{'#'*100}")
            print(f"[output] Game Over after {max_iter - iterations + 1} iterations! winner is {winner}.")
            print(f"{'#'*100}")
            break
        
    return moves
        


def main():
    parser = argparse.ArgumentParser(description='Offline Game')
    parser.add_argument('--output', type=str, default='game_moves.json', help='Output file name')
    args = parser.parse_args()
    
    # 初始化棋盘
    board = ChessBoard(size=15)
    
    # 初始化对弈双方bot
    bot1 = LLMAgent(player_id=1, board_size=15)
    bot2 = LLMAgent(player_id=-1, board_size=15)
    bots = [bot1, bot2]
    
    # 开始游戏
    moves = start_game(board, bots, max_iter=50)

    # 自定义函数来格式化列表
    def custom_format(obj):
        if isinstance(obj, list):
            formatted_items = []
            for item in obj:
                if isinstance(item, list):
                    formatted_items.append(' ' * 6 + '[' + ', '.join(map(str, item)) + ']')
                else:
                    formatted_items.append(' ' * 4 + json.dumps(item))
            return '[\n  ' + ',\n  '.join(formatted_items) + '\n    ]'
        return json.dumps(obj, indent=4)
    
    # 保存移动记录到JSON文件
    with open(args.output, 'w') as f:
        f.write('{\n')
        items = list(moves.items())
        for i, (key, value) in enumerate(items):
            f.write(f'    "{key}": {custom_format(value)}')
            if i < len(items) - 1:
                f.write(',\n')
            else:
                f.write('\n')
        f.write('}\n')
    
    
if __name__ == '__main__':
    main()  