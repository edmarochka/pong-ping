import socket
import json
import threading
import time
import random

WIDTH, HEIGHT = 800, 600
BALL_SPEED = 6
PADDLE_SPEED = 12
COUNTDOWN_START = 3

class GameServer:
    def __init__(self, host='localhost', port=8080):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(2)
        print(f"🎮 Сервер запущено на {host}:{port}")

        self.clients = {0: None, 1: None}
        self.connected = {0: False, 1: False}
        self.lock = threading.Lock()
        self.reset_game_state()
        self.sound_event = None

    def reset_game_state(self):
        self.paddles = {0: 250, 1: 250}
        self.scores = [0, 0]
        self.ball = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "vx": BALL_SPEED * random.choice([-1, 1]),
            "vy": BALL_SPEED * random.choice([-1, 1])
        }
        self.countdown = COUNTDOWN_START
        self.game_over = False
        self.winner = None

    def handle_client(self, pid):
        conn = self.clients[pid]
        try:
            while True:
                data = conn.recv(64).decode()
                if not data: break
                with self.lock:
                    if "UP" in data:
                        self.paddles[pid] = max(0, self.paddles[pid] - PADDLE_SPEED)
                    elif "DOWN" in data:
                        self.paddles[pid] = min(HEIGHT - 100, self.paddles[pid] + PADDLE_SPEED)
        except:
            print(f"Гравець {pid} відключився")
        finally:
            self.connected[pid] = False
            self.game_over = True

    def broadcast_state(self):
        with self.lock:
            state_dict = {
                "paddles": self.paddles,
                "ball": self.ball,
                "scores": self.scores,
                "countdown": self.countdown,
                "winner": self.winner if self.game_over else None,
                "sound_event": self.sound_event
            }
        
        packet = (json.dumps(state_dict) + "\n").encode()
        for pid in [0, 1]:
            if self.connected[pid] and self.clients[pid]:
                try:
                    self.clients[pid].sendall(packet)
                except:
                    self.connected[pid] = False

    def game_logic(self):
       
        while self.countdown > 0:
            self.broadcast_state()
            time.sleep(1)
            self.countdown -= 1
        
        
        while not self.game_over:
            with self.lock:
                self.ball['x'] += self.ball['vx']
                self.ball['y'] += self.ball['vy']

                
                if self.ball['y'] <= 10 or self.ball['y'] >= HEIGHT - 10:
                    self.ball['vy'] *= -1
                    self.sound_event = "wall_hit"

                
                if (self.ball['x'] <= 45 and self.paddles[0] <= self.ball['y'] <= self.paddles[0] + 100) or \
                   (self.ball['x'] >= WIDTH - 45 and self.paddles[1] <= self.ball['y'] <= self.paddles[1] + 100):
                    self.ball['vx'] *= -1
                    self.sound_event = 'platform_hit'

                
                if self.ball['x'] < 0:
                    self.scores[1] += 1
                    self.reset_ball()
                elif self.ball['x'] > WIDTH:
                    self.scores[0] += 1
                    self.reset_ball()

            
                if self.scores[0] >= 10:
                    self.game_over = True
                    self.winner = 0
                elif self.scores[1] >= 10:
                    self.game_over = True
                    self.winner = 1

            self.broadcast_state()
            self.sound_event = None
            time.sleep(0.016)

    def reset_ball(self):
        self.ball.update({
            "x": WIDTH // 2, "y": HEIGHT // 2,
            "vx": BALL_SPEED * random.choice([-1, 1]),
            "vy": BALL_SPEED * random.choice([-1, 1])
        })

    def run(self):
        while True:
            for pid in [0, 1]:
                conn, addr = self.server.accept()
                self.clients[pid] = conn
                self.connected[pid] = True
                conn.sendall(f"{pid}\n".encode())
                threading.Thread(target=self.handle_client, args=(pid,), daemon=True).start()
                print(f"Гравець {pid} готовий")

            self.reset_game_state()
            self.game_logic()
            
            print(f"Раунд завершено. Переможець: {self.winner}")
            time.sleep(5)
            for pid in [0, 1]:
                if self.clients[pid]:
                    self.clients[pid].close()
                    self.clients[pid] = None
                    self.connected[pid] = False

if __name__ == "__main__":
    GameServer().run()