const path = require("path");
const vscode = require("vscode");
const { LanguageClient, TransportKind } = require("vscode-languageclient/node");

let client;

function activate(context) {

    const serverModule = context.asAbsolutePath(
        path.join("server", "server.py")
    );

    const pythonPath = "F:\\PyPlone\\python\\python.exe";

    const serverOptions = {
        command: pythonPath,
        args: [serverModule],
        transport: TransportKind.stdio
    };

    const clientOptions = {
        documentSelector: [
            { scheme: "file", language: "pyplone" }
        ],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher("**/*.pylo")
        }
    };

    client = new LanguageClient(
        "pyploneLanguageServer",
        "PyPlone Language Server",
        serverOptions,
        clientOptions
    );

    context.subscriptions.push(client.start());
}

function deactivate() {
    if (!client) {
        return undefined;
    }
    return client.stop();
}

module.exports = {
    activate,
    deactivate
};