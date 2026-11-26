"""
UI-01 Accessible Interface: keyboard support for the whole app.
setup_keyboard() is called once in app_ui.py when the app starts, and it applies to every window.

What it does:
  - Tab / Shift+Tab moves between fields, buttons, checkboxes, dropdowns and tables
  - Enter presses the button that is focused (tkinter only does this with Space by default)
  - Every focused field and button gets a dark outline, so keyboard users can see where they are
"""

FOCUS_COLOUR = "#1A5FB4"  # dark blue outline, easy to see on white and grey


def setup_keyboard(root):
    # A visible outline around whatever has the keyboard focus
    for widget in ("Button", "Entry", "Checkbutton", "Radiobutton", "Scale", "Text"):
        root.option_add(f"*{widget}.highlightThickness", 2)
        root.option_add(f"*{widget}.highlightColor", FOCUS_COLOUR)

    # Enter (and the keypad Enter) presses a focused button, checkbox or radio button
    for widget in ("Button", "Checkbutton", "Radiobutton"):
        root.bind_class(widget, "<Return>", lambda event: event.widget.invoke(), add="+")
        root.bind_class(widget, "<KP_Enter>", lambda event: event.widget.invoke(), add="+")


def make_clickable(widget, action):
    """
    Lets a label or a frame (like a navigation link or a car card) be reached with Tab and opened with
    Enter or Space, the same as clicking it with the mouse.
    """
    widget.config(takefocus=1, cursor="hand2", highlightthickness=2,
                  highlightcolor=FOCUS_COLOUR, highlightbackground=widget.cget("bg"))
    widget.bind("<Button-1>", lambda event: action())
    widget.bind("<Return>", lambda event: action())
    widget.bind("<space>", lambda event: action())
