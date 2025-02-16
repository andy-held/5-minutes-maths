#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from dataclasses import dataclass, field
from enum import Enum
import time
from imgui.integrations.pygame import PygameRenderer
import OpenGL.GL as gl
import imgui
import pygame
import sys
import numpy as np


class HiddenNumber(Enum):
    HIDA = 0
    HIDB = 1
    HIDC = 2


class TaskType(Enum):
    ADDITION = 0
    SUBTRACTION = 1
    MULTIPLICATION = 2
    DIVISION = 3


@dataclass
class Task:
    type: TaskType
    hidden_number: HiddenNumber
    a: int
    b: int
    c: int

    def check(self, guess):
        if self.hidden_number == HiddenNumber.HIDA:
            return guess == self.a
        elif self.hidden_number == HiddenNumber.HIDB:
            return guess == self.b
        elif self.hidden_number == HiddenNumber.HIDC:
            return guess == self.c


game_time = 5*60. # 5 minutes per game
nof_tasks = 50


TASK_TYPE_TO_OPERATOR = {
    TaskType.ADDITION: '+',
    TaskType.SUBTRACTION: '-',
    TaskType.DIVISION: ':',
    TaskType.MULTIPLICATION: '·'
}

@dataclass
class State:
    game_running: bool = False
    start_time: float = 0
    tasks: list[Task] = field(default_factory=list)
    guesses: list[int] = field(default_factory=list)

    def new_round(self):
        self.tasks
        self.game_running = True
        self.start_time = time.time()
        self.tasks = [generate_task() for _ in range(nof_tasks)]
        self.guesses = ['']*nof_tasks

    def tick(self):
        if time.time() - self.start_time > game_time:
            self.game_running = False

    def task_string(self, task: Task):
        operator = TASK_TYPE_TO_OPERATOR[task.type]
        hidden_number = task.hidden_number
        if hidden_number == HiddenNumber.HIDA:
            return f'{self.guess} {operator} {task.b} = {task.c}'
        elif hidden_number == HiddenNumber.HIDB:
            return f'{task.a} {operator} {self.guess} = {task.c}'
        elif hidden_number == HiddenNumber.HIDC:
            return f'{task.a} {operator} {task.b} = {self.guess}'

    def result_string(self):
        solved_tasks = np.sum([task.check(guess) for task, guess in zip(self.tasks, self.guesses)])
        return f'{solved_tasks} richtig von {nof_tasks}'


def main():
    pygame.init()
    size = 1600, 1000

    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    font = io.fonts.add_font_from_file_ttf('fonts/OpenSans/static/OpenSans-Bold.ttf', 20)
    font_big = io.fonts.add_font_from_file_ttf('fonts/OpenSans/static/OpenSans-Bold.ttf', 50)
    impl.refresh_font_texture()

    from theme import theme
    theme(imgui.get_style())

    state = State()

    MAIN_WINDOW_FLAGS = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_DECORATION

    def draw_task(i, size):
        task = state.tasks[i]
        guess = state.guesses[i]

        def draw_input():
            imgui.same_line()
            imgui.align_text_to_frame_padding()
            imgui.push_item_width(60)
            changed, int_val = imgui.input_text(f'##input_hidden{i}', str(guess), flags=imgui.INPUT_TEXT_CHARS_DECIMAL)
            if changed:
                state.guesses[i] = int(int_val)
            imgui.pop_item_width()

        def padding_aligned_text(*args, **kwargs):
            imgui.same_line()
            imgui.align_text_to_frame_padding()
            imgui.text(*args, **kwargs)

        with imgui.begin_child(f'task{i}', *size, True, MAIN_WINDOW_FLAGS):
            operator = TASK_TYPE_TO_OPERATOR[task.type]
            if task.hidden_number == HiddenNumber.HIDA:
                draw_input()
                padding_aligned_text(f'{operator} {task.b} = {task.c}')
            elif task.hidden_number == HiddenNumber.HIDB:
                padding_aligned_text(f'{task.a} {operator}')
                draw_input()
                padding_aligned_text(f'= {task.c}')
            elif task.hidden_number == HiddenNumber.HIDC:
                padding_aligned_text(f'{task.a} {operator} {task.b} =')
                draw_input()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

            impl.process_event(event)
        impl.process_inputs()

        imgui.new_frame()

        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, imgui.get_window_width()*0.02)
        imgui.push_font(font)

        with imgui.begin_main_menu_bar():
            with imgui.begin_menu('File', True):

                if imgui.menu_item('Start Game', 'Enter')[0]:
                    state.new_round()

                if imgui.menu_item('Quit', 'Ctrl+Q')[0]:
                    sys.exit(0)
                menu_height = imgui.get_window_height()

        imgui.set_next_window_position(0, menu_height)
        imgui.set_next_window_size(io.display_size.x, io.display_size.y - menu_height)
        with imgui.begin('main_window', flags=MAIN_WINDOW_FLAGS):

            window_size = np.array(imgui.get_window_size())
            padding = imgui.get_style().item_spacing

            if state.game_running:
                imgui.push_font(font_big)
                tasks_per_col = 10
                tasks_per_line = nof_tasks/tasks_per_col
                task_window_size = ((window_size - padding)/np.array([tasks_per_line, tasks_per_col])).astype(int)-padding
                for i in range(nof_tasks):
                    draw_task(i, task_window_size)
                    if i%(tasks_per_line) != (tasks_per_line-1):
                        imgui.same_line(spacing=padding[0])
                state.tick()
                imgui.pop_font()

            else:
                if state.guesses:
                        imgui.text(state.result_string())
                button_size = window_size*0.15
                imgui.set_cursor_pos(window_size*0.5 - button_size*0.5)
                if imgui.button('Start Game', *button_size):
                    state.new_round()

        imgui.pop_font()
        imgui.pop_style_var()

        gl.glClearColor(1, 1, 1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()



def generate_task():
    task_type = np.random.choice(list(TaskType))
    hidden_number = HiddenNumber.HIDC
    if (task_type in [TaskType.ADDITION, TaskType.SUBTRACTION]):
        hidden_number = np.random.choice(list(HiddenNumber))

    if task_type == TaskType.ADDITION:
        a = np.random.randint(1, 1000)
        b = np.random.randint(1, 1000 - a)
        c = a + b
    elif task_type == TaskType.SUBTRACTION:
        a = np.random.randint(1, 1000)
        b = np.random.randint(1, a)  # Ensure non-negative results
        c = a - b
    elif task_type == TaskType.MULTIPLICATION:
        a = np.random.randint(1, 20)
        b = np.random.randint(1, 10)
        c = a * b
    elif task_type == TaskType.DIVISION:
        b = np.random.randint(1, 20)
        c = np.random.randint(1, 10)
        a = b * c  # Ensure real division without remainder

    return Task(type=task_type, hidden_number=hidden_number, a=a, b=b, c=c)


if __name__ == '__main__':
    main()
