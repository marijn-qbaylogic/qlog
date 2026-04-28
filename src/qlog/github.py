
import requests
import lxml

from .util import *
from .config import *

@functools.lru_cache(maxsize=None)
def get_pr(digest):
    html = requests.get(COMMIT_URL.format(project=PROJECT,commit=digest)).content
    doc = lxml.html.fromstring(html)
    prs = doc.cssselect(".pull-request > a")
    prs = tuple({int(pr.text.strip()[1:]) for pr in prs})
    if len(prs) == 1:
        return prs[0]
    elif len(prs) > 1:
        prs = ", ".join(str(pr) for pr in prs)
        eprint(f"Multiple PRs for {digest}: {prs}")
    else:
        eprint(f"No PR for {digest}")
