import re


def parse_code(code, lang="python"):
    pattern = rf"```{lang}\n(.*?)\n```"
    matches = re.findall(pattern, code, re.DOTALL)
    return matches[0] if matches else code
