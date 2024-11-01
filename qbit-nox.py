import os
import shlex
import subprocess
import sys
from pathlib import Path

from contextlib import chdir as chdir_ctx

project_base_path = Path(__file__, "../src/").resolve()

libtorrent_path = project_base_path.joinpath("libtorrent").resolve()
qbittorrent_path = project_base_path.joinpath("qBittorrent").resolve()
boost_path = project_base_path.joinpath("boost").resolve()
qt6_src_path = project_base_path.joinpath("qt").resolve()

CCACHE_DIR = project_base_path.parent.joinpath(".ccache")

cmake_prefix_path = project_base_path.parent.joinpath("include").resolve()
build_path = project_base_path.parent.joinpath("build").resolve()

project_base_path.mkdir(exist_ok=True, parents=True)

build_path.mkdir(exist_ok=True, parents=True)


COMMON_ENVIRON = {
    "CMAKE_CXX_COMPILER_LAUNCHER": "sccache",
    "CMAKE_C_COMPILER_LAUNCHER": "sccache",
    "CMAKE_INSTALL_PREFIX": cmake_prefix_path.as_posix(),
}


def compile_qt():
    qt_build_path = build_path.joinpath("qt")
    if not qt_build_path.exists():
        qt_build_path.mkdir(exist_ok=True)
        with chdir_ctx(qt_build_path):
            subprocess.check_call(
                [
                    qt6_src_path.joinpath("configure").as_posix(),
                    "-submodules",
                    "qtbase,qttools",
                    "-prefix",
                    str(cmake_prefix_path),
                    "-static",
                    # "-shared",
                ],
                env=os.environ | COMMON_ENVIRON,
            )
    with chdir_ctx(qt_build_path):
        subprocess.check_call(
            shlex.split("cmake --build ."),
            env=os.environ | COMMON_ENVIRON,
        )
        subprocess.check_call(shlex.split("cmake --install ."))


def ensure_boost():
    build_boost_path = build_path.joinpath("boost")
    build_boost_path.mkdir(exist_ok=True, parents=True)
    with chdir_ctx(build_boost_path):
        subprocess.check_call(
            [
                "cmake",
                boost_path,
                "-D",
                "BUILD_SHARED_LIBS=OFF",
                "-D",
                "BUILD_TESTING=OFF",
            ],
            env=os.environ | COMMON_ENVIRON,
        )
        subprocess.check_call(
            shlex.split("cmake --build . --config RelWithDebInfo"),
            env=os.environ | COMMON_ENVIRON,
        )
        subprocess.check_call(
            shlex.split(
                f"cmake --install . --config RelWithDebInfo --prefix '{cmake_prefix_path}'"
            )
        )


def ensure_libtorrent():
    with chdir_ctx(libtorrent_path):
        for shared in [
            # "ON",
            "OFF",
        ]:
            subprocess.check_call(
                shlex.split(
                    f"""
                    cmake -B {build_path.joinpath("libtorrent")} -G Ninja
                        -D CMAKE_BUILD_TYPE=RelWithDebInfo
                        -D deprecated-functions=OFF
                        -D BUILD_SHARED_LIBS={shared}
                        -D BOOST_ROOT={cmake_prefix_path}
                        -D CMAKE_INSTALL_PREFIX={cmake_prefix_path}
                        -D CMAKE_INCLUDE_PATH={cmake_prefix_path / "include"}
                        -D CMAKE_LIBRARY_PATH={cmake_prefix_path / "lib"}
                        -D CMAKE_INSTALL_LIBDIR=lib
                    """,
                ),
                env=os.environ | COMMON_ENVIRON,
            )
            subprocess.check_call(
                shlex.split(f"""cmake --build {build_path / "libtorrent"}"""),
                env=os.environ | COMMON_ENVIRON,
            )
            subprocess.check_call(
                shlex.split(
                    f"""cmake --install {build_path / "libtorrent"} --prefix {cmake_prefix_path}"""
                ),
                env=os.environ | COMMON_ENVIRON,
            )


def compile_qb():
    with chdir_ctx(qbittorrent_path):
        subprocess.check_call(
            [
                "cmake",
                *["-B", build_path.joinpath("qb").as_posix()],
                *["-G", "Ninja"],
                *["-D", "TESTING=OFF", "-D", "GUI=OFF"],
                *["-D", "CMAKE_BUILD_TYPE=RelWithDebInfo"],
                *["-D", f"BOOST_ROOT={cmake_prefix_path}"],
                *["-D", f"CMAKE_PREFIX_PATH={cmake_prefix_path}"],
                *["-D", f"CMAKE_INCLUDE_PATH={cmake_prefix_path / 'include'}"],
                *["-D", f"CMAKE_LIBRARY_PATH={cmake_prefix_path / 'lib'}"],
                "-DCMAKE_CXX_FLAGS='-Werror -Wno-error=deprecated-declarations'",
                "-DBoost_USE_STATIC_LIBS=ON",
                *shlex.split("-D ZLIB_USE_STATIC_LIBS=ON"),
                *shlex.split("-D ZLIB_LIBRARY=/usr/lib/x86_64-linux-gnu/libz.a"),
                *shlex.split("-D OPENSSL_USE_STATIC_LIBS=true"),
            ],
            env=os.environ | COMMON_ENVIRON,
        )

        subprocess.check_call(
            shlex.split(f"cmake --build {build_path / 'qb'}"),
            env=os.environ | COMMON_ENVIRON,
        )


match sys.argv[1]:
    case "boost":
        ensure_boost()
    case "lt":
        ensure_libtorrent()
    case "qt":
        compile_qt()
    case "qb":
        compile_qb()
    case _:
        print("Unknown compile target")
        sys.exit(1)
