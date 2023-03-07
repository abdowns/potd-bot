import httpx
from bs4 import BeautifulSoup, Tag, NavigableString
from models import ProblemModel


def clean_html(html: str) -> str:
    return html.replace('&nbsp;', '').replace('&minus;', '-')

def download_mathopolis_question(question_id: int) -> ProblemModel:
    MATHOPOLIS_YEAR_TO_COURSE = {
        '2': 'Grade 2',
        '3': 'Grade 3',
        '4': 'Grade 4',
        '5': 'Grade 5',
        '6': 'Grade 6',
        '7': 'Grade 7',
        '8': 'Grade 8',
        'G': 'Geometry',
        'S': 'Statistics',
        'A1': 'Algebra 1',
        'A2': 'Algebra 2',
        'C': 'Calculus'
    }

    data = httpx.get('https://www.mathopolis.com/questions/pwa.php', params={'id': question_id}).json()

    # Get help URLs
    help_urls = {}

    if data['helpTitle']:
        help_urls[data['helpTitle']] = 'https://www.mathsisfun.com' + data['helpLocn']
    
    if data['helpTitle2']:
        help_urls[data['helpTitle2']] = 'https://www.mathsisfun.com' + data['helpLocn2']

    # Clean up the question
    soup = BeautifulSoup(clean_html(data['q']), 'html.parser')
    
    for image in soup.select('img'):
        if 'alt' in image.attrs.keys():
            del image.attrs['alt']

        if 'class' in image.attrs.keys():
            del image.attrs['class']
        
        image.attrs['src'] = f'https://www.mathopolis.com/questions/{image.attrs["src"]}'
    
    for tag in soup.find_all():
        if 'style' in tag.attrs.keys():
            del tag.attrs['style']

    return ProblemModel(
        topic=data['subject'],
        help_urls=help_urls,
        percentage_people_got_right=float(data['rightAvg']),
        answers=[answer['ans'] for answer in data['anss']],
        explaination=data['method'],
        correct_answer=(data['rightn'] - 12) % 5,  # need to deobfuscate answer
        question=str(soup),
        course=MATHOPOLIS_YEAR_TO_COURSE[data['year']],
    )

def download_amc_answer_key(test_id: str) -> list[str]:
    response = httpx.get(f'https://artofproblemsolving.com/wiki/index.php/{test_id}_Answer_Key')
    soup = BeautifulSoup(response.text, 'html.parser')
    content: Tag = soup.find('.mw-parser-output').find('ol')
    answers: list[str] = []

    for answer in content.children:
        answers.append(answer.text)
    
    return answers

def download_amc_problem(test_id: str, problem_id: int, answer_key: list[str]):
    problem_url = f'https://artofproblemsolving.com/wiki/index.php/{test_id}_Problems/Problem_{problem_id}'
    response = httpx.get(problem_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    content: Tag = soup.select_one('.mw-parser-output')
    mode = 0  # 0 for nothing, 1 for problem, 2 for solution
    problem = ProblemModel(course='', explaination='', answers=[], correct_answer=-1)

    def to_latex(tag: Tag) -> str:
        buf = ''
        for c in tag:
            if type(c) == NavigableString:
                buf += '\\text{' + c + '}'
            elif type(c) == Tag:
                buf += c.attrs.get('alt').replace('$', '')
                buf += to_latex(c)
        
        return buf

    for child in content.children:
        t = child.text.lower()

        if child.name == 'h2':
            if t.startswith('problem'):
                mode = 1
            elif t.startswith('solution'):
                mode = 2
            else:
                mode = 0
        elif child.name == 'p':
            if mode == 1:
                problem.question = to_latex(child)
                break
    
    return problem

    # $\textbf{(A)}\ 24.00 \qquad \textbf{(B)}\ 24.50 \qquad \textbf{(C)}\ 25.50 \qquad \textbf{(D)}\ 28.00 \qquad \textbf{(E)}\ 30.00$

download_amc_problem('2022_AMC_10A', 15, [])

# print(download_mathopolis_question(14688).question)

# download_mathopolis_question(14688)

# <p>
#   <img class="postimg" src="images/8/c/5f2e17c2f516cf6ca547a8fb93f4522.gif" alt="[image]" />
#   <br />The diagram shows an electric circuit with two resistors R <sub>1</sub> ohms and R <sub>2</sub> ohms joined in parallel. <br />
#   <br />If the total resistance&nbsp; in the circuit is R ohms, then the formula connecting R <sub>1</sub>, R <sub>2</sub> and R is <br />&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; <img src="latex/9/d/9569f9b8d4f26439cb1594416b0a8a1.svg" alt="[cached] 0.015020370483398 ms" style="margin: 4px" />
#   <br />
#   <br />What is the value of R if R <sub>1</sub> = 2R &minus; 1 and R <sub>2</sub> = R + 4 ?
# </p>