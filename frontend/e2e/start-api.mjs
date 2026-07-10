import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { existsSync } from 'node:fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = resolve(__dirname, '..', '..');

const isWindows = process.platform === 'win32';
const venvPython = resolve(rootDir, isWindows ? 'venv/Scripts/python.exe' : 'venv/bin/python');
const python = existsSync(venvPython) ? venvPython : 'python';

const env = {
  ...process.env,
  AI_PROVIDER: 'mock',
  EMAIL_PROVIDER: 'memory',
  STORAGE_PROVIDER: 'memory',
  FASTAPI_DATABASE_URI: 'sqlite:///fastapi_e2e.db',
};

const seed = spawn(python, ['frontend/e2e/seed.py'], { cwd: rootDir, env });
seed.stdout.on('data', (data) => process.stdout.write(data));
seed.stderr.on('data', (data) => process.stderr.write(data));

seed.on('close', (code) => {
  if (code !== 0) {
    process.exit(code ?? 1);
  }

  const proc = spawn(python, ['-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8001'], {
    cwd: rootDir,
    env,
  });

  proc.stdout.on('data', (data) => process.stdout.write(data));
  proc.stderr.on('data', (data) => process.stderr.write(data));

  process.on('SIGTERM', () => {
    proc.kill('SIGTERM');
  });

  process.on('exit', () => {
    proc.kill();
  });
});
