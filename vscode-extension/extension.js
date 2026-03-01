/**
 * PyPLone VS Code Extension
 * Provides Run, Compile, and Emit Python commands for .pylo files
 */

const vscode = require('vscode');
const { exec, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

let outputChannel;

function activate(context) {
    outputChannel = vscode.window.createOutputChannel('PyPLone');

    // ── Run File ──────────────────────────────────────────────────────────
    const runCmd = vscode.commands.registerCommand('pyplone.runFile', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('PyPLone: No active editor.');
            return;
        }
        const filePath = editor.document.fileName;
        if (!filePath.endsWith('.pylo')) {
            vscode.window.showErrorMessage('PyPLone: Active file is not a .pylo file.');
            return;
        }

        // Save first
        editor.document.save().then(() => {
            const compiler = getCompilerPath(filePath);
            const cmd = `${compiler} "${filePath}" --run`;
            outputChannel.clear();
            outputChannel.show(true);
            outputChannel.appendLine(`▶ Running: ${path.basename(filePath)}`);
            outputChannel.appendLine(`  Command: ${cmd}`);
            outputChannel.appendLine('─'.repeat(60));

            const proc = exec(cmd, { cwd: path.dirname(filePath) });
            proc.stdout.on('data', d => outputChannel.append(d));
            proc.stderr.on('data', d => outputChannel.append(d));
            proc.on('close', code => {
                outputChannel.appendLine('─'.repeat(60));
                outputChannel.appendLine(`Process exited with code ${code}`);
            });
        });
    });

    // ── Compile to Exe ───────────────────────────────────────────────────
    const compileCmd = vscode.commands.registerCommand('pyplone.compileFile', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        const filePath = editor.document.fileName;

        editor.document.save().then(() => {
            const compiler = getCompilerPath(filePath);
            const cmd = `${compiler} "${filePath}"`;
            outputChannel.clear();
            outputChannel.show(true);
            outputChannel.appendLine(`⚙ Compiling: ${path.basename(filePath)}`);
            outputChannel.appendLine('─'.repeat(60));

            exec(cmd, { cwd: path.dirname(filePath) }, (err, stdout, stderr) => {
                if (stdout) outputChannel.append(stdout);
                if (stderr) outputChannel.append(stderr);
                if (err) {
                    outputChannel.appendLine(`✗ Compilation failed (code ${err.code})`);
                    vscode.window.showErrorMessage('PyPLone: Compilation failed. See output.');
                } else {
                    outputChannel.appendLine('✓ Compiled successfully!');
                    vscode.window.showInformationMessage('PyPLone: Compiled successfully!');
                }
            });
        });
    });

    // ── Emit Python ──────────────────────────────────────────────────────
    const emitCmd = vscode.commands.registerCommand('pyplone.emitPython', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        const filePath = editor.document.fileName;

        editor.document.save().then(() => {
            const compiler = getCompilerPath(filePath);
            const pyFile = filePath.replace('.pylo', '.py');
            const cmd = `${compiler} "${filePath}" --py -o "${pyFile}"`;

            exec(cmd, { cwd: path.dirname(filePath) }, (err, stdout, stderr) => {
                if (err) {
                    vscode.window.showErrorMessage(`PyPLone: ${stderr || err.message}`);
                    return;
                }
                // Open the generated .py file
                vscode.workspace.openTextDocument(pyFile).then(doc => {
                    vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
                });
                vscode.window.showInformationMessage(`PyPLone: Python source emitted: ${path.basename(pyFile)}`);
            });
        });
    });

    context.subscriptions.push(runCmd, compileCmd, emitCmd, outputChannel);

    // Status bar item
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBar.command = 'pyplone.runFile';
    statusBar.text = '$(play) PyPLone';
    statusBar.tooltip = 'Run .pylo file (F5)';

    // Show status bar only for .pylo files
    vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor && editor.document.fileName.endsWith('.pylo')) {
            statusBar.show();
        } else {
            statusBar.hide();
        }
    });

    if (vscode.window.activeTextEditor &&
        vscode.window.activeTextEditor.document.fileName.endsWith('.pylo')) {
        statusBar.show();
    }
    context.subscriptions.push(statusBar);
}

function getCompilerPath(filePath) {
    const config = vscode.workspace.getConfiguration('pyplone');
    const userPath = config.get('compilerPath', '');

    if (userPath && userPath.trim()) {
        return userPath;
    }

    // Auto-detect: look for PyPlone-compiler.py next to the file
    const dir = path.dirname(filePath);
    const candidates = [
        path.join(dir, 'PyPlone-compiler.py'),
        path.join(dir, '..', 'PyPlone-compiler.py'),
        'PyPlone-compiler.py',
    ];

    for (const c of candidates) {
        if (fs.existsSync(c)) {
            return `python "${c}"`;
        }
    }

    // Check for compiled exe
    const exeCandidates = [
        path.join(dir, 'PyPlone-compiler.exe'),
        path.join(dir, 'PyPlone-compiler'),
        'PyPlone-compiler',
    ];
    for (const c of exeCandidates) {
        if (fs.existsSync(c)) return `"${c}"`;
    }

    return 'python PyPlone-compiler.py';
}

function deactivate() {}

module.exports = { activate, deactivate };
