
import datetime
import pytz

def format_date(date):
    time_values = {
        "seconds": ("minutes", 60),
        "minutes": ("hours", 60),
        "hours": ("days", 24),
        "days": ("months", 30),
        "months": ("years", 12),
        "years": ("centuries", 100),
    }
    seconds = (datetime.datetime.now(pytz.UTC) - date.replace(tzinfo=pytz.UTC)).total_seconds()
    info = {"seconds": seconds}
    for label, time_value in time_values.items():
        if info[label] >= time_value[1]:
            info[time_value[0]] = info[label] // time_value[1]
            info[label] %= time_value[1]
        else:
            break

    used_info = list(info.keys())[-2:]
    used_info.reverse()

    return " ".join(f"{int(info[label])} {label}" for label in used_info)

