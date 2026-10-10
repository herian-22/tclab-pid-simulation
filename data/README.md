# Dataset

Dataset publik yang dipakai: **TCLab open-loop step response** (CBE 32338, Univ. of Notre Dame, J. C. Kantor).

- File: `raw/tclab-data.csv`
- URL: https://jckantor.github.io/CBE32338/data/tclab-data.csv
- Kolom: `Time` (s), `T1`, `T2` (degC), `Q1`, `Q2` (% daya heater)
- Eksperimen: heater 1 = 50% konstan, heater 2 = 0%; T1 naik dari sekitar 23.8 degC menuju sekitar 55 degC.

Unduh dengan `python scripts/download_data.py`.

Sumber pendukung lain (TCLab, APMonitor):
- https://github.com/jckantor/TCLab
- https://apmonitor.com/pdc/index.php/Main/TCLabRegression
- https://apmonitor.com/do/index.php/Main/TCLabC (data step 2 heater, 600 s)
