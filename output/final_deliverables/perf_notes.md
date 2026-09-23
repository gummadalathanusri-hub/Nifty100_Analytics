# Sprint 6 Performance Notes

## API Concurrency Test

- Endpoint: GET /api/v1/screener
- Concurrent requests: 10
- Successful responses: 10/10
- HTTP status codes: 200
- Total elapsed time: 0.302 seconds
- Requirement: less than 10 seconds
- Result: PASS

## Company Profile Performance

- Endpoint: GET /api/v1/companies/{ticker}
- Tickers tested: TCS, INFY, HDFCBANK, RELIANCE, ITC
- Successful responses: 5/5
- HTTP status codes: 200
- Total elapsed time: 0.099 seconds
- Requirement: less than 3 seconds
- Result: PASS

## Services

- FastAPI: http://127.0.0.1:8000
- Streamlit: http://localhost:8501

## Notes

- No additional database indexes were required based on measured performance.
- Streamlit reported use_container_width deprecation warnings; application remained functional.

## Sprint 6 - Clustering, REST API and QA

Sprint 6 added:

- KMeans clustering with 5 company archetypes
- Correlation heatmap and sector outlier analysis
- Portfolio KPI statistics
- 16 FastAPI REST endpoints
- OpenAPI and Postman documentation
- 102 automated tests with 0 failures
- API concurrency and performance testing
- 12-page Analyst Guide

### Sprint 6 Outputs

- output\cluster_labels.csv
- output\outlier_report.csv
- output\portfolio_stats.csv
- reports\elbow_plot.png
- reports\correlation_heatmap.png
- docs\openapi.json
- docs\postman_collection.json
- docs\analyst_guide.pdf

### Performance

- 10 concurrent screener requests: 0.302 seconds
- 5 company profile requests: 0.099 seconds
- FastAPI: port 8000
- Streamlit: port 8501