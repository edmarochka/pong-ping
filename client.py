from pygame import*
import socket
import json
from threading import Thread
from menu import ConnectWindow


win = ConnectWindow()
win.mainloop()
name = win.name
target_host = win.host
target_port = int(win.port)


WIDTH, HEIGHT = 800, 600
init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("pong-ping")


def connect_to_server(h, p):
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((h, p))
            
            # Очікуємо ID гравця (0 або 1)
            data = client.recv(1024).decode().strip()
            if "\n" in data:
                data = data.split("\n")[0]
            
            my_id = int(data)
            print(f"Підключено! Ваш ID: {my_id}")
            return my_id, {}, "", client
        except Exception as e:
            print(f"Очікування сервера на {h}:{p}...")
            time.sleep(1)

def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            if not data: break
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            break

font_win = font.Font(None, 50)
font_main = font.Font(None, 36)
try:
    background = transform.scale(image.load('back.png'), (WIDTH, HEIGHT))
    startbackground = transform.scale(image.load('bg_1_1.png'), (WIDTH, HEIGHT))
    endbackground = transform.scale(image.load('Starset.png'), (WIDTH, HEIGHT))
    kick = mixer.Sound('collision.wav')
    mixer.music.load("game.ogg")
    mixer.music.play(-1)
except:
    print("Помилка: Перевірте наявність файлів зображень та звуків!")


game_over = False
you_winner = None
my_id, game_state, buffer, client = connect_to_server(target_host, target_port)
Thread(target=receive, daemon=True).start()


while True:
    for e in event.get():
        if e.type == QUIT:
            exit()


    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.blit(startbackground, (0, 0))
        countdown_text = font.Font(None, 100).render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - 25, HEIGHT // 2 - 50))
        display.update()
        continue


    if "winner" in game_state and game_state["winner"] is not None:
        screen.blit(endbackground, (0, 0))
        if you_winner is None:
            you_winner = (game_state["winner"] == my_id)

        text = "Ти переміг!" if you_winner else "Пощастить наступним разом!"
        win_text = font_win.render(text, True, (255, 215, 0))
        screen.blit(win_text, win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        
        display.update()
        continue


    if game_state and 'paddles' in game_state:
        screen.blit(background, (0, 0))
        
        draw.rect(screen, (0, 255, 0), (20, game_state['paddles']['0'], 20, 100))
        draw.rect(screen, (255, 0, 255), (WIDTH - 40, game_state['paddles']['1'], 20, 100))
        

        draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)
        
        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - 25, 20))

        if game_state.get('sound_event') == 'platform_hit':
            try: kick.play() 
            except: pass

    else:
        screen.fill((0, 0, 0))
        wating_text = font_main.render("Очікування суперника...", True, (255, 255, 255))
        screen.blit(wating_text, (WIDTH // 2 - 150, HEIGHT // 2))

    display.update()
    clock.tick(60)


    keys = key.get_pressed()
    if keys[K_w]:
        client.send(b"UP")
    elif keys[K_s]:
        client.send(b"DOWN")