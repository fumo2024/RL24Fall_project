from ChessBoard import ChessBoard
from llm_agent import Agent

def start_game(board, players):
    
    curr_player = 0     # players[0]先手
    
    iterations = 5      # 此处限制最大回合数，仅作演示，实际对局中游戏分出胜负则终局
    
    while iterations > 0:
        
        print(f'iteration: {5 - iterations + 1}')
        
        # 调用agent决策落子位置
        state = board.get_state()
        move = players[curr_player].query_llm(state)
        
        # 更新棋盘状态
        board.play_stone(move)
        board.display_board()
        curr_player = 1 - curr_player
        
        iterations -= 1
        
        


def main():
    
    # 初始化棋盘
    board = ChessBoard(size=9)
    
    # 初始化对弈双方bot
    bot1 = Agent(player_id=1, board_size=9)
    bot2 = Agent(player_id=-1, board_size=9)
    bots = [bot1, bot2]
    
    # 开始游戏
    start_game(board, bots)
    
    
if __name__ == '__main__':
    main()  