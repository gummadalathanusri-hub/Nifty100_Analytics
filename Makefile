.PHONY: load ratios test report dashboard api clean

load:
	python -m src.etl.loader

ratios:
	python -m src.analytics.ratios

test:
	pytest -v

report:
	python -m src.reports.report

dashboard:
	streamlit run src/dashboard/app.py

api:
	uvicorn src.api.main:app --reload

clean:
	python -c "import shutil; shutil.rmtree('__pycache__', ignore_errors=True)"