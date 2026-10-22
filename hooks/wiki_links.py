"""MkDocs hook: adapt the GitHub-oriented docs to the wiki.

The pages in docs/en and docs/it are also read on GitHub, where each one links
to its translation ("[Italiano](../it/X.md)") and to files outside docs/.
In the wiki the language selector replaces the translation links, and files
outside docs/ are linked on GitHub.
"""
import re

REPO_BLOB = "https://github.com/MzTechnology97/K2-OpenHost/blob/main/"

# "[Italiano](../it/X.md)" / "[English](../en/X.md)", with the separator
# that precedes it on the "Updated: ..." line.
LANGUAGE_LINK = re.compile(
    r"(?:\s*[.|·-]?\s*)\[(?:Italiano|English)\]\(\.\./(?:it|en)/[^)]*\)")
# Links that leave docs/: ../../releases/stable.json and the like.
OUTSIDE_DOCS = re.compile(r"\]\(\.\./\.\./(?!images/)([^)#\s]+)")


def on_page_markdown(markdown, page, config, files):
    markdown = LANGUAGE_LINK.sub("", markdown)
    return OUTSIDE_DOCS.sub(lambda m: "](" + REPO_BLOB + m.group(1), markdown)
