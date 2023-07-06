#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from dataclasses import dataclass
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


KEYMAP = {
    pygame.K_0: '0',
    pygame.K_1: '1',
    pygame.K_2: '2',
    pygame.K_3: '3',
    pygame.K_4: '4',
    pygame.K_5: '5',
    pygame.K_6: '6',
    pygame.K_7: '7',
    pygame.K_8: '8',
    pygame.K_9: '9'
}


game_time = 5*60. # 5 minutes per game
nof_tasks = 50


@dataclass
class State:
    game_running: bool = False
    start_time: float = 0
    task: Task = None
    guess: str = '_'
    tasks_done: int = 0
    tasks_correct: int = 0

    def new_round(self):
        self.tasks_done = 0
        self.tasks_correct = 0
        self.game_running = True
        self.start_time = time.time()
        self.new_task()

    def new_task(self):
        self.task = generate_task()
        self.guess = '_'

    def solved_one(self, was_correct):
        self.tasks_done += 1
        if was_correct:
            self.tasks_correct += 1
            
        if self.tasks_done >= nof_tasks:
            self.game_running = False

    def tick(self):
        if time.time() - self.start_time > game_time:
            self.game_running = False
            
    def check_guess(self):
        guess = int(self.guess)
        task = self.task
        hidden_number = task.hidden_number
        if hidden_number == HiddenNumber.HIDA:
            return guess == task.a
        elif hidden_number == HiddenNumber.HIDB:
            return guess == task.b
        elif hidden_number == HiddenNumber.HIDC:
            return guess == task.c


    def task_string(self):
        operator = '+' if self.task.plus else '-'
        task = self.task
        hidden_number = task.hidden_number
        if hidden_number == HiddenNumber.HIDA:
            return f'{self.guess} {operator} {task.b} = {task.c}'
        elif hidden_number == HiddenNumber.HIDB:
            return f'{task.a} {operator} {self.guess} = {task.c}'
        elif hidden_number == HiddenNumber.HIDC:
            return f'{task.a} {operator} {task.b} = {self.guess}'
        

    def result_string(self):
        return f'{self.tasks_correct} richtig von {nof_tasks}'


def main():
    pygame.init()
    size = 800, 600

    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    state = State()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            if state.game_running:
                if event.type == pygame.KEYDOWN:
                    if event.key in KEYMAP.keys():
                        if state.guess == '_':
                            state.guess = ''
                        state.guess += KEYMAP[event.key]
                    elif event.key == pygame.K_BACKSPACE:
                        if state.guess:
                            state.guess = state.guess[:-1]
                        if not state.guess:
                            state.guess = '_'
                    elif event.key == pygame.K_RETURN:
                        state.solved_one(state.check_guess())
                        state.new_task()

            impl.process_event(event)
        impl.process_inputs()

        imgui.new_frame()

        if imgui.begin_main_menu_bar():
            if imgui.begin_menu('File', True):

                if imgui.menu_item('Start Game', 'Enter')[0]:
                    state.new_round()

                if imgui.menu_item('Quit', 'Ctrl+Q')[0]:
                    sys.exit(0)

                imgui.end_menu()
            imgui.end_main_menu_bar()

        if state.game_running:
            with imgui.begin('Aufgabe'):
                imgui.text(state.task_string())
                
            state.tick()
        elif state.task is not None:
            with imgui.begin('Ergebnis'):
                imgui.text(state.result_string())

        #         imgui.text_colored('Eggs', 0.2, 1.0, 0.0)
        
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
