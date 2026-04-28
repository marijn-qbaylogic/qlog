import re
import os
import sys
import time
import functools
import subprocess
import requests

import yaml
import json

from collections import defaultdict

from .util import *
from .config import *
from .entry import *

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
                if issues:
                    if not "n" in input(f"Confirm issues {issues} [Y/n]:").lower():
                        break
                else:
                    if "y" in input("Are you absolutely sure you do not want to link any issues? [y/N]:").lower():
                        break
    if cat is None:
        cat = "<category>"
        if interactive:
            available = sorted(list(DEFAULT_CATS.keys())+["CUSTOM"],key=lambda c: CATS[c]["rank"])
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

    timestamp = time.strftime(TIME_FORMAT)

    fname = ENTRY_FILENAME_FORMAT.format(title=title,time=timestamp,cat=cat,issues=issues)
    
    with open(os.path.join(ENTRY_DIR,fname),"w") as fp:
        fp.write(ENTRY_TEMPLATE.format(issues=issues,cat=cat,contents=contents))
        
    print(os.path.abspath(os.path.join(ENTRY_DIR,fname)))


def collect(version=None, date=None, delete=False, skip_on_error=False, out=None, prepend=None, append=None, insert=None):
    cat_names = {}
    cat_blobs = defaultdict(list)

    if version is None:
        version = "<version>"
    if date is None:
        date = time.strftime(DATE_FORMAT)

    entry_files = os.listdir(ENTRY_DIR)
    entry_files.sort()

    # collect entries from all files
    success=[]
    for fname in entry_files:
        path = os.path.join(ENTRY_DIR,fname)
        entry = Entry.open(path)
        
        if entry is None:
            continue

        for cats,blob in entry.parse():
            for cat_name,cat in cats:
                cat_names[cat] = cat_name
                cat_blobs[cat].append(blob)

        success.append(fname)

    if len(success)!=len(entry_files):
        if not skip_on_error:
            exit(1)

    # restore default names
    for cat in DEFAULT_CATS.keys():
        cat_names[cat] = DEFAULT_CATS[cat]["title"]

    # sort categories
    cat_blobs = list(cat_blobs.items())
    cat_blobs.sort(key=lambda c: CATS[c[0]]["rank"])

    # generate output

    res = [TITLE_FORMAT.format(version=version, date=date),""]
    
    for cat,blobs in cat_blobs:
        if len(blobs)>1 or CATS[cat]["itemize"] or not CATS[cat]["notitle"]:
            res.append(HEADER_FORMAT.format(cat = cat_names[cat]))
        if len(blobs)==1 and not CATS[cat]["itemize"]:
            res.append(blobs[0])
        else:
            res.extend([item(blob) for blob in blobs])
        res.append("")
        
    res = "\n".join(res).strip()+"\n"

    error = False
    if out is None and prepend is None and append is None and insert is None:
        print(res)
    else:
        if not out is None:
            try:
                with open(out,"w") as fp:
                    fp.write(out)
            except Exception as e:
                eprint(f"ERROR: Could not write file {out}: {e}")
                error = True
            else:
                eprint("Wrote to {out}")
        if not prepend is None:
            try:
                with open(prepend,"r") as fp:
                    txt = fp.read()
            except Exception as e:
                eprint(f"ERROR: Could not read file {prepend}: {e}")
                error = True
            else:
                try:
                    with open(prepend,"w") as fp:
                        fp.write(res+"\n"+txt)
                except Exception as e:
                    eprint(f"ERROR: Could not write file {prepend}: {e}")
                    error = True
                else:
                    eprint("Prepended to {prepend}")
        if not append is None:
            try:
                with open(append,"r") as fp:
                    txt = fp.read()
            except:
                eprint(f"ERROR: Could not read file {append}: {e}")
                error = True
            else:
                try:
                    with open(append,"w") as fp:
                        fp.write(txt+"\n"+res)
                except Exception as e:
                    eprint(f"ERROR: Could not write file {append}: {e}")
                    error = True
                else:
                    eprint("Appended to {append}")
        if not insert is None:
            try:
                with open(insert,"r") as fp:
                    txt = fp.read()
            except:
                eprint(f"ERROR: Could not read file {insert}: {e}")
                error = True
            else:
                m = re.search(INSERT_BEFORE_PATTERN,txt)
                if m:
                    i = m.span()[0]
                    txt = txt[:i]+res+"\n"+txt[i:]
                    try:
                        
                        with open(insert,"w") as fp:
                            fp.write(txt)
                    except Exception as e:
                        eprint(f"ERROR: Could not write file {insert}: {e}")
                        error = True
                    else:
                        eprint("Inserted into {insert}")
                else:
                    eprint("ERROR: Could not find insertion point")
                    error = True

    # delete only entries that were actually used and only if writing output was successful
    if delete:
        if error:
            eprint("Errors detected; not deleting entries")
        else:
            for fname in success:
                os.remove(os.path.join(ENTRY_DIR,fname))
            eprint("Deleted entries")
    


def check(paths = None, all=False):
    find_newest = not paths and not all
    if all or not paths:
        paths = [os.path.join(ENTRY_DIR,fname) for fname in sorted(os.listdir(ENTRY_DIR))]

    if find_newest:
        # get last edited
        if paths:
            paths = [min((os.path.getmtime(path),path) for path in paths)[1]]
        else:
            eprint("No entries to check")

    error = False
    for path in paths:
        eprint(f"Checking {path}")

        entry = Entry.open(path)
        if entry is None:
            error = True
            continue

        if not entry.issues:
            eprint("WARN: no linked issues")
            
    if error:
        exit(1)


def clean(delete = False):
    error = False
    
    entries = os.listdir(ENTRY_DIR)

    if delete:
        for fname in entries:
            try:
                os.remove(os.path.join(ENTRY_DIR,fname))
            except Exception as e:
                eprint(f"ERROR: Error deleting entry {fname}: {e}")
                error = True
            else:
                eprint(f"Deleted {fname}")
    elif entries:
        eprint("ERROR: There are still entries left; to delete them, use the --delete flag.")
        exit(1)

    if error:
        exit(1)
        
    eprint("All clean!")

def github(post_issues=False, post_prs=False, lst=False, version=None, out=None, exec_commands=False):
    error = False
    
    if not (post_issues or post_prs):
        eprint("Please indicate whether to look at issues (-i) or PRs (-p)")
        exit(1)

    # if the version is part of the message, make sure it's been supplied
    if not lst and version is None:
        try:
            if post_issues:
                GH_ISSUE_MESSAGE.format()
            if post_prs:
                GH_PR_MESSAGE.format()
        except KeyError as e:
            eprint(f"ERROR: Failed to render GitHub message (please provide the version number!): {repr(e)}")
            exit(1)

    entry_files = os.listdir(ENTRY_DIR)
    # collect all issues
    issues = []
    if post_issues:
        issues=set()

        success=0
        for fname in entry_files:
            path = os.path.join(ENTRY_DIR,fname)
            entry = Entry.open(path)
            
            if entry is None:
                continue

            issues=issues.union(entry.issues)
            success+=1
            
        issues=sorted(list(issues))
    
    # detect PRs
    prs = []
    if post_prs:
        prs = set()
        for fname in entry_files:
            try:
                result = subprocess.run(["git","blame","-l",os.path.join(ENTRY_DIR,fname)], check=True, capture_output=True)
            except Exception as e:
                eprint(f"ERROR: Failed to blame entry {fname}: {e}")
                exit(1)
            blame_lines = result.stdout.splitlines()

            for blame_line in blame_lines:
                commit = blame_line.split()[0].decode()
                if not (pr:=get_pr(commit)) is None:
                    prs.extend(pr)
        prs = sorted(list(prs))

    # only list pr/issue numbers that have been collected
    if lst:
        if not (version is None and out is None) or exec_commands:
            eprint("Ignoring other output options")
            
        if post_issues:
            print("Issues:", *issues)
        if post_prs:
            print("PRs:", *prs)

        return

    # generate commands
    commands = []
    if post_issues:
        message_string = json.dumps(GH_ISSUE_MESSAGE.format(version=version,project=PROJECT))
        for issue in issues:
            url = ISSUE_URL.format(issue=issue,project=PROJECT)
            cmd = GH_ISSUE_CMD.format(issue_url=url, message_string=message_string)
            commands.append(cmd)
    if post_prs:
        message_string = json.dumps(GH_PR_MESSAGE.format(version=version,project=PROJECT))
        for pr in prs:
            url = PR_URL.format(pr=pr,project=PROJECT)
            cmd = GH_PR_CMD.format(pr_url=url, message_string=message_string)
            commands.append(cmd)

    res = "\n".join(commands)+"\n"

    # store to file
    if out is None:
        print(res)
    else:
        try:
            with open(out,"w") as fp:
                fp.write(res)
        except Exception as e:
            eprint(f"ERROR: Failed to write {out}: {e}")
            error = True

    # execute commands
    if exec_commands:
        if error:
            eprint("Errors detected; not executing commands")
        else:
            for cmd in commands:
                if z:= os.system(cmd):
                    eprint(f"ERROR: Exit code {z} for command {cmd}")
                    error = True
        
    if error:
        exit(1)


def init():
    try:
        os.makedirs(CHANGELOG_DIR, exist_ok=True) # not really needed but might be nice
        os.makedirs(ENTRY_DIR, exist_ok=True)
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE,"w") as fp:
                fp.write("")
    except Exception as e:
        eprint(f"ERROR: Failed to create directories/config file: {e}")
        exit(1)
