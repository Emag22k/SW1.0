import random
from db import session, GameResult

class Ship:
    def __init__(self, coordinates):
        self.coordinates = coordinates
        self.hits = set()

    def is_hit(self, shot):
        if shot in self.coordinates:
            self.hits.add(shot)
            return True
        return False

    def is_sunk(self):
        return set(self.coordinates) == self.hits


class Board:
    SIZE = 6

    def __init__(self):
        self.ships = []
        self.shots = {}

    def auto_place_ships(self):
        self.ships.clear()
        ship_sizes = [3, 2, 2, 1, 1, 1, 1]
        for size in ship_sizes:
            self.place_ship_correctly(size)

    def can_place_ship(self, ship):
        for x, y in ship.coordinates:
            if not (0 <= x < self.SIZE and 0 <= y < self.SIZE):
                return False
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if (x + dx, y + dy) in [cell for s in self.ships for cell in s.coordinates]:
                        return False
        return True

    def place_ship(self, ship):
        self.ships.append(ship)

    def place_ship_correctly(self, size):
        attempts = 100
        while attempts > 0:
            x = random.randint(0, self.SIZE - 1)
            y = random.randint(0, self.SIZE - 1)
            direction = random.choice(["H", "V"])

            if direction == "H":
                ship_cells = [(x + i, y) for i in range(size) if x + i < self.SIZE]
            else:
                ship_cells = [(x, y + i) for i in range(size) if y + i < self.SIZE]

            if len(ship_cells) == size:
                ship = Ship(ship_cells)
                if self.can_place_ship(ship):
                    self.place_ship(ship)
                    return
            attempts -= 1

        self.ships.clear()
        self.auto_place_ships()

    def receive_shot(self, x, y):
        for ship in self.ships:
            if ship.is_hit((x, y)):
                self.shots[(x, y)] = "hit" if not ship.is_sunk() else "sink"
                return True
        self.shots[(x, y)] = "miss"
        return False

    def all_ships_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)

    def display(self, show_ships=False):
        print("  " + " ".join(str(i) for i in range(self.SIZE)))
        for y in range(self.SIZE):
            row = []
            for x in range(self.SIZE):
                if (x, y) in self.shots:
                    row.append("X" if self.shots[(x, y)] == "hit" else "#" if self.shots[(x, y)] == "sink" else "o")
                elif show_ships and any((x, y) in ship.coordinates for ship in self.ships):
                    row.append("■")
                else:
                    row.append(".")
            print(f"{y} " + " ".join(row))


class Player:
    def __init__(self, name):
        self.name = name
        self.board = Board()
        self.enemy_board = Board()
        self.board.auto_place_ships()

    def make_move(self, enemy):
        raise NotImplementedError


class HumanPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.shots_made = set()

    def make_move(self, enemy):
        while True:
            try:
                coords = input(f"{self.name}, ваш ход (формат 'x y'): ").split()
                x, y = map(int, coords)
                if not (0 <= x < Board.SIZE and 0 <= y < Board.SIZE):
                    print("Координаты вне поля.")
                    continue
                if (x, y) in self.shots_made:
                    print("Вы уже стреляли в эту клетку. Попробуйте снова.")
                    continue

                self.shots_made.add((x, y))
                hit = enemy.board.receive_shot(x, y)
                result = enemy.board.shots[(x, y)]
                if result == "hit":
                    print("Попадание!")
                elif result == "sink":
                    print("Корабль потоплен!")
                else:
                    print("Мимо!")
                break
            except ValueError:
                print("Некорректный ввод.")


class BotPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.possible_shots = [(x, y) for x in range(Board.SIZE) for y in range(Board.SIZE)]
        random.shuffle(self.possible_shots)

    def make_move(self, enemy):
        print(f"{self.name} делает ход...")
        x, y = self.possible_shots.pop()
        hit = enemy.board.receive_shot(x, y)
        result = enemy.board.shots[(x, y)]
        if result == "hit":
            print("Попадание!")
        elif result == "sink":
            print("Корабль потоплен!")
        else:
            print("Мимо!")


class MediumBotPlayer(BotPlayer):
    def __init__(self, name):
        super().__init__(name)
        self.hit_cells = []

    def make_move(self, enemy):
        print(f"{self.name} делает ход...")
        if self.hit_cells:
            x, y = self.hit_cells.pop()
        else:
            x, y = self.possible_shots.pop()

        hit = enemy.board.receive_shot(x, y)
        result = enemy.board.shots[(x, y)]

        if result == "hit" or result == "sink":
            self.hit_cells.extend([(x + dx, y + dy) for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)] if
                                   0 <= x + dx < Board.SIZE and 0 <= y + dy < Board.SIZE and (
                                   x + dx, y + dy) not in enemy.board.shots])
        print("Попадание!" if result == "hit" else "Корабль потоплен!" if result == "sink" else "Мимо!")


class HardBotPlayer(MediumBotPlayer):
    def __init__(self, name):
        super().__init__(name)
        self.possible_shots = [(x, y) for x in range(Board.SIZE) for y in range(Board.SIZE)]
        random.shuffle(self.possible_shots)
        self.hit_cells = []
        self.last_hit = None

    def make_move(self, enemy):
        print(f"{self.name} делает ход...")

        if self.hit_cells:
            x, y = self.hit_cells.pop(0)
        else:
            x, y = self.possible_shots.pop()

        hit = enemy.board.receive_shot(x, y)
        result = enemy.board.shots[(x, y)]

        if result == "hit":
            self.last_hit = (x, y)
            self.hit_cells.extend([(x + dx, y + dy) for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)] if
                                   0 <= x + dx < Board.SIZE and 0 <= y + dy < Board.SIZE and
                                   (x + dx, y + dy) not in enemy.board.shots])
            print("Попадание!")
        elif result == "sink":
            self.hit_cells.clear()
            print("Корабль потоплен!")
        else:
            print("Мимо!")


class Game:
    def __init__(self, player1, player2):
        self.players = [player1, player2]

    def start(self):
        turn = 0
        while True:
            current_player = self.players[turn % 2]
            enemy = self.players[(turn + 1) % 2]
            print(f"\nХод игрока: {current_player.name}")
            enemy.board.display()
            current_player.make_move(enemy)
            if enemy.board.all_ships_sunk():
                print(f"\n{current_player.name} победил!")
                self.save_result(current_player.name, turn + 1)
                break
            turn += 1

    def save_result(self, winner, moves):
        game_result = GameResult(winner=winner, moves=moves)
        session.add(game_result)
        session.commit()
        print("Saved to DB")


if __name__ == "__main__":
    while True:
        difficulty = int(input("Выберите сложность бота (1 - Легкий, 2 - Средний, 3 - Сложный): "))
        bot_class = [BotPlayer, MediumBotPlayer, HardBotPlayer][difficulty - 1]

        player_choice = input("Выберите режим (1 - Человек vs Бот, 2 - Бот vs Бот): ")
        player1 = bot_class("Бот 1") if player_choice == "2" else HumanPlayer("Игрок")
        player2 = bot_class("Бот 2")

        game = Game(player1, player2)
        game.start()

        replay = input("Хотите сыграть ещё раз? (y/n): ").strip().lower()
        if replay != "y":
            print("Спасибо за игру! До встречи.")
            break