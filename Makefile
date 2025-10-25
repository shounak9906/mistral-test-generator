PYTHON := python
TEST_DIR := tests
SRC := main.py under_test.py

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make test       - Run all pytest tests"
	@echo "  make coverage   - Run tests with coverage report"
	@echo "  make htmlcov    - Generate HTML coverage report"
	@echo "  make clean      - Remove temporary and cache files"
	@echo "  make gen        - Generates tests and saves in a single test file, use SPEC='' to give specifications"
	@echo "  make gen-clean  - Generates tests and saves them per-symbol with cleanup, use SPEC='' to give specifications"
	@echo "  make run        - Runs the latest test file"
	@echo "  make api-test   - Runs API integration tests"

# Run all tests
.PHONY: test
test:
	$(PYTHON) -m pytest -v $(TEST_DIR)

# Run coverage and show missing lines
.PHONY: coverage
coverage:
	coverage run -m pytest -q $(TEST_DIR)
	coverage report -m 

# Generate an HTML coverage report
.PHONY: htmlcov
htmlcov:
	coverage run -m pytest -q $(TEST_DIR)
	coverage html --include=$(SRC)
	@echo "Open htmlcov/index.html in your browser to view the report."

# Clean up temporary files
.PHONY: clean
clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -type f -name "*.pyc" -delete

.PHONY: gen run
# Single test file
gen:
	python cli.py generate under_test.py --spec "$${SPEC:-n/a}" 

# Per-symbol mode with cleanup
gen-clean:
	python cli.py generate under_test.py --spec "$${SPEC:-n/a}" --cleanup

run:
	python cli.py run --enable

# Run API integration tests 
api-test:
	pytest -v tests/test_api.py

