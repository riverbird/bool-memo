from flet.core.textfield import TextField


class CustomTextField(TextField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.undo_stack = []
        self.redo_stack = []
        self.previous_value = ""
        self.on_change = self._on_text_change

    def _on_text_change(self, e):
        if e.control.value != self.previous_value:
            self.undo_stack.append(self.previous_value)
            self.redo_stack.clear()  # 新输入后清空 redo 栈
            self.previous_value = e.control.value

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.previous_value)
            self.previous_value = self.undo_stack.pop()
            self.value = self.previous_value
            self.update()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.previous_value)
            self.previous_value = self.redo_stack.pop()
            self.value = self.previous_value
            self.update()

