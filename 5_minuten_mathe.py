#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
import sys
import time

from imgui.integrations.pygame import PygameRenderer
import imgui
import numpy as np
import OpenGL.GL as gl
import pygame
import yaml


class HiddenNumber(Enum):
    A = 0
    B = 1
    C = 2


class ProblemType(Enum):
    ADDITION = 0
    SUBTRACTION = 1
    MULTIPLICATION = 2
    DIVISION = 3


@dataclass
class Problem:
    type: ProblemType
    hidden_number: HiddenNumber
    a: int
    b: int
    c: int

    def check(self, guess):
        if self.hidden_number == HiddenNumber.A:
            return guess == self.a
        elif self.hidden_number == HiddenNumber.B:
            return guess == self.b
        elif self.hidden_number == HiddenNumber.C:
            return guess == self.c


@dataclass
class Task:
    problem: Problem
    guess: int | None = None

    def solved(self):
        return self.problem.check(self.guess)


game_time = 5*5.  # 5 minutes per game


TASK_TYPE_TO_OPERATOR = {
    ProblemType.ADDITION: '+',
    ProblemType.SUBTRACTION: '-',
    ProblemType.DIVISION: ':',
    ProblemType.MULTIPLICATION: '·'
}


@dataclass
class State:
    start_time: float = time.time()
    tasks: list[Task] = field(default_factory=lambda: [Task(generate_problem())])

    def current_task(self) -> Task:
        return self.tasks[-1]

    def new_task(self):
        self.tasks.append(Task(generate_problem()))

    def submit_guess(self, guess):
        self.current_task().guess = guess

    def stats(self):
        nof_tasks = max(1, len(self.tasks) - 1)
        solved_correctly = int(np.sum([task.solved() for task in self.tasks]))
        solved_incorrectly = nof_tasks - solved_correctly
        return solved_correctly, solved_incorrectly, nof_tasks

    def result_string(self):
        solved_correctly, solved_incorrectly, nof_tasks = self.stats()
        return f'{solved_correctly} richtig, {solved_incorrectly} falsch von insgesamt {nof_tasks}'


def write_result(state: State):
    def task_to_builtin(task: Task):
        prob = task.problem
        return {
            'guess': task.guess,
            'problem': f'{prob.a} {TASK_TYPE_TO_OPERATOR[prob.type]} {prob.b} = {prob.c}',
            'hidden': prob.hidden_number.name
        }

    cache_dir = Path.home() / ".cache" / "5_minuten_mathe"
    # Create the directory if it doesn't exist
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate a filename based on the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile_path = cache_dir / f"result_{current_time}.yml"

    solved_correctly, solved_incorrectly, nof_tasks = state.stats()
    task_data = [task_to_builtin(task) for task in state.tasks]
    data = {
        'solved_correctly': solved_correctly,
        'solved_incorrectly': solved_incorrectly,
        'nof_tasks': nof_tasks,
        'tasks': task_data
    }
    with open(logfile_path, 'w', encoding="utf-8") as logfile:
        yaml.dump(data, logfile)


class GameOver(Exception):
    pass


def main():
    pygame.init()
    size = 800, 600

    pygame.display.set_mode(size, pygame.DOUBLEBUF |
                            pygame.OPENGL | pygame.RESIZABLE)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    font = io.fonts.add_font_from_file_ttf(
        'fonts/OpenSans/static/OpenSans-Bold.ttf', 20)
    font_big = io.fonts.add_font_from_file_ttf(
        'fonts/OpenSans/static/OpenSans-Bold.ttf', 50)
    impl.refresh_font_texture()

    from theme import theme
    theme(imgui.get_style())

    def draw_task(problem: Problem, size: tuple[int, int]):
        guess = ''

        def draw_input():
            imgui.same_line()
            imgui.align_text_to_frame_padding()
            imgui.push_item_width(90)
            changed, int_val = imgui.input_text(f'##input_hidden', str(guess), flags=imgui.INPUT_TEXT_CHARS_DECIMAL)
            imgui.set_keyboard_focus_here()
            if changed:
                state.submit_guess(int(int_val))
            imgui.pop_item_width()

        def padding_aligned_text(*args, **kwargs):
            imgui.same_line()
            imgui.align_text_to_frame_padding()
            imgui.text(*args, **kwargs)

        with imgui.begin_child(f'task', *size, True, MAIN_WINDOW_FLAGS):
            operator = TASK_TYPE_TO_OPERATOR[problem.type]
            if problem.hidden_number == HiddenNumber.A:
                draw_input()
                padding_aligned_text(f'{operator} {problem.b} = {problem.c}')
            elif problem.hidden_number == HiddenNumber.B:
                padding_aligned_text(f'{problem.a} {operator}')
                draw_input()
                padding_aligned_text(f'= {problem.c}')
            elif problem.hidden_number == HiddenNumber.C:
                padding_aligned_text(f'{problem.a} {operator} {problem.b} =')
                draw_input()

    state: State = None
    last_result = ''

    MAIN_WINDOW_FLAGS = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_DECORATION

    def tick():
        if state is None:
            return
        if time.time() - state.start_time > game_time:
            raise GameOver

    while True:
        try:
            tick()
        except GameOver:
            last_result = state.result_string()
            write_result(state)
            state = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            if state is not None:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        state.new_task()
            impl.process_event(event)
        impl.process_inputs()

        imgui.new_frame()

        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING,
                             imgui.get_window_width()*0.02)
        imgui.push_font(font)

        with imgui.begin_main_menu_bar():
            with imgui.begin_menu('Datei', True):

                if imgui.menu_item('Spiel starten', 'Enter')[0]:
                    state = State()

                if imgui.menu_item('Beenden', 'Strg+Q')[0]:
                    sys.exit(0)
                menu_height = imgui.get_window_height()

        imgui.set_next_window_position(0, menu_height)
        imgui.set_next_window_size(
            io.display_size.x, io.display_size.y - menu_height)

        with imgui.begin('main_window', flags=MAIN_WINDOW_FLAGS):

            window_size = np.array(imgui.get_window_size())
            padding = imgui.get_style().item_spacing

            if state is not None:
                imgui.push_font(font_big)
                task_window_size = (window_size - (padding[0]*2, padding[1]*4))
                task = state.current_task()
                draw_task(task.problem, task_window_size)
                imgui.pop_font()
            else:
                if last_result:
                    imgui.text(last_result)
                button_size = window_size*0.15
                imgui.set_cursor_pos(window_size*0.5 - button_size*0.5)
                if imgui.button('Spiel starten', *button_size):
                    state = State()

        imgui.pop_font()
        imgui.pop_style_var()

        gl.glClearColor(1, 1, 1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())
        pygame.display.flip()


def generate_problem():
    problem_type = np.random.choice(list(ProblemType))
    hidden_number = HiddenNumber.C
    if problem_type in [ProblemType.ADDITION, ProblemType.SUBTRACTION]:
        hidden_number = np.random.choice(list(HiddenNumber))

    if problem_type == ProblemType.ADDITION:
        a = np.random.randint(1, 1000)
        b = np.random.randint(1, 1000 - a)
        c = a + b
    elif problem_type == ProblemType.SUBTRACTION:
        a = np.random.randint(1, 1000)
        b = np.random.randint(1, a)
        c = a - b
    elif problem_type == ProblemType.MULTIPLICATION:
        b = np.random.randint(1, 10)
        a = np.random.randint(1, 20)
        if a > 10:
            b = np.random.randint(1, 6)
        c = a * b
    elif problem_type == ProblemType.DIVISION:
        b = np.random.randint(1, 10)
        c = np.random.randint(1, 10)
        a = b * c

    return Problem(type=problem_type, hidden_number=hidden_number, a=a, b=b, c=c)


if __name__ == '__main__':
    main()
