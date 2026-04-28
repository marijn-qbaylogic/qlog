
import sys
import re
import unicodedata

# print to stderr
def eprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

# remove special characters, make upper case (a tad overkill, but it works well)
def clean_string(s):
    return re.sub(r"\W+","",
                  unicodedata.normalize("NFD",s)
                     .encode("ascii","ignore")
                     .decode("utf-8")
                     .upper().replace("-","_")
                     .replace(" ","_")
                     .replace("\n","_")
                  ).strip("_").replace("__","_").replace("__","_")

# custom assert
def assertt(cond,msg):
    if not cond:
        eprint(msg)
        exit(1)

# indent with a leading dash and no spaces on newlines, and no trailing newline
def item(b):
    return "- " + re.sub(r"^\s+$", "", b.replace("\n","\n  "), re.MULTILINE).rstrip()
