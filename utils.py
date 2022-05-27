import re
from datetime import datetime

def to_lowercase(input):
    return input.lower()

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%I:%S")

def build_intl_phone_number( number, ton ):

    ret = number
    country_prefix = "996"
    m = re.match(r'^0(\d{3,3})(\d{6,6})$', str(number))

    if str(ton) == "161" and m:
        # remove leading '0' and add country prefix
        ret = country_prefix + m.group(1) + m.group(2)

    return ret
