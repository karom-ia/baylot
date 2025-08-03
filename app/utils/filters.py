def get_flag(country_code):
    if not country_code or len(country_code) != 2:
        return ""
    return chr(127397 + ord(country_code.upper()[0])) + chr(127397 + ord(country_code.upper()[1]))
