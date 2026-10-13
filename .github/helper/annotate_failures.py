"""Turn the failing part of a test log into GitHub annotations, so failures can be read
without downloading the full job log."""

import re
import sys

ANSI = re.compile(r"\x1b\[[0-9;]*m")

MAX_ANNOTATIONS = 10
MAX_CHARS = 3500


def escape(text):
	return text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")


def main(paths):
	lines = []
	for path in paths:
		try:
			with open(path, errors="replace") as f:
				lines += ANSI.sub("", f.read()).splitlines()
		except FileNotFoundError:
			continue

	# unittest failure blocks: from "FAIL: ..." / "ERROR: ..." up to the next "=====" or "-----" rule
	interesting, inside = [], False
	for line in lines:
		bare = line.strip()
		if re.match(r"^(FAIL|ERROR)[: ] ?\S", bare):
			inside = True
			interesting.append("=" * 40)
		elif inside and bare.startswith("=" * 20):
			inside = False
		if inside:
			interesting.append(line)
		elif bare.startswith(("Ran ", "FAILED", "OK")) or "✖" in bare:
			interesting.append(line)

	if not any(re.match(r"^(FAIL|ERROR)[: ] ?\S", line.strip()) for line in interesting):
		interesting = lines[-200:]

	chunks, current = [], ""
	for line in interesting:
		if len(current) + len(line) + 1 > MAX_CHARS:
			chunks.append(current)
			current = ""
		current += line + "\n"
	if current:
		chunks.append(current)

	# first chunks hold the first failure; last chunk holds the summary
	if len(chunks) > MAX_ANNOTATIONS:
		chunks = chunks[: MAX_ANNOTATIONS - 1] + chunks[-1:]

	for i, chunk in enumerate(chunks, 1):
		print(f"::error title=Test output {i}/{len(chunks)}::{escape(chunk)}")


if __name__ == "__main__":
	main(sys.argv[1:])
