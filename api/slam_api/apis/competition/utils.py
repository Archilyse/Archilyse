def format_percents(percent):
    without_dot = str(percent).rstrip("0").rstrip(".")

    return round(percent, 2) if "." in without_dot else without_dot
