"""Build the Windows portable desktop release. Run with the build environment's Python."""
from pathlib import Path
import importlib.metadata
import hashlib
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'build'
DIST = ROOT / 'dist'
VERSION = '0.1.0'

def main():
    if sys.platform != 'win32':
        raise SystemExit('Build on Windows x64 using Python 3.13.')
    WORK.mkdir(exist_ok=True)
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir',
               '--windowed', '--noupx', '--name', 'FreeVoice',
               '--distpath', str(DIST), '--workpath', str(WORK / 'pyinstaller'),
               '--specpath', str(WORK), '--collect-all', 'pedalboard',
               '--collect-all', '_sounddevice_data', '--collect-all', '_soundfile_data',
               str(ROOT / 'freevoice.py')]
    subprocess.run(command, check=True, cwd=ROOT)
    app = DIST / 'FreeVoice'
    for name in ('LICENSE', 'PEDALBOARD-NOTICE', 'README.md'):
        shutil.copy2(ROOT / name, app / name)
    # Keep installed dependency license notices with the binary distribution.
    notices = app / 'THIRD_PARTY_NOTICES'
    notices.mkdir(exist_ok=True)
    inventory = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata['Name']
        inventory.append(f'{name}=={distribution.version}')
        for entry in distribution.files or []:
            if any(word in str(entry).lower() for word in ('license', 'copying', 'notice', 'copyright')):
                source = Path(distribution.locate_file(entry))
                if source.is_file():
                    relative = Path(*[p for p in entry.parts if p not in ('..', '.')])
                    target = notices / name / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    (notices / 'PACKAGES.txt').write_text('\n'.join(sorted(inventory)), encoding='utf-8')
    source_names = ['freevoice.py', 'requirements.txt', 'requirements-build.txt', 'build.py',
                    'README.md', 'LICENSE', 'PEDALBOARD-NOTICE', '.gitignore',
                    '.github/workflows/release.yml']
    source_zip = DIST / f'FreeVoice-{VERSION}-source.zip'
    with zipfile.ZipFile(source_zip, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in source_names:
            archive.write(ROOT / name, name)
    binary_zip = Path(shutil.make_archive(str(DIST / f'FreeVoice-{VERSION}-Windows-x64'), 'zip', DIST, 'FreeVoice'))
    checksums = '\n'.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}'
                          for path in (binary_zip, source_zip))
    (DIST / 'SHA256SUMS.txt').write_text(checksums + '\n', encoding='utf-8')
    print(binary_zip)

if __name__ == '__main__':
    main()
