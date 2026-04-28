
import os
import re
import yaml
from collections import defaultdict

from .util import *

### fixed SETTINGS
CHANGELOG_DIR = "changelog"
ENTRY_DIR = os.path.join(CHANGELOG_DIR,"entries")

ENTRY_PATTERN = re.compile(r"\s*^\-\-\-\n(.*)^\-\-\-\n(.*)", re.MULTILINE | re.DOTALL)
HEADER_PATTERN = re.compile(r"^#[^#].*$", re.MULTILINE)

CONFIG_FILE = os.path.join(CHANGELOG_DIR,"config.yaml")

ENTRY_TEMPLATE = """
---
issues: {issues}
---

# {cat}
{contents}
""".lstrip() # util, cat, contents

### configurable SETTINGS
try:
    with open(CONFIG_FILE,"r") as fp:
        CONFIG = yaml.load(fp,yaml.Loader)
except Exception as e:
    eprint(f"ERROR: Could not open config file {CONFIG_FILE} (consider running 'changelog init'): {e}")
    config_found = False
else:
    config_found = True

    def key(k,*vars, d=None):
        try:
            v = CONFIG[k]
        except:
            if d is None:
                eprint(f"ERROR: Could not find key '{k}'")
                exit(1)
            return d
        
        try:
            v+""
        except:
            eprint(f"ERROR: Value for '{k}' must be string")
            exit(1)
            
        try:
            v.format({v:"" for v in vars})
        except Exception as e:
            eprint(f"ERROR: Value for '{k}' could not be formatted using {vars}: {e}")
            exit(1)

        return v

    def get_typed(d,k,dflt,t):
        x = d.get(k,dflt)
        if type(x)!=t:
            eprint(f"ERROR: Key '{k}' must be of type {t}")
            exit(1)
        return x

    PROJECT = key("project")

    ISSUE_URL  = key("issue_url","project","issue",d="https://github.com/{project}/issues/{issue}") # project, issue
    PR_URL     = key("pr_url"   ,"project","pr"   ,d="https://github.com/{project}/pull/{pr}") # project, pr
    COMMIT_URL = key("commit_url","project","commit",d="https://github.com/{project}/branch_commits/{commit}") # project, commit

    MD_ISSUE_LINK = key("md_issue_link","issue","issue_url",d="[#{issue}]({issue_url})") # issue, issue_url

    GH_ISSUE_MESSAGE = key("gh_issue_message","project","version",d="We've released [v{version}](https://github.com/{project}/releases/tag/v{version}), which includes a fix for this issue.") # version, project
    GH_PR_MESSAGE    = key("gh_pr_message"   ,"project","version",d="We've released [v{version}](https://github.com/{project}/releases/tag/v{version}), which includes this PR.") # version, project

    GH_ISSUE_CMD = key("gh_issue_cmd","issue","issue_url","message_string",d="gh issue comment {issue_url} -b {message_string}") # issue, issue_url, message_string
    GH_PR_CMD    = key("gh_pr_cmd"   ,"pr"   ,"pr_url"   ,"message_string",d="gh pr comment {pr_url} -b {message_string}") # pr, pr_url, message_string

    try:
        dc = CONFIG["default_cats"]
    except:
        DEFAULT_CATS = {
            "HIGHLIGHT":    dict(title="Highlights" ,rank=-1,itemize=False,notitle=True), # if there's only one entry, do not itemize, and remove the "Highlights" title
            "ADDED":        dict(title="Added"      ,rank= 1,itemize=True),
            "CHANGED":      dict(title="Changes"    ,rank= 2,itemize=True),
            "FIXED":        dict(title="Fixes"      ,rank= 3,itemize=True),
            "DEPRICATED":   dict(title="Depricated" ,rank= 4,itemize=True),
            "REMOVED":      dict(title="Removed"    ,rank= 5,itemize=True),
        }
    else:
        assertt(typeof(dc)==dict,"ERROR: 'default_cats' must be a dictionary")
        DEFAULT_CATS = {}
        for cat in dc.keys():
            assertt(typeof(dc[cat])==dict,f"ERROR: default category '{cat}' must be a dictionary")
            DEFAULT_CATS[clean_string(cat)] = dict(
                title  =get_typed(dc[cat],"title"  ,cat  ,str),
                rank   =get_typed(dc[cat],"rank"   ,100  ,int),
                itemize=get_typed(dc[cat],"itemize",True ,bool),
                notitle=get_typed(dc[cat],"notitle",False,bool),
            )
    CATS = defaultdict(lambda: dict(rank=0,itemize=False,notitle=False),DEFAULT_CATS)

    DEFAULT_CAT = key("default_cat",d="HIGHLIGHT")
    if not DEFAULT_CAT in DEFAULT_CATS.keys():
        eprint(f"ERROR: Default category {DEFAULT_CAT} does not exist.")
        exit(1)

    TIME_FORMAT = key("time_format",d="%Y-%M-%d_T%H:%M:%S") # use standard strftime parameters

    ENTRY_FILENAME_FORMAT = key("entry_filename_format","time","title",d="{time}_{title}.md") # time, title

    DATE_FORMAT = key("date_format",d="%d %b, %Y") # use standard strftime parameters
    TITLE_FORMAT = key("title_format","version","date",d="## {version} - *{date}*") # version, date

    HEADER_FORMAT = key("cat_header_format","cat",d="### {cat}:") # cat

    INSERT_BEFORE_PATTERN = key("insert_before_pattern",d=r"^##[^#]")
