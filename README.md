# qlog
A changelog tool. You can:

After running `qlog init`, you can:
- Make entries: `qlog entry`
- Check entries: `qlog check`
- Collect all entries, and join them into a single document: `qlog collect`
- Check all entries have been removed or delete them: `qlog clean`

`qlog` supports:
- Markdown syntax
- Sorting entries by category
- Highlighting parts under custom categories
- Displaying the same message under multiple categories (for example, in both an additions and a highlights section)
- Defining messages for different categories in the same file.

## Installation
Clone the repository. Then, in the root folder, run `pipx install . --force`.
This command can be repeated to update the tool (after pulling from the repository).


# Usage
This section goes into the standard usage of the `qlog` tool.
For all options, see `qlog --help` and `qlog <subcommand> --help`.

## Setup
Go to your repository's root folder and run `qlog init`.
This will create a folder called `changelog` containing a `config.yaml` file,
and a folder called `entries` with a `.gitkeep` file inside.

The command should detect the git repository it's been put in and configure
the config file accordingly.

The `qlog` command will look for a folder called `changelog` in the current
working directory. If this folder is not found, it will look for the folder in
the current git repo's root directory.

You might want to change some of the configurations, and create a `CHANGELOG.md`
file for your project.

## Writing changelog entries

To create an entry, run `qlog entry`. This will start an interactive process.

First comes the title: this is merely used for the filename. It gets stripped of special characters, is made lower case, etc.

Then, the list of related issues. If you do not enter any, the tool _will_ complain.
The names of the issues are retreived from the repo to make it harder to make mistakes.

The next is the category. Entries will be grouped by this category.
Enter the number or first few letters of one of the listed categories.
For custom categories, select `CUSTOM` first, then enter the full title as it should
be displayed in the changelog entry.
The custom categories are mostly meant for messages at the top of the changelog that
describe big changes that are spread across many smaller changes.

Finally, enter the entry's message.
Either enter a single line, or enter an empty line to enter multiline mode.
The entry text has full markdown support.

There are command line options for setting options directly.

For example:
```
$ qlog entry
Title (used for file name): fix infinite loop
Confirm title "fix_infinite_loop" [Y/n]: 
Related issues: 4
Issues: [4]
4: Add PR metadata tag
Confirm issues [Y/n]:
Category (0:HIGHLIGHT/1:CUSTOM/2:ADDED/3:CHANGED/4:FIXED/5:DEPRECATED/6:REMOVED): fix
Confirm category FIXED [Y/n]: 
Enter contents
To enter multiple lines, enter an empty line, then terminate with 3 empty lines
> Fixed an infinite loop bug that caused the application to hang.
/home/me/project/changelog/entries/2026-06-02_T22:02:39_fix_infinite_loop.md
```

### Categories
There are a number of categories present by default.
Entries are grouped by their category, and listed in a bullet point list.

There are a few exceptions. Entries in the category `HIGHLIGHT` are placed without
title or bullet points, as long as there is only one entry.
Similarly, custom categories do not use bullet points
as long as only one entry is entered under the category.

By default, the categories get listed as `HIGHLIGHT`, custom categories, `ADDED`, `CHANGED`, `FIXED`, `DEPRICATED`, `REMOVED`. The categories can be fully configured through the configuration file.

### Editing entries by hand
It's often useful to edit the entry files by hand; this is fully intended.
Editing the files by hand allows you to do some things that are not directly supported
through the interactive editor.

Most importantly, you can put multiple entries (linked to the same issues) in a single file.
Every entry starts with a markdown header (i.e. `# ADDED`) denoting the category.
Any such header not in the list of categories is treated as a custom category.

It is also possible to make a message appear in multiple categories by separating them with pipes
(i.e. `# ADDED | CHANGED`), though it's generally better to just write multiple messages.

Entering any text before the category header puts it in the `HIGHLIGHTS` category.


### Checking entries
To check whether there are any issues with your entries, run `qlog check`.
This will check the last edited entry by default. It's also possible to
pass the path to an entry file, or check all entries with `-a`.


## Combining changelog entries
For a release, all entry files are combined into a single changelog.
This can be done with `changelog collect`. The release version, used in the title,
can be provided with `--version`.

By default, the output will be printed to the terminal directly.
Using the different output options, it can be written to a file,
appended or prepended to, or inserted into an existing file.
The changelog will be inserted before the previous changelog entry.

A typical use looks like: `qlog collect -v "1.2.3" -i CHANGELOG.md`
(followed by `qlog clean -D`).

### Entry cleanup
After collecting the entries, they must be deleted.
It is possible to do this by providing `qlog collect` with `-D`/`--delete` directly,
but it's generally advisable to delete them afterwards, in case something goes wrong.

To clean the entries, `qlog clean` can be used with the same flag to delete the files;
without the flag, the command will simply error if there are any entries left
(which can be used to easily check if the entries have all been deleted correctly).

It is advisable to collect the entries and delete the entry files in the same commit,
so it can easily be cherry-picked.

## Posting messages to GitHub
Finally, `qlog` has builtin tools for posting messages to the linked issues,
as well as the PRs that added/changed the changelog entry files.

The main command is `qlog gh`. To target the linked issues, use `-i`/`--issues`,
and to find and target prs, use `-p`/`--prs`.
The default message references the update version, which requires you to specify it using `-v`/`--version`.

By default, the command will output a list of commands to post the messages. These can be stored to a file by specifying `-o`/`--out`, or executed immediately using `-x`/`--exec`.

For example, `qlog gh -i -v "1.2.3" -o post_msgs.sh`,
followed by `bash post_msgs.sh` after checking everything is in order.

It's also possible to only list the PR/issue numbers using `-l`/`--list`.

Note that the default message assumes the version is created
with a specific tag including the version number,
which generally does not exist yet when the entry files are deleted
(since this happens when creating the changelog, which is still part of the release process).
It might be easier to go back to an earlier commit that still has the files.
