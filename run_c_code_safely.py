import tempfile
import subprocess
import os
import shutil
from threading import Thread
import uuid

def read_stream(stream, buffer):
    try:
        while True:
            line = stream.readline()
            if not line:
                break
            buffer.append(line)
    finally:
        stream.close()

def run_c_code_safely(code_str, input_data_list=[""], wait_time=1, compile_timeout=10, execution=True):
    if not input_data_list:
        input_data_list = [""]

    temp_dir = tempfile.mkdtemp()
    results = []

    try:
        # Cソースコードを一時ファイルに書き込み
        code_file = os.path.join(temp_dir, "program.c")
        with open(code_file, "w") as f:
            f.write(code_str)

        # コンパイル
        compile_cmd = [
            "docker", "run", "--rm", "--network", "none",
            "-v", f"{temp_dir}:/app", "c_runner_base",
            "bash", "-c", "gcc /app/program.c -o /app/program"
        ]
        compile_result = subprocess.run(
            compile_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=compile_timeout
        )

        if compile_result.returncode != 0:
            return {
                "success": False,
                "results": [],
                "compile_error": compile_result.stderr.decode(errors="replace")
            }

        if not execution:
            return {
                "success": True,
                "results": [],
                "compile_error": None
            }

        # 実行＆採点処理
        for input_data in input_data_list:
            container_name = f"c_runner_{uuid.uuid4().hex[:12]}"
            try:
                run_cmd = [
                    "docker", "run", "-i", "--rm", "--init", "--network", "none",
                    "--name", container_name,
                    "-v", f"{temp_dir}:/app", "c_runner_base",
                    "stdbuf", "-oL", "/app/program"
                ]

                proc = subprocess.Popen(
                    run_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # 入力送信（必要なら改行追加）
                if input_data:
                    if not input_data.endswith("\n"):
                        input_data += "\n"
                    proc.stdin.write(input_data.encode())
                    proc.stdin.flush()
                # stdinは開いたまま（閉じない）

                stdout_lines = []
                stderr_lines = []

                # 非同期に出力を読み取り
                t_out = Thread(target=read_stream, args=(proc.stdout, stdout_lines))
                t_err = Thread(target=read_stream, args=(proc.stderr, stderr_lines))
                t_out.start()
                t_err.start()

                try:
                    proc.wait(timeout=wait_time)
                    status = "ok" if proc.returncode == 0 else "runtime_error"
                except subprocess.TimeoutExpired:
                    proc.kill()
                    subprocess.run(
                        ["docker", "rm", "-f", container_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    status = "timeout"

                t_out.join(timeout=1)
                t_err.join(timeout=1)

                results.append({
                    "input": input_data,
                    "returncode": proc.returncode if status != "timeout" else None,
                    "output": b''.join(stdout_lines).decode(errors="replace"),
                    "error": b''.join(stderr_lines).decode(errors="replace"),
                    "status": status
                })

            except Exception as e:
                results.append({
                    "input": input_data,
                    "returncode": None,
                    "output": "",
                    "error": f"Unexpected error: {str(e)}",
                    "status": "exception"
                })

        return {
            "success": True,
            "results": results,
            "compile_error": None
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "results": [],
            "compile_error": "Timeout: compilation took too long."
        }

    finally:
        shutil.rmtree(temp_dir)
