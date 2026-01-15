import copy
import urllib.request
import json
import yaml
import argparse

from jsonschema import validate

url = (
    "https://raw.githubusercontent.com/apache/airflow/"
    "3314d54c3595f410a147790b7119392a0922268c/chart/values.schema.json"
)
global_params_to_keep = ["$schema", "description", "type", "definitions"]
values_params_to_keep = [
    "fullnameOverride",
    "revisionHistoryLimit",
    "securityContexts",
    "nodeSelector",
    "affinity",
    "topologySpreadConstraints",
    "labels",
    "airflowConfigAnnotations",
    "airflowLocalSettings",
    "executor",
    "env",
    "volumes",
    "volumeMounts",
    "enableBuiltInSecretEnvVars.AIRFLOW__CORE__SQL_ALCHEMY_CONN",
    "enableBuiltInSecretEnvVars.AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
    "enableBuiltInSecretEnvVars.AIRFLOW_CONN_AIRFLOW_DB",
    "extraEnv",
    "extraEnvFrom",
    "extraSecrets",
    "extraConfigMaps",
    "data",
    "fernetKey",
    "fernetKeySecretName",
    "fernetKeySecretAnnotations",
    "apiSecretKey",
    "apiSecretAnnotations",
    "apiSecretKeySecretName",
    "jwtSecret",
    "jwtSecretName",
    "jwtSecretAnnotations",
    # "kerberos",
    "workers.replicas",
    "workers.command",
    "workers.args",
    "workers.hpa",
    "workers.persistence.enabled",
    "workers.persistence.size",
    "workers.persistence.storageClassName",
    # "workers.kerberosSidecar.enabled",
    # "workers.kerberosSidecar.resources",
    # "workers.kerberosInitContainer.enabled",
    # "workers.kerberosInitContainer.resources",
    "workers.resources",
    "workers.extraVolumes",
    "workers.hostAliases",
    "workers.extraVolumeMounts",
    "workers.logGroomerSidecar",
    "scheduler.replicas",
    "scheduler.command",
    "scheduler.args",
    "scheduler.resources",
    "scheduler.logGroomerSidecar",
    "dagProcessor.replicas",
    "dagProcessor.command",
    "dagProcessor.args",
    "dagProcessor.resources",
    "dagProcessor.logGroomerSidecar",
    "createUserJob.enabled",
    "createUserJob.defaultUser",
    "createUserJob.resources",
    "createUserJob.useHelmHooks",
    "migrateDatabaseJob.enabled",
    "migrateDatabaseJob.jobAnnotations",
    "migrateDatabaseJob.serviceAccount.annotations",
    "migrateDatabaseJob.resources",
    "migrateDatabaseJob.useHelmHooks",
    "apiServer.replicas",
    "apiServer.allowPodLogReading",
    "apiServer.command",
    "apiServer.args",
    "apiServer.strategy",
    "apiServer.resources",
    "apiServer.apiServerConfig",
    "statsd.enabled",
    "statsd.resources",
    "databaseCleanup.enabled",
    "databaseCleanup.resources",
    "config",
    "logs.persistence.enabled",
    "logs.persistence.size",
    "logs.persistence.storageClassName",
]


def reuse_existing_params():
    community_schema = json.loads(urllib.request.urlopen(url).read())
    community_schema["properties"]["securityContexts"]["properties"]["containers"] = \
        community_schema["properties"]["securityContexts"]["properties"]["container"]
    customized_schema_internal = {}
    for global_param in global_params_to_keep:
        customized_schema_internal[global_param] = copy.deepcopy(
            community_schema[global_param]
        )
    customized_schema_internal["properties"] = {}

    for values_param in values_params_to_keep:
        values_param_path_array = values_param.split(".")
        path_counter = 0
        current_customized_element = customized_schema_internal
        current_community_element = community_schema
        for values_param_single in values_param_path_array:
            path_counter = path_counter + 1
            if (
                "properties" in current_customized_element
                and values_param_single in current_customized_element["properties"]
            ):
                current_customized_element = current_customized_element["properties"][
                    values_param_single
                ]
                current_community_element = current_community_element["properties"][
                    values_param_single
                ]
                continue
            if path_counter == len(values_param_path_array):
                current_customized_element["properties"][values_param_single] = (
                    copy.deepcopy(
                        current_community_element["properties"][values_param_single]
                    )
                )
                continue
            else:
                current_customized_element["properties"][values_param_single] = (
                    copy.deepcopy(
                        current_community_element["properties"][values_param_single]
                    )
                )
                current_customized_element = current_customized_element["properties"][
                    values_param_single
                ]
                current_community_element = current_community_element["properties"][
                    values_param_single
                ]
                current_customized_element["properties"] = {}
                if "additionalProperties" in current_customized_element:
                    current_customized_element["additionalProperties"] = True
    return customized_schema_internal


def compare_complex_element(
    values_param, current_schema_element, values_default, customized_schema_internal
):
    for key, value in values_default.items():
        if "properties" not in current_schema_element:
            ref = current_schema_element["$ref"]
            element_path = ref.replace("#/", "", 1).split("/")
            ref_value = customized_schema_internal
            for ref_param in element_path:
                ref_value = ref_value[ref_param]
            if "default" in ref_value["properties"][key]:
                if value == ref_value["properties"][key]["default"]:
                    print(f"values for {values_param}.{key} are the same!")
                else:
                    print(f"values for {values_param}.{key} are different!")
                    raise ValueError(
                        "Updating in refs is not supported since it might affect Airflow defaults"
                    )
                continue
            else:
                compare_complex_element(
                    f"{values_param}.{key}",
                    ref_value["properties"][key],
                    value,
                    customized_schema_internal,
                )
        elif "default" in current_schema_element["properties"][key]:
            if value == current_schema_element["properties"][key]["default"]:
                print(f"values for {values_param}.{key} are the same!")
            else:
                print(f"values for {values_param}.{key} are different, updating...")
                current_schema_element["properties"][key]["default"] = value
        else:
            compare_complex_element(
                f"{values_param}.{key}",
                current_schema_element["properties"][key],
                value,
                customized_schema_internal,
            )


def update_defaults_for_existing_schema(
    values_data_internal, customized_schema_internal
):
    for values_param in values_params_to_keep:
        values_param_path_array = values_param.split(".")
        values_default = values_data_internal
        current_schema_element = customized_schema_internal
        for values_param_single in values_param_path_array:
            current_schema_element = current_schema_element["properties"][
                values_param_single
            ]
            values_default = values_default[values_param_single]
        if "default" not in current_schema_element:
            compare_complex_element(
                values_param,
                current_schema_element,
                values_default,
                customized_schema_internal,
            )
            continue
        if values_default == current_schema_element["default"]:
            print(f"values for {values_param} are the same!")
        else:
            print(f"values for {values_param} are different, updating...")
            current_schema_element["default"] = values_default


def validate_properties_in_defaults(values, default_values_schema, param_path):
    for key, value in default_values_schema["properties"].items():
        if key not in values:
            print(f"{param_path}{key} is not present in values!")
            raise ValueError(f"{param_path}{key} is not present in values!")
        elif "properties" in value:
            validate_properties_in_defaults(values[key], value, f"{param_path}{key}.")


def validate_defaults(values, default_values_schema, param_path):
    for key, value in values.items():
        if key in default_values_schema["properties"]:
            if "default" in default_values_schema["properties"][key]:
                if default_values_schema["properties"][key]["default"] != value:
                    print(f"{param_path}{key} is different!")
                    raise ValueError(f"{param_path}{key} is different!")
            else:
                validate_defaults(
                    value,
                    default_values_schema["properties"][key],
                    f"{param_path}{key}.",
                )


def remove_common_key(current_element, excessive_key):
    if isinstance(current_element, dict):
        for key in list(current_element.keys()):
            if key == excessive_key:
                del current_element[key]
            else:
                remove_common_key(current_element[key], excessive_key)


def replace_common_key(current_element, old_key, new_key):
    if isinstance(current_element, dict):
        for key in list(current_element.keys()):
            if key == old_key:
                current_element[new_key] = current_element[key]
                del current_element[key]
            else:
                replace_common_key(current_element[key], old_key, new_key)


def add_qubership_custom_schema(qubership_schema_internal, customized_schema_internal):
    replace_common_key(qubership_schema_internal, "airflow_base_ref", "$ref")
    customized_schema_internal["properties"] = (
        customized_schema_internal["properties"]
        | qubership_schema_internal["properties"]
    )


parser = argparse.ArgumentParser()
parser.add_argument("--complete_values", default="qubership_values.yaml")
parser.add_argument("--additional_schema", default="qubership_values.schema.json")
parser.add_argument("--target_schema", default="target/values.schema.json")
args = parser.parse_args()
customized_schema = reuse_existing_params()
with open(args.complete_values, "r") as default_qubership_values:
    qubership_values = yaml.safe_load(default_qubership_values)
update_defaults_for_existing_schema(qubership_values, customized_schema)
remove_common_key(customized_schema, "x-docsSection")
with open(args.additional_schema, "r") as file:
    qubership_schema = json.load(file)
add_qubership_custom_schema(qubership_schema, customized_schema)
# print(json.dumps(customized_schema, indent=4))

validate(instance=qubership_values, schema=customized_schema)
validate_properties_in_defaults(qubership_values, qubership_schema, "")
validate_defaults(qubership_values, qubership_schema, "")
with open(args.target_schema, "w") as values_schema_json:
    json.dump(customized_schema, values_schema_json, indent=4)  # type: ignore
