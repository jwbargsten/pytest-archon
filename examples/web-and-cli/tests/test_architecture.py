import myapp


def test_logic_dependencies(archrule):
    (
        archrule("Logic dependencies")
        .match("myapp.logic*")
        .may_import("myapp.logic*")
        .should_not_import("myapp.*")
        .check(myapp)
    )


def test_cli_dependencies(archrule):
    (
        archrule("CLI dependencies")
        .match("myapp.cli*")
        .may_import("myapp.logic*")
        .should_not_import("myapp.*")
        .check(myapp)
    )


def test_web_dependencies(archrule):
    (
        archrule("Web dependencies")
        .match("myapp.web*")
        .may_import("myapp.logic*", "myapp.database*")
        .should_not_import("myapp.*")
        .check(myapp)
    )
