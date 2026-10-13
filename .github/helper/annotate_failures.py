"""Turn the failing part of a test log into GitHub annotations, so failures can be read
without downloading the full job log."""

import sys

MAX_ANNOTATIONS = 10
MAX_CHARS = 3500


def escape(text):
	return text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")


def main(paths):
	lines = []
	for path in paths:
		try:
			with open(path, errors="replace") as f:
				lines += f.read().splitlines()
		except FileNotFoundError:
			continue

	# keep from the first failure/traceback marker onwards, otherwise the tail
	markers = ("Traceback", "ERROR", "FAIL", "Error", "error:")
	start = next((i for i, line in enumerate(lines) if line.lstrip().startswith(markers)), None)
	interesting = lines[max(0, start - 5) :] if start is not None else lines[-200:]

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
