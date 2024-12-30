from ChessBoard import Board, Game
from agent import LLMAgent, AIAgent, HumanAgent
import json
import argparse
import logging

def main():
    parser = argparse.ArgumentParser(description='Offline Game')
    parser.add_argument('--output', type=str, default=None, help='Output file name')
    parser.add_argument('--DEBUG', action='store_true', help='Debug mode')
    args = parser.parse_args()
    # logging.basicConfig(level=logging.DEBUG if args.DEBUG else logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')
    # logging.basicConfig(level=logging.DEBUG if args.DEBUG else logging.INFO,format='%(message)s')
    logging.basicConfig(filename='DEBUG.log', filemode='w',level=logging.DEBUG if args.DEBUG else logging.INFO,format='%(message)s')

    # 初始化棋盘
    board = Board(size=15)
    game = Game(board)
    
    # 初始化对弈双方bot
    bot1 = LLMAgent(board_size=15)
    bot2 = AIAgent(board_size=15)

    # 开始游戏
    game.start_play(bot1, bot2, start_player=0, is_shown=1, max_iter=25)

    # 获取游戏记录
    moves = game.board.get_moves()

    if args.output is not None:
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