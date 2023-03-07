from pydantic import BaseModel


class Node(BaseModel):
    type: str
    data: str


class ProblemSource(BaseModel):
    type: str


class LinkSource(ProblemSource):
    link: str


class TestSource(ProblemSource):
    name: str
    problem: str


class Problem(BaseModel):
    source: ProblemSource
    text: list[Node]


class Answers(BaseModel):
    choices: dict[str, str]
    correct: str


class VideoSolution(BaseModel):
    link: str
    creator: str | None


class TextSolution(BaseModel):
    name: str
    text: list[Node]


class Solutions(BaseModel):
    video: list[VideoSolution]
    text: list[TextSolution]


class FullProblem(BaseModel):
    id: int
    problem: Problem
    answers: Answers
    solutions: Solutions