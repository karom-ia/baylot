# app/utils/jinja.py
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

# Функция-флаг
def get_flag(country_code):
    if not country_code or len(country_code) != 2:
        return ""
    return chr(127397 + ord(country_code.upper()[0])) + chr(127397 + ord(country_code.upper()[1]))

# Регистрируем фильтр
templates.env.filters["get_flag"] = get_flag
