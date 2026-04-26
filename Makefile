.PHONY: simulate report serve test lint verify clean

HOST ?= 0.0.0.0
PORT ?= 8000

simulate:
	python3 -m app.cli simulate

report:
	python3 -m app.cli report

serve:
	python3 -m uvicorn app.web:app --host $(HOST) --port $(PORT)

test:
	pytest -q

lint:
	ruff check app tests

verify: lint test report

clean:
	rm -rf generated
