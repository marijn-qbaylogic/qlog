# simple tool for converting old changelog files

import sys
import re
import os
import argparse

parser = argparse.ArgumentParser(prog="convert.py", description="Convert old changelog entries to new format.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-s","--save", action="store_true", dest="save", help="Save converted entries to ./changelog/entries")
parser.add_argument("-d","--delete", action="store_true", dest="delete", help="Delete old entries")
parser.add_argument("path", help="File or folder of files to convert")

args = parser.parse_args()

SAVE = args.save
DELETE = args.delete
todo = args.path



WHITE="\033[97m"
RED="\033[91m"
GREEN="\033[92m"
BLACK="\033[90m"
YELLOW="\033[93m"

if os.path.isdir(todo):
    files = [os.path.join(todo,x) for x in os.listdir(todo) if not x=="README.md" and not x.endswith(".py")]
else:
    files = [todo]

for file in files:
    print(BLACK+"-"*150)
    print(file)
    with open(file,"r") as fp:
        text = fp.read()
    text=text.strip()

    print(RED+text)

    if m:=re.match(r"([A-Z]+):\s*(.*)",text,re.DOTALL):
        cat,text = m.groups()
    else:
        cat = None
    
    if m:=re.match(r"(.*?)( See| Fixes)? \[#(\d+)\]\(.*\)\.?$",text,re.DOTALL):
        text,_,issue = m.groups()
    else:
        issue = None
    
    text=text.strip()

    try:
        result = subprocess.run(["qlog","gh","blame",path], check=True, capture_output=True)
    except Exception as e:
        print(WHITE+"Error fetching PRs:",RED+str(e))
        prs = []
    else:
        prs = [int(line.strip().split(":")[0]) for line in result.stdout.splitlines()[1:]]

    print(f"""{WHITE}Category: {YELLOW}{cat}
{WHITE}Issue: {YELLOW}{issue}
{WHITE}PRs: {prs}
{WHITE}Content:
{YELLOW}{text.strip()}
""")

    if not issue: issue = ""

    output = f"""---
issues: [{issue}]
prs: {prs}
---

# {cat}
{text}
"""

    print(GREEN+output)
    
    if DELETE:
        os.remove(file)

    if SAVE:
        file = os.path.basename(file)
        if not file.endswith(".md"):
            file+=".md"
        with open(os.path.join("changelog/entries",file),"w") as fp:
            fp.write(output)


