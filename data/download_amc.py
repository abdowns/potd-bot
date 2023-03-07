import httpx
from httpx import Response
from bs4 import BeautifulSoup, Tag, NavigableString
import string
from dataclasses import dataclass
from models import *
import json


@dataclass
class AMCParseProblem:
    problem: list[Tag]
    solutions: dict[str, list[Tag]]
    answer_choices: dict[str, str]


class AMCTestParser:
    def __init__(self, test_id: str) -> None:
        self.test_id = test_id
    
    @staticmethod
    def filter_printable(response: Response):
        return ''.join(filter(lambda x: x in string.printable, response.text))
    
    def download_answers(self) -> list[str]:
        response = httpx.get(f'https://artofproblemsolving.com/wiki/index.php/{self.test_id}_Answer_Key', follow_redirects=True)
        soup = BeautifulSoup(self.filter_printable(response), 'html.parser')
        elements: Tag = soup.select_one('.mw-parser-output').find('ol')
        return list(filter(lambda x: x != '\n', [answer.text[0] for answer in elements.children]))
    
    def get_problem_url(self, problem_id: int) -> str:
        return f'https://artofproblemsolving.com/wiki/index.php/{self.test_id}_Problems/Problem_{problem_id}'

    def download_problem(self, problem_id: int) -> AMCParseProblem:
        response = httpx.get(self.get_problem_url(problem_id), follow_redirects=True)
        soup = BeautifulSoup(self.filter_printable(response), 'html.parser')
        main_content = soup.select_one('.mw-parser-output')

        # Parse document
        contents = {}
        parsing_section = ''

        for child in main_content:
            if child.name == 'h2':
                parsing_section = child.text
                contents[parsing_section] = []
            elif parsing_section:
                contents[parsing_section].append(child)

        # Parse problem
        closest_problem_section_matches = list(filter(lambda x: x, [key if key.lower().startswith('problem') else None for key in contents.keys()]))  # not all problem headers go by the exact same name
        problem_data = contents[closest_problem_section_matches[0]]

        problem = problem_data[1:-2]

        # Parse answer choices
        # Find answer choices image
        for i in range(len(problem_data)):
            p_tag: Tag = problem_data[-i]
            img = p_tag.find('img')
            
            if isinstance(img, Tag) and img and 'class' in img.attrs and 'latex' in img.attrs['class']:
                break
        
        answer_choices_latex = img.attrs['alt'].removeprefix('\\[').removesuffix('\\]').removeprefix('$').removesuffix('$').replace('\\qquad', '').replace('\\ ', '')

        answer_choices = {
            seg[0]: seg[1:].removeprefix(')}').removeprefix(') }').strip() for seg in answer_choices_latex.split('\\textbf{(')[1:]
        }

        # Parse solutions
        solutions = {
            solution: contents[solution][1:-1] for solution in filter(lambda x: 'Solution' in x and not 'Solutions' in x, contents.keys())
        }

        return AMCParseProblem(
            answer_choices=answer_choices,
            problem=problem,
            solutions=solutions
        )


def tag_list_to_nodes(tags: list[Tag]) -> list[Node]:
    nodes = []

    for tag in tags:
        if type(tag) == NavigableString:
            nodes.append(Node(
                type='text1',
                data=tag.text
            ))
        else:
            for element in tag.descendants:
                if type(element) == NavigableString:
                    nodes.append(Node(
                        type='text2',
                        data=element.text
                    ))
                elif type(element) == Tag:
                    if element.name == 'img':
                        nodes.append(Node(
                            type='latex',
                            data=element.attrs['alt'].removeprefix('\\[').removesuffix('\\]').removeprefix('$').removesuffix('$')  # remove the $$
                        ))
                    else:
                        nodes.extend(tag_list_to_nodes(element.descendants))

    return nodes


def download_test(test_id: str):
    parser = AMCTestParser(test_id)
    answers = parser.download_answers()
    problems = []

    with open('problems.json', 'wt') as file:
        for i in range(1, len(answers) + 1):
            problem = parser.download_problem(i)

            problems.append(FullProblem(
                id=i,
                problem=Problem(
                    source=LinkSource(
                        type='link',
                        link=parser.get_problem_url(i)
                    ),
                    text=tag_list_to_nodes(problem.problem)
                ),
                answers=Answers(
                    choices=problem.answer_choices,
                    correct=answers[i - 1]
                ),
                solutions=Solutions(
                    video=[
                        VideoSolution(
                            link=tags[0].select_one('a').attrs['href'],
                            creator=tags[1].text[1:-1].strip().strip('\n') if len(tags) == 2 else None
                        ) for name, tags in filter(lambda x: 'video' in x[0].lower(), problem.solutions.items())
                    ],
                    text=[
                        TextSolution(
                            name=name,
                            text=tag_list_to_nodes(tag)
                        ) for name, tag in filter(lambda x: 'video' not in x[0].lower(), problem.solutions.items())
                    ]
                )
            ).dict())

            file.seek(0)
            json.dump(problems, file, indent=4)

    return problems

download_test('2022_AMC_10B')
