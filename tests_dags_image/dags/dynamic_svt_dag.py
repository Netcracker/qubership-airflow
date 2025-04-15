from airflow.utils.dates import days_ago

from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator


def create_dag(branch_count, branch_length):
    args = {
        'owner': 'airflow',
        'start_date': days_ago(2),
    }

    dag = DAG(
        dag_id=dag_id,
        default_args=args,
        # schedule_interval="*/1 * * * *",
        schedule_interval=None,
        tags=['noop'],
        catchup=False
    )

    def noop():
        print("Running no-op task")

    for i in range(0, branch_count):
        branch = []
        for j in range(0, branch_length):
            task_id = f"{branch_count}_{branch_length}_task_{i}_{j}"
            task = PythonOperator(
                task_id=task_id,
                python_callable=noop,
                dag=dag,
            )
            branch.append(task)

            if j > 0:
                branch[j - 1] >> branch[j]

    return dag


BRANCHES_COUNT = [1, 5, 10, 20, 50, 100]
BRANCHES_LENGTH = [1, 5, 10, 20, 50, 100]

for branch_count in BRANCHES_COUNT:
    for branch_length in BRANCHES_LENGTH:
        dag_id = "dynamic_dag_%s_%s" % (branch_count, branch_length)
        globals()[dag_id] = create_dag(branch_count, branch_length)
