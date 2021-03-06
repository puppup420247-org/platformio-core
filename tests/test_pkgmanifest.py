# Copyright (c) 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re

import jsondiff
import pytest

from platformio.compat import WINDOWS
from platformio.package.manifest import parser
from platformio.package.manifest.schema import ManifestSchema, ManifestValidationError


def test_library_json_parser():
    contents = """
{
    "name": "TestPackage",
    "keywords": "kw1, KW2, kw3",
    "platforms": ["atmelavr", "espressif"],
    "url": "http://old.url.format",
    "exclude": [".gitignore", "tests"],
    "include": "mylib",
    "build": {
        "flags": ["-DHELLO"]
    },
    "customField": "Custom Value"
}
"""
    mp = parser.LibraryJsonManifestParser(contents)
    assert not jsondiff.diff(
        mp.as_dict(),
        {
            "name": "TestPackage",
            "platforms": ["atmelavr", "espressif8266"],
            "export": {"exclude": [".gitignore", "tests"], "include": ["mylib"]},
            "keywords": ["kw1", "kw2", "kw3"],
            "homepage": "http://old.url.format",
            "build": {"flags": ["-DHELLO"]},
            "customField": "Custom Value",
        },
    )

    contents = """
{
    "keywords": ["sound", "audio", "music", "SD", "card", "playback"],
    "frameworks": "arduino",
    "platforms": "atmelavr",
    "export": {
        "exclude": "audio_samples"
    }
}
"""
    mp = parser.LibraryJsonManifestParser(contents)
    assert not jsondiff.diff(
        mp.as_dict(),
        {
            "keywords": ["sound", "audio", "music", "sd", "card", "playback"],
            "frameworks": ["arduino"],
            "export": {"exclude": ["audio_samples"]},
            "platforms": ["atmelavr"],
        },
    )


def test_module_json_parser():
    contents = """
{
  "author": "Name Surname <name@surname.com>",
  "description": "This is Yotta library",
  "homepage": "https://yottabuild.org",
  "keywords": [
    "mbed",
    "Yotta"
  ],
  "licenses": [
    {
      "type": "Apache-2.0",
      "url": "https://spdx.org/licenses/Apache-2.0"
    }
  ],
  "name": "YottaLibrary",
  "repository": {
    "type": "git",
    "url": "git@github.com:username/repo.git"
  },
  "version": "1.2.3",
  "customField": "Custom Value"
}
"""

    mp = parser.ModuleJsonManifestParser(contents)
    assert not jsondiff.diff(
        mp.as_dict(),
        {
            "name": "YottaLibrary",
            "description": "This is Yotta library",
            "homepage": "https://yottabuild.org",
            "keywords": ["mbed", "Yotta"],
            "license": "Apache-2.0",
            "platforms": ["*"],
            "frameworks": ["mbed"],
            "export": {"exclude": ["tests", "test", "*.doxyfile", "*.pdf"]},
            "authors": [{"email": "name@surname.com", "name": "Name Surname"}],
            "version": "1.2.3",
            "repository": {"type": "git", "url": "git@github.com:username/repo.git"},
            "customField": "Custom Value",
        },
    )


def test_library_properties_parser():
    # Base
    contents = """
name=TestPackage
version=1.2.3
author=SomeAuthor <info AT author.com>
sentence=This is Arduino library
customField=Custom Value
"""
    mp = parser.LibraryPropertiesManifestParser(contents)
    assert not jsondiff.diff(
        mp.as_dict(),
        {
            "name": "TestPackage",
            "version": "1.2.3",
            "description": "This is Arduino library",
            "sentence": "This is Arduino library",
            "platforms": ["*"],
            "frameworks": ["arduino"],
            "export": {
                "exclude": ["extras", "docs", "tests", "test", "*.doxyfile", "*.pdf"]
            },
            "authors": [{"email": "info@author.com", "name": "SomeAuthor"}],
            "keywords": ["uncategorized"],
            "customField": "Custom Value",
        },
    )

    # Platforms ALL
    data = parser.LibraryPropertiesManifestParser(
        "architectures=*\n" + contents
    ).as_dict()
    assert data["platforms"] == ["*"]
    # Platforms specific
    data = parser.LibraryPropertiesManifestParser(
        "architectures=avr, esp32\n" + contents
    ).as_dict()
    assert data["platforms"] == ["atmelavr", "espressif32"]

    # Remote URL
    data = parser.LibraryPropertiesManifestParser(
        contents,
        remote_url=(
            "https://raw.githubusercontent.com/username/reponame/master/"
            "libraries/TestPackage/library.properties"
        ),
    ).as_dict()
    assert data["export"] == {
        "exclude": ["extras", "docs", "tests", "test", "*.doxyfile", "*.pdf"],
        "include": ["libraries/TestPackage"],
    }
    assert data["repository"] == {
        "url": "https://github.com/username/reponame",
        "type": "git",
    }

    # Hope page
    data = parser.LibraryPropertiesManifestParser(
        "url=https://github.com/username/reponame.git\n" + contents
    ).as_dict()
    assert data["repository"] == {
        "type": "git",
        "url": "https://github.com/username/reponame.git",
    }


def test_library_json_schema():
    contents = """
{
  "name": "ArduinoJson",
  "keywords": "JSON, rest, http, web",
  "description": "An elegant and efficient JSON library for embedded systems",
  "homepage": "https://arduinojson.org",
  "repository": {
    "type": "git",
    "url": "https://github.com/bblanchon/ArduinoJson.git"
  },
  "version": "6.12.0",
  "authors": {
    "name": "Benoit Blanchon",
    "url": "https://blog.benoitblanchon.fr"
  },
  "exclude": [
    "fuzzing",
    "scripts",
    "test",
    "third-party"
  ],
  "frameworks": "arduino",
  "platforms": "*",
  "license": "MIT",
  "examples": [
    {
        "name": "JsonConfigFile",
        "base": "examples/JsonConfigFile",
        "files": ["JsonConfigFile.ino"]
    },
    {
        "name": "JsonHttpClient",
        "base": "examples/JsonHttpClient",
        "files": ["JsonHttpClient.ino"]
    }
  ]
}
"""
    raw_data = parser.ManifestParserFactory.new(
        contents, parser.ManifestFileType.LIBRARY_JSON
    ).as_dict()

    data, errors = ManifestSchema(strict=True).load(raw_data)
    assert not errors

    assert data["repository"]["url"] == "https://github.com/bblanchon/ArduinoJson.git"
    assert data["examples"][1]["base"] == "examples/JsonHttpClient"
    assert data["examples"][1]["files"] == ["JsonHttpClient.ino"]

    assert not jsondiff.diff(
        data,
        {
            "name": "ArduinoJson",
            "keywords": ["json", "rest", "http", "web"],
            "description": "An elegant and efficient JSON library for embedded systems",
            "homepage": "https://arduinojson.org",
            "repository": {
                "url": "https://github.com/bblanchon/ArduinoJson.git",
                "type": "git",
            },
            "version": "6.12.0",
            "authors": [
                {"name": "Benoit Blanchon", "url": "https://blog.benoitblanchon.fr"}
            ],
            "export": {"exclude": ["fuzzing", "scripts", "test", "third-party"]},
            "frameworks": ["arduino"],
            "platforms": ["*"],
            "license": "MIT",
            "examples": [
                {
                    "name": "JsonConfigFile",
                    "base": "examples/JsonConfigFile",
                    "files": ["JsonConfigFile.ino"],
                },
                {
                    "name": "JsonHttpClient",
                    "base": "examples/JsonHttpClient",
                    "files": ["JsonHttpClient.ino"],
                },
            ],
        },
    )


def test_library_properties_schema():
    contents = """
name=U8glib
version=1.19.1
author=oliver <olikraus@gmail.com>
maintainer=oliver <olikraus@gmail.com>
sentence=A library for monochrome TFTs and OLEDs
paragraph=Supported display controller: SSD1306, SSD1309, SSD1322, SSD1325
category=Display
url=https://github.com/olikraus/u8glib
architectures=avr,sam
"""
    raw_data = parser.ManifestParserFactory.new(
        contents, parser.ManifestFileType.LIBRARY_PROPERTIES
    ).as_dict()

    data, errors = ManifestSchema(strict=True).load(raw_data)
    assert not errors

    assert not jsondiff.diff(
        data,
        {
            "description": (
                "A library for monochrome TFTs and OLEDs. Supported display "
                "controller: SSD1306, SSD1309, SSD1322, SSD1325"
            ),
            "repository": {"url": "https://github.com/olikraus/u8glib", "type": "git"},
            "frameworks": ["arduino"],
            "platforms": ["atmelavr", "atmelsam"],
            "version": "1.19.1",
            "export": {
                "exclude": ["extras", "docs", "tests", "test", "*.doxyfile", "*.pdf"]
            },
            "authors": [
                {"maintainer": True, "email": "olikraus@gmail.com", "name": "oliver"}
            ],
            "keywords": ["display"],
            "name": "U8glib",
        },
    )

    # Broken fields
    contents = """
name=Mozzi
version=1.0.3
author=Tim Barrass and contributors as documented in source, and at https://github.com/sensorium/Mozzi/graphs/contributors
maintainer=Tim Barrass <faveflave@gmail.com>
sentence=Sound synthesis library for Arduino
paragraph=With Mozzi, you can construct sounds using familiar synthesis units like oscillators, delays, filters and envelopes.
category=Signal Input/Output
url=https://sensorium.github.io/Mozzi/
architectures=*
dot_a_linkage=false
includes=MozziGuts.h
"""
    raw_data = parser.ManifestParserFactory.new(
        contents,
        parser.ManifestFileType.LIBRARY_PROPERTIES,
        remote_url=(
            "https://raw.githubusercontent.com/sensorium/Mozzi/"
            "master/library.properties"
        ),
    ).as_dict()

    data, errors = ManifestSchema(strict=False).load(raw_data)
    assert errors["authors"]

    assert not jsondiff.diff(
        data,
        {
            "name": "Mozzi",
            "version": "1.0.3",
            "description": (
                "Sound synthesis library for Arduino. With Mozzi, you can construct "
                "sounds using familiar synthesis units like oscillators, delays, "
                "filters and envelopes."
            ),
            "repository": {"url": "https://github.com/sensorium/Mozzi", "type": "git"},
            "platforms": ["*"],
            "frameworks": ["arduino"],
            "export": {
                "exclude": ["extras", "docs", "tests", "test", "*.doxyfile", "*.pdf"]
            },
            "authors": [
                {
                    "maintainer": True,
                    "email": "faveflave@gmail.com",
                    "name": "Tim Barrass",
                }
            ],
            "keywords": ["signal", "input", "output"],
            "homepage": "https://sensorium.github.io/Mozzi/",
        },
    )


def test_platform_json_schema():
    contents = """
{
  "name": "atmelavr",
  "title": "Atmel AVR",
  "description": "Atmel AVR 8- and 32-bit MCUs deliver a unique combination of performance, power efficiency and design flexibility. Optimized to speed time to market-and easily adapt to new ones-they are based on the industrys most code-efficient architecture for C and assembly programming.",
  "url": "http://www.atmel.com/products/microcontrollers/avr/default.aspx",
  "homepage": "http://platformio.org/platforms/atmelavr",
  "license": "Apache-2.0",
  "engines": {
    "platformio": "<5"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/platformio/platform-atmelavr.git"
  },
  "version": "1.15.0",
  "frameworks": {
    "arduino": {
      "package": "framework-arduinoavr",
      "script": "builder/frameworks/arduino.py"
    },
    "simba": {
      "package": "framework-simba",
      "script": "builder/frameworks/simba.py"
    }
  },
  "packages": {
    "toolchain-atmelavr": {
      "type": "toolchain",
      "version": "~1.50400.0"
    },
    "framework-arduinoavr": {
      "type": "framework",
      "optional": true,
      "version": "~4.2.0"
    },
    "framework-simba": {
      "type": "framework",
      "optional": true,
      "version": ">=7.0.0"
    },
    "tool-avrdude": {
      "type": "uploader",
      "optional": true,
      "version": "~1.60300.0"
    }
  }
}
"""
    raw_data = parser.ManifestParserFactory.new(
        contents, parser.ManifestFileType.PLATFORM_JSON
    ).as_dict()
    raw_data["frameworks"] = sorted(raw_data["frameworks"])
    data, errors = ManifestSchema(strict=False).load(raw_data)
    assert not errors

    assert not jsondiff.diff(
        data,
        {
            "name": "atmelavr",
            "title": "Atmel AVR",
            "description": (
                "Atmel AVR 8- and 32-bit MCUs deliver a unique combination of "
                "performance, power efficiency and design flexibility. Optimized to "
                "speed time to market-and easily adapt to new ones-they are based "
                "on the industrys most code-efficient architecture for C and "
                "assembly programming."
            ),
            "homepage": "http://platformio.org/platforms/atmelavr",
            "license": "Apache-2.0",
            "repository": {
                "url": "https://github.com/platformio/platform-atmelavr.git",
                "type": "git",
            },
            "frameworks": sorted(["arduino", "simba"]),
            "version": "1.15.0",
        },
    )


def test_package_json_schema():
    contents = """
{
    "name": "tool-scons",
    "description": "SCons software construction tool",
    "url": "http://www.scons.org",
    "version": "3.30101.0"
}
"""
    raw_data = parser.ManifestParserFactory.new(
        contents, parser.ManifestFileType.PACKAGE_JSON
    ).as_dict()

    data, errors = ManifestSchema(strict=False).load(raw_data)
    assert not errors

    assert not jsondiff.diff(
        data,
        {
            "name": "tool-scons",
            "description": "SCons software construction tool",
            "homepage": "http://www.scons.org",
            "version": "3.30101.0",
        },
    )

    mp = parser.ManifestParserFactory.new(
        '{"system": "*"}', parser.ManifestFileType.PACKAGE_JSON
    )
    assert "system" not in mp.as_dict()

    mp = parser.ManifestParserFactory.new(
        '{"system": "all"}', parser.ManifestFileType.PACKAGE_JSON
    )
    assert "system" not in mp.as_dict()

    mp = parser.ManifestParserFactory.new(
        '{"system": "darwin_x86_64"}', parser.ManifestFileType.PACKAGE_JSON
    )
    assert mp.as_dict()["system"] == ["darwin_x86_64"]


def test_parser_from_dir(tmpdir_factory):
    pkg_dir = tmpdir_factory.mktemp("package")
    pkg_dir.join("library.json").write('{"name": "library.json"}')
    pkg_dir.join("library.properties").write("name=library.properties")

    data = parser.ManifestParserFactory.new_from_dir(str(pkg_dir)).as_dict()
    assert data["name"] == "library.json"

    data = parser.ManifestParserFactory.new_from_dir(
        str(pkg_dir), remote_url="http://localhost/library.properties"
    ).as_dict()
    assert data["name"] == "library.properties"


def test_examples_from_dir(tmpdir_factory):
    package_dir = tmpdir_factory.mktemp("project")
    package_dir.join("library.json").write(
        '{"name": "pkg", "version": "1.0.0", "examples": ["examples/*/*.pde"]}'
    )
    examples_dir = package_dir.mkdir("examples")

    # PlatformIO project #1
    pio_dir = examples_dir.mkdir("PlatformIO").mkdir("hello")
    pio_dir.join(".vimrc").write("")
    pio_ini = pio_dir.join("platformio.ini")
    pio_ini.write("")
    if not WINDOWS:
        pio_dir.join("platformio.ini.copy").mksymlinkto(pio_ini)
    pio_dir.mkdir("include").join("main.h").write("")
    pio_dir.mkdir("src").join("main.cpp").write("")

    # wiring examples
    arduino_dir = examples_dir.mkdir("1. General")
    arduino_dir.mkdir("SomeSketchIno").join("SomeSketchIno.ino").write("")
    arduino_dir.mkdir("SomeSketchPde").join("SomeSketchPde.pde").write("")

    # custom examples
    demo_dir = examples_dir.mkdir("demo")
    demo_dir.join("demo.cpp").write("")
    demo_dir.join("demo.h").write("")
    demo_dir.join("util.h").write("")

    # PlatformIO project #2
    pio_dir = examples_dir.mkdir("world")
    pio_dir.join("platformio.ini").write("")
    pio_dir.join("README").write("")
    pio_dir.join("extra.py").write("")
    pio_dir.mkdir("include").join("world.h").write("")
    pio_dir.mkdir("src").join("world.c").write("")

    # example files in root
    examples_dir.join("root.c").write("")
    examples_dir.join("root.h").write("")

    # invalid example
    examples_dir.mkdir("invalid-example").join("hello.json")

    # Do testing

    raw_data = parser.ManifestParserFactory.new_from_dir(str(package_dir)).as_dict()
    assert isinstance(raw_data["examples"], list)
    assert len(raw_data["examples"]) == 6

    def _to_unix_path(path):
        return re.sub(r"[\\/]+", "/", path)

    def _sort_examples(items):
        for i, item in enumerate(items):
            items[i]["base"] = _to_unix_path(items[i]["base"])
            items[i]["files"] = [_to_unix_path(f) for f in sorted(items[i]["files"])]
        return sorted(items, key=lambda item: item["name"])

    raw_data["examples"] = _sort_examples(raw_data["examples"])

    data, errors = ManifestSchema(strict=True).load(raw_data)
    assert not errors

    assert not jsondiff.diff(
        data,
        {
            "version": "1.0.0",
            "name": "pkg",
            "examples": _sort_examples(
                [
                    {
                        "name": "PlatformIO/hello",
                        "base": os.path.join("examples", "PlatformIO", "hello"),
                        "files": [
                            "platformio.ini",
                            os.path.join("include", "main.h"),
                            os.path.join("src", "main.cpp"),
                        ],
                    },
                    {
                        "name": "1_General/SomeSketchIno",
                        "base": os.path.join("examples", "1. General", "SomeSketchIno"),
                        "files": ["SomeSketchIno.ino"],
                    },
                    {
                        "name": "1_General/SomeSketchPde",
                        "base": os.path.join("examples", "1. General", "SomeSketchPde"),
                        "files": ["SomeSketchPde.pde"],
                    },
                    {
                        "name": "demo",
                        "base": os.path.join("examples", "demo"),
                        "files": ["demo.h", "util.h", "demo.cpp"],
                    },
                    {
                        "name": "world",
                        "base": "examples/world",
                        "files": [
                            "platformio.ini",
                            os.path.join("include", "world.h"),
                            os.path.join("src", "world.c"),
                            "README",
                            "extra.py",
                        ],
                    },
                    {
                        "name": "Examples",
                        "base": "examples",
                        "files": ["root.c", "root.h"],
                    },
                ]
            ),
        },
    )


def test_broken_schemas():
    # non-strict mode
    data, errors = ManifestSchema(strict=False).load(dict(name="MyPackage"))
    assert set(errors.keys()) == set(["version"])
    assert data.get("version") is None

    # invalid keywords
    data, errors = ManifestSchema(strict=False).load(dict(keywords=["kw1", "*^[]"]))
    assert errors
    assert data["keywords"] == ["kw1"]

    # strict mode

    with pytest.raises(
        ManifestValidationError, match="Missing data for required field"
    ):
        ManifestSchema(strict=True).load(dict(name="MyPackage"))

    # broken SemVer
    with pytest.raises(
        ManifestValidationError, match=("Invalid semantic versioning format")
    ):
        ManifestSchema(strict=True).load(
            dict(name="MyPackage", version="broken_version")
        )

    # broken value for Nested
    with pytest.raises(ManifestValidationError, match=r"authors.*Invalid input type"):
        ManifestSchema(strict=True).load(
            dict(
                name="MyPackage",
                description="MyDescription",
                keywords=["a", "b"],
                authors=["should be dict here"],
                version="1.2.3",
            )
        )
