import pygame as pg
from settings import FONT_SIZE

HOVER_COLOR = '#D0E0FF'


class Widget:
    def __init__(self, app, pos=[0, 0], size=[1, 1]):
        self.app = app
        self.pos = list(pos)
        self.size = list(size)
        self.rect = pg.Rect(pos, size)

    def set_position(self, pos):
        self.pos = list(pos)
        self.rect = pg.Rect(pos, self.size)

    def set_size(self, size):
        self.size = list(size)
        self.rect = pg.Rect(self.pos, size)

    def get_position(self):
        return self.pos

    def get_size(self):
        return self.size

    def get_x(self):
        return self.pos[0]

    def get_y(self):
        return self.pos[1]

    def get_width(self):
        return self.size[0]

    def get_height(self):
        return self.size[1]

    def draw(self, surface):
        pass

class Button(Widget):
    def __init__(self, app, pos, text):
        self.app = app
        self.padding = 4
        self.text = str(text)
        self.text_rect = self.app.font.get_rect(self.text, size=FONT_SIZE)
        self.char_rect = self.app.font.get_rect('Ag', size=FONT_SIZE)
        self.pos = list(pos)
        self.size = [self.text_rect.width + self.padding * 2, self.char_rect.height + self.padding * 2]
        self.rect = pg.rect.Rect(pos, self.size)
        self.hovered = False
        self.callback = None
        self.last_frame_click = False

    def draw(self, surface):
        rect_color = HOVER_COLOR if self.hovered else 'white'
        pg.draw.rect(surface=surface, color=rect_color,
                     rect=self.rect)
        self.app.font.render_to(surface, (self.pos[0] + self.padding, self.pos[1] + self.padding),
                                     text=str(self.text), size=FONT_SIZE, fgcolor='black')

    def check_events(self):
        mouse_pos = pg.mouse.get_pos()
        mouse_pressed = pg.mouse.get_pressed()
        self.hovered = self.rect.collidepoint(mouse_pos)
        if mouse_pressed[0] and not self.last_frame_click:
            if self.hovered:
                if self.callback:
                        self.callback(self)
            self.last_frame_click = mouse_pressed[0]
        if not mouse_pressed[0]:
            self.last_frame_click = False


    def set_text(self, text):
        self.text = str(text)
        self.text_rect = self.app.font.get_rect(self.text, size=FONT_SIZE)
        self.set_size_to_fit_text()

    def set_size_to_fit_text(self):
        self.set_size([self.text_rect.width + self.padding * 2, self.char_rect.height + self.padding * 2])

class ButtonCheckbox(Button):
    def __init__(self, app, pos, text):
        super().__init__(app, pos, text)
        self.set_size_to_fit_text()
        # self.set_size([self.char_rect.height + self.text_rect.width + 2 + self.padding * 2 + 4,
        #                self.char_rect.height + 1 + self.padding * 2])
        self.checked = False

    def draw(self, surface):
        rect_color = HOVER_COLOR if self.hovered else 'white'
        pg.draw.rect(surface=surface, color=rect_color,
                     rect=self.rect)
        self.app.font.render_to(surface, (self.pos[0] + self.char_rect.height + self.padding + 5,
                                          self.pos[1] + self.padding),
                                     text=str(self.text), size=FONT_SIZE, fgcolor='black')
        if self.checked:
            pg.draw.lines(surface=surface, color='green3', closed=False,
                          points=[(self.pos[0] + self.padding,
                                   self.pos[1] + self.padding),
                                  (self.pos[0] + self.char_rect.height + self.padding,
                                   self.pos[1] + self.char_rect.height + self.padding)],
                          width=1)
            pg.draw.lines(surface=surface, color='green3', closed=False,
                          points=[(self.pos[0] + self.padding,
                                   self.pos[1] + self.char_rect.height + self.padding),
                                  (self.pos[0] + self.char_rect.height + self.padding,
                                   self.pos[1] + self.padding)],
                          width=1)
        pg.draw.rect(surface=surface, color='black',
                     rect=[self.pos[0] + self.padding, self.pos[1] + self.padding,
                           self.char_rect.height + 1, self.char_rect.height + 1], width = 1)
    def check_events(self, event=None):
        mouse_pos = pg.mouse.get_pos()
        mouse_pressed = pg.mouse.get_pressed()
        self.hovered = self.rect.collidepoint(mouse_pos)
        if mouse_pressed[0] and not self.last_frame_click:
            if self.hovered:
                self.checked ^= True
                if self.callback:
                        self.callback(self)
            self.last_frame_click = mouse_pressed[0]
            return
        if not mouse_pressed[0]:
            self.last_frame_click = False

    def set_text(self, text):
        self.text = str(text)
        self.text_rect = self.app.font.get_rect(self.text, size=FONT_SIZE)

    def set_size_to_fit_text(self):
        self.set_size([self.char_rect.height + self.text_rect.width + self.padding * 2 + 4,
                                 self.char_rect.height + self.padding * 2])


class ButtonMenu(Widget):
    def __init__(self, app, pos=[0, 0], size=[1, 1]):
        self.app = app
        self.pos = list(pos)
        self.size = list(size)
        self.rect = pg.Rect(pos, size)
        self.buttons = []

    def add_button(self, text, checkbox=False):
        last_y = self.pos[1] if len(self.buttons) == 0 else self.buttons[-1].pos[1]+self.buttons[-1].rect.height
        if checkbox:
            self.buttons.append(ButtonCheckbox(app=self.app, pos=[self.pos[0], last_y], text=text))
        else:
            self.buttons.append(Button(app=self.app, pos=[self.pos[0], last_y], text=text))
        self.update_menu_width()

    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)

    def check_events(self):
        for button in self.buttons:
            button.check_events()

    def update_menu_width(self):
        max_rect_width = max([i.size[0] for i in self.buttons])
        for button in self.buttons:
            button.set_size([max_rect_width, button.get_height()])
        self.set_size([max_rect_width, sum([i.size[1] for i in self.buttons])])

    def set_position(self, pos):
        next_pos = [0, 0]
        super().set_position(pos)
        for button in self.buttons:
            button.set_position([x + y for x, y in zip(pos, next_pos)])
            next_pos[1] += button.get_height()
