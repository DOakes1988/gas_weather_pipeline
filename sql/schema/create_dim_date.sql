CREATE TABLE dim_date (
	date DATE PRIMARY KEY,
	week_number INT,
	month_number INT,
	quarter_number INT,
	year INT,
	day_name TEXT,
	month_name TEXT,
	start_of_week DATE,
	start_of_month DATE,
	start_of_quarter DATE,
	start_of_year DATE
);