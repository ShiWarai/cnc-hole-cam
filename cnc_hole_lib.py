from jinja2 import Environment, FileSystemLoader
from frange import frange

def get_gcode(args: dict) -> str:
    # Предварительная подготовка аргументов
    depth_steps_array = list(map(lambda x: round(x, 2), frange(args['depth_step'], args['depth_material']+args['depth_step'], args['depth_step'])))
    args['depth_steps_array'] = depth_steps_array

    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)
    template = env.get_template('base.j2')

    # Генерируем gcode с помощью шаблона
    gcode = template.render(args)

    # Добавляем конечное кол-во строк
    gcode = gcode.replace(";file_total_lines: 0", ";file_total_lines: " + str(gcode.count('\n')))

    return gcode