import random
import tkinter as tk
import tkinter.font as tkfont

from strokes_data import CHARACTERS, STROKE_PALETTE


BACKGROUND = "#2c3e50"
CANVAS_BACKGROUND = "#34495e"
TEXT = "#ecf0f1"
BUTTON = "#3498db"
CORRECT = "#27ae60"
WRONG = "#e74c3c"
HINT = "#f39c12"
MUTED = "#95a5a6"


def get_font_family(root):
    available = set(tkfont.families(root))
    for family in ("Microsoft YaHei", "SimHei", "SimSun", "Arial"):
        if family in available:
            return family
    return "Arial"


class HanziHangmanGame:
    def __init__(self, root):
        self.root = root
        self.root.title("笔画猜猜猜 / 汉字版 Hangman")
        self.root.geometry("760x790")
        self.root.configure(bg=BACKGROUND)

        self.font_family = get_font_family(root)
        self.stroke_font = tkfont.Font(
            root=root, family=self.font_family, size=10, weight="bold"
        )
        stroke_names = [
            stroke
            for entry in STROKE_PALETTE
            for stroke in (entry["name"], entry.get("alt"))
            if stroke
        ]
        self.stroke_width_units = self._text_width_units(
            max(stroke_names, key=self.stroke_font.measure)
        )
        self.target = None
        self.strokes = []
        self.revealed = []
        self.wrong_guesses = 0
        self.max_wrong_guesses = 6
        self.game_over = False
        self.hint_shown = False
        self.round_id = 0
        self.flash_after_ids = {}

        self.create_widgets()
        self.new_game()

    def _text_width_units(self, text, padding=2, font=None):
        measured_font = font or self.stroke_font
        unit_width = max(measured_font.measure("0"), 1)
        text_width = measured_font.measure(text)
        return (text_width + unit_width - 1) // unit_width + padding

    def create_widgets(self):
        title_label = tk.Label(
            self.root,
            text="笔画猜猜猜 / 汉字版 Hangman",
            font=(self.font_family, 24, "bold"),
            bg=BACKGROUND,
            fg=TEXT,
        )
        title_label.pack(pady=8)

        self.canvas = tk.Canvas(
            self.root,
            width=200,
            height=200,
            bg=CANVAS_BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack(pady=6)

        self.slot_frame = tk.Frame(self.root, bg=BACKGROUND)
        self.slot_frame.pack(pady=6)

        status_frame = tk.Frame(self.root, bg=BACKGROUND)
        status_frame.pack(pady=3)
        self.wrong_label = tk.Label(
            status_frame,
            text="猜错次数: 0/6",
            font=(self.font_family, 12, "bold"),
            bg=BACKGROUND,
            fg=WRONG,
        )
        self.wrong_label.pack(side="left", padx=12)
        self.total_label = tk.Label(
            status_frame,
            text="共 0 笔",
            font=(self.font_family, 12),
            bg=BACKGROUND,
            fg=MUTED,
        )
        self.total_label.pack(side="left", padx=12)

        self.hint_label = tk.Label(
            self.root,
            text="拼音首字母: ?",
            font=(self.font_family, 11, "bold"),
            bg=BACKGROUND,
            fg=HINT,
        )
        self.hint_label.pack(pady=4)

        self.keyboard_frame = tk.Frame(self.root, bg=BACKGROUND)
        self.keyboard_frame.pack(pady=7)
        self.stroke_buttons = {}
        for index, entry in enumerate(STROKE_PALETTE):
            name = entry["name"]
            button_text = (
                f"{name}\n{entry['alt']}" if entry.get("alt") else name
            )
            row = index // 6
            column = index % 6
            button = tk.Button(
                self.keyboard_frame,
                text=button_text,
                font=(self.font_family, 10, "bold"),
                width=self.stroke_width_units,
                height=2,
                bg=BUTTON,
                fg="white",
                activebackground="#2980b9",
                activeforeground="white",
                relief="flat",
                command=lambda stroke_name=name: self.guess_stroke(stroke_name),
            )
            button.grid(row=row, column=column, padx=2, pady=2)
            self.stroke_buttons[name] = button

        self.legend_label = tk.Label(
            self.root,
            text="按钮上的两个笔画名,本游戏不区分",
            font=(self.font_family, 9),
            bg=BACKGROUND,
            fg=MUTED,
        )
        self.legend_label.pack(pady=(0, 4))

        buttons_frame = tk.Frame(self.root, bg=BACKGROUND)
        buttons_frame.pack(pady=8)
        hint_button = tk.Button(
            buttons_frame,
            text="显示提示",
            font=(self.font_family, 12, "bold"),
            bg=HINT,
            fg="white",
            activebackground="#e67e22",
            activeforeground="white",
            relief="flat",
            padx=18,
            pady=5,
            command=self.show_hint,
        )
        hint_button.pack(side="left", padx=8)

        new_game_button = tk.Button(
            buttons_frame,
            text="开始新游戏",
            font=(self.font_family, 12, "bold"),
            bg=CORRECT,
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            relief="flat",
            padx=18,
            pady=5,
            command=self.new_game,
        )
        new_game_button.pack(side="left", padx=8)

    def new_game(self):
        self._cancel_flashes()
        self.round_id += 1
        self.target = random.choice(CHARACTERS)
        self.strokes = list(self.target["strokes"])
        self.revealed = [False] * len(self.strokes)
        self.wrong_guesses = 0
        self.game_over = False
        self.hint_shown = False

        for button in self.stroke_buttons.values():
            button.config(bg=BUTTON)

        self.canvas.delete("all")
        self.draw_gallows()
        self.hint_label.config(text="拼音首字母: ?")
        self.update_display()

    def draw_gallows(self):
        self.canvas.create_line(20, 180, 100, 180, width=3, fill=TEXT)
        self.canvas.create_line(60, 180, 60, 20, width=3, fill=TEXT)
        self.canvas.create_line(60, 20, 120, 20, width=3, fill=TEXT)
        self.canvas.create_line(120, 20, 120, 40, width=3, fill=TEXT)

    def draw_hangman(self):
        if self.wrong_guesses >= 1:
            self.canvas.create_oval(105, 40, 135, 70, width=3, outline=TEXT)
        if self.wrong_guesses >= 2:
            self.canvas.create_line(120, 70, 120, 120, width=3, fill=TEXT)
        if self.wrong_guesses >= 3:
            self.canvas.create_line(120, 80, 90, 100, width=3, fill=TEXT)
        if self.wrong_guesses >= 4:
            self.canvas.create_line(120, 80, 150, 100, width=3, fill=TEXT)
        if self.wrong_guesses >= 5:
            self.canvas.create_line(120, 120, 90, 150, width=3, fill=TEXT)
        if self.wrong_guesses >= 6:
            self.canvas.create_line(120, 120, 150, 150, width=3, fill=TEXT)

    def guess_stroke(self, name):
        if self.game_over:
            return

        hit = False
        for index, stroke in enumerate(self.strokes):
            if stroke == name and not self.revealed[index]:
                self.revealed[index] = True
                hit = True
                break

        if hit:
            self._flash_button(name, CORRECT)
        else:
            self.wrong_guesses += 1
            self._flash_button(name, WRONG)
            self.draw_hangman()

        self.update_display()
        self.check_game_over()

    def _flash_button(self, name, color):
        button = self.stroke_buttons[name]
        previous_id = self.flash_after_ids.pop(name, None)
        if previous_id is not None:
            try:
                self.root.after_cancel(previous_id)
            except tk.TclError:
                pass

        button.config(bg=color)
        current_round = self.round_id

        def restore():
            self.flash_after_ids.pop(name, None)
            if current_round == self.round_id:
                button.config(bg=BUTTON)

        self.flash_after_ids[name] = self.root.after(250, restore)

    def _cancel_flashes(self):
        for after_id in self.flash_after_ids.values():
            try:
                self.root.after_cancel(after_id)
            except tk.TclError:
                pass
        self.flash_after_ids.clear()

    def update_display(self):
        for child in self.slot_frame.winfo_children():
            child.destroy()

        for index, stroke in enumerate(self.strokes):
            is_revealed = self.revealed[index]
            slot = tk.Label(
                self.slot_frame,
                text=f"{index + 1}\n{stroke if is_revealed else '?'}",
                font=(self.font_family, 10, "bold"),
                width=self.stroke_width_units,
                height=2,
                justify="center",
                bg=CORRECT if is_revealed else CANVAS_BACKGROUND,
                fg="white" if is_revealed else MUTED,
            )
            slot.grid(row=index // 6, column=index % 6, padx=3, pady=3)

        self.wrong_label.config(
            text=f"猜错次数: {self.wrong_guesses}/{self.max_wrong_guesses}"
        )
        self.total_label.config(text=f"共 {len(self.strokes)} 笔")

    def show_hint(self):
        if not self.hint_shown and not self.game_over:
            self.hint_shown = True
            self.hint_label.config(
                text=f"拼音首字母: {self.target['initial']}"
            )

    def check_game_over(self):
        if all(self.revealed):
            self.game_over = True
            self.show_result_dialog(won=True)
            return

        if self.wrong_guesses >= self.max_wrong_guesses:
            self.game_over = True
            self.revealed = [True] * len(self.strokes)
            self.update_display()
            self.show_result_dialog(won=False)

    def show_result_dialog(self, won):
        dialog = tk.Toplevel(self.root)
        dialog.title("恭喜!" if won else "游戏结束")
        dialog.configure(bg=BACKGROUND)
        dialog.transient(self.root)
        dialog.resizable(False, False)

        closed = False

        def close_dialog():
            nonlocal closed
            if closed:
                return
            closed = True
            try:
                dialog.grab_release()
            except tk.TclError:
                pass
            dialog.destroy()

        def start_new_game():
            close_dialog()
            self.new_game()

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

        character_label = tk.Label(
            dialog,
            text=self.target["character"],
            font=(self.font_family, 48, "bold"),
            bg=BACKGROUND,
            fg=TEXT,
        )
        character_label.pack(pady=(12, 2))

        stroke_label = tk.Label(
            dialog,
            text=f"笔顺: {' '.join(self.strokes)}",
            font=(self.font_family, 11),
            bg=BACKGROUND,
            fg=TEXT,
            wraplength=700,
        )
        stroke_label.pack(padx=16, pady=4)

        sentence_label = tk.Label(
            dialog,
            text="例句:",
            font=(self.font_family, 11, "bold"),
            bg=BACKGROUND,
            fg=HINT,
        )
        sentence_label.pack(pady=(5, 2))

        sentences = self.target.get("sentences", [])
        sentence = random.choice(sentences) if sentences else "(暂无例句)"
        sentence_font = tkfont.Font(
            root=dialog, family=self.font_family, size=12
        )
        sentence_width_units = self._text_width_units(
            sentence, padding=2, font=sentence_font
        )
        sentence_text = tk.Text(
            dialog,
            width=sentence_width_units,
            height=1,
            wrap="char",
            font=sentence_font,
            bg=BACKGROUND,
            fg=TEXT,
            insertbackground=BACKGROUND,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=8,
            pady=4,
        )
        sentence_text.tag_configure(
            "character",
            foreground=HINT,
            font=(self.font_family, 12, "bold"),
        )
        for character in sentence:
            if character == self.target["character"]:
                sentence_text.insert("end", character, "character")
            else:
                sentence_text.insert("end", character)
        sentence_text.config(state="disabled")
        sentence_text.pack(padx=16, pady=(0, 8))

        dialog_buttons = tk.Frame(dialog, bg=BACKGROUND)
        dialog_buttons.pack(pady=(0, 14))
        play_again_button = tk.Button(
            dialog_buttons,
            text="再来一局",
            font=(self.font_family, 11, "bold"),
            bg=CORRECT,
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            relief="flat",
            padx=18,
            pady=5,
            command=start_new_game,
        )
        play_again_button.pack(side="left", padx=8)
        close_button = tk.Button(
            dialog_buttons,
            text="关闭",
            font=(self.font_family, 11, "bold"),
            bg=BUTTON,
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            relief="flat",
            padx=18,
            pady=5,
            command=close_dialog,
        )
        close_button.pack(side="left", padx=8)

        self.root.update_idletasks()
        dialog.update_idletasks()
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        dialog_x = root_x + max(0, (root_width - dialog_width) // 2)
        dialog_y = root_y + max(0, (root_height - dialog_height) // 2)
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
        dialog.grab_set()


def main():
    root = tk.Tk()
    HanziHangmanGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
