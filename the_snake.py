import sys
from random import randint

import pygame as pg

# --- Константы поля и сетки -------------------------------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# --- Направления движения ---------------------------------------------------
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# --- Цвета ------------------------------------------------------------------
BOARD_BACKGROUND_COLOR = (0, 0, 0)  # фон (чёрный)
BORDER_COLOR = (93, 216, 228)  # цвет рамки клетки
APPLE_COLOR = (255, 0, 0)  # красный
SNAKE_COLOR = (0, 255, 0)  # зелёный
WHITE_COLOR = (255, 255, 255)

# --- Начальная позиция ------------------------------------------------------
DEFAULT_POSITION = (
    (SCREEN_WIDTH // 2 // GRID_SIZE) * GRID_SIZE,
    (SCREEN_HEIGHT // 2 // GRID_SIZE) * GRID_SIZE,
)

# --- Скорость игры ----------------------------------------------------------
SPEED = 10  # кадров в секунду

# --- Инициализация окна и часов ---------------------------------------------
pg.init()
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
pg.display.set_caption('Змейка')
clock = pg.time.Clock()


# ============================ ИГРОВЫЕ КЛАССЫ ================================
class GameObject:
    """Базовый игровой объект: хранит позицию и цвет."""

    def __init__(self, position=DEFAULT_POSITION, body_color=WHITE_COLOR):
        self.position = position
        self.body_color = body_color

    def draw_cell(self, position, color=None):
        """Отрисовывает одну клетку на экране."""
        rect = pg.Rect(position, (GRID_SIZE, GRID_SIZE))
        pg.draw.rect(screen, color or self.body_color, rect)
        pg.draw.rect(screen, BORDER_COLOR, rect, 1)

    def draw(self):
        """Абстрактный метод: должен быть переопределён в дочерних классах."""
        raise NotImplementedError(
            f'Метод draw() не реализован в классе {self.__class__.__name__}'
        )


class Apple(GameObject):
    """Яблоко: квадрат 1×1 клетки, появляется в случайной свободной клетке."""

    def __init__(self, body_color=APPLE_COLOR, forbidden=None):
        super().__init__(body_color=body_color)
        self.randomize_position(forbidden=forbidden)

    def randomize_position(self, forbidden=None):
        """Ставит яблоко в случайную клетку, избегая занятых позиций."""
        forbidden = set(forbidden or [])
        while True:
            x = randint(0, GRID_WIDTH - 1) * GRID_SIZE
            y = randint(0, GRID_HEIGHT - 1) * GRID_SIZE
            if (x, y) not in forbidden:
                self.position = (x, y)
                break

    def draw(self):
        """Отрисовывает яблоко на экране."""
        self.draw_cell(self.position, self.body_color)


class Snake(GameObject):
    """Змейка: список сегментов, голова — первый элемент."""

    def __init__(self, body_color=SNAKE_COLOR):
        super().__init__(body_color=body_color)
        self.length = 1
        self.direction = RIGHT
        self.next_direction = None
        self.last = None

    def get_head_position(self):
        """Возвращает координаты головы."""
        return self.positions[0]

    def update_direction(self):
        """Применяет следующее направление, если оно задано."""
        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None

    def move(self):
        """Двигает змейку на одну клетку с телепортом через края."""
        head_x, head_y = self.get_head_position()
        dx, dy = self.direction
        new_x = (head_x + dx * GRID_SIZE) % SCREEN_WIDTH
        new_y = (head_y + dy * GRID_SIZE) % SCREEN_HEIGHT
        new_head = (new_x, new_y)

        self.positions.insert(0, new_head)

        if len(self.positions) > self.length:
            self.last = self.positions.pop()
        else:
            self.last = None

    def draw(self):
        """Рисует змейку и затирает последний сегмент."""
        for position in self.positions[1:]:
            self.draw_cell(position, self.body_color)

        self.draw_cell(self.get_head_position(), self.body_color)

        if self.last:
            rect = pg.Rect(self.last, (GRID_SIZE, GRID_SIZE))
            pg.draw.rect(screen, BOARD_BACKGROUND_COLOR, rect)

    def reset(self):
        """Сбрасывает змейку к исходному состоянию (центр, длина=1, вправо)."""
        self.position = DEFAULT_POSITION
        self.length = 1
        self.positions = [self.position]
        self.direction = RIGHT
        self.next_direction = None
        self.last = None


# ============================ УПРАВЛЕНИЕ =====================================
def handle_keys(game_object):
    """Обрабатывает события: клавиши движения и выход из игры."""
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            sys.exit()
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                pg.quit()
                sys.exit()
            if (event.key in (pg.K_UP, pg.K_w)
                    and game_object.direction != DOWN):
                game_object.next_direction = UP
            elif (event.key in (pg.K_DOWN, pg.K_s)
                  and game_object.direction != UP):
                game_object.next_direction = DOWN
            elif (event.key in (pg.K_LEFT, pg.K_a)
                  and game_object.direction != RIGHT):
                game_object.next_direction = LEFT
            elif (event.key in (pg.K_RIGHT, pg.K_d)
                  and game_object.direction != LEFT):
                game_object.next_direction = RIGHT


# ============================ ОСНОВНОЙ ЦИКЛ ==================================
def main():
    """Главный цикл игры."""
    screen.fill(BOARD_BACKGROUND_COLOR)

    snake = Snake()
    apple = Apple(forbidden=snake.positions)

    while True:
        handle_keys(snake)
        snake.update_direction()
        snake.move()

        if snake.get_head_position() == apple.position:
            snake.length += 1
            apple.randomize_position(forbidden=snake.positions)
        elif snake.get_head_position() in snake.positions[4:]:
            snake.reset()
            screen.fill(BOARD_BACKGROUND_COLOR)
            apple.randomize_position(forbidden=snake.positions)

        snake.draw()
        apple.draw()
        pg.display.update()
        clock.tick(SPEED)


if __name__ == '__main__':
    main()
