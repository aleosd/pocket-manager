import curses
import sys
import webbrowser
from urllib.parse import urlparse
from curses import wrapper

from . import database
from . import http


KEY_ESC = 27
KEY_SPACE = 32

KEY_o = 111
KEY_O = 79
KEY_d = 100
KEY_D = 68
KEY_j = 106
KEY_k = 107
KEY_q = 113
KEY_Q = 81


class StatusLine:
    STATUS_LINE_HEIGHT = 2

    def __init__(self, parent):
        self.parent = parent
        self.height, self.width = parent.screen.getmaxyx()
        self.window = parent.screen.subwin(
            self.STATUS_LINE_HEIGHT, self.width,
            self.height - self.STATUS_LINE_HEIGHT, 0)
        self.window.keypad(True)

    def display(self, custom_text=None):
        self.window.clear()
        self.window.hline(0, 0, '-', self.width)
        if custom_text:
            status_text = self.validate_text(custom_text)
        else:
            status_text = self._default_text
        style = curses.color_pair(2) | curses.A_BOLD
        self.window.addstr(1, 0, status_text, style)
        self.window.refresh()

    @property
    def _default_text(self):
        text = f'Total: {len(self.parent.records)} | ESC (Quit) | ' \
               f'O (Open) | (D) Delete'
        return self.validate_text(text)

    def validate_text(self, text):
        if len(text) > self.width:
            text = text[:self.width - 4] + '...'
        return text


class Window:
    MAX_DATE_COLUMN_LENGTH = 14

    def __init__(self, stdsct):
        """
        :param stdsct: curses window object

        self.index - index of first displayed on screen record, taken from
        records array. So it can take values from 0 to len(records) - window
        height

        self.selected_record_index - index of currently selected record, taken
        from subset of records displayed on screen, so it's value bounded by
        0 and window height

        self.current_records - array of records, currently displayed on screen
        """
        self._setup_curses()
        self.screen = stdsct
        self.records = database.get_records()

        self.index = 0
        self.selected_record_index = 0
        self.height, self.width = self.screen.getmaxyx()
        self.records_window_height = self.height - StatusLine.STATUS_LINE_HEIGHT
        self.title_column_length = self._get_title_column_length()
        self.created_column_length = self._get_created_column_length()
        self.http_status_column_length = 4
        self.url_column_length = self._get_url_column_length()
        self.current_records = []

        self.records_window = self.screen.subwin(
            self.records_window_height, self.width, 0, 0
        )
        self.records_window.keypad(True)
        self.status_window = StatusLine(self)

        self.key_handlers = self._get_key_handlers()

        self.display()

    def _get_url_column_length(self):
        return self.width - self.title_column_length - \
               self.created_column_length - self.http_status_column_length

    def _get_created_column_length(self):
        created_length = self.width // 6
        if created_length > self.MAX_DATE_COLUMN_LENGTH:
            created_length = self.MAX_DATE_COLUMN_LENGTH
        return created_length

    def _get_title_column_length(self):
        return self.width // 3 * 2

    def _get_key_handlers(self):
        return {
            curses.KEY_EXIT: self.exit,
            KEY_q: self.exit,
            KEY_Q: self.exit,
            KEY_d: self.delete_record,
            KEY_D: self.delete_record,
            curses.KEY_HOME: self.move_to_first,
            curses.KEY_END: self.move_to_last,
            KEY_o: self.open_link_in_browser,
            KEY_O: self.open_link_in_browser,
            curses.KEY_UP: self.move_up,
            KEY_k: self.move_up,
            KEY_j: self.move_down,
            curses.KEY_DOWN: self.move_down,
            curses.KEY_PPAGE: self.previous_page,
            curses.KEY_NPAGE: self.next_page,
            KEY_SPACE: self.next_page,
        }

    @staticmethod
    def _setup_curses():
        curses.noecho()
        curses.cbreak()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.curs_set(0)

    @staticmethod
    def _trim_string(string, max_length):
        if len(string) >= max_length:
            return string[:max_length - 4] + '...'
        return string

    def display(self):
        self.status_window.display()
        self.refresh()
        while True:
            self.process_keypress(self.records_window.getch())
            self.refresh()

    def process_keypress(self, c):
        if c in self.key_handlers:
            self.key_handlers[c]()

    def delete_record(self):
        link = self.current_records[self.selected_record_index]
        self.status_window.display(
            f'Deleting link "{link.resolved_title.expandtabs(1)}"')
        result = http.delete_link(link.id)
        if result['action_results'][0] and result['status'] == 1:
            database.delete_link(link.id)
            self.records = database.get_records()
            self.refresh()
        self.status_window.display()

    def open_link_in_browser(self):
        link = self.current_records[self.selected_record_index]
        url = link.resolved_url or link.given_url
        if url:
            webbrowser.open(url, new=2, autoraise=True)

    def refresh(self):
        start = self.index
        end = self.records_window_height + self.index
        self.records_window.clear()
        self.current_records = self.records[start:end]
        for i, record in enumerate(self.current_records):
            if i == self.selected_record_index:
                styles = curses.color_pair(1) | curses.A_BOLD
            else:
                styles = curses.color_pair(1)

            title = self.get_title(record)
            self.records_window.addstr(i, 0, title, styles)

            url = self.get_url(record)
            url_position = self.title_column_length
            self.records_window.addstr(i, url_position, url, styles)

            http_status = str(record.check_result or ' - ')
            http_status_position = self.title_column_length + \
                self.url_column_length
            self.records_window.addstr(
                i, http_status_position, http_status, styles)

            created = self.get_created(record)
            created_position = http_status_position + \
                self.http_status_column_length
            self.records_window.addstr(
                i, created_position,
                created, styles)

    def get_created(self, record):
        if not record.created_at:
            return ''
        created_str = record.created_at.strftime('%d %b, %Y')
        if len(created_str) > self.created_column_length:
            return created_str[:self.created_column_length]
        return created_str

    def get_title(self, record):
        title = (record.resolved_title or record.given_title)
        title = " ".join(title.split())
        return self._trim_string(title, self.title_column_length)

    def get_url(self, record):
        """Returns domain from record url"""
        url = record.resolved_url or record.given_url
        if not url:
            return ''
        parsed_url = urlparse(url)
        return self._trim_string(parsed_url.netloc, self.url_column_length)

    def move_up(self):
        if self.selected_record_index > 0:
            self.selected_record_index -= 1
        if self.move_up_allowed() and self.selected_record_index == 0:
            self.index -= 1
        self.refresh()

    def move_down(self):
        if self.move_down_allowed() and self.selected_record_index == \
                self.records_window_height - 1:
            self.index += 1
        if self.selected_record_index < self.records_window_height - 1:
            self.selected_record_index += 1
        self.refresh()

    def next_page(self):
        new_index = self.index + self.records_window_height
        while self.move_down_allowed() and self.index < new_index:
            self.index += 1
        self.refresh()

    def previous_page(self):
        new_index = self.index - self.records_window_height
        while self.move_up_allowed() and self.index > new_index:
            self.index -= 1
        self.refresh()

    def move_up_allowed(self):
        return self.index > 0

    def move_down_allowed(self):
        return self.index < len(self.records) - self.records_window_height

    def exit(self):
        curses.nocbreak()
        self.screen.keypad(False)
        curses.echo()
        curses.endwin()
        sys.exit()

    def move_to_last(self):
        if self.move_down_allowed():
            self.index = len(self.records) - self.records_window_height
            self.selected_record_index = self.records_window_height - 1

    def move_to_first(self):
        if self.move_up_allowed():
            self.index = 0
            self.selected_record_index = 0


if __name__ == '__main__':
    wrapper(Window)
