from pytest_archon.collect import (
    collect_imports_from_path,
)


# so, it seems that airflow has some really weird stuff going on in
# https://github.com/apache/airflow/blob/main/airflow/kubernetes/__init__.py
# they create a ModuleType on the fly, leading to a
# "ValueError: airflow.kubernetes.pod_generator.__spec__ is None"
# Now ValueError is caught and considered the same as "ModuleNotFoundError"
def test_collect_modules_for_hacky_airflow_kubernetes_module(create_testset):
    code = """\
from types import ModuleType
import sys
full_module_name = "airflow.kubernetes.pod_generator"
module_type = ModuleType(full_module_name)
sys.modules.setdefault(full_module_name, module_type)
"""

    path = create_testset(
        ("mymodule.py", "from airflow.kubernetes import pod_generator"),
        ("airflow/__init__.py", ""),
        ("airflow/kubernetes/__init__.py", code),
    )
    from airflow.kubernetes import pod_generator  # noqa: F401

    collected = {name: imports for name, imports in collect_imports_from_path(path, "pkg")}

    assert "pkg.mymodule" in collected
    assert "pkg.airflow.kubernetes" in collected
    assert "airflow.kubernetes.pod_generator" in collected["pkg.mymodule"]
