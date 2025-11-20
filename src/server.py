#!/usr/bin/env python3
import random
import os
import socket
import threading
import sys

# 从环境变量获取flag
FLAG = os.environ.get('GZCTF_FLAG', 'sdpcsec{gu3ss_numb3r_g4m3_[TEAM_HASH]}')

class GuessGame:
    def __init__(self):
        self.target_number = random.randint(1, 1000000)
        self.attempts_left = 30
        self.game_over = False
        
    def guess(self, number):
        """猜数字，有10%概率给出错误反馈"""
        if self.game_over:
            return "Game over! Please start a new game."
            
        if self.attempts_left <= 0:
            self.game_over = True
            return "No attempts left! Game over!"
        
        try:
            guess_num = int(number)
        except ValueError:
            return "Please enter a valid number!"
        
        if guess_num < 1 or guess_num > 1000000:
            return "Number must be between 1 and 1000000!"
        
        self.attempts_left -= 1
        
        # 10%概率给出错误反馈
        give_wrong_feedback = random.random() < 0.1
        
        if guess_num == self.target_number:
            self.game_over = True
            return f"🎉 Congratulations! You guessed it! The number was {self.target_number}.\nHere's your flag: {FLAG}"
        
        # 正常逻辑
        if guess_num < self.target_number:
            correct_feedback = "Too small!"
        else:
            correct_feedback = "Too big!"
        
        # 10%概率反转反馈
        if give_wrong_feedback:
            if "small" in correct_feedback:
                feedback = "Too big! (⚠️ Deceptive feedback)"
            else:
                feedback = "Too small! (⚠️ Deceptive feedback)"
        else:
            feedback = correct_feedback
        
        if self.attempts_left == 0:
            self.game_over = True
            return f"{feedback}\nNo attempts left! The number was {self.target_number}. Game over!"
        
        return f"{feedback} Attempts left: {self.attempts_left}"

def handle_client(conn, addr):
    """处理客户端连接"""
    game = GuessGame()
    
    banner = f"""
🎯 Number Guessing Challenge 🎯

I'm thinking of a number between 1 and 1,000,000.
You have {game.attempts_left} attempts to guess it.

⚠️  WARNING: There's a 10% chance that the feedback 
    (Too big/Too small) will be DECEPTIVE!

Enter your guess (1-1000000) or 'quit' to exit:
"""
    
    try:
        conn.sendall(banner.encode())
        
        while not game.game_over and game.attempts_left > 0:
            conn.sendall(b"\nGuess: ")
            data = conn.recv(1024).decode().strip()
            
            if not data:
                break
                
            if data.lower() in ['quit', 'exit', 'q']:
                conn.sendall(f"Game ended. The number was {game.target_number}\n".encode())
                break
            
            result = game.guess(data)
            conn.sendall(f"{result}\n".encode())
            
    except Exception as e:
        conn.sendall(f"Error: {e}\n".encode())
    finally:
        conn.close()

def main():
    """主函数 - 启动socket服务"""
    host = '0.0.0.0'
    port = 9999
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((host, port))
        server.listen(5)
        print(f"Guess Game Server started on {host}:{port}", file=sys.stderr)
        print(f"Waiting for connections...", file=sys.stderr)
        
        while True:
            conn, addr = server.accept()
            print(f"Connection from {addr}", file=sys.stderr)
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
            
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
    finally:
        server.close()

if __name__ == '__main__':
    main()
