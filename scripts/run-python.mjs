import { existsSync } from 'node:fs';
import { spawn, spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const windows = process.platform === 'win32';
const localPython = join(root, '.venv', ...(windows ? ['Scripts', 'python.exe'] : ['bin', 'python']));
const candidates = [
    ...(process.env.DI_PYTHON ? [[process.env.DI_PYTHON, []]] : []),
    ...(existsSync(localPython) ? [[localPython, []]] : []),
    ...(process.env.VIRTUAL_ENV ? [[join(process.env.VIRTUAL_ENV, ...(windows ? ['Scripts', 'python.exe'] : ['bin', 'python'])), []]] : []),
    ...(!windows ? [['python3', []]] : []),
    ['python', []],
    ...(windows ? [['py', ['-3']]] : [])
];
const interpreter = candidates.find(([command, prefix]) => {
    const result = spawnSync(command, [...prefix, '-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'], { windowsHide: true });
    return result.status === 0;
});

if (!interpreter) {
    console.error('Python 3.10+ was not found. Install Python, create .venv, and install backend/requirements.txt. Set DI_PYTHON to choose an interpreter.');
    process.exit(1);
}

const [command, prefix] = interpreter;
const child = spawn(command, [...prefix, ...process.argv.slice(2)], { stdio: 'inherit', windowsHide: true });
child.on('error', error => {
    console.error(`Unable to start Python: ${error.message}`);
    process.exitCode = 1;
});
child.on('exit', code => { process.exitCode = code ?? 1; });
for (const signal of ['SIGINT', 'SIGTERM']) {
    process.on(signal, () => { if (!child.killed) child.kill(signal); });
}
