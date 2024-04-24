import base64
import os, sys
from jinja2 import Environment, FileSystemLoader
from frange import frange


def resource_path(relative_path: str) -> str:
    """ Получить абсолютный путь к ресурсу, работает для dev и для PyInstaller """
    try:
        # PyInstaller создает временную папку и сохраняет путь в переменной _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_gcode(args: dict) -> str:
    # Предварительная подготовка аргументов
    depth_steps_array = list(map(lambda x: round(x, 2), frange(args['plunge_step'], args['depth_material'] + args['plunge_step'], args['plunge_step'])))

    if args['image_path'] != "":
        # Чтения файла иконки
        with open(args['image_path'], 'rb') as f:
            image_bytes = f.read()
        img_str = ";thumbnail: data:image/png;base64," + base64.b64encode(image_bytes).decode()

    args['max_x'] = max(args['holes_coords'], key=lambda x: x['X'])['X']
    args['max_y'] = max(args['holes_coords'], key=lambda x: x['Y'])['Y']
    args['max_z'] = args['idling_h']
    args['min_x'] = min(args['holes_coords'], key=lambda x: x['X'])['X']
    args['min_y'] = min(args['holes_coords'], key=lambda x: x['Y'])['Y']
    args['min_z'] = -args['depth_material']
    try:
        args['thumbnail_image'] = img_str
    except NameError:
        args['thumbnail_image'] = ''
    args['depth_steps_array'] = depth_steps_array

    # Загрузка шаблонов
    file_loader = FileSystemLoader(resource_path("templates"))
    env = Environment(loader=file_loader)
    template = env.get_template('base.j2')

    # Генерируем gcode с помощью шаблона
    gcode = template.render(args)

    # Добавляем конечное кол-во строк
    gcode = gcode.replace(";file_total_lines: 0", ";file_total_lines: " + str(gcode.count('\n') + 1))

    return gcode
