.PHONY: clean

clean:
	@echo "Cleaning up..."
	@find -type d -name ".venv" -exec rm -r {} +
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@echo "Cleaned!"