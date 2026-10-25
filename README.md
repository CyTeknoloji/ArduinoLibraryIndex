# ArduinoLibraryIndex

Weekly slim copy of the official Arduino Library Manager index
(`downloads.arduino.cc/libraries/library_index.json.gz`) for the
Arduino Projeler ve Dersler Android app.

- Output (branch `data`, single force-pushed commit):
  - `libraries.json.gz` — one entry per library: `n` name, `v` versions (newest first),
    `a` author, `s` sentence, `c` category, `ar` architectures, `i` provided includes,
    `d` dependencies, `r` repository.
  - `meta.json` — `format`, `generated`, `hash`, `count`.
- Run manually: Actions → Build library index → Run workflow.
