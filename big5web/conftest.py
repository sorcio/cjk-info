import argparse
from pathlib import Path
from typing import TYPE_CHECKING
import pytest

if TYPE_CHECKING:
    from typing import TypeGuard


WPT_BIG5_TESTS_PATH = "encoding/legacy-mb-tchinese/big5"
WPT_PATH_FIXTURE_NAME = "wpt_path"

wpt_path_key = pytest.StashKey[list[Path]]()


def is_list_of_paths(o: object) -> "TypeGuard[list[Path]]":
    if isinstance(o, list):
        if not o:
            return True
        return isinstance(o[0], Path)
    return False


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--web-platform-tests",
        type=argparse.FileType(),
        help="path to web-platform-tests/wpt repository",
    )
    parser.addini(
        name="web-platform-tests",
        help="path to web-platform-tests/wpt repository",
        type="paths",
    )


def pytest_configure(config: pytest.Config):
    wpt_paths = config.getini("web-platform-tests") or []
    print(wpt_paths)
    assert is_list_of_paths(wpt_paths)
    cmd_path_option = config.getoption("web_platform_tests")
    if cmd_path_option:
        cmd_path = Path(cmd_path_option)
        wpt_paths.insert(0, cmd_path)
    valid_paths = []
    already_seen = set()
    for path in wpt_paths:
        if path.is_dir():
            big5path = path / WPT_BIG5_TESTS_PATH
            if big5path.is_dir():
                path = big5path
            resolved = path.resolve()
            if resolved not in already_seen:
                valid_paths.append(path)
                already_seen.add(resolved)
    if not valid_paths:
        config.issue_config_time_warning(
            pytest.PytestConfigWarning(
                "no valid web-platform-tests paths given; will skip wpt tests"
            ),
            2,
        )
    config.stash[wpt_path_key] = valid_paths


def _get_big5_wpt_tests(path):
    if not path:
        path = Path(__file__).parent.parent.parent / "wpt"
    else:
        path = Path(path)
    assert path.is_dir()
    # Find files like:
    # wpt/encoding/legacy-mb-tchinese/big5/big5_chars.html
    return [*path.glob("big5_chars*.html")]


def pytest_generate_tests(metafunc: pytest.Metafunc):
    if WPT_PATH_FIXTURE_NAME in metafunc.fixturenames:
        paths = metafunc.config.stash.get(wpt_path_key, [])
        tests: list[Path] = []
        for path in paths:
            tests.extend(_get_big5_wpt_tests(path))
        metafunc.parametrize(
            WPT_PATH_FIXTURE_NAME, tests, ids=[t.stem for t in tests], scope="module"
        )


@pytest.fixture(scope="module")
def wpt_path(wpt_path: Path):
    return wpt_path


@pytest.fixture(scope="module")
def wpt_bytes(wpt_path: Path):
    return wpt_path.read_bytes()


@pytest.fixture(scope="module")
def wpt_decoded(wpt_bytes: bytes):
    return wpt_bytes.decode("big5web")
