.PHONY: test backtest api install clean

install:
	pip install -e .

test:
	pytest tests/ -q

backtest:
	python scripts/run_backtest.py

api:
	uvicorn aegisflow.api.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
