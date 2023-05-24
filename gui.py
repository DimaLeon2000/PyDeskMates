import pygame as pg
from settings import FONT_SIZE
import bit_reader

HOVER_COLOR = '#90C0FF'


class Button:
    def __init__(self, app, x, y, text):
        self.app = app
        self.padding = 4
        self.text = str(text)
        self.text_rect = self.app.font.get_rect(self.text, size=FONT_SIZE)
        self.char_rect = self.app.font.get_rect('A', size=FONT_SIZE)
        self.rect = pg.rect.Rect(x, y,
                                 self.text_rect.width + self.padding * 2,
                                 self.char_rect.height + self.padding * 2)
        self.x = x
        self.y = y
        self.hovered = False
        self.clicked = False
        self.callback = lambda: None

    def draw(self, surface):
        action = False
        mouse_pos = pg.mouse.get_pos()

        if self.rect.collidepoint(mouse_pos):
            self.hovered = True
            if pg.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                self.callback(self)
                action = True
        else:
            self.hovered = False

        if pg.mouse.get_pressed()[0] == 0:
            self.clicked = False

        rect_color = HOVER_COLOR if self.hovered else 'white'
        pg.draw.rect(surface=surface, color=rect_color,
                     rect=self.rect)
        self.app.font.render_to(surface, (self.x + self.padding, self.y + self.padding),
                                     text=str(self.text), size=FONT_SIZE, fgcolor='black')
        return action

    def set_text(self, text):
        self.text = str(text)
        self.text_rect = self.app.font.get_rect(self.text, size=FONT_SIZE)
        self.rect = pg.rect.Rect(self.x, self.y + self.char_rect.top,
                                 self.text_rect.width + self.padding * 2,
                                 self.char_rect.height + self.padding * 2)


class ButtonCheckbox(Button):
    def __init__(self, app, x, y, text):
        super().__init__(app, x, y, text)
        self.rect = pg.rect.Rect(x, y,
                                 self.char_rect.height + self.text_rect.width + 2 + self.padding * 2 + 4,
                                 self.char_rect.height + 1 + self.padding * 2)
        self.checked = False

    def draw(self, surface):
        action = False
        mouse_pos = pg.mouse.get_pos()

        if self.rect.collidepoint(mouse_pos):
            self.hovered = True
            if pg.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                self.checked ^= True
                self.callback(self)
                action = True
        else:
            self.hovered = False

        if pg.mouse.get_pressed()[0] == 0:
            self.clicked = False

        rect_color = HOVER_COLOR if self.hovered else 'white'
        pg.draw.rect(surface=surface, color=rect_color,
                     rect=self.rect)
        self.app.font.render_to(surface, (self.x + self.char_rect.height + self.padding + 5,
                                          self.y + self.padding),
                                     text=str(self.text), size=FONT_SIZE, fgcolor='black')
        if self.checked:
            pg.draw.lines(surface=surface, color='green2', closed=False,
                          points=[(self.x + self.padding,
                                   self.y + self.padding),
                                  (self.x + self.char_rect.height + self.padding,
                                   self.y + self.char_rect.height + self.padding)],
                          width=1)
            pg.draw.lines(surface=surface, color='green2', closed=False,
                          points=[(self.x + self.padding,
                                   self.y + self.char_rect.height + self.padding),
                                  (self.x + self.char_rect.height + self.padding,
                                   self.y + self.padding)],
                          width=1)
        pg.draw.rect(surface=surface, color='black',
                     rect=[self.x + self.padding, self.y + self.padding,
                           self.char_rect.height + 1, self.char_rect.height + 1], width = 1)
        return action

    def set_text(self, text):
        self.text = str(text)
        self.text_rect = self.app.font.get_rect(self.text, size=FONT_SIZE)
        self.rect = pg.rect.Rect(self.x, self.y,
                                 self.char_rect.height + self.text_rect.width + self.padding * 2 + 4,
                                 self.char_rect.height + self.padding * 2)


class ButtonMenu:
    def __init__(self, app, x, y):
        self.app = app
        self.x, self.y = x, y
        self.buttons = []

    def add_button(self, text, checkbox=False):
        last_y = self.y if len(self.buttons) == 0 else self.buttons[-1].y+self.buttons[-1].rect.height
        if checkbox:
            self.buttons.append(ButtonCheckbox(app=self.app, x=self.x, y=last_y, text=text))
        else:
            self.buttons.append(Button(app=self.app, x=self.x, y=last_y, text=text))
        self.update_menu_width()

    def draw(self, surface):
        for i, button in enumerate(self.buttons):
            button.draw(surface)

    def update_menu_width(self):
        max_rect_width = max([i.rect.width for i in self.buttons])
        for i, button in enumerate(self.buttons):
            button.rect.width = max_rect_width
