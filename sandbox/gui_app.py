import tkinter as tk
from tkinter import messagebox

class FunApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aria's Fun GUI")
        self.geometry("400x200")
        self.configure(bg="#f0f8ff")
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self, text="Hello, Friend!", font=("Helvetica", 16), bg="#f0f8ff")
        self.label.pack(pady=20)
        self.button = tk.Button(self, text="Click me!", command=self.say_hello)
        self.button.pack(pady=10)

    def say_hello(self):
        messagebox.showinfo("Greetings", "Aria says hi! 🎉")

if __name__ == "__main__":
    app = FunApp()
    app.mainloop()
