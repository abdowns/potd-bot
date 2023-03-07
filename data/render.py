from models import FullProblem
import httpx
from bs4 import BeautifulSoup
from PIL import Image, ImageColor, ImageFont
from PIL.ImageDraw import ImageDraw
from PIL.ImageFont import FreeTypeFont
from io import BytesIO
import json
from cairosvg import svg2png

BACKGROUND_COLOR = (247, 241, 227)
TEXT_COLOR = (0, 0, 0)
IMAGE_WIDTH = 800


class Renderable:
    def get_width(self) -> int:
        raise NotImplementedError()

    def get_height(self) -> int:
        raise NotImplementedError()
    
    def render(self, xy: tuple[int, int], draw: ImageDraw, target_image: Image.Image):
        raise NotImplementedError()


class RText(Renderable):
    def __init__(self, text: str, font: FreeTypeFont) -> None:
        self.text = text
        self.font = font
    
    def get_width(self) -> int:
        return self.font.getlength(self.text)
    
    def get_height(self) -> int:
        return self.font.getbbox(self.text)[3]

    def render(self, xy: tuple[int, int], draw: ImageDraw, target_image: Image.Image):
        draw.text(xy, self.text, fill=TEXT_COLOR, font=self.font)


class RLatex(Renderable):
    def __init__(self, latex: str, font_size: int, space_width: int) -> None:
        self.latex = latex
        self.response = httpx.get('https://latex.codecogs.com/svg.latex?' + latex)
        self.space_width = space_width

        # 18 is the default font size
        with BytesIO(svg2png(self.response.text, background_color='#%02x%02x%02x' % BACKGROUND_COLOR, scale=font_size / 18)) as png_data:
            self.image = Image.open(png_data)
            self.image.load()
    
    def get_width(self) -> int:
        return self.image.width

    def get_height(self) -> int:
        return self.image.height
    
    def render(self, xy: tuple[int, int], draw: ImageDraw, target_image: Image.Image):
        target_image.paste(self.image, xy)


class ProblemImage:
    def __init__(self, problem: FullProblem, width: int, font_size: int) -> None:
        self.font_size = font_size
        self.problem = problem
        self.width = width
        self.x = 0
        self.y = 0

        self.font_regular = ImageFont.truetype('font/Vollkorn-VariableFont_wght.ttf', size=self.font_size)
        self.lines: list[list[Renderable]] = [[]]

    def precalculate(self):
        current_line = 0
        current_width = 0

        for node in self.problem.problem.text:
            match node.type:
                case 'text1' | 'text2':
                    current_phrase = ''
                    lines = node.data.split('\n')

                    while lines:
                        line = lines.pop(0)

                        for word in line.split(' '):
                            word_width = self.font_regular.getlength(word + ' ')

                            if current_width + word_width > self.width:
                                self.lines[current_line].append(RText(current_phrase, self.font_regular))
                                self.lines.append([])
                                current_line += 1
                                current_width = 0
                                current_phrase = ''
                        
                            current_phrase += word + ' '
                            current_width += word_width

                        if lines:
                            self.lines[current_line].append(RText(current_phrase, self.font_regular))
                            self.lines.append([])
                            current_line += 1
                            current_width = 0
                            current_phrase = ''
                    
                    self.lines[current_line].append(RText(current_phrase, self.font_regular))

                case 'latex':
                    r = RLatex(node.data, self.font_size, self.font_regular.getlength(' '))
                    width = r.get_width()

                    if width + current_width > self.width:
                        self.lines.append([])
                        current_line += 1
                        current_width = 0
                    
                    self.lines[current_line].append(r)
                    current_width += width
    
    def render(self):
        render_option_height = round(self.font_size * 2)
        option_count = len(self.problem.answers.choices)
        line_heights = []
        x = 0
        y = 0

        # Render question
        for line in self.lines:
            line_height = 0

            for renderable in line:
                line_height = max(line_height, renderable.get_height())
            
            line_heights.append(round(line_height * 1.05))

        image = Image.new('RGB', (self.width, sum(line_heights) + render_option_height * option_count), BACKGROUND_COLOR)
        draw = ImageDraw(image)

        for i in range(len(self.lines)):
            for renderable in self.lines[i]:
                renderable.render((x, y + round(line_heights[i] / 2 - renderable.get_height() / 2)), draw, image)
                x += round(renderable.get_width())
            
            x = 0
            y += line_heights[i]
        
        # Render answer options

        for i in range(option_count):
            option_name = list(self.problem.answers.choices.keys())[i]
            option_value = list(self.problem.answers.choices.values())[i]

            y = round(image.height - ((option_count - i) * render_option_height))
            x = 5

            option_name_text = RText(option_name, self.font_regular)
            option_name_text.render((x, y), draw, image)

            latex = RLatex(option_value, self.font_size, self.font_regular.getlength(' '))
            latex.render((x + round(self.font_regular.getlength(option_name) * 2), y + int(latex.get_height() / 2)), draw, image)

            draw.line([(0, y), (image.width, y)], fill=TEXT_COLOR, width=2)
        
        with open('image.webp', 'wb') as file:
            image.save(file, 'webp')
        


with open('problems.json', 'rt') as problems_file:
    problems = json.load(problems_file)
    img = ProblemImage(FullProblem.parse_obj(problems[7]), 1000, 56)
    img.precalculate()
    img.render()