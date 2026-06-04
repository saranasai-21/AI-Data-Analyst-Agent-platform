import ast


class CodeValidator:

    ALLOWED_IMPORTS = []

    FORBIDDEN_NODES = (

        ast.Import,
        ast.ImportFrom,

        ast.Global,
        ast.Nonlocal,

        ast.With,
        ast.AsyncWith,

        ast.Try,

        ast.Raise,

        ast.Lambda

    )

    FORBIDDEN_NAMES = {

        "eval",
        "exec",
        "compile",

        "open",

        "__import__",

        "globals",
        "locals",

        "input",

        "exit",
        "quit"

    }

    FORBIDDEN_MODULES = {

        "os",
        "sys",
        "subprocess",
        "socket",
        "shutil",
        "pathlib",
        "requests",
        "httpx"
    }

    @classmethod
    def validate(
        cls,
        code
    ):

        tree = ast.parse(code)

        for node in ast.walk(tree):

            if isinstance(
                node,
                cls.FORBIDDEN_NODES
            ):

                raise ValueError(
                    f"Forbidden syntax: {type(node).__name__}"
                )

            if isinstance(
                node,
                ast.Name
            ):

                if node.id in cls.FORBIDDEN_NAMES:

                    raise ValueError(
                        f"Forbidden name: {node.id}"
                    )

            if isinstance(
                node,
                ast.Attribute
            ):

                if hasattr(node, "value"):

                    if hasattr(
                        node.value,
                        "id"
                    ):

                        module_name = (
                            node.value.id
                        )

                        if module_name in cls.FORBIDDEN_MODULES:

                            raise ValueError(
                                f"Forbidden module: {module_name}"
                            )

        return True