WITH dates_ AS (
	SELECT generate_series(
		'1997-01-10', 
		current_date + INTERVAL '2 year', 
		'1 day'
	)::date AS d
),

helpers_ AS (
	SELECT
		dates_.*,
		EXTRACT(DAY FROM d)::INTEGER AS day_number,
		EXTRACT(MONTH FROM d) AS month_number,
		EXTRACT(QUARTER FROM d) AS quarter_number,
		EXTRACT(YEAR FROM d) AS year,
		TRIM(TO_CHAR(d, 'Day')) AS day_name,
		TRIM(TO_CHAR(d, 'Month')) AS month_name,
		EXTRACT(DOW FROM d)::INTEGER AS dow_,
		DATE_TRUNC('month', d)::DATE AS start_of_month,
		DATE_TRUNC('quarter', d)::DATE AS start_of_quarter,
		DATE_TRUNC('year', d)::DATE AS start_of_year
	FROM dates_
),

dow_ AS(
	SELECT
		helpers_.*,
		CASE WHEN dow_ = 6
			THEN d
			ELSE d - dow_ - 1
		END AS start_of_week	
	FROM helpers_
),

week_num AS (
	SELECT
		d.*,
		DENSE_RANK() OVER(ORDER BY d.start_of_week) AS week_number
	FROM dow_ AS d
)

INSERT INTO dim_date (
	date, 
	week_number, 
	month_number, 
	quarter_number, 
	year, 
	day_name, 
	month_name, 
	start_of_week, 
	start_of_month, 
	start_of_quarter, 
	start_of_year)
	
SELECT
	w.d,
	w.week_number,
	w.month_number,
	w.quarter_number,
	w.year,
	w.day_name,
	w.month_name,
	w.start_of_week,
	w.start_of_month,
	w.start_of_quarter,
	w.start_of_year
FROM week_num AS w