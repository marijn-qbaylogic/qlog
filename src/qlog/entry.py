
import re

from .util import *
from .config import *

class Entry:
    def __init__(self, path, contents, issues, prs):
        self.path = path
        self.contents = contents
        self.issues = issues
        self.prs = prs

    # open entry and return Entry if successful
    @staticmethod
    def open(path):
        # open file
        try:
            with open(path,"r") as fp:
                entry_text = fp.read()
        except:
            error(f"Could not read file {path}")
            return

        # split into metadata and contents
        try:
            m = ENTRY_PATTERN.fullmatch(entry_text)
            meta = m.group(1)
            contents = m.group(2)
        except Exception as e:
            error(f"Could not find metadata section in {path}: {e}")
            return
        
        # extract issues
        try:
            header = yaml.load(meta,yaml.Loader)

            match header:
                case {**rest}:
                    pass
                case None:
                    pass
                case _:
                    raise Exception("Invalid metadata format")

            # issues
            match header:
                case {"issues": [*all_issues],**rest} if all(isinstance(issue, int) for issue in all_issues):
                    issues = all_issues
                case {"issues": int() as issue, **rest}:
                    issues = [issue]
                case {"issues": _, **rest}:
                    raise Exception("Invalid issue list")
                case _:
                    issues = []
            
            # prs  
            match header:
                case {"prs": [*all_prs],**rest} if all(isinstance(pr, int) for pr in all_prs):
                    prs = all_prs
                case {"prs": int() as pr, **rest}:
                    prs = [pr]
                case {"prs": _, **rest}:
                    raise Exception("Invalid pr list")
                case _:
                    prs = []
        except Exception as e:
            error(f"{e} in {path}")
            return

        return Entry(path, contents, issues, prs)

    def parse(self,link_comments=False):
        links = " ".join([issue_link(C,issue,include_title=link_comments) for issue in self.issues] + 
                         [pr_link(C,pr,include_title=link_comments) for pr in self.prs])

        # split into sections
        
        sections = re.split(HEADER_PATTERN,self.contents)
        titles = [f"# {C.DEFAULT_CAT}",*re.findall(HEADER_PATTERN,self.contents)] #TODO: make configurable/defined elsewhere

        res = []
        for title,section in zip(titles,sections):
            section = section.strip()
            if not section:
                continue

            section+="\n"+links
            
            cats = [cat.strip().rstrip(":") for cat in title[1:].split("|")] # TODO: make the [1:] more flexible? also see f"# ..." above
            res.append(([(cat,clean_string(cat)) for cat in cats], section))
        return res

    def check_order(self):
        ... #TODO: check that the order of the blobs matches the order of the sections?
