#!/usr/bin/env python3
import sys
import os
import math

class FactorGame:
    def __init__(self):
        self.level = 2
        self.max_number = 100
        self.initial_counter = 37
        self.counter = self.initial_counter
        self.board = list(range(1, self.max_number + 1))
        self.player_score = 0
        self.opponent_score = 0
        self.assigned = set()
        
    def get_factors(self, n):
        """获取一个数的所有真因子（不包括自身）"""
        factors = set()
        for i in range(1, int(math.sqrt(n)) + 1):
            if n % i == 0:
                factors.add(i)
                if i != 1 and i != n:  # 排除1和自身
                    factors.add(n // i)
        return factors
    
    def has_available_factors(self, n):
        """检查选择的数字是否还有未分配的真因子"""
        factors = self.get_factors(n)
        available_factors = factors - self.assigned
        return len(available_factors) > 0
    
    def choose_number(self, number):
        """玩家选择一个数字"""
        if number not in self.board:
            return False, "Number not on board"
        if number in self.assigned:
            return False, "Number already assigned"
        if not self.has_available_factors(number):
            return False, "No available factors for this number"
        
        # 玩家获得该数字的分数
        self.player_score += number
        self.assigned.add(number)
        self.counter -= 1
        
        # 对手获得所有真因子的分数
        factors = self.get_factors(number)
        for factor in factors:
            if factor in self.board and factor not in self.assigned:
                self.opponent_score += factor
                self.assigned.add(factor)
        
        return True, "Success"
    
    def get_game_state(self):
        """获取游戏状态"""
        available_numbers = [n for n in self.board if n not in self.assigned and self.has_available_factors(n)]
        return {
            'player_score': self.player_score,
            'opponent_score': self.opponent_score,
            'counter': self.counter,
            'assigned': sorted(self.assigned),
            'available_numbers': sorted(available_numbers),
            'max_number': self.max_number
        }
    
    def is_game_over(self):
        """检查游戏是否结束"""
        if self.counter <= 0:
            return True
        
        # 检查是否还有可选的数字
        available_numbers = [n for n in self.board if n not in self.assigned and self.has_available_factors(n)]
        return len(available_numbers) == 0
    
    def end_game(self):
        """结束游戏，剩余分数归对手"""
        remaining_numbers = [n for n in self.board if n not in self.assigned]
        for number in remaining_numbers:
            self.opponent_score += number
            self.assigned.add(number)

def play_game():
    game = FactorGame()
    
    print("=== Factor Selection Game - Level 2 ===")
    print(f"Board: numbers 1 to {game.max_number}")
    print(f"Counter: {game.counter} moves remaining")
    print("Rules:")
    print("- Choose a number, you get its points")
    print("- Opponent gets points from all factors of your chosen number")
    print("- You can only choose numbers with at least one unassigned factor")
    print("- Game ends when counter reaches 0 or no moves left")
    print("- Highest score wins!")
    print("=" * 50)
    sys.stdout.flush()
    
    while not game.is_game_over():
        state = game.get_game_state()
        
        print(f"\nYour score: {state['player_score']}")
        print(f"Opponent score: {state['opponent_score']}")
        print(f"Moves remaining: {state['counter']}")
        print(f"Available numbers: {state['available_numbers'][:20]}{'...' if len(state['available_numbers']) > 20 else ''}")
        sys.stdout.flush()
        
        try:
            print("\nEnter a number to choose (or 'quit' to exit):")
            sys.stdout.flush()
            choice = sys.stdin.readline().strip()
            
            if choice.lower() == 'quit':
                print("Game quit!")
                sys.stdout.flush()
                return False
                
            number = int(choice)
            success, message = game.choose_number(number)
            
            if success:
                print(f"✅ You chose {number} and gained {number} points!")
                factors = game.get_factors(number)
                opponent_gains = [f for f in factors if f in game.board and f not in game.assigned]
                if opponent_gains:
                    print(f"🤖 Opponent gained factors: {opponent_gains}")
            else:
                print(f"❌ {message}")
            sys.stdout.flush()
                
        except ValueError:
            print("❌ Please enter a valid number")
            sys.stdout.flush()
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.stdout.flush()
    
    # 游戏结束
    game.end_game()
    final_state = game.get_game_state()
    
    print("\n" + "=" * 50)
    print("🎮 GAME OVER!")
    print(f"Your final score: {final_state['player_score']}")
    print(f"Opponent final score: {final_state['opponent_score']}")
    sys.stdout.flush()
    
    # 检查是否获胜
    if final_state['player_score'] > final_state['opponent_score']:
        print("🎉 You win! Here's your flag:")
        sys.stdout.flush()
        
        # 获取flag
        flag = None
        if os.path.exists('/flag'):
            with open("/flag", "r") as f:
                flag = f.read().strip()
        elif os.environ.get('GZCTF_FLAG_BACKUP'):
            flag = os.environ.get('GZCTF_FLAG_BACKUP')
        
        if flag:
            print(f"🏁 {flag}")
        else:
            print("🏁 sdpcsec{Ez_game_fun_default}")
        sys.stdout.flush()
        return True
    else:
        print("💀 You lost! Try again to get the flag.")
        sys.stdout.flush()
        return False

def main():
    # 强制立即输出
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    print("Welcome to Factor Selection Game!")
    print("Win the game to get the flag!")
    print("=" * 50)
    sys.stdout.flush()
    
    # 直接开始游戏
    play_game()
    
    print("\nThank you for playing!")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
