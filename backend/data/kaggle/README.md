# Kaggle benchmark data

This directory contains a privacy-sanitized copy of the Kaggle **Civic and Municipality Complaint System Dataset**:

- Source: https://www.kaggle.com/datasets/wajahattaj/civic-and-municipality-complaint-system-dataset
- File: `municipal_training_set_1100_sanitized.csv`
- Original size: 1,100 municipal complaint records and 26 columns.
- Retained fields: complaint description, issue type, status, date, coarse location, coordinates, department, priority, severity, area importance, and report count.
- Removed fields: resident name, resident ID, email, and phone number.

The source describes the records as a benchmark dataset built for municipal triage and says they cover multiple US cities. It is used here for model/demo benchmarking only, not as official Indian government data. The application must use authorized local data before production deployment.
