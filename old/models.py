from dataclasses import dataclass


@dataclass
class ProblemModel:
    question: str
    solutions: list[str]
    answers: list[str]
    correct_answer: int