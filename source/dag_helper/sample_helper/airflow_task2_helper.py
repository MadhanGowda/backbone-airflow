"""Database Helper File."""
import csv
import logging
from airflow.models import Variable
from airflow.hooks.postgres_hook import PostgresHook


def database_helper(*args, **kwargs):
    """Database display."""
    db_connection = PostgresHook(
        postgres_conn_id='airflow_postgres',
        schema='sample_airflow',
    )
    dcm_data = "SELECT distinct(Placement) from test.DCM_TEST_DATA1;"
    meta_data = "SELECT * from test.metadata;"
    res_dcm_data = db_connection.get_records(dcm_data)
    res_meta_data = db_connection.get_records(meta_data)
    logging.info(res_dcm_data)
    logging.info(res_meta_data)


def read_distinct_raw_data_from_db(*args, **kwargs):
    """Read distinct raw data from the Database."""
    db_connection = PostgresHook(
        postgres_conn_id='airflow_postgres',
        schema='sample_airflow',
    )
    distinct_data = '''SELECT distinct Placement, Placement_ID from
    test.DCM_TEST_DATA1;'''
    res_distinct_placement_data = db_connection.get_records(distinct_data)
    # load the raw DCM data.
    kwargs['ti'].xcom_push(
        key='unloaded_data',
        value=res_distinct_placement_data
    )


def read_meta_data_from_db(*args, **kwargs):
    """Read meta data from the Database."""
    db_connection = PostgresHook(
        postgres_conn_id='airflow_postgres',
        schema='sample_airflow',
    )
    meta_data = "SELECT * from test.metadata;"  # loads the meta data.
    res_meta_data = db_connection.get_records(meta_data)
    kwargs['ti'].xcom_push(
        key='unloaded_data1',
        value=res_meta_data
    )


def split_placement_data(*args, **kwargs):
    """The Placement column of Raw Data is split."""
    ti = kwargs['ti']
    res_distinct_placement_data = ti.xcom_pull(
        task_ids='read_distinct_raw_data',
        key='unloaded_data'
    )
    print(res_distinct_placement_data)
    res_meta_data = ti.xcom_pull(
        task_ids='read_meta_data',
        key='unloaded_data1'
    )
    print(res_meta_data)
    list_of_new_data = []
    list_intermediate = []
    split_data_var = Variable.get("split_value")
    # Split the data based on split value.
    for each in res_distinct_placement_data:
        split_data = each[0].split(split_data_var)
        for index, value in enumerate(split_data):
            list_intermediate = [each[1],  # Placement_ID
                                 index,  # Index
                                 res_meta_data[index],  # Key_name
                                 value  # Value
                                 ]
            list_of_new_data.append(list_intermediate)
    kwargs['ti'].xcom_push(
        key='unloaded_data2',
        value=list_of_new_data
    )


def store_data_in_csv(*args, **kwargs):
    """Store data to CSV."""
    ti = kwargs['ti']
    list_of_new_data = ti.xcom_pull(
        task_ids='split_data',
        key='unloaded_data2'
    )
    list_headings = ['Placement_ID', 'Index', 'Key_name', 'Value']
    for i in range(0, len(list_of_new_data)):
        # loading the data to csv file.
        file = open('source/data/Split_Data.csv', 'w', newline='')
        writer = csv.writer(file)
        writer.writerow(list_headings)
        writer.writerows(list_of_new_data)
    file.close()
