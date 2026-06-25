
import sys
import re
import os
import unicodedata
import subprocess

WORKING_DIR = os.getcwd()

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

# get entries ignoring .gitkeep etc
def get_entries(ENTRY_DIR):
    return [e for e in os.listdir(ENTRY_DIR) if not e.startswith(".")]

# find a git repo root dir
def root_dir(CONFIG_FILE):
    # try finding the config locally first
    if os.path.exists(CONFIG_FILE):
        return
    # else, try the git root dir
    result = subprocess.run("git rev-parse --show-toplevel".split(), capture_output=True)
    if result.returncode:
        pass
    else:
        git_root = result.stdout.decode().strip()
        if os.path.exists(os.path.join(git_root,CONFIG_FILE)):
            os.chdir(git_root)

ISSUE_TITLES = {}
def issue_link(C, issue, include_title=False):
    link = C.MD_ISSUE_LINK.format(issue=issue, issue_url=C.ISSUE_URL.format(issue=issue,project=C.PROJECT))
    if include_title:
        if not issue in ISSUE_TITLES:
            result = subprocess.run(C.GH_ISSUE_TITLE_CMD.format(issue=issue), shell=True, capture_output=True)
            if result.returncode:
                ISSUE_TITLES[issue] = result.stderr.decode().strip()
            else:
                ISSUE_TITLES[issue] = result.stdout.decode().strip()
        link += f" <!-- {ISSUE_TITLES[issue]} -->"
    return link
