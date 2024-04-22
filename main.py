from datetime import datetime
from cnc_hole_lib import get_gcode
import sys

import tkinter as tk
from tkinter import ttk, scrolledtext, TclError

class HoleWidget(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ttk.Label(self, text="X:").grid(row=0, column=0)
        self.entry_x = ttk.Entry(self, width=6)
        self.entry_x.grid(row=0, column=1)

        ttk.Label(self, text="Y:").grid(row=0, column=2)
        self.entry_y = ttk.Entry(self, width=6)
        self.entry_y.grid(row=0, column=3)

        self.button_remove = ttk.Button(self, text="Удалить", command=self.destroy)
        self.button_remove.grid(row=0, column=4)

    def get_coordinates(self):
        return [self.entry_x.get(), self.entry_y.get()]

class App(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.left_frame = ttk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky="nsew")

        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        self.button_add = ttk.Button(self.left_frame, text="+", command=self.add_hole)
        self.button_add.pack(side="bottom")

        self.hole_container = scrolledtext.ScrolledText(self.left_frame)
        self.hole_container.pack(side="top", fill="both", expand=False)

        ttk.Label(self.right_frame, text="Скорость холостого хода:").pack()
        self.thrust_speed = ttk.Entry(self.right_frame)
        self.thrust_speed.insert(0, "300")
        self.thrust_speed.pack()

        ttk.Label(self.right_frame, text="Скорость работы:").pack()
        self.work_speed = ttk.Entry(self.right_frame)
        self.work_speed.insert(0, "200")
        self.work_speed.pack()

        ttk.Label(self.right_frame, text="Скорость углубления:").pack()
        self.plunge_speed = ttk.Entry(self.right_frame)
        self.plunge_speed.insert(0, "100")
        self.plunge_speed.pack()

        ttk.Label(self.right_frame, text="Шаг сверления:").pack()
        self.plunge_step = ttk.Entry(self.right_frame)
        self.plunge_step.insert(0, "0.05")
        self.plunge_step.pack()

        ttk.Label(self.right_frame, text="Кол-во итераций сверления:").pack()
        self.plunge_iterations = ttk.Entry(self.right_frame)
        self.plunge_iterations.insert(0, "4")
        self.plunge_iterations.pack()

        ttk.Label(self.right_frame, text="Высота подъёма между отверстиями").pack()
        self.lift_h = ttk.Entry(self.right_frame)
        self.lift_h.insert(0, "1.0")
        self.lift_h.pack()

        ttk.Label(self.right_frame, text="Глубина материала:").pack()
        self.plunge_depth = ttk.Entry(self.right_frame)
        self.plunge_depth.insert(0, "1.0")
        self.plunge_depth.pack()

        self.button_create_gcode = ttk.Button(self.right_frame, text="Создать gcode", command=self.create_gcode)
        self.button_create_gcode.pack(side="bottom")

        self.hole_widgets = []

    def add_hole(self):
        hole_widget = HoleWidget(self.hole_container)
        hole_widget.pack()

        self.hole_widgets.append(hole_widget)

    def create_gcode(self):
        holes_coords = list()

        id = 0
        for widget in self.hole_widgets:
            try:
                xy = widget.get_coordinates()
                id+=1
                holes_coords.append({'id': id, 'X': float(xy[0]), 'Y': float(xy[1])})
            except TclError:
                pass

        variables = {
            'platform': 'snapmaker',
            'holes_coords': holes_coords,
            'idling_h': 30.0,
            'X_size': 30.0,
            'Y_size': 30.0,
            'lift_h': float(self.lift_h.get()),
            'lowering_iters': int(self.plunge_iterations.get()),
            'depth_material': float(self.plunge_depth.get()),
            'plunge_step': float(self.plunge_speed.get()),
            'thrust_v': float(self.thrust_speed.get()),
            'work_v': float(self.work_speed.get()),
            'plunge_v': float(self.plunge_speed.get()),
            'current_date': datetime.now().strftime("%a %b %d %Y %H:%M:%S"),
            'image_path': 'photo.png',
        }

        print(variables)

        with open('file.cnc', 'w') as f:
            f.write(get_gcode(variables))


root = tk.Tk()
root.geometry('500x400')  # Устанавливаем размер окна 600x400
root.resizable(True, True)  # Запрещаем изменение размера окна
root.title("CNC Hole CAM")

# Отладка интерфейса
if len(sys.argv) >= 2:
    if sys.argv[1] == '--build':
        from TkDeb.TkDeb import Debugger
        Debugger(root)

app = App(root)
app.pack(fill="both", expand=False)
root.mainloop()