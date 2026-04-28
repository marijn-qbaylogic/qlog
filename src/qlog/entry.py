
import re

from .util import *

class Entry:
    def __init__(self, path, contents, issues):
        self.path = path
        self.contents = contents
        self.issues = issues

    # open entry and return Entry if successful
    @staticmethod
    def open(path):
        # open file
        try:
            with open(path,"r") as fp:
                entry_text = fp.read()
        except:
            eprint(f"ERROR: Could not read file {path}")
            return

        # split into metadata and contents
        try:
            m = ENTRY_PATTERN.fullmatch(entry_text)
            meta = m.group(1)
            contents = m.group(2)
        except:
            eprint(f"ERROR: Could not find metadata section in {fname}")
            return
        
        # extract issues
        try:
            match yaml.load(meta,yaml.Loader):
                case {"issues": [*all_issues],**rest} if all(isinstance(issue, int) for issue in all_issues):
                    issues = all_issues
                case {"issues": int() as issue, **rest}:
                    issues = [issue]
                case {"issues": _, **rest}:
                    raise Exception("Invalid issue list")
                case {**rest}:
                    issues = []
                case None:
                    issues = []
                case _:
                    raise Exception("Invalid metadata format")
        except Exception as e:
            eprint(f"ERROR: {e} in {path}")
            return

        return Entry(path, contents, issues)

    def parse(self):
        issue_links = " ".join([MD_ISSUE_LINK.format(issue=issue, issue_url=ISSUE_URL.format(issue=issue,project=PROJECT)) for issue in self.issues])

        # split into sections
        
        sections = re.split(HEADER_PATTERN,self.contents)
        titles = [f"# {DEFAULT_CAT}",*re.findall(HEADER_PATTERN,self.contents)] #TODO: make configurable/defined elsewhere

        res = []
        for title,section in zip(titles,sections):
            section = section.strip()
            if not section:
                continue

            section+="\n"+issue_links
            
            cats = [cat.strip().rstrip(":") for cat in title[1:].split("|")] # TODO: make the [1:] more flexible? also see f"# ..." above
            res.append(([(cat,clean_string(cat)) for cat in cats], section))
        return res

    def check_order(self):
        ... #TODO: check that the order of the blobs matches the order of the sections?
