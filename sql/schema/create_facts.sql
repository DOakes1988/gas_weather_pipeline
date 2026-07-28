CREATE TABLE fact_gas_price (
	date DATE,
	gas_price NUMERIC,
	price_region INT,
	PRIMARY KEY (date, price_region),

	CONSTRAINT fk_region
		FOREIGN KEY (price_region)
		REFERENCES dim_region (region_key),

	CONSTRAINT fk_date
		FOREIGN KEY (date)
		REFERENCES dim_date (date)
);


CREATE TABLE fact_gas_storage (
	date DATE,
	gas_total NUMERIC,
	storage_region INT,
	PRIMARY KEY (date, storage_region),

	CONSTRAINT fk_region
		FOREIGN KEY (storage_region)
		REFERENCES dim_region (region_key),

	CONSTRAINT fk_date
		FOREIGN KEY (date)
		REFERENCES dim_date (date)
);


CREATE TABLE fact_degree_days (
	date DATE,
	degree_days INT,
	degree_day_region INT,
	PRIMARY KEY (date, degree_day_region),

	CONSTRAINT fk_region
		FOREIGN KEY (degree_day_region)
		REFERENCES dim_region (region_key),

	CONSTRAINT fk_date
		FOREIGN KEY (date)
		REFERENCES dim_date (date)
);