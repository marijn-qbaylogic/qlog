
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

def pr_link(pr, include_title=False):
    link = C.MD_PR_LINK.format(pr=pr, pr_url=C.PR_URL.format(pr=pr,project=C.PROJECT))
    if include_title:
        (title,_) = get_issue_title(issue)
        link += f" <!-- {title} -->"
    return link


def github_get(fname,entry,get_issues=False, get_prs=False,get_titles=False):
    res = {}
    def mustbe(ty,ty2):
        if ty==ty2:
            return ""
        error(f"{ty} listed as {ty2}")
        return f"[{ty}] "

    if get_issues:
        res["issues"] = [(i, mustbe(get_issue_title(i)[1],"ISSUE") + get_issue_title(i)[0] if get_titles else None) for i in entry.issues]
    if get_prs:
        res["prs"] = [(p, mustbe(get_issue_title(i)[1],"PR") + get_issue_title(p)[0] if get_titles else None) for p in entry.prs]
    return res


def check_links(entry):
    if bool(entry.issues or entry.prs) == entry.no_links:
        if entry.no_links:
            error("No links flag set while issues/PRs were linked")
        else:
            error("No issues/PRs linked without explicitly setting no-links flag")

def check_link_types(entry):
    for i in entry.issues:
        match get_issue_title(i):
            case (title,"PR"):
                error(f"Linked issues {i} is actually a PR")

    for p in entry.prs:
        match get_issue_title(p):
            case (title,"ISSUE"):
                error(f"Linked PR {p} is actually a normal issue")
