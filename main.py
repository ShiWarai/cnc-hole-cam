from datetime import datetime
import re
import sys
from tkinter import Tk, ttk, TclError, filedialog, messagebox, Canvas, Frame, Scrollbar, BooleanVar

from cnc_hole_lib import get_gcode


def find_key_by_value(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
    return None


def parse_holesizes(lines):
    pattern = re.compile(r'(T\d+)C(\d+\.\d+)')
    holesizes = {}

    for line in lines:
        match = pattern.search(line)
        if match:
            tool = match.group(1)
            size = float(match.group(2))
            holesizes[tool] = size

    return holesizes


class HoleWidget(ttk.Frame):

    hole_widgets = []

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ttk.Label(self, text="X:").grid(row=0, column=0)
        self.entry_x = ttk.Entry(self, width=6)
        self.entry_x.grid(row=0, column=1)

        ttk.Label(self, text="Y:").grid(row=0, column=2)
        self.entry_y = ttk.Entry(self, width=6)
        self.entry_y.grid(row=0, column=3)

        self.button_remove = ttk.Button(self, text="Удалить", command=self.remove_hole)
        self.button_remove.grid(row=0, column=4)

        HoleWidget.hole_widgets.append(self)

    def get_coordinates(self) -> list[float]:
        return [float(self.entry_x.get()), float(self.entry_y.get())]

    def remove_hole(self):
        HoleWidget.hole_widgets.remove(self)
        self.destroy()


class App(ttk.Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.left_frame = ttk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky="nsew")

        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        self.open_drl_button = ttk.Button(self.left_frame, text="Открыть .DRL", command=self.open_drl)
        self.open_drl_button.pack(side="top")

        self.button_clear = ttk.Button(self.left_frame, text="Очистить", command=self.clear_hole_widgets)
        self.button_clear.pack(side="bottom")

        self.button_add = ttk.Button(self.left_frame, text="Добавить отверстие", command=self.add_hole_widget)
        self.button_add.pack(side="bottom")

        self.holes_canvas = Canvas(self.left_frame, borderwidth=0, background="#ffffff")
        self.holes_frame = Frame(self.holes_canvas, background="#ffffff")
        self.holes_scrollbar = Scrollbar(self.left_frame, orient="vertical", command=self.holes_canvas.yview)
        self.holes_canvas.configure(yscrollcommand=self.holes_scrollbar.set)
        self.holes_scrollbar.pack(side="right", fill="y")
        self.holes_canvas.pack(side="left", fill="both", expand=True)
        self.holes_canvas.create_window((4, 4), window=self.holes_frame, anchor="nw")
        self.holes_frame.bind("<Configure>", self.on_holes_frame_configure)

        ttk.Label(self.right_frame, text="Выбор платформы").pack()
        self.platform_selector = ttk.Combobox(self.right_frame, values=["snapmaker",])
        self.platform_selector.current(0)
        self.platform_selector.pack()

        ttk.Label(self.right_frame, text="Выбор диаметра отверстий").pack()
        self.diameter_input = ttk.Entry(self.right_frame)
        self.diameter_input.insert(0, "1.0")
        self.diameter_input.pack()


        ttk.Label(self.right_frame, text="Максимальный размер по X").pack()
        self.x_size = ttk.Entry(self.right_frame)
        self.x_size.insert(0, "100.0")
        self.x_size.pack()

        ttk.Label(self.right_frame, text="Максимальный размер по Y").pack()
        self.y_size = ttk.Entry(self.right_frame)
        self.y_size.insert(0, "100.0")
        self.y_size.pack()

        ttk.Label(self.right_frame, text="Выбор конечного центра отсчёта").pack()
        self.zero_selector = ttk.Combobox(self.right_frame, values=["центр", "левый-верхний угол"])
        self.zero_selector.current(0)
        self.zero_selector.pack()

        ttk.Label(self.right_frame, text="Скорость холостого хода").pack()
        self.thrust_speed = ttk.Entry(self.right_frame)
        self.thrust_speed.insert(0, "500")
        self.thrust_speed.pack()

        ttk.Label(self.right_frame, text="Скорость работы").pack()
        self.work_speed = ttk.Entry(self.right_frame)
        self.work_speed.insert(0, "500")
        self.work_speed.pack()

        ttk.Label(self.right_frame, text="Скорость углубления").pack()
        self.plunge_speed = ttk.Entry(self.right_frame)
        self.plunge_speed.insert(0, "3")
        self.plunge_speed.pack()

        self.iterations_enabled_var = BooleanVar(value=False)
        self.iterations_enabled = ttk.Checkbutton(self.right_frame, text="Итеративное сверление", variable=self.iterations_enabled_var, command=self.toggle_entries)
        self.iterations_enabled.pack()

        ttk.Label(self.right_frame, text="Шаг сверления").pack()
        self.plunge_step = ttk.Entry(self.right_frame)
        self.plunge_step.insert(0, "0.05")
        self.plunge_step.pack()

        ttk.Label(self.right_frame, text="Кол-во итераций сверления").pack()
        self.lowering_iterations = ttk.Entry(self.right_frame)
        self.lowering_iterations.insert(0, "4")
        self.lowering_iterations.pack()

        ttk.Label(self.right_frame, text="Высота подъёма").pack()
        self.lift_h = ttk.Entry(self.right_frame)
        self.lift_h.insert(0, "0.5")
        self.lift_h.pack()

        ttk.Label(self.right_frame, text="Глубина материала").pack()
        self.plunge_depth = ttk.Entry(self.right_frame)
        self.plunge_depth.insert(0, "1.0")
        self.plunge_depth.pack()

        self.button_open_image = ttk.Button(self.right_frame, text="Выбрать изображение", command=self.open_file)
        self.button_open_image.pack()

        self.button_create_gcode = ttk.Button(self.right_frame, text="Создать gcode", command=self.create_gcode)
        self.button_create_gcode.pack()

        self.image_icon = ""
        self.toggle_entries()

    def on_holes_frame_configure(self, event):
        self.holes_canvas.configure(scrollregion=self.holes_canvas.bbox("all"))

    def clear_hole_widgets(self):
        for hole_widget in HoleWidget.hole_widgets:
            hole_widget: HoleWidget
            hole_widget.destroy()

        HoleWidget.hole_widgets.clear()
        self.diameter_input.state(['!disabled'])

    def toggle_entries(self):
        if self.iterations_enabled_var.get():
            self.plunge_step.state(['!disabled'])
            self.lowering_iterations.state(['!disabled'])
        else:
            self.plunge_step.state(['disabled'])
            self.lowering_iterations.state(['disabled'])

    # Обработчики событий
    def open_file(self):
        self.image_icon = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])

    def open_drl(self):
        drl_file_path = filedialog.askopenfilename(filetypes=[("DRL files", "*.drl")])

        if drl_file_path != '':
            self.clear_hole_widgets()

            with open(drl_file_path, 'r') as f:
                lines = f.readlines()

            holes_types = parse_holesizes(lines)

            pattern = re.compile(r'X(-?\d+)Y(-?\d+)')
            holes = {}

            current_tool = None
            for line in lines:
                if line.startswith('T'):
                    current_tool = line.strip()
                else:
                    match = pattern.search(line)
                    if match:
                        x = float(match.group(1)[:-3] + '.' + match.group(1)[-3:])
                        y = float(match.group(2)[:-3] + '.' + match.group(2)[-3:])

                        if current_tool in holes:
                            holes[current_tool].append((x, y))
                        else:
                            holes[current_tool] = [(x, y)]

            key = find_key_by_value(holes_types, float(self.diameter_input.get()))
            if key in holes:
                for hole in holes[key]:
                    self.add_hole_widget(hole[0], hole[1])

                self.diameter_input.state(['disabled'])

    def add_hole_widget(self, x=0.0, y=0.0) -> HoleWidget:
        hole_widget = HoleWidget(self.holes_frame)
        hole_widget.entry_x.insert(0, str(x))
        hole_widget.entry_y.insert(0, str(y))
        hole_widget.pack()

        return hole_widget

    def create_gcode(self):
        cnc_file_path = filedialog.asksaveasfilename(defaultextension=".cnc", filetypes=[("CNC files", "*.cnc")])

        if cnc_file_path != '':
            holes_coords = list()

            hole_id = 0
            zero_type = self.zero_selector.get()
            x_size = round(float(self.x_size.get()),2)
            y_size = round(float(self.y_size.get()),2)
            for widget in HoleWidget.hole_widgets:
                try:
                    xy = widget.get_coordinates()
                    hole_id += 1
                    if zero_type == 'центр':
                        holes_coords.append({'id': hole_id, 'X': round(xy[0]-x_size/2,2), 'Y': round(xy[1]+y_size/2,2)})
                    else:
                        holes_coords.append({'id': hole_id, 'X': round(xy[0],2), 'Y': round(xy[1],2)})

                except TclError:
                    pass

            if hole_id == 0:
                messagebox.showerror("Нет координат", "Координаты не указаны для создания g-code")

            if not bool(self.iterations_enabled_var.get()):
                plunge_step = round(float(self.plunge_depth.get()),2)
                lowering_iters = 1
            else:
                plunge_step = round(float(self.plunge_step.get()), 2)
                lowering_iters = int(self.lowering_iterations.get())

            variables = {
                'platform': self.platform_selector.get(),
                'holes_coords': holes_coords,
                'idling_h': 30.0,
                'X_size': x_size,
                'Y_size': y_size,
                'lift_h': float(self.lift_h.get()),
                'lowering_iters': lowering_iters,
                'depth_material': round(float(self.plunge_depth.get()),2),
                'plunge_step': plunge_step,
                'thrust_v': int(self.thrust_speed.get()),
                'work_v': int(self.work_speed.get()),
                'plunge_v': int(self.plunge_speed.get()),
                'current_date': datetime.now().strftime("%a %b %d %Y %H:%M:%S"),
                'image_path': self.image_icon,
            }

            print(variables)

            with open(cnc_file_path, 'w') as f:
                f.write(get_gcode(variables, optimize=True))

            messagebox.showinfo("Файл создан", "Создан g-code по пути: " + cnc_file_path)


root = Tk()
root.geometry('500x580')  # Устанавливаем размер окна 600x400
root.resizable(True, True)  # Запрещаем изменение размера окна
root.title("CNC Hole CAM")

# Отладка интерфейса
if len(sys.argv) >= 2:
    if sys.argv[1] == '--build':
        from third_party.TkDeb.TkDeb import Debugger

        Debugger(root)

app = App(root)
app.pack(fill="both", expand=False)
root.mainloop()
