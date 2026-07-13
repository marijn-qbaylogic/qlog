import re
import os
import sys
import time
import subprocess
import requests

import yaml
import json

from collections import defaultdict

from .util import *
from .config import *
from .entry import *
from .github import *
from .helpers import *

def make_entry(title=None, issues=None, cat=None, contents=None, interactive=True):
    if title is None:
        title="<title>"
        if interactive:
            while True:
                title = input("Title (used for file name): ")
                title = clean_string(title).lower()
                if not "n" in input(f"Confirm title \"{title}\" [Y/n]: ").lower():
                    break

    if issues is None:
        issues = []
        if interactive:
            while True:
                issues = input("Related issues: ")
                issues = [int(i) for i in re.split(r"[\s,;]+",issues) if i.isnumeric()]
                eprint(f"Issues: {issues}")
                if issues:
                    issues_ok = True
                    for i in issues:
                        eprint(f"{i}: ",end="")
                        (t,r) = get_issue_title(i)
                        issues_ok = issues_ok and r
                        eprint(t)

                    if issues_ok:
                        if not "n" in input("Confirm issues [Y/n]:").lower():
                            break
                    else:
                        if "y" in input(f"Are you absolutely sure you want to keep the issue list as-is? [y/N]: ").lower():
                            break
                else:
                    if "y" in input("Are you absolutely sure you do not want to link any issues? [y/N]: ").lower():
                        break

    if cat is None:
        cat = "<category>"
        if interactive:
            available = sorted(list(C.DEFAULT_CATS.keys())+["CUSTOM"],key=lambda c: C.CATS[c]["rank"])
            cats = "/".join(f"{i}:{available[i]}" for i in range(len(available)))
            while True:
                cat = input(f"Category ({cats}): ").upper()
                try:
                    i = int(cat)
                except:
                    # find as string
                    for c in available:
                        if c.startswith(cat):
                            cat=c
                            break
                    else:
                        eprint("Invalid category - did you mean to create a CUSTOM category?")
                        continue
                else:
                    # find by index
                    try:
                        cat = available[i]
                    except IndexError:
                        eprint("Invalid index")
                        continue
                    
                if cat == "CUSTOM":
                    cat = input("Enter category title: ")
                if not "n" in input(f"Confirm category {cat} [Y/n]: "):
                    break

    if contents is None:
        contents = "<contents>"
        if interactive:
            N=3
            line = input(f"Enter contents\nTo enter multiple lines, enter an empty line, then terminate with {N} empty lines\n> ")
            if line:
                contents = line
            else:
                lines = []
                while lines[-N:] != [""]*N:
                    lines.append(input("> "))
                contents = "\n".join(lines[:-N])

    timestamp = time.strftime(C.TIME_FORMAT)

    fname = C.ENTRY_FILENAME_FORMAT.format(title=title,time=timestamp,cat=cat,issues=issues)
    
    with open(os.path.join(ENTRY_DIR,fname),"w") as fp:
        fp.write(ENTRY_TEMPLATE.format(issues=issues,cat=cat,contents=contents))
        
    print(os.path.abspath(os.path.join(ENTRY_DIR,fname)))


def collect(version=None, date=None, delete=False, skip_on_error=False, issue_comments=False, out=None, prepend=None, append=None, insert=None):
    cat_names = {}
    cat_blobs = defaultdict(list)

    if version is None:
        version = "<version>"
        warn("Version not supplied! Replace the title placeholder manually.")
    if date is None:
        date = time.strftime(C.DATE_FORMAT)

    entry_files = get_entries()

    # collect entries from all files
    success=[]
    for fname in entry_files:
        path = os.path.join(ENTRY_DIR,fname)
        entry = Entry.open(path)
        
        if entry is None:
            continue

        for cats,blob in entry.parse(issue_comments):
            for cat_name,cat in cats:
                cat_names[cat] = cat_name
                cat_blobs[cat].append(blob)

        success.append(fname)

    if len(success)!=len(entry_files):
        if not skip_on_error:
            exit(1)

    # restore default names
    for cat in C.DEFAULT_CATS.keys():
        cat_names[cat] = C.DEFAULT_CATS[cat]["title"]

    # sort categories
    cat_blobs = list(cat_blobs.items())
    cat_blobs.sort(key=lambda c: C.CATS[c[0]]["rank"])

    # generate output

    res = [C.TITLE_FORMAT.format(version=version, date=date),""]
    
    for cat,blobs in cat_blobs:
        if len(blobs)>1 or C.CATS[cat]["itemize"] or not C.CATS[cat]["notitle"]:
            res.append(C.HEADER_FORMAT.format(cat = cat_names[cat]))
        if len(blobs)==1 and not C.CATS[cat]["itemize"]:
            res.append(blobs[0])
        else:
            res.extend([item(blob) for blob in blobs])
        res.append("")
        
    res = "\n".join(res).strip()+"\n"

    if out is None and prepend is None and append is None and insert is None:
        print(res)
    else:
        if not out is None:
            out = os.path.join(WORKING_DIR,out)
            try:
                with open(out,"w") as fp:
                    fp.write(res)
            except Exception as e:
                error(f"Could not write file {out}: {e}")
            else:
                eprint(f"Wrote to {out}")
        if not prepend is None:
            prepend = os.path.join(WORKING_DIR,prepend)
            try:
                with open(prepend,"r") as fp:
                    txt = fp.read()
            except Exception as e:
                error(f"Could not read file {prepend}: {e}")
            else:
                try:
                    with open(prepend,"w") as fp:
                        fp.write(res+"\n"+txt)
                except Exception as e:
                    error(f"Could not write file {prepend}: {e}")
                else:
                    eprint(f"Prepended to {prepend}")
        if not append is None:
            append = os.path.join(WORKING_DIR,append)
            try:
                with open(append,"r") as fp:
                    txt = fp.read()
            except:
                error(f"Could not read file {append}: {e}")
            else:
                try:
                    with open(append,"w") as fp:
                        fp.write(txt+"\n"+res)
                except Exception as e:
                    error(f"Could not write file {append}: {e}")
                else:
                    eprint(f"Appended to {append}")
        if not insert is None:
            insert = os.path.join(WORKING_DIR,insert)
            try:
                with open(insert,"r") as fp:
                    txt = fp.read()
            except:
                error(f"Could not read file {insert}: {e}")
            else:
                m = re.search(C.INSERT_BEFORE_PATTERN,txt,re.MULTILINE)
                if m:
                    i = m.span()[0]
                    txt = txt[:i]+res+"\n"+txt[i:]
                    try:
                        
                        with open(insert,"w") as fp:
                            fp.write(txt)
                    except Exception as e:
                        error(f"Could not write file {insert}: {e}")
                    else:
                        eprint(f"Inserted into {insert}")
                else:
                    error("Could not find insertion point")

    # delete only entries that were actually used and only if writing output was successful
    if delete:
        if has_failed():
            eprint("Errors detected; not deleting entries")
        else:
            for fname in success:
                os.remove(os.path.join(ENTRY_DIR,fname))
            eprint("Deleted entries")
    


def check(paths = None, all=False):
    find_newest = not paths and not all
    if all or not paths:
        paths = [os.path.join(ENTRY_DIR,fname) for fname in get_entries()]

    if find_newest:
        # get last edited
        if paths:
            # print([(os.path.getmtime(path),path) for path in paths])
            paths = [max((os.path.getmtime(path),path) for path in paths)[1]]
        else:
            eprint("No entries to check")

    for path in paths:
        eprint(f"Checking {path}")

        entry = Entry.open(path)
        if entry is None:
            continue

        if not entry.issues:
            warn("no linked issues")
            
    if has_failed():
        exit(1)


def clean(delete = False):
    entries = get_entries()

    if delete:
        for fname in entries:
            try:
                os.remove(os.path.join(ENTRY_DIR,fname))
            except Exception as e:
                error(f"Error deleting entry {fname}: {e}")
            else:
                eprint(f"Deleted {fname}")
    elif entries:
        error("There are still entries left; to delete them, use the --delete flag.")
        exit(1)

    if has_failed():
        exit(1)
        
    eprint("All clean!")



def github_list(post_issues=False, post_prs=False, per_entry=False, include_titles=False):
    if not (post_issues or post_prs):
        eprint("Please indicate whether to look at issues (-i) or PRs (-p)")
        exit(1)
    # only list pr/issue numbers that have been collected

    data = map_entries(lambda fname,entry: github_get(fname,entry,get_issues=post_issues,get_prs=post_prs,get_titles=include_titles))

    # print a simple list, or list of titles
    def print_set(issues,prs):
        if include_titles:
            if post_issues:
                print("Issues:")
                for (i,t) in issues:
                    print(f"  {i}: {t}")
            if post_prs:
                print("PRs:")
                for (p,t) in prs:
                    print(f"  {p}: {t}")
        else:
            if post_issues:
                print("Issues:", *[i for (i,_) in issues])
            if post_prs:
                print("PRs:", *[p for (p,_) in prs])

    # print per entry or aggregate
    if per_entry:
        for e in data:
            print(e)
            print_set(data[e].get("issues"),data[e].get("prs"))
    else:
        issues=set()
        prs=set()
        if post_issues:
            for d in data.values():
                for i in d["issues"]:
                    issues.add(i)
        if post_prs:
            for d in data.values():
                for p in d["prs"]:
                    prs.add(p)

        issues = sorted(list(issues))
        prs = sorted(list(prs))
        print_set(issues,prs)


def github_msg(post_issues=False, post_prs=False, version=None, out=None, exec_commands=False, include_titles=False):
    if not (post_issues or post_prs):
        eprint("Please indicate whether to look at issues (-i) or PRs (-p)")
        exit(1)

    # if the version is part of the message, make sure it's been supplied
    if version is None:
        try:
            if post_issues:
                C.GH_ISSUE_MESSAGE.format()
            if post_prs:
                C.GH_PR_MESSAGE.format()
        except KeyError as e:
            error(f"Failed to render GitHub message (please provide the version number!): {repr(e)}")
            exit(1)

    data = map_entries(lambda fname,entry: github_get(fname,entry,get_issues=post_issues,get_prs=post_prs))

    # collect all issues
    issues = []
    if post_issues:
        issues=set()
        for d in data.values():
            for i in d["issues"]:
                issues.add(i)
        issues=sorted(list(issues))
    
    # detect PRs
    prs = []
    if post_prs:
        prs = set()
        for d in data.values():
            for p in d["prs"]:
                prs.add(p)
        prs = sorted(list(prs))

    # generate commands
    commands = []
    if post_issues:
        message_string = json.dumps(C.GH_ISSUE_MESSAGE.format(version=version,project=C.PROJECT))
        for (issue,title) in issues:
            if include_titles:
                commands.append(f"# {title}")
            url = C.ISSUE_URL.format(issue=issue,project=C.PROJECT)
            cmd = C.GH_ISSUE_CMD.format(issue_url=url, message_string=message_string)
            commands.append(cmd)
    if post_prs:
        message_string = json.dumps(C.GH_PR_MESSAGE.format(version=version,project=C.PROJECT))
        for (pr,title) in prs:
            if include_titles:
                commands.append(f"# {title}")
            url = C.PR_URL.format(pr=pr,project=C.PROJECT)
            cmd = C.GH_PR_CMD.format(pr_url=url, message_string=message_string)
            commands.append(cmd)

    res = "\n".join(commands)+"\n"

    # store to file
    if out is None:
        print(res)
    else:
        out = os.path.join(WORKING_DIR,out)
        try:
            with open(out,"w") as fp:
                fp.write(res)
        except Exception as e:
            error(f"Failed to write {out}: {e}")

    # execute commands
    if exec_commands:
        if has_failed():
            eprint("Errors detected; not executing commands")
        else:
            for cmd in commands:
                if z:= os.system(cmd):
                    error(f"Exit code {z} for command {cmd}")
        
    if has_failed():
        exit(1)


def init():
    try:
        # try to get project github link
        project = "???/???"
        result = subprocess.run("git config --get remote.origin.url".split(), capture_output=True)
        try:
            if result.returncode:
                raise Exception
            repo = result.stdout.decode().strip()
            if repo.startswith("git@github.com:") and repo.endswith(".git"):
                project = repo.split(":",1)[1].rsplit(".",1)[0]
            else:
                raise Exception(repr(repo)+" "+str(result))
        except Exception as e:
            eprint(f"Could not detect github repo to use in config file: {e}")

        # make dirs
        os.makedirs(CHANGELOG_DIR, exist_ok=True) # not really needed but might be nice
        os.makedirs(ENTRY_DIR, exist_ok=True)

        # make config
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE,"w") as fp:
                print(f'project: "{project}"', file=fp)

        # add a .gitkeep file to the entries dir so it never removed by git
        GITKEEP = os.path.join(ENTRY_DIR,".gitkeep")
        if not os.path.exists(GITKEEP):
            with open(GITKEEP,"w") as fp:
                fp.write("")
    except Exception as e:
        error(f"Failed to create directories/files: {e}")
        exit(1)
