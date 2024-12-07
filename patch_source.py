"""
patch pyx file path in cython generated c files

we need this file to generated correct pyx code coverage

more details: https://github.com/cython/cython/issues/6186
"""

import sys
from pathlib import Path

raw = """
static const char *__pyx_f[] = {
  "_quoting_c.pyx",
  "<stringsource>",
  "type.pxd",
};
"""

if sys.platform == "win32":
    repl = r"""
static const char *__pyx_f[] = {
  "yarl\\\\_quoting_c.pyx",
  "<stringsource>",
  "type.pxd",
};
"""
else:
    repl = """
static const char *__pyx_f[] = {
  "yarl/_quoting_c.pyx",
  "<stringsource>",
  "type.pxd",
};
"""

input_file, output_file = sys.argv[1:]

Path(output_file).write_text(
    Path(input_file).read_text(encoding="utf-8").replace(raw, repl),
    encoding="utf-8",
)
