# pyright: strict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
import re
import sys
from typing import IO, Any, Iterable, NamedTuple, Type, TypeVar
from urllib.parse import urljoin, urlparse
import requests


V = TypeVar("V", bound="Visitor")


class Visitor:
    def visit_enter(self, node: "Node"):
        pass

    def visit_exit(self, node: "Node"):
        pass

    def collect(self, parent: "Node | None", nodes: Iterable["Node"]):
        for node in nodes:
            node.accept(self)

    @classmethod
    def for_node(cls: Type[V], node: "Node") -> V:
        visitor = cls()
        node.accept(visitor)
        return visitor


@dataclass
class Node:
    type: str = field(init=False)

    def __post_init__(self):
        self.type = self.__class__.__name__

    def accept(self, visitor: Visitor):
        visitor.visit_enter(self)
        visitor.visit_exit(self)


@dataclass
class TextNode(Node):
    text: str


@dataclass
class LineBreak(Node):
    pass


@dataclass
class NodeWithChildren(Node):
    children: list["Node"] = field(default_factory=list)

    def accept(self, visitor: Visitor):
        visitor.visit_enter(self)
        visitor.collect(self, self.children)
        visitor.visit_exit(self)


@dataclass
class Block(NodeWithChildren):
    pass


@dataclass
class InlineNode(Node):
    # inline nodes cannot be nested
    label: str = field(default="")


class InlineCode(InlineNode):
    pass


@dataclass
class Heading(Block):
    level: int = field(default=1)


@dataclass
class OrderedList(Block):
    pass


@dataclass
class ListItem(NodeWithChildren):
    pass


@dataclass
class Anchor(InlineNode):
    href: str = field(default="")


@dataclass
class MainNode(Block):
    pass


from textwrap import wrap


class RenderVisitor(Visitor):
    def __init__(self, width: int = 80):
        self.width = width
        # renderer state:
        self.chunk: list[str] = []
        self.lines: list[str] = []
        self.list_counter: list[ListCounter] = []
        self.prefix_stack: list[str] = []
        self.indent: int = 0
        self.next_prefix: str = ""
        self.parent: list[Node] = []

    def _push_prefix(self, prefix: str):
        if prefix:
            self.next_prefix += prefix
            self.indent += len(prefix)
        self.prefix_stack.append(prefix)

    def _consume_prefix(self):
        prefix = self.next_prefix
        indent = self.indent
        self.next_prefix = " " * indent
        return prefix, self.next_prefix

    def _pop_prefix(self):
        popped = self.prefix_stack.pop()
        self.indent -= len(popped)
        self.next_prefix = self.next_prefix[: self.indent]

    def visit_enter(self, node: Node) -> None:
        if self.chunk and isinstance(node, Block):
            if self._produce_block():
                self.dangling_block = False

        self.parent.append(node)
        match node:
            case Heading(level=level):
                prefix = "#" * level + " "
                self._push_prefix(prefix)
            case OrderedList():
                highest_counter = len(node.children)
                self.list_counter.append(
                    ListCounter(is_ordered=True, highest=highest_counter)
                )
            case ListItem():
                prefix = self.list_counter[-1].next_prefix()
                self._push_prefix(prefix)
            case _:
                pass

    def _produce_block(self):
        text = "".join(self.chunk).strip()
        self.chunk.clear()
        if text:
            prefix, subsequent_prefix = self._consume_prefix()
            lines = wrap(
                text,
                width=self.width,
                initial_indent=prefix,
                subsequent_indent=subsequent_prefix,
                break_long_words=False,
            )
            self.lines.extend(lines)
            self.lines.append("")
            return True
        return False

    def visit_exit(self, node: Node) -> None:
        self.parent.pop()
        match node:
            case TextNode(text=text):
                assert "\n" not in text
                self.chunk.append(text)
            case LineBreak():
                self.chunk.append("\n")
            case Anchor(label=label, href=href):
                self.chunk.append(f"[{label}]({href})")
            case InlineCode(label=label):
                self.chunk.append(f"`{label}`")
            case ListItem():
                if self.chunk:
                    self._produce_block()
                self._pop_prefix()
            case OrderedList():
                self.list_counter.pop()
            case Heading():
                self._produce_block()
                self._pop_prefix()
            case Block():
                self._produce_block()
            case _:
                pass

    def collect(self, parent: Node | None, nodes: Iterable["Node"]):
        for node in nodes:
            node.accept(self)


class StripLinks(Visitor):
    def __init__(self):
        self.links: set[tuple[str, str]] = set()

    def collect(self, parent: Node | None, nodes: Iterable["Node"]):
        assert isinstance(parent, NodeWithChildren)
        marked_for_removal: list[Anchor] = []
        for node in nodes:
            if isinstance(node, Anchor):
                marked_for_removal.append(node)
            node.accept(self)
        # Remove all anchors
        for a in marked_for_removal:
            self.links.add((a.label, a.href))
            parent.children.remove(a)
        # Check if we still have meaningful content, otherwise drop tree.
        for node in parent.children:
            if isinstance(node, TextNode):
                if any(c.isalnum() for c in node.text):
                    break
            else:
                break
        else:
            parent.children.clear()


class TreePrinter(Visitor):
    def __init__(self):
        self.level = 0

    def visit_enter(self, node: "Node"):
        prefix = "  " * self.level + "*"
        match node:
            case TextNode(text=text):
                data = text
            case _:
                data = ""

        print(prefix, colorize(node.type, "green"), colorize(data, "blue"))
        self.level += 1

    def visit_exit(self, node: "Node"):
        self.level -= 1


class FindTitleVisitor(Visitor):
    def __init__(self):
        self.title = None

    def visit_exit(self, node: Node) -> None:
        if self.title is None and isinstance(node, Heading):
            self.title = "".join(
                c.text for c in node.children if isinstance(c, TextNode)
            )


@dataclass
class ListCounter:
    counter: int = field(default=0)
    highest: int = field(default=0)
    is_ordered: bool = field(default=False)

    def next_prefix(self) -> str:
        next_counter = self.counter + 1
        self.counter = next_counter
        if self.is_ordered:
            width = len(str(self.highest)) + 2
            return f"{next_counter})".ljust(width)
        else:
            return "* "


class ParserState(Enum):
    Root = auto()
    InMainSection = auto()


class CCLITermsParser(HTMLParser):
    MAIN_SECTION_ID = "sectionMainContent"
    LARGE_HEADER_CLASS = "mainContentLargeHeader"
    SMALL_HEADER_CLASS = "mainContentSmallHeader"

    def __init__(self, href: str = "http://example.com/"):
        super().__init__()
        self.main_node: MainNode | None = None
        self.href = href
        # parser state:
        self.stack: list[Node | None] = []
        self.state: ParserState = ParserState.Root
        self.dangling = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
        S: Type[ParserState] = ParserState,
    ) -> None:
        match self.state, tag, attrs:
            case S.Root, _, [["id", self.MAIN_SECTION_ID], *_]:
                self.state = S.InMainSection
                self._push(MainNode())
            case S.Root, _, _:
                self._push(None)
            case S.InMainSection, _, [["class", self.LARGE_HEADER_CLASS], *_]:
                self._push(Heading(level=1))
            case S.InMainSection, _, [["class", self.SMALL_HEADER_CLASS], *_]:
                self._push(Heading(level=2))
            case S.InMainSection, "p" | "div", _:
                self._push(Block())
            case S.InMainSection, "ol", _:
                self._push(OrderedList())
            case S.InMainSection, "li", _:
                self._push(ListItem())
            case S.InMainSection, "a", [["href", a_href], *_] if a_href:
                href = urljoin(self.href, a_href)
                self._push(Anchor(href=href))
            case S.InMainSection, "br", _:
                self._push(LineBreak())
            case S.InMainSection, _, _:
                self._push(None)
            case _:
                assert False, "unreachable"

    def _push(self, node: Node | None):
        self.stack.append(node)

    def _shift(self, node: Node, shift_to: Type[NodeWithChildren] = NodeWithChildren):
        for ancestor in reversed(self.stack):
            if isinstance(ancestor, shift_to):
                ancestor.children.append(node)
                break
        else:
            assert False, f"cannot shift {node} to {shift_to}"

    def handle_endtag(self, tag: str, S: Type[ParserState] = ParserState) -> None:
        head = self.stack.pop()
        match self.state, head:
            case S.Root, _:
                pass
            case S.InMainSection, MainNode() as main_node:
                self.state = S.Root
                self.main_node = main_node
            case S.InMainSection, ListItem() as node:
                self._shift(node, OrderedList)
            case S.InMainSection, Node() as node:
                self._shift(node)
            case S.InMainSection, None:
                pass
            case _:
                assert False, "invalid parser state"

    def handle_data(self, data: str) -> None:
        head = self.stack[-1] if self.stack else None
        if isinstance(head, (Block, ListItem)):
            text = re.sub(r"\s+", " ", data).removeprefix(" ")
            head.children.append(TextNode(text))
        elif isinstance(head, InlineNode):
            text = re.sub(r"\s+", " ", data)
            head.label += text


def retrieve_url(session: requests.Session, url: str, file_path: Path):
    r = session.get(url)
    r.raise_for_status()
    file_path.write_text(r.text)
    return url, file_path


class DownloadPath(NamedTuple):
    url: str
    path: Path


class DocPath(NamedTuple):
    doc_title: str
    doc_url: str
    doc_path: Path
    terms_path: Path
    source: str


DownloadList = list[DownloadPath]
DocsList = list[DocPath]


def get_url_path(url: str) -> PurePosixPath:
    """Return the path component of a URL as a PurePosixPath

    >>> get_url_path("http://example.com/foo/bar.html")
    PurePosixPath('/foo/bar.html')
    """
    parsed_url = urlparse(url)
    return PurePosixPath(parsed_url.path)


def prepare_urls(urls: list[str]) -> tuple[DownloadList, DownloadList]:
    to_download: DownloadList = []
    ready: DownloadList = []
    for url in urls:
        url_path = get_url_path(url)
        file_path = Path(url_path.name)
        if not file_path.is_file():
            to_download.append(DownloadPath(url, file_path))
        else:
            ready.append(DownloadPath(url, file_path))
    return to_download, ready


def download_urls(urls: DownloadList):
    with requests.Session() as session, ThreadPoolExecutor(4) as pool:
        fs = [pool.submit(retrieve_url, session, url, path) for url, path in urls]
        for f in as_completed(fs):
            url, path = f.result()
            print(f"Downloaded {path.name}")
            yield DownloadPath(url, path)


def render(node: Node, out: IO[str]) -> tuple[str | None, str | None]:
    find_title = FindTitleVisitor.for_node(node)
    doc_title = find_title.title

    # This modifies the doc tree:
    extract_links = StripLinks.for_node(node)

    file_url = None
    for label, href in extract_links.links:
        if label.casefold().strip() == "accept and download":
            file_url = href

    renderer = RenderVisitor()
    node.accept(renderer)
    out.writelines(f"{l}\n" for l in renderer.lines)

    return doc_title, file_url


def parse_ccli_terms_file(
    url: str, data: str, out: IO[str]
) -> tuple[str | None, str | None]:
    parser = CCLITermsParser(href=url)
    parser.feed(data)
    if parser.main_node is None:
        raise Exception("Could not find main section in HTML")
    doc_title, file_url = render(parser.main_node, out)
    return doc_title, file_url


def parse_all_ccli_terms(ready: DownloadList) -> DocsList:
    docs: DocsList = []
    for url, html_path in ready:
        md_path = html_path.with_suffix(".md")
        with md_path.open("w+") as out:
            doc_title, file_url = parse_ccli_terms_file(url, html_path.read_text(), out)
            if file_url:
                url_path = get_url_path(file_url)
                file_path = Path(url_path.name)
                if not doc_title:
                    doc_title = url_path.name
                docs.append(DocPath(doc_title, file_url, file_path, md_path, "CCLI"))
        html_path.unlink()
    return docs


def colorize(text: str, color: str | None) -> str:
    if color is None or not sys.stdout.isatty():
        return text
    code = {
        "bold": 1,
        "faint": 2,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
    }[color]
    return f"\033[{code}m{text}\033[0m"


def confirm(text: str, default: bool | None = None, color: str | None = None) -> bool:
    """Prompt for confirmation (yes/no question)"""
    choices = "y/n" if default is None else ("Y/n" if default else "y/N")
    prompt = f"{text} [{choices}]"

    while True:
        response = input(colorize(prompt, color))
        match response.strip().lower():
            case "y" | "yes":
                valid_response = True
            case "n" | "no":
                valid_response = False
            case "" if default is not None:
                valid_response = default
            case _:
                continue
        return valid_response


def collect_ccli_docs(terms_urls: str) -> DocsList:
    urls = terms_urls.split()
    to_download, ready = prepare_urls(urls)
    if to_download:
        print(f"Downloading {len(to_download)} Terms of Use files...")
        ready.extend(download_urls(to_download))
        print("✅ All Terms of Use files downloaded.")
    else:
        print("✅ All Terms of Use files already downloaded.")

    docs = parse_all_ccli_terms(ready)
    return docs


def download_collected_docs(docs: DocsList):
    docs_to_download: DownloadList = []
    for doc_title, doc_url, doc_path, terms_path, source in docs:
        need_to_download = True
        if doc_path.is_file():
            path_text = colorize(str(doc_path), "green")
            title_text = colorize(doc_title, "blue")
            confirm_prompt = (
                f"\n{path_text} ({title_text}) is already downloaded. Download again?"
            )
            need_to_download = confirm(confirm_prompt, default=False, color="blue")
        if need_to_download:
            print()
            print(
                colorize(
                    "Terms of Use must be accepted to download this document.", "red"
                )
            )
            print()
            print(terms_path.read_text())
            print()
            print(colorize("A local copy of this agreement is available:", "blue"))
            print(colorize(f"    {terms_path}", "blue"))

            print()
            print(
                colorize(
                    "If you accept this agreement, this document will be downloaded:",
                    "blue",
                )
            )
            print(colorize(f" URL    : {doc_url}", "faint"))
            print(colorize(f" Title  : {doc_title}", "faint"))
            print(colorize(f" Path   : {doc_path}", "faint"))
            print(colorize(f" Source : {source}", "faint"))
            print()
            accepted = confirm("DO YOU ACCEPT THE ABOVE TERMS OF USE?", color="red")
            if accepted:
                docs_to_download.append(DownloadPath(doc_url, doc_path))

    if docs_to_download:
        print()
        print(f"Downloading {len(docs_to_download)} document files...")
        [*ready_docs] = download_urls(docs_to_download)
        assert len(ready_docs) == len(docs_to_download)
        print()
        print("✅ All documents downloaded.")
    else:
        print("✅ No documents to download.")

    print()
    print(colorize(f"<!-- THIS LIST IS GENERATED AUTOMATICALLY", "faint"))
    print(colorize(f"     Run download.py to update it -->", "faint"))
    print()
    # render doc snippet
    ol = OrderedList()
    for doc_title, doc_url, doc_path, terms_path, source in docs:
        li = ListItem()
        b1 = Block()
        b1.children.append(Anchor(doc_title, str(doc_path)))
        b1.children.append(TextNode(" ("))
        b1.children.append(Anchor("Terms of Use", str(terms_path)))
        b1.children.append(TextNode(")"))
        li.children.append(b1)
        b2 = Block()
        b2.children.append(TextNode("Source: "))
        b2.children.append(InlineCode(doc_url))
        b2.children.append(TextNode(f" ({source})"))
        li.children.append(b2)
        ol.children.append(li)
    renderer = RenderVisitor.for_node(ol)
    for line in renderer.lines:
        print(line)
    print()
    print(colorize(f"<!-- END OF GENERATED LIST -->", "faint"))
    print()
    print("✅ All done! You can include the above snippet in the README.md file.")


def get_ckan_resources_info(
    datasets: dict[str, dict[str, str]]
) -> dict[str, dict[str, Any]]:
    info: dict[str, dict[str, Any]] = {}
    for dataset_name in datasets.keys():
        r = requests.get(
            "https://data.gov.hk/en-data/api/3/action/package_show",
            {"id": dataset_name, "use_default_schema": True},
        )
        try:
            info[dataset_name] = r.json()
        except requests.RequestException as exc:
            print(f"❌ Cannot get information for {dataset_name}: {exc}")
    return info


def find_ckan_resources(
    datasets: dict[str, dict[str, str]],
    info: dict[str, dict[str, Any]],
    accept_newer: bool = False,
) -> DocsList:
    docs: DocsList = []
    for dataset_name, known in datasets.items():
        try:
            dataset_info = info[dataset_name]
        except KeyError:
            continue

        try:
            resources: list[dict[str, Any]] = dataset_info["result"]["resources"]
        except KeyError:
            print(f"❌ Invalid CKAN API response for {dataset_name}")
            continue

        if len(resources) == 0:
            print(f"❌ No resources found for {dataset_name}")
            continue

        last_known_date = known.get("last_known_date")
        last_known_filename = known.get("last_known_filename")

        candidates: list[tuple[dict[str, Any], Path, bool, str]] = []
        for resource in resources:
            try:
                url: str = resource["url"]
            except KeyError:
                continue

            url_path = get_url_path(url)
            file_path = Path(url_path.name)
            modified = resource.get("last_modified") or resource.get("created")

            if last_known_filename and last_known_filename != file_path.name:
                continue

            wrong_date = True
            reason = ""
            if last_known_date:
                if isinstance(modified, str):
                    if modified == last_known_date:
                        wrong_date = False
                    elif modified > last_known_date:
                        reason = (
                            colorize("file is newer", "red")
                            + f": {modified} > {last_known_date}"
                        )
                        wrong_date = not accept_newer
                    elif modified < last_known_date:
                        reason = (
                            colorize("file is older", "red")
                            + f": {modified} > {last_known_date}"
                        )
                else:
                    print("⚠️ Warning: CKAN API did not provide a valid date")
                    wrong_date = True
                    reason = (
                        colorize("no valid date provided by CKAN API", "red")
                        + f": {modified!r}"
                    )

            candidates.append((resource, file_path, wrong_date, reason))

        if len(candidates) == 0:
            print(f"❌ No matching resources found for {dataset_name}")

        matching_date = [c for c in candidates if not c[2]]
        if len(matching_date) == 1:
            found = matching_date[0]
        else:
            print(f"No exactly matching resources found for {dataset_name}:")
            for i, (resource, file_path, _, reason) in enumerate(candidates, 1):
                print(f"\n {i}) {colorize(file_path.name, 'blue')}: {reason}")
            choices = [*map(str, range(1, 1 + len(candidates))), "s"]
            prompt = f"\nSelect a resource that looks right or 's' to skip [{','.join(choices)}] "
            while (selected := input(prompt)) not in choices:
                pass
            if selected != "s":
                number = int(selected) - 1
                found = candidates[number]
            else:
                found = None

        if found:
            resource, file_path, *_ = found
            title: str = resource.get("name") or file_path.name
            url = resource["url"]
            docs.append(
                DocPath(
                    doc_title=title,
                    doc_url=url,
                    doc_path=file_path,
                    terms_path=Path("data_gov_hk_terms.md"),
                    source="DATA.GOV.HK",
                )
            )
            print(f"✅ Found: {title}")

    return docs


def collect_ckan_docs(datasets: dict[str, dict[str, str]]):
    print("Fetching information about DATA.GOV.HK datasets...")
    ckan_info = get_ckan_resources_info(datasets)
    print("Collecting DATA.GOV.HK datasets...")
    return find_ckan_resources(datasets, ckan_info)


def _get_sources():
    sources_code = Path("sources.py").read_text()
    sources: dict[str, Any] = {}
    exec(sources_code, sources)
    return sources


def main():
    sources = _get_sources()
    docs_list: DocsList = []
    docs_list.extend(collect_ccli_docs(sources["CCLI_TERMS_URLS"]))
    docs_list.extend(collect_ckan_docs(sources["CKAN_DATASETS"]))

    download_collected_docs(docs_list)


if __name__ == "__main__":
    main()
