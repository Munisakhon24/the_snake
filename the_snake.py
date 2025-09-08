from random import randint

import pygame

# 
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 490
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

#  Направления движения 

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

#  Цвета 

BOARD_BACKGROUND_COLOR = (0, 0, 0)      # фон (чёрный)
BORDER_COLOR = (93, 216, 228)           # цвет рамки клетки
APPLE_COLOR = (255, 0, 0)               # красный
SNAKE_COLOR = (0, 255, 0)               # зелёный

#  Скорость игры 

SPEED = 10  # «шагов» (кадров) в секунду p.s мне показалось что 20 слишком быстро)


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
pygame.display.set_caption('Змейка')
clock = pygame.time.Clock()


#  ИГРОВЫЕ КЛАССЫ 

class GameObject:
    """Базовый игровой объект: хранит позицию и цвет, умеет отрисовываться."""

    def __init__(self, position=None, body_color=(255, 255, 255)):
        """
        position: координаты (x, y) верхнего левого угла в пикселях;
                  по умолчанию — центр поля, кратно GRID_SIZE.
        body_color: RGB-цвет объекта.
        """
        if position is None:
            cx = (SCREEN_WIDTH // 2 // GRID_SIZE) * GRID_SIZE
            cy = (SCREEN_HEIGHT // 2 // GRID_SIZE) * GRID_SIZE
            position = (cx, cy)
        self.position = position
        self.body_color = body_color

    def draw(self):
        """Абстрактный метод: конкретная отрисовка в наследниках."""
        # В тестах важно только наличие метода; реализация — в потомках.
        pass


class Apple(GameObject):
    """Яблоко: квадрат 1×1 клетки, появляется в случайной свободной клетке."""

    def __init__(self):
        super().__init__(body_color=APPLE_COLOR)
        self.randomize_position()

    def randomize_position(self, forbidden=None):
        """
        Ставит яблоко в случайную клетку, не попадая на занятые позиции.
        forbidden: коллекция координат (x, y), куда ставить нельзя (например, сегменты змейки).
        """
        forbidden = set(forbidden or [])
        while True:
            x = randint(0, GRID_WIDTH - 1) * GRID_SIZE
            y = randint(0, GRID_HEIGHT - 1) * GRID_SIZE
            if (x, y) not in forbidden:
                self.position = (x, y)
                return

    def draw(self):
        """Отрисовывает яблоко на экране."""
        rect = pygame.Rect(self.position, (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, self.body_color, rect)
        pygame.draw.rect(screen, BORDER_COLOR, rect, 1)


class Snake(GameObject):
    """
    Змейка: список сегментов (positions), голова — первый элемент.
    Хранит текущее и следующее направления, длину и последний удалённый сегмент.
    """

    def __init__(self, body_color=SNAKE_COLOR):
        super().__init__(body_color=body_color)
        self.length = 1
        self.positions = [self.position]   # сегменты: голова — нулевой элемент
        self.direction = RIGHT             # стартовое направление
        self.next_direction = None         # буфер направления (ставится в handle_keys)
        self.last = None                   # последний удалённый сегмент (для «затирания следа»)

    def get_head_position(self):
        """Возвращает координаты головы (первого сегмента)."""
        return self.positions[0]

    def update_direction(self):
        """Применяет следующее направление; разворот на 180° запрещён."""
        if self.next_direction:
            ndx, ndy = self.next_direction
            cdx, cdy = self.direction
            # запрет разворота: противоположные вектора дают сумму по осям == 0
            if not (ndx + cdx == 0 and ndy + cdy == 0):
                self.direction = self.next_direction
            self.next_direction = None

    def move(self):
        """
        Двигает змейку на одну клетку:
        - вставляет новую голову (с «телепортом» через края),
        - если не выросли — удаляет хвост и запоминает его в self.last.
        """
        head_x, head_y = self.get_head_position()
        dx, dy = self.direction

        new_x = (head_x + dx * GRID_SIZE) % SCREEN_WIDTH
        new_y = (head_y + dy * GRID_SIZE) % SCREEN_HEIGHT
        new_head = (new_x, new_y)

        # новая голова
        self.positions.insert(0, new_head)

        # если не росли — удаляем хвост
        if len(self.positions) > self.length:
            self.last = self.positions.pop()
        else:
            self.last = None

        # синхронизируем базовую позицию в GameObject
        self.position = new_head

    def draw(self):
        """Рисует все сегменты и затирает последнюю убранную клетку цветом фона."""
        # тело (кроме головы)
        for position in self.positions[1:]:
            rect = pygame.Rect(position, (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, self.body_color, rect)
            pygame.draw.rect(screen, BORDER_COLOR, rect, 1)

        # голова
        head_rect = pygame.Rect(self.positions[0], (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, self.body_color, head_rect)
        pygame.draw.rect(screen, BORDER_COLOR, head_rect, 1)

        # затирание хвоста
        if self.last:
            last_rect = pygame.Rect(self.last, (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, last_rect)

    def reset(self):
        """Сбрасывает змейку к исходному состоянию (центр, длина=1, вправо)."""
        cx = (SCREEN_WIDTH // 2 // GRID_SIZE) * GRID_SIZE
        cy = (SCREEN_HEIGHT // 2 // GRID_SIZE) * GRID_SIZE
        self.position = (cx, cy)
        self.length = 1
        self.positions = [self.position]
        self.direction = RIGHT
        self.next_direction = None
        self.last = None


# ============================ УПРАВЛЕНИЕ =====================================

def handle_keys(game_object):
    """
    Обрабатывает события Pygame.
    - На стрелки/WSAD ставит game_object.next_direction.
    - На закрытие окна — завершает программу.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w) and game_object.direction != DOWN:
                game_object.next_direction = UP
            elif event.key in (pygame.K_DOWN, pygame.K_s) and game_object.direction != UP:
                game_object.next_direction = DOWN
            elif event.key in (pygame.K_LEFT, pygame.K_a) and game_object.direction != RIGHT:
                game_object.next_direction = LEFT
            elif event.key in (pygame.K_RIGHT, pygame.K_d) and game_object.direction != LEFT:
                game_object.next_direction = RIGHT


# ============================ ОСНОВНОЙ ЦИКЛ ==================================

def main():
    """
    Главный цикл игры:
    - обработка ввода → обновление направления → ход змейки
    - поедание яблока (рост) → самоукус (сброс)
    - отрисовка и обновление экрана
    """
    # фон
    screen.fill(BOARD_BACKGROUND_COLOR)

    # объекты
    snake = Snake()
    apple = Apple()
    apple.randomize_position(forbidden=snake.positions)

    while True:
        # 1) ввод
        handle_keys(snake)

        # 2) смена направления
        snake.update_direction()

        # 3) движение
        snake.move()

        # 4) поедание яблока
        if snake.get_head_position() == apple.position:
            snake.length += 1
            apple.randomize_position(forbidden=snake.positions)

        # 5) самоукус → сброс
        if snake.get_head_position() in snake.positions[1:]:
            snake.reset()
            screen.fill(BOARD_BACKGROUND_COLOR)
            apple.randomize_position(forbidden=snake.positions)

        # 6) отрисовка и кадр
        snake.draw()
        apple.draw()
        pygame.display.update()

        # 7) ограничение скорости
        clock.tick(SPEED)


# Локальный запуск (для тебя). В тестах это не помешает.
if __name__ == '__main__':
    main()


# Метод draw класса Apple
# def draw(self):
#     rect = pygame.Rect(self.position, (GRID_SIZE, GRID_SIZE))
#     pygame.draw.rect(screen, self.body_color, rect)
#     pygame.draw.rect(screen, BORDER_COLOR, rect, 1)

# # Метод draw класса Snake
# def draw(self):
#     for position in self.positions[:-1]:
#         rect = (pygame.Rect(position, (GRID_SIZE, GRID_SIZE)))
#         pygame.draw.rect(screen, self.body_color, rect)
#         pygame.draw.rect(screen, BORDER_COLOR, rect, 1)

#     # Отрисовка головы змейки
#     head_rect = pygame.Rect(self.positions[0], (GRID_SIZE, GRID_SIZE))
#     pygame.draw.rect(screen, self.body_color, head_rect)
#     pygame.draw.rect(screen, BORDER_COLOR, head_rect, 1)

#     # Затирание последнего сегмента
#     if self.last:
#         last_rect = pygame.Rect(self.last, (GRID_SIZE, GRID_SIZE))
#         pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, last_rect)

# Функция обработки действий пользователя
# def handle_keys(game_object):
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             raise SystemExit
#         elif event.type == pygame.KEYDOWN:
#             if event.key == pygame.K_UP and game_object.direction != DOWN:
#                 game_object.next_direction = UP
#             elif event.key == pygame.K_DOWN and game_object.direction != UP:
#                 game_object.next_direction = DOWN
#             elif event.key == pygame.K_LEFT and game_object.direction != RIGHT:
#                 game_object.next_direction = LEFT
#             elif event.key == pygame.K_RIGHT and game_object.direction != LEFT:
#                 game_object.next_direction = RIGHT

# Метод обновления направления после нажатия на кнопку
# def update_direction(self):
#     if self.next_direction:
#         self.direction = self.next_direction
#         self.next_direction = None
