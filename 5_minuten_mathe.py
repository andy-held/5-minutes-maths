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


@dataclass
class Task:
    plus: bool
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
        self.guesses = [-1]*nof_tasks

    def tick(self):
        if time.time() - self.start_time > game_time:
            self.game_running = False

    def task_string(self, task: Task):
        operator = '+' if task.plus else '-'
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
    size = 1200, 800

    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    state = State()

    MAIN_WINDOW_FLAGS = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_DECORATION

    def draw_task(i, size):
        task = state.tasks[i]
        guess = state.guesses[i]

        def draw_input():
            imgui.push_item_width(30)
            changed, int_val = imgui.input_int(f'##input_hidden{i}', guess, 0, 0)
            if changed:
                state.guesses[i] = int_val
            imgui.pop_item_width()

        with imgui.begin_child(f'task{i}', *size, True, MAIN_WINDOW_FLAGS):
            operator = '+' if task.plus else '-'
            if task.hidden_number == HiddenNumber.HIDA:
                draw_input()
                imgui.same_line()
                imgui.text(f'{operator} {task.b} = {task.c}')
            elif task.hidden_number == HiddenNumber.HIDB:
                imgui.text(f'{task.a} {operator}')
                imgui.same_line()
                draw_input()
                imgui.same_line()
                imgui.text(f'= {task.c}')
            elif task.hidden_number == HiddenNumber.HIDC:
                imgui.text(f'{task.a} {operator} {task.b} =')
                imgui.same_line()
                draw_input()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

            impl.process_event(event)
        impl.process_inputs()

        imgui.new_frame()

        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, imgui.get_window_width()*0.02)

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
                tasks_per_col = 10
                tasks_per_line = nof_tasks/tasks_per_col
                task_window_size = ((window_size - padding)/np.array([tasks_per_line, tasks_per_col])).astype(int)-padding
                for i in range(nof_tasks):
                    draw_task(i, task_window_size)
                    if i%(tasks_per_line) != (tasks_per_line-1):
                        imgui.same_line(spacing=padding[0])
                state.tick()

            else:
                if state.guesses:
                        imgui.text(state.result_string())
                button_size = window_size*0.1
                imgui.set_cursor_pos(window_size*0.5 - button_size*0.5)
                if imgui.button('Start Game', *button_size):
                    state.new_round()

        imgui.pop_style_var()

        gl.glClearColor(1, 1, 1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()


def generate_task():
    get_rand_up_to = lambda n: int(np.random.rand()*(n+1))

    hidden_number = HiddenNumber(get_rand_up_to(2))
    plus_task = np.random.rand() > 0.5

    a = get_rand_up_to(20)
    if plus_task:
        b = get_rand_up_to(20-a)
        c = a + b
    else:
        b = get_rand_up_to(a)
        c = a - b

    return Task(plus_task, hidden_number, a, b, c)


if __name__ == '__main__':
    main()
