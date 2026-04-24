import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import littlefs

WATCH_DIR = "./src"
OUTPUT_BIN = "./binaries/fs.bin"
EXTENSIONS = {".py", ".json", ".txt"}

BLOCK_SIZE = 4096
PAGE_SIZE   = 256
FS_SIZE     = 0x200000  # 2 MB

def gerar_fs_bin():
    print("Gerando fs.bin...")
    Path("./binaries").mkdir(exist_ok=True)

    try:
        fs = littlefs.LittleFS(
            block_size=BLOCK_SIZE,
            block_count=FS_SIZE // BLOCK_SIZE,
        )

        src_path = Path(WATCH_DIR)
        for file_path in src_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in EXTENSIONS:
                rel = file_path.relative_to(src_path)
                lfs_path = "/" + str(rel).replace(os.sep, "/")

                # Cria subdiretórios se necessário
                parent = str(rel.parent).replace(os.sep, "/")
                if parent != ".":
                    try:
                        fs.mkdir("/" + parent)
                    except Exception:
                        pass

                with open(file_path, "rb") as f:
                    data = f.read()
                with fs.open(lfs_path, "wb") as f:
                    f.write(data)
                print(f"  + {lfs_path} ({len(data)} bytes)")

        with open(OUTPUT_BIN, "wb") as f:
            f.write(bytes(fs.context.buffer))

        print(f" fs.bin gerado com sucesso! ({FS_SIZE // 1024} KB)")

    except Exception as e:
        print(f" Erro ao gerar fs.bin: {e}")


class RebuildHandler(FileSystemEventHandler):
    def __init__(self):
        self._last_run = 0
        self._cooldown = 1.5

    def on_modified(self, event):
        self._trigger(event)

    def on_created(self, event):
        self._trigger(event)

    def _trigger(self, event):
        if event.is_directory:
            return
        if Path(event.src_path).suffix not in EXTENSIONS:
            return
        now = time.time()
        if now - self._last_run < self._cooldown:
            return
        self._last_run = now
        print(f"\n Mudança detectada: {event.src_path}")
        gerar_fs_bin()


if __name__ == "__main__":
    print(f"  Monitorando: {Path(WATCH_DIR).resolve()}")
    print("─" * 40)

    gerar_fs_bin()

    handler = RebuildHandler()
    observer = Observer()
    observer.schedule(handler, WATCH_DIR, recursive=True)
    observer.start()

    print("\n Watcher ativo! Salve qualquer arquivo para atualizar o fs.bin")
    print("   (Ctrl+C para parar)\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n Watcher encerrado.")
    observer.join()