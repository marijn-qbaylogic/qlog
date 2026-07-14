import functools
import requests
import lxml.html

from .util import *
from .config import *


@functools.lru_cache(maxsize=None)
def get_issue_title(i):
    result = subprocess.run(C.GH_ISSUE_TITLE_CMD.format(issue=i, project=C.PROJECT), shell=True, capture_output=True)
    if result.returncode:
        err = result.stderr.decode().strip()
        error(err)
        return (err, "ERROR")
    else:
        title = result.stdout.decode().strip()
        ty,title = title.split(maxsplit=1)
        return (title, ty)

@functools.lru_cache(maxsize=None)
def get_pr(digest):
    html = requests.get(C.COMMIT_URL.format(project=C.PROJECT,commit=digest)).content
    try:
        doc = lxml.html.fromstring(html)
    except:
        prs = []
    else:
        prs = doc.cssselect(".pull-request > a")
        prs = tuple({int(pr.text.strip()[1:]) for pr in prs})
    if len(prs) == 1:
        return prs[0]
    elif len(prs) > 1:
        prs = ", ".join(str(pr) for pr in prs)
        eprint(f"Multiple PRs for {digest}: {prs}")
    else:
        eprint(f"No PR for {digest}")
