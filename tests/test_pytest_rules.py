from py3arch.pytest.plugin import rule

def test_rules2():
    (
        rule("abc", "def")
        .match(r"collect")
        .should_not_import("py3arch.import_finder")
        .check("py3arch", path=["."])
    )


def test_rules():
    pass
    # (
    #     rule("always import py3arch", comment="because I want it")
    #     .for_module(r".*")
    #     .without_module("special.module")
    #     .should_import("py3arch")
    # )

    # (
    #     rule("never import py3arch", comment="because I want it")
    #     .for_module(r".*")
    #     .should_not_import("py3arch")
    # )
    # api rule: only one module, the api, can be imported. submodules not
