from typing import Optional
from pyspark.sql import SparkSession # type: ignore
from pyspark.sql.dataframe import DataFrame # type: ignore

def query_2(output_table_name: str) -> str:
    query = f"""
    WITH yesterday AS (
        SELECT
            *
        FROM
            {output_table_name}
        WHERE
            DATE = DATE('2022-12-31')
    ),
    today AS (
        SELECT
            wbe.user_id,
            d.browser_type,
            ARRAY_AGG(DISTINCT CAST(date_trunc('day', wbe.event_time) AS DATE)) AS event_date_array
        FROM
            devices d
        LEFT JOIN web_events wbe
        ON
            d.device_id = wbe.device_id 
        WHERE
            date_trunc('day', wbe.event_time) = DATE('2023-01-01')
        AND wbe.event_time IS NOT NULL
        GROUP BY
            wbe.user_id,
            d.browser_type
    )
    SELECT
        COALESCE(y.user_id, t.user_id) AS user_id,
        COALESCE(y.browser_type, t.browser_type) AS browser_type,
        CASE
            WHEN y.dates_active IS NOT NULL 
            THEN event_date_array || y.dates_active
            ELSE event_date_array
        END AS dates_active,
        DATE('2023-01-01') AS DATE
    FROM
        yesterday y
    FULL OUTER JOIN today t
    ON
        y.user_id = t.user_id
    """
    return query

def job_2(spark_session: SparkSession, output_table_name: str) -> Optional[DataFrame]:
    output_df = spark_session.table(output_table_name)
    output_df.createOrReplaceTempView(output_table_name)
    return spark_session.sql(query_2(output_table_name))

def main():
    output_table_name: str = "user_devices_cumulated"
    spark_session: SparkSession = (SparkSession.builder.master("local").appName("job_2").getOrCreate()
    )
    output_df = job_2(spark_session, output_table_name)
    output_df.write.mode("overwrite").insertInto(output_table_name)

if __name__ == "__main__":
    main()