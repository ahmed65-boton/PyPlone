from pygls.server import LanguageServer
from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
)

server = LanguageServer("pyplone-lsp", "0.1.0")

VALID_STARTERS = {
    "get",
    "grove",
    "seed",
    "branch",
    "otherwise",
    "let",
    "give",
    "echo",
    "yes",
    "no",
    "nothing",
    "bloom",
    "leaf",
    "text",
    "popup",
}

BANNED_PYTHON = {
    "class": "grove",
    "def": "seed",
    "import": "get",
    "print": "echo",
    "return": "give",
    "True": "yes",
    "False": "no",
    "None": "nothing",
}


def validate_text(text):

    diagnostics = []
    lines = text.splitlines()

    for i, line in enumerate(lines):

        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        # Python keyword check
        for bad, good in BANNED_PYTHON.items():
            if bad in stripped.split():
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=i, character=0),
                            end=Position(line=i, character=len(line)),
                        ),
                        message=f"{bad} is not valid in PyLo. Use '{good}' instead.",
                        severity=DiagnosticSeverity.Error,
                        source="pyplone",
                    )
                )

        first_word = stripped.split()[0]

        if first_word not in VALID_STARTERS and "=" not in stripped:
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=i, character=0),
                        end=Position(line=i, character=len(line)),
                    ),
                    message="Unknown PyLo syntax.",
                    severity=DiagnosticSeverity.Error,
                    source="pyplone",
                )
            )

    return diagnostics


@server.feature("textDocument/didOpen")
def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):

    text = params.text_document.text
    diagnostics = validate_text(text)

    ls.publish_diagnostics(params.text_document.uri, diagnostics)


@server.feature("textDocument/didChange")
def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):

    text = params.content_changes[0].text
    diagnostics = validate_text(text)

    ls.publish_diagnostics(params.text_document.uri, diagnostics)


if __name__ == "__main__":
    server.start_io()
