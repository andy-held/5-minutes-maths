from enum import Enum
from dataclasses import dataclass

import numpy as np

class HiddenNumber(Enum):
    A = 0
    B = 1
    C = 2


class _ProblemType(Enum):
    ADDITION = 0
    SUBTRACTION = 1
    MULTIPLICATION = 2
    DIVISION = 3


@dataclass(frozen=True)
class Problem:
    type: _ProblemType
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


TASK_TYPE_TO_OPERATOR = {
    _ProblemType.ADDITION: '+',
    _ProblemType.SUBTRACTION: '-',
    _ProblemType.DIVISION: ':',
    _ProblemType.MULTIPLICATION: '·'
}


def generate_task():
    problem_type = np.random.choice(list(_ProblemType))
    hidden_number = HiddenNumber.C
    if problem_type in [_ProblemType.ADDITION, _ProblemType.SUBTRACTION]:
        hidden_number = np.random.choice(list(HiddenNumber))

    if problem_type == _ProblemType.ADDITION:
        a = np.random.randint(1, 1000)
        b = np.random.randint(1, 1000 - a)
        c = a + b
    elif problem_type == _ProblemType.SUBTRACTION:
        a = np.random.randint(1, 1000)
        b = np.random.randint(1, a)
        c = a - b
    elif problem_type == _ProblemType.MULTIPLICATION:
        b = np.random.randint(1, 10)
        a = np.random.randint(1, 20)
        if a > 10:
            b = np.random.randint(1, 6)
        c = a * b
    elif problem_type == _ProblemType.DIVISION:
        b = np.random.randint(1, 10)
        c = np.random.randint(1, 10)
        a = b * c

    return Task(
        Problem(
            problem_type,
            hidden_number,
            a,b, c)
    )
