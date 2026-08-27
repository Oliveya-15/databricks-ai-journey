CREATE OR REFRESH STREAMING TABLE current_employees_bronze_sdp
COMMENT "Raw employee data ingested from CSV files in the myfiles volume."
AS SELECT *
FROM STREAM read_files(
  '/Volumes/dbacademy/get_started_de/myfiles/',
  format => 'csv',
  header => true,
  inferSchema => true
);

CREATE OR REFRESH MATERIALIZED VIEW current_employees_silver_sdp(
  CONSTRAINT valid_id EXPECT (ID IS NOT NULL),
  CONSTRAINT valid_name EXPECT (FirstName IS NOT NULL)
)
COMMENT "Cleaned and enriched employee data with data quality expectations."
AS SELECT
  ID,
  FirstName,
  Country,
  UPPER(Role) AS Role,
  current_timestamp() AS processed_timestamp,
  current_date() AS processed_date
FROM current_employees_bronze_sdp;

CREATE OR REFRESH MATERIALIZED VIEW total_roles_gold_sdp
COMMENT "Employee count by role — business-ready aggregation."
AS SELECT
  Role,
  COUNT(*) AS TotalEmployees
FROM current_employees_silver_sdp
GROUP BY Role;