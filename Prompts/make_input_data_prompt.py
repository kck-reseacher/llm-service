"""
Service의 경우, DB에서 값들을 다 가져오고 분석을 시켜야 한다.
예를 들어, 해당 문제는 어떠한 구간에서 문제가 발생했다.
dbsln_result_service_performance 테이블에서 결과 가져오기
    - time
    - target_id

xaiops_meta_metric 테이블에서 metric_id와 매핑되는 metric_desc
    - metric_id
"""


def generate_service_input_prompt(time_of_anomaly: str, target_name: str, instance_type: str, anomalous_metrics: dict):
    """
    OS WAS 입력 프롬프트를 동적으로 생성하며, 각 지표의 정상 범위와 현재 값을 포함.

    :param time_of_anomaly: 이상이 탐지된 시각
    :param target_name: 이상이 발생한 대상 이름
    :param instance_type: 이상이 발생한 인스턴스 유형
    :param anomalous_metrics: 튜플 리스트로, 각 요소는 (지표명, 정상 범위, 현재 값) 형태입니다.
                              정상 범위는 (최소값, 최대값) 형태의 튜플이어야 합니다.
    :return: 포맷팅된 프롬프트 문자열
    """
    metrics_str = ""
    for idx, (metric_name, (lower, upper, avg, real_value)) in enumerate(anomalous_metrics.items(), start=1):
        # metrics_str += f" 4.{idx}. {metric_name}: The percentage contributing to the anomaly is {contribution}%, and the actual value is {actual_value}.\n"
        metrics_str += (
            f" 4.{idx}. {metric_name}: The predicted allowable range is {lower} to {upper}, "
            f"the average value is {avg}, and the current actual value is {real_value}.\n"
        )

    prompt = f"""

1. Time of anomaly: {time_of_anomaly}
2. Target Name: {target_name}
3. Instance type of anomaly: {instance_type}
4. Anomalous metrics:
{metrics_str}""".strip()

    return prompt


def generate_os_was_input_prompt(time_of_anomaly: str, target_id: str, instance_type: str, anomalous_metrics: dict):
    """
    OS WAS 입력 프롬프트를 동적으로 생성합니다.

    :param time_of_anomaly: 이상이 감지된 시각
    :param target_id: 이상이 발생한 대상 이름
    :param instance_type: 이상이 발생한 인스턴스 유형
    :param anomalous_metrics: (지표명, 기여도 퍼센트, 실제 값) 형태의 튜플 리스트
    :return: 포맷팅된 프롬프트 문자열
    """
    metrics_str = ""
    for idx, (metric_name, (lower, upper, avg, real_value)) in enumerate(anomalous_metrics.items(), start=1):
        # metrics_str += f" 4.{idx}. {metric_name}: The percentage contributing to the anomaly is {contribution}%, and the actual value is {actual_value}.\n"
        metrics_str += (
            f" 4.{idx}. {metric_name}: The predicted allowable range is {lower} to {upper}, "
            f"the average value is {avg}, and the current actual value is {real_value}.\n"
        )


    prompt = f"""

1. Time of anomaly: {time_of_anomaly}
2. Target Name: {target_id}
3. Instance type of anomaly: {instance_type}
4. Anomalous metrics:
{metrics_str}""".strip()

    return prompt


def generate_metrics_definition_prompt(metrics: dict):
    """
    Metrics 정의 형식 만들기
    :param metrics: 정의가 필요한 지표들
    :return:
    """
    metrics_definition_str = ""
    for metric_name, metric_definition in metrics.items():
        metrics_definition_str += (
            f"\t\t- {metric_name}: {metric_definition}\n"
        )

    return metrics_definition_str
