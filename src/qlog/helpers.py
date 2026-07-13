
from .util import *
from .config import *
from .github import *
from .entry import *

# get entries ignoring .gitkeep etc
def get_entries():
    return sorted([e for e in os.listdir(ENTRY_DIR) if not e.startswith(".")])

# run a function on each entry and return a map of results
def map_entries(f):
    res = {}
    for fname in get_entries():
        path = os.path.join(ENTRY_DIR,fname)
        entry = Entry.open(path)
        
        if entry is None:
            continue

        res[fname] = f(fname,entry)
    return res


def issue_link(issue, include_title=False):
    link = C.MD_ISSUE_LINK.format(issue=issue, issue_url=C.ISSUE_URL.format(issue=issue,project=C.PROJECT))
    if include_title:
        (title,_) = get_issue_title(issue)
        link += f" <!-- {title} -->"
    return link


def github_get(fname,entry,get_issues=False, get_prs=False,get_titles=False):
    res = {}
    if get_issues:
        res["issues"] = [(i, get_issue_title(i)[0] if get_titles else None) for i in entry.issues]
    if get_prs:
        prs = set()

        try:
            result = subprocess.run(["git","blame","-l",os.path.join(ENTRY_DIR,fname)], check=True, capture_output=True)
        except Exception as e:
            error(f"Failed to blame entry {fname}: {e}")
        else:
            blame_lines = result.stdout.splitlines()

            for blame_line in blame_lines:
                commit = blame_line.split()[0].decode()
                if not (pr:=get_pr(commit)) is None:
                    prs.add((pr,get_issue_title(pr)[0] if get_titles else None))
        res["prs"] = sorted(list(prs))
    return res
    