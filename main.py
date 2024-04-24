from datetime import datetime
import re
import sys
from tkinter import Tk, ttk, TclError, filedialog, messagebox, Canvas, Frame, Scrollbar

from cnc_hole_lib import get_gcode


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

        ttk.Label(self.right_frame, text="Максимальный размер по X").pack()
        self.x_size = ttk.Entry(self.right_frame)
        self.x_size.insert(0, "100.0")
        self.x_size.pack()

        ttk.Label(self.right_frame, text="Максимальный размер по Y").pack()
        self.y_size = ttk.Entry(self.right_frame)
        self.y_size.insert(0, "100.0")
        self.y_size.pack()

        ttk.Label(self.right_frame, text="Выбор центра отсчёта").pack()
        self.zero_selector = ttk.Combobox(self.right_frame, values=["центр", "левый-верхний угол"])
        self.zero_selector.current(0)
        self.zero_selector.pack()

        ttk.Label(self.right_frame, text="Скорость холостого хода").pack()
        self.thrust_speed = ttk.Entry(self.right_frame)
        self.thrust_speed.insert(0, "500")
        self.thrust_speed.pack()

        ttk.Label(self.right_frame, text="Скорость работы").pack()
        self.work_speed = ttk.Entry(self.right_frame)
        self.work_speed.insert(0, "300")
        self.work_speed.pack()

        ttk.Label(self.right_frame, text="Скорость углубления").pack()
        self.plunge_speed = ttk.Entry(self.right_frame)
        self.plunge_speed.insert(0, "100")
        self.plunge_speed.pack()

        ttk.Label(self.right_frame, text="Шаг сверления").pack()
        self.plunge_step = ttk.Entry(self.right_frame)
        self.plunge_step.insert(0, "0.05")
        self.plunge_step.pack()

        ttk.Label(self.right_frame, text="Кол-во итераций сверления").pack()
        self.plunge_iterations = ttk.Entry(self.right_frame)
        self.plunge_iterations.insert(0, "4")
        self.plunge_iterations.pack()

        ttk.Label(self.right_frame, text="Высота подъёма между отверстиями").pack()
        self.lift_h = ttk.Entry(self.right_frame)
        self.lift_h.insert(0, "1.0")
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

    def on_holes_frame_configure(self, event):
        self.holes_canvas.configure(scrollregion=self.holes_canvas.bbox("all"))

    def clear_hole_widgets(self):
        for hole_widget in HoleWidget.hole_widgets:
            hole_widget: HoleWidget
            hole_widget.destroy()

        HoleWidget.hole_widgets.clear()

    # Обработчики событий
    def open_file(self):
        self.image_icon = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])

    def open_drl(self):
        drl_file_path = filedialog.askopenfilename(filetypes=[("DRL files", "*.drl")])

        if drl_file_path != '':
            self.clear_hole_widgets()

            holes = []
            pattern = re.compile(r'X(-?\d+)Y(-?\d+)')
            with open(drl_file_path, 'r') as f:
                lines = f.readlines()

                for line in lines:
                    match = pattern.search(line)
                    if match:
                        x = float(match.group(1)[:-3] + '.' + match.group(1)[-3:])
                        y = float(match.group(2)[:-3] + '.' + match.group(2)[-3:])
                        holes.append((x, y))

            print(holes)

            for hole in holes:
                self.add_hole_widget(hole[0], hole[1])

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

            variables = {
                'platform': self.platform_selector.get(),
                'holes_coords': holes_coords,
                'idling_h': 30.0,
                'X_size': x_size,
                'Y_size': y_size,
                'lift_h': float(self.lift_h.get()),
                'lowering_iters': int(self.plunge_iterations.get()),
                'depth_material': round(float(self.plunge_depth.get()),2),
                'plunge_step': round(float(self.plunge_step.get()),2),
                'thrust_v': float(self.thrust_speed.get()),
                'work_v': float(self.work_speed.get()),
                'plunge_v': float(self.plunge_speed.get()),
                'current_date': datetime.now().strftime("%a %b %d %Y %H:%M:%S"),
                'image_path': self.image_icon,
            }

            print(variables)

            with open(cnc_file_path, 'w') as f:
                f.write(get_gcode(variables))

            messagebox.showinfo("Файл создан", "Создан g-code по пути: " + cnc_file_path)


root = Tk()
root.geometry('500x500')  # Устанавливаем размер окна 600x400
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
