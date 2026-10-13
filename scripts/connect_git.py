"""Connect an existing ZIP download to Git while backing up its files locally."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPOSITORY = 'https://github.com/YmamG/Mawj.git'
BRANCH = 'django-templates'
PRIVATE_NAMES = {'.env', '.env.local', 'db.sqlite3', 'media', '.venv', 'venv', 'node_modules'}


def run_git(*args, cwd=None, capture=False):
    return subprocess.run(
        ['git', *args], cwd=cwd, check=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def connect(root, repository=REPOSITORY):
    root = Path(root).resolve()
    if not (root / 'manage.py').is_file() or not (root / 'requirements.txt').is_file():
        raise RuntimeError('Run this command inside the project folder containing manage.py and requirements.txt.')
    if not shutil.which('git'):
        raise RuntimeError('Git is not installed or not on PATH. Install Git for Windows and reopen the terminal.')
    if (root / '.git').exists():
        branch = run_git('branch', '--show-current', cwd=root, capture=True).stdout.decode().strip()
        if branch != BRANCH:
            raise RuntimeError(f'This folder already uses Git on branch {branch!r}. Review git status and switch to {BRANCH} before pulling.')
        remote = run_git('remote', 'get-url', 'origin', cwd=root, capture=True).stdout.decode().strip()
        if remote != repository:
            raise RuntimeError('This Git folder has a different origin. Review git remote -v before updating.')
        print('Already connected. Update with: git pull --ff-only origin django-templates')
        return None

    backup = root.parent / f'{root.name}-backup-{datetime.now():%Y%m%d-%H%M%S-%f}'
    # Include personal data and configuration in the local backup; omit reproducible caches.
    shutil.copytree(
        root, backup,
        ignore=shutil.ignore_patterns('.git', '.venv', 'venv', 'node_modules', '.next', '__pycache__', '*.pyc'),
    )
    print(f'Local backup: {backup}', flush=True)
    with tempfile.TemporaryDirectory(prefix='mawj-git-', dir=root.parent) as temporary:
        checkout = Path(temporary) / 'checkout'
        run_git('clone', '--single-branch', '--branch', BRANCH, repository, str(checkout))
        tracked = run_git('ls-files', '-z', cwd=checkout, capture=True).stdout.decode().split('\0')
        for filename in filter(None, tracked):
            parts = Path(filename).parts
            if any(part in PRIVATE_NAMES for part in parts) or filename.endswith('.sqlite3'):
                raise RuntimeError(f'The remote tracks a local-data path: {filename}. Backup retained; conversion stopped.')
        # Only copy versioned code. Existing DB, uploads, configuration and venv are preserved.
        for filename in filter(None, tracked):
            source = checkout / filename
            target = root / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        # Install Git metadata last, after the new code has copied successfully.
        shutil.move(str(checkout / '.git'), str(root / '.git'))
    run_git('status', '--short', cwd=root)
    print(f'Connected to branch {BRANCH}. Your backup remains at: {backup}')
    print('Future updates: git pull --ff-only origin django-templates')
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.', help='Existing Mawj project folder')
    args = parser.parse_args()
    try:
        connect(args.project)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f'Could not finish connecting Git: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
