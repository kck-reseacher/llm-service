import requests
import time
import traceback
import psycopg2 as pg2
from sentence_transformers import SentenceTransformer


def pre_base_prompt():
    prompt = f"""
    You are an AI Assistant specializing in analyzing anomaly detection results for multivariate time series data.
    The categories of information you are given are OS (Operating System), WAS (Web Application Server), and Service (A series of steps to process a user request).
    For each category, you will be given an indicator and explanation of the anomaly detected.
    """
    return prompt


def rule_prompt():
    prompt = f"""
    You must follow the rules below.
    1. You must answer in Korean.
    2. provide a clear and logical analysis based on the input data.
    3. analyze the cause of the anomaly detection and provide possible scenarios.
    4. Provide specific suggestions for possible actions for each anomaly.
    5. Maintain a consistent response format to improve readability.
    """
    return prompt


def anomaly_model_prompt():
    prompt = f"""
    ※ Model Overview:
    GDN (Graph Detection Network) is a model that detects anomalies in multivariate time-series data by leveraging Graph Attention Networks (GAT).
    It analyzes the relationships between time-series features and assigns attention scores to neighboring features.
    Using these attention scores, a weighted sum of the features is calculated and passed through an activation function to generate the final output.
    The contribution indicates the extent to which each metric influenced the anomaly detection and is expressed as a percentage.
    The sum of all contributions across metrics equals 100%.
    """
    return prompt


def metric_prompt(type):
    metric_prompt = {
        "OS": f"""
        OS (Operating System)

        "OS" refers to system software that controls a user's hardware, manages system resources, and provides general services to programs.
        We observe and monitor the "OS" target using the following metrics:
        1. swap_free:  Available swap memory (MB)
        2. network: Allowed transmission and reception capacity (bytes)
        3. rx_discards_delta: Received discarded bytes (bytes)
        4. cpu_user: CPU usage by user processes (%)
        5. rx_pkts_delta: The number of received packets
        6. rx_bytes_delta: Received bytes (bytes)
        7. cpu_usage: Total CPU usage (user + system + wait) (%)
        8. tx_bytes_delta: Transmitted bytes (bytes)
        9. cpu_idle: Available CPU percentage (%)
        10. memory_usage: Physical memory usage (%)
        11. cpu_system: CPU usage by system processes (%)
        12. swap_used: Used swap memory (MB)
        13. phy_total: Total physical memory (MB)
        14. swap_total: Total swap memory (MB)
        15. cpu_usage_max: Maximum total CPU usage (user + system + wait) (%)
        16. phy_free: Available physical memory (MB)
        17. memory_used: Used physical memory (MB)
        """,

        "WAS": f"""
        WAS (Web Application Server)

        "WAS" refers to a software framework that provides the functionality to create and run a web application and server environment.
        We observe and monitor the "WAS" target using the following metrics:
        1. tps: Transactions per second (txn_end_count)
        2. os_cpu_usage: OS CPU usage (%)
        3. sql_prepare_count: Total number of SQL prepare statements 
        4. sql_fetch_count: Total number of SQL fetch operations
        5. jvm_gc_time: Garbage collection time (ms)
        6. active_db_sessions: The number of active database connections 
        7. active_txns: The number of active service/transactions
        8. os_used_memory: OS memory usage (MB)
        9. sql_elapse: Total SQL execution time (ms)
        10. jvm_thread_count: The number of active threads 
        11. request_rate: The number of requests processed 
        12. jvm_gc_count: The number of garbage collection occurrences 
        13. os_memory_usage: OS memory usage percentage (%)
        14. jvm_heap_usage: JVM heap memory usage (%)
        15. open_socket_count: The number of open sockets 
        16. txn_elapse: Transaction execution time (ms)
        17. sql_exec_count: Total number of SQL executions 
        18. jvm_cpu_usage: JVM CPU usage (%)
        """,

        "service": f"""
        "SERVICE" refers to the overall targets composed of transactions such as account transfers and withdrawals.

        We observe and monitor the "SERVICE" target using the following metrics:
        1. elapse_avg: Average execution time for the entire E2E section (ms)
        2. elapse06_avg: Average execution time for MCI (ms)
        3. elapse07_avg: Average execution time for FEP (ms)
        4. elapse08_avg: Average execution time for EAI (ms)
        5. sql_elapse06: Average execution time for MCI SQL (ms)
        6. sql_elapse07: Average execution time for FEP SQL (ms)
        7. sql_elapse08: Average execution time for EAI SQL (ms)
        8. error_count:The number of errors in the entire E2E section
        9. exec_count: The number of executions in the entire E2E section
        """,

        "DB": f"""
        We observe and monitor the "DB" target using the following metrics:
        This refers to the metric for the ORACLE type among the product types corresponding to the DB type.

        1. enqueue_requests: Queue allocation request count 
        2. user_calls: User Calls per second for Oracle 
        3. library_cache_lock: Library cache lock event wait time (ms)
        4. os_cpu_usage: OS CPU usage (%)
        5. consistent_gets: The number of consistent get requests
        6. non_idle_wait_time: Non-idle wait time
        7. active_sessions: The number of active sessions
        8. session_logical_reads: The number of blocks read from memory per second
        9. file_io_wait_time: Total I/O wait time
        10. enqueue_waits: Queue allocation wait time
        11. physical_writes_direct: The number of blocks written directly to disk
        12. lock_waiting_sessions: The number of waiting sessions
        13. cpu_used_by_this_session: CPU time used by the session
        14. user_commits: The number of transaction commits performed
        15. physical_writes: Total number of data blocks written to disk
        16. log_file_sync: Log file sync' event wait time
        17. concurrency_wait_time: Concurrency wait time
        18. buffer_busy_waits: Buffer busy waits' event duration
        19. recursive_calls: The number of recursive calls
        20. row_cache_lock: Row cache lock' event wait time
        21. execute_count: The number of SQL executions
        22. physical_reads: The number of blocks read from disk per second
        23. file_io_service_time: Total I/O service time
        24. physical_reads_direct: The number of reads directly from disk
        25. cursor_pin_s_wait_on_x: The wait time for other sessions to access the cursor
        26. os_memory_usage: OS MEMORY usage (%)
        27. db_block_gets: The number of data in the current block
        28. db_file_sequential_read: Time taken for disk I/O completion (s)
        29. db_block_changes: The number of changes to the DB block
        30. parse_time_elapsed: Time taken to parse the SQL requested by the user
        31. user_rollbacks: The number of transaction rollbacks performed
        32. db_file_scattered_read: Wait time for completion of multi-block I/O request
        33. db_time: DB response time
        """
    }

    return metric_prompt[type]


def get_event_info(anomaly_features):
    query = f"""
        SELECT event_name, description, solutions, overlap_count
    FROM (
        SELECT event_name, description, solutions,
               array_length(
                   array(
                       SELECT unnest(affected_metrics) 
                       INTERSECT 
                       SELECT unnest(%s::text[])
                   ), 
                   1
               ) AS overlap_count
        FROM event_prompt_test
        GROUP BY event_name, description, solutions, affected_metrics
    ) AS subquery
    WHERE overlap_count >= 1  
    ORDER BY overlap_count DESC
    LIMIT 1;
    """
    db_conn_str = ""  # DB 접속 정보 필요
    try:
        conn = pg2.connect(db_conn_str)
        cursor = conn.cursor(cursor_factory=pg2.extras.RealDictCursor)
        cursor.execute(query, (anomaly_features,))
        result = cursor.fetchone()
        return result
    except Exception:
        tb = traceback.format_exc()
        print(f"{tb}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# 5. Ollama LLM 호출
def query_ollama():
    base = pre_base_prompt()
    rules = rule_prompt()
    model = anomaly_model_prompt()
    metric = metric_prompt('WAS')
    anomaly_features = "API GET from anomaly detection model output or DB query"
    event = get_event_info(anomaly_features)

    full_prompt = f"{base.strip()}\n\n{rules.strip()}\n\n{model.strip()}\n\n{metric.strip()}\n\n{event.strip()}"

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False
    }

    response = requests.post(f"http://10.10.34.20:11435/api/generate", json=payload)
    response.raise_for_status()
    return response.json()["response"].strip()


if __name__ == "__main__":
    ollama_serv_start = time.time()
    answer = query_ollama()
    print(f"ollama serv elapsed: {time.time() - ollama_serv_start}")

    print("💬 답변:", answer)
