
import argparse, pathlib

from .util import *
from .config import config_found
from .qlog import make_entry, collect, check, clean, github, init

class App:
    def __init__(self):
        PROG = "qlog"
        
        DESCRIPTION_ENTRY=f"""
    Create a changelog entry.

    Note that by editing the file, you can do a little more:
    - You can create multiple entries in different categories in a single file,
    by simply adding multiple `# <category>` sections.
    - You can make an entry show up in multiple sections using pipes:
    `# <cat1>|<cat2>|...`

    Upon creation, the program returns the file name, which you can pipe you your favorite editor directly:
    > nano $({PROG} entry -I -t "my entry")
    """.strip()


        parser = argparse.ArgumentParser(prog=PROG, description="Changelog management tool.\nSee subcommand help for more information.", formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(dest="command")

        parser_entry = subparsers.add_parser("entry", help="create an entry", description=DESCRIPTION_ENTRY, formatter_class=argparse.RawTextHelpFormatter)
        parser_entry.add_argument("-t","--title"            , type=str                                  , help="title to use")
        parser_entry.add_argument("-i","--issue"            , type=int, nargs="+"                       , help="add issue number")
        parser_entry.add_argument("-c","--cat"              , type=str                                  , help="entry category")
        parser_entry.add_argument("-C","--content"          , type=str                                  , help="entry content")
        parser_entry.add_argument("-I","--no-interactive"   , action="store_false", dest="interactive"  , help="do not run interactive script to fill in missing info")

        parser_collect = subparsers.add_parser("collect", help="collect entries together", description="Collect all entries together.")
        parser_collect.add_argument("-v","--version"        , type=str              , help="a version to use as the title")
        parser_collect.add_argument("-d","--date"           , type=str              , help="the date to use in the title")
        parser_collect.add_argument("-D","--delete"         , action="store_true"   , help="delete entries afterwards if successful")
        parser_collect.add_argument("-e","--skip-on-error"  , action="store_true"   , help="skip entries that yield errors")
        parser_collect.add_argument("-o","--out"            , type=pathlib.Path     , help="file to write output to")
        parser_collect.add_argument("-p","--prepend"        , type=pathlib.Path     , help="file to prepend output to")
        parser_collect.add_argument("-a","--append"         , type=pathlib.Path     , help="file to append output to")
        parser_collect.add_argument("-i","--insert"         , type=pathlib.Path     , help="file to insert output into, based on settings")
        #TODO: add a way to include only select files?

        parser_check = subparsers.add_parser("check", help="check if an entry is correct", description="Check one or more entries for errors.")
        parser_check.add_argument("path"        , nargs="*", type=pathlib.Path  , help="entry to check; defaults to last edited")
        parser_check.add_argument("-a","--all"  , action="store_true"           , help="check all entries")

        parser_clean = subparsers.add_parser("clean", help="clean up entries, or check all entries have been collected", description="Make sure all entries have been removed." )
        parser_clean.add_argument("-D","--delete", action="store_true", help="delete remaining entries; if this flag is not specified, the program will error if any entries are left")

        parser_github = subparsers.add_parser("gh", help="post release messages on GitHub", description="Generate GitHub CLI commands to post to all issues combined in this changelog.")
        parser_github.add_argument("-i","--issues"  , action="store_true"   , help="send messages to issues")
        parser_github.add_argument("-p","--prs"     , action="store_true"   , help="send messages to PRs")
        parser_github.add_argument("-l","--list"    , action="store_true"   , help="do not produce messages; just list the issues/prs that would be affected")
        parser_github.add_argument("-v","--version" , type=str              , help="a version to use in the message")
        parser_github.add_argument("-o","--out"     , type=pathlib.Path     , help="output commands to file")
        parser_github.add_argument("-x","--exec"    , action="store_true"   , help="execute generated commands; fails if version is not specified but required for messages")

        parser_init = subparsers.add_parser("init", help="initialise the right directories; does nothing to existing files")

        self.parser = parser
    
    def run(self):
        args = self.parser.parse_args()

        if not config_found and not args.command in [None,"init"]:
            eprint("ERROR: Cannot run command with missing configuration.")
            exit(1)

        match args.command:
            case None:
                self.parser.print_help()
            case "entry":
                make_entry(
                    title = args.title,
                    issues = args.issue,
                    cat = args.cat,
                    contents = args.content,
                    interactive = args.interactive,
                )
            case "collect":
                collect(
                    version = args.version,
                    delete = args.delete,
                    skip_on_error = args.skip_on_error,
                    out = args.out,
                    prepend = args.prepend,
                    append = args.append,
                    insert = args.insert,
                )
            case "check":
                check(
                    paths = args.path,
                    all = args.all,
                )
            case "clean":
                clean(
                    delete = args.delete,
                )
            case "gh":
                github(
                    post_issues = args.issues,
                    post_prs = args.prs,
                    lst = args.list,
                    version = args.version,
                    out = args.out,
                    exec_commands = args.exec,
                )
            case "init":
                init()

    def __call__(self):
        self.run()

app=App()
if __name__=="__main__":
    app()
