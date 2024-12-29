from typing import Set, List
from typing_extensions import Literal

class Board(object):
    '''
    Chess Board
    A gomoku board class.
    '''
    def __init__(self, size:int=15, win_len:int=5) -> None:
        '''
        Initialize a board.
        ## Parameters\n
        size: int, optional
            Size of the gomoku board. Default is 15, which is the standard size.
            Don't passed a number greater than 15.
        win_len: int, optional
            Number of stones in a line needed to win a game. Default is 5.
        '''
        self.size = size
        self.win_len = win_len
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        # board states stored as a dict,
        # key: move as location on the board,
        # value: player as pieces type
        self.states = {}
        self.players = [1, 2]  # player1 and player2

    def init_board(self, start_player:int=0) -> None:
        '''
        Initialize the board.
        ## Parameters\n
        start_player: int, optional
            The player who plays first. Default is 0.
        '''
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.states = {}
        self.current_player = self.players[start_player]
        self.last_move = -1
        self.winner = -1

    def is_legal(self, move:tuple) -> bool:
        '''
        Judge whether a stone can be placed at given coordinate.
        ## Parameters
        move: tuple
            The coordinate of move about to be judged.
        '''
        i, j = move
        is_inside = i >= 0 and i < self.size and j >= 0 and j < self.size
        is_vacancy = self.board[i][j] == 0
        return is_inside and is_vacancy

    def play_stone(self, move:tuple) -> None:
        '''
        Play a stone at the given coordinate.
        ## Parameters\n
        move: tuple
            The coordinate of move to be played.
        '''
        if not self.is_legal(move):
            pass
            # warnings.warn(f'Cannot play a stone at {move}.', Warning, 3)
        else:
            self.board[move[0]][move[1]] = self.current_player
            self.states[move] = self.current_player
            self.current_player = (
            self.players[0] if self.current_player == self.players[1]
            else self.players[1]
        )
            self.last_move = move

    def get_state(self) -> list:
        '''
        Get the state of the board.
        ## Returns\n
        out: list
            A list of list, which represents the state of the board.
        '''
        return self.board
    
    def display_state(self, state):
        '''
        display a given state
        '''
        board_str = ""
        i_ticks = '  0 1 2 3 4 5 6 7 8 9 A B C D E'
        i_ticks = i_ticks[0:1+2*self.size]
        board_str += i_ticks + '\n'
        for i in range(self.size):
            if i < 10:
                board_str += str(i)
            else:
                board_str += chr(55 + i)
            for j in range(self.size):
                board_str += ' '
                if state[i][j] == self.players[0]:
                    board_str += 'o'
                elif state[i][j] == self.players[1]:
                    board_str += 'x'
                else:
                    board_str += '-'
                if j == self.size - 1:
                    board_str += '\n'
        return board_str
    
    def display_board(self):
        '''
        return the board.
        '''
        return self.display_state(self.board)

    def adjacent_vacancies(self) -> Set[tuple]:
        '''
        ## Returns\n
        out: Set[tuple]
        A set which contains all available moves around existed stones. \
        'Around' means the horizontal AND vertival distance between a vacancy and \
        the nearest stone is no greater than 1.
        '''
        vacancies = set()
        if self.states != {}:
            bias = range(-1, 2)
            for move in self.states.keys():
                for i in bias:
                    if move[0]-i < 0 or move[0]-i >= self.size:
                        continue
                    for j in bias:
                        if move[1]-j < 0 or move[1]-j >= self.size:
                            continue
                        vacancies.add((move[0]-i, move[1]-j))
            occupied = set(self.states.keys())
            vacancies -= occupied
        return vacancies

    def is_ended(self) -> bool:
        '''
        Judge whether the game is ended or not. The winner will be passed to `self.winner`. \
        The algorithm is not easy to understand. You can check it by traverse the `for` loop.
        ## Returns\n
        out: bool
            Return `True` if the game ended, otherwise `False`.
        '''
        if self.states == {}:
            return False
        print(self.last_move)
        loc_i, loc_j = self.last_move
        color = 1 if self.current_player == self.players[0] else -1
        sgn_i = [1, 0, 1, 1]
        sgn_j = [0, 1, 1, -1]
        for iter in range(4):
            length = 0
            prm1 = loc_i if sgn_i[iter] == 1 else loc_j
            prm2 = loc_j if sgn_j[iter] == 1 else (loc_i if sgn_j[iter] == 0 else self.size - 1 - loc_j)
            start_bias = -min(prm1, prm2) if min(prm1, prm2) < self.win_len-1 else -self.win_len+1
            end_bias = self.size - 1 - max(prm1, prm2) if max(prm1, prm2) > self.size-self.win_len else self.win_len-1
            for k in range(start_bias, end_bias+1):
                stone = 1 if self.board[loc_i + k * sgn_i[iter]][loc_j + k * sgn_j[iter]] == self.players[0] else -1 if self.board[loc_i + k * sgn_i[iter]][loc_j + k * sgn_j[iter]] == self.players[1] else 0
                if color > 0 and stone > 0 or color < 0 and stone < 0:
                    length += 1
                else:
                    length = 0
                if length == self.win_len:
                    self.winner = self.players[0] if color > 0 else self.players[1]
                    return True
        if len(self.states) == self.size ** 2:
            return True
        else:
            return False
    
    def get_current_player(self):
        '''
        Get the current player.
        ## Returns\n
        out: int
            The current player.
            None
            noninit board
        '''
        return self.current_player
    
    def get_moves(self):
        '''
        获取所有的移动。
        ## Returns\n
        out: dict
            一个包含所有移动的字典，键为"white"和"black"。
        '''
        moves = {"black": [], "white": []}
        for move, player in self.states.items():
            if player == self.players[0]:
                moves["black"].append(move)
            else:
                moves["white"].append(move)
        return moves
        

class Game(object):
    """game server"""

    def __init__(self, board, **kwargs):
        self.board = board

    def graphic(self, board, player1, player2):
        """Draw the board and show game info"""
        width = board.size
        height = board.size

        print("Player", player1, "with o".rjust(3))
        print("Player", player2, "with x".rjust(3))
        print()
        print(board.display_board())

    def start_play(self, player1, player2, start_player=0, is_shown=1, max_iter=10000):
        """start a game between two players"""
        if start_player not in (0, 1):
            raise Exception('start_player should be either 0 (player1 first) '
                            'or 1 (player2 first)')
        self.board.init_board(start_player)
        p1, p2 = self.board.players
        player1.set_player_ind(p1)
        player2.set_player_ind(p2)
        players = {p1: player1, p2: player2}
        iter = 0
        while iter < max_iter:
            if is_shown:
                print(f"{'#'*100}")
                print(f'[output] iteration: {iter + 1}')
                print(f"{'#'*100}")
                self.graphic(self.board, player1.player, player2.player)
            current_player = self.board.get_current_player()
            player_in_turn = players[current_player]
            move = player_in_turn.act(self.board)
            self.board.play_stone(move)
            end = self.board.is_ended()
            if end or iter == max_iter-1:
                if is_shown:
                    print(f"{'#'*100}")
                    if self.board.winner != -1:
                        print(f"[output] Game Over after {iter + 1} iterations! winner is {players[self.board.winner]}.")
                        print(f"{'#'*100}")
                    elif iter == max_iter-1:
                        print(f"[output] Game end after {iter + 1} iterations! Reached the maximum iteration limit.")
                        print(f"{'#'*100}")
                    else:
                        print(f"[output] Game end after {iter + 1} iterations! Tie")
                        print(f"{'#'*100}")
                    self.graphic(self.board, player1.player, player2.player)
                return self.board.winner
            iter += 1