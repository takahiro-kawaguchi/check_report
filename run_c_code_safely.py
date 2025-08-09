import tempfile
import subprocess
import os
import shutil
from threading import Thread
import uuid

def read_stream(stream, buffer):
    """
    ストリームから非同期的にデータを読み込み、バッファに追加します。
    """
    try:
        while True:
            line = stream.readline()
            if not line:
                break
            buffer.append(line)
    finally:
        stream.close()

def run_c_code_safely(
    code_str,
    input_data_list=[""],
    wait_time=1,
    compile_timeout=10,
    execution=True,
    extra_files=None,
    expected_output_files=None
):
    """
    指定されたC言語のコードを安全にコンパイル・実行します。
    ファイルアップロード機能と、新規作成されたファイルの取得機能が追加されています。

    :param code_str: 実行するC言語のソースコード (str)
    :param input_data_list: プログラムへの標準入力として与えるデータ。リスト形式で複数指定可能 (list[str])
    :param wait_time: プログラム実行のタイムアウト時間 (秒)
    :param compile_timeout: コンパイルのタイムアウト時間 (秒)
    :param execution: Trueの場合、コンパイル後に実行。Falseの場合、コンパイルのみ。
    :param extra_files: プログラム実行前に一時ディレクトリに配置する追加ファイル。
                        辞書のリスト形式で、{"filename": "ファイル名", "content": "ファイル内容"} を指定。
    :param expected_output_files: プログラムが生成することを期待するファイル名のリスト。
                                  これらのファイルは結果としてcreated_filesに格納されます。
    :return: 実行結果を含む辞書
    """
    if not input_data_list:
        input_data_list = [""]

    temp_dir = tempfile.mkdtemp()
    results = []
    
    # 実行前に一時ディレクトリに存在していたファイルの一覧を保持
    original_files = {"program.c", "program"}
    if extra_files:
        original_files.update({f["filename"] for f in extra_files})

    try:
        # Cソースコードを一時ファイルに書き込み
        code_file = os.path.join(temp_dir, "program.c")
        with open(code_file, "w") as f:
            f.write(code_str)
        
        # 追加ファイルを一時ディレクトリに書き込み
        if extra_files:
            for file_info in extra_files:
                file_path = os.path.join(temp_dir, file_info["filename"])
                with open(file_path, "w") as f:
                    f.write(file_info["content"])

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

                # 入力送信
                if input_data:
                    if not input_data.endswith("\n"):
                        input_data += "\n"
                    proc.stdin.write(input_data.encode())
                    proc.stdin.flush()

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
                

                # 実行後、新規作成されたファイルをチェック
                created_files = {}
                other_files = {}

                # 新規作成されたファイルの集合を取得
                new_files_set = set(os.listdir(temp_dir)) - original_files

                # 1. expected_output_files の順序で created_files を構築
                if expected_output_files:
                    for filename in expected_output_files:
                        if filename in new_files_set:
                            file_path = os.path.join(temp_dir, filename)
                            if os.path.isfile(file_path):
                                try:
                                    with open(file_path, "r", encoding="utf-8") as f:
                                        created_files[filename] = f.read()
                                except Exception as e:
                                    created_files[filename] = f"Error reading file: {str(e)}"
                
                # 2. expected_output_files に含まれない新規ファイルを other_files に追加
                processed_files_set = set(created_files.keys())
                for filename in new_files_set:
                    if filename not in processed_files_set:
                        file_path = os.path.join(temp_dir, filename)
                        if os.path.isfile(file_path):
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    other_files[filename] = f.read()
                            except Exception as e:
                                other_files[filename] = f"Error reading file: {str(e)}"
                

                results.append({
                    "input": input_data,
                    "returncode": proc.returncode if status != "timeout" else None,
                    "output": b''.join(stdout_lines).decode(errors="replace"),
                    "error": b''.join(stderr_lines).decode(errors="replace"),
                    "status": status,
                    "created_files": created_files,
                    "other_files": other_files
                })

            except Exception as e:
                results.append({
                    "input": input_data,
                    "returncode": None,
                    "output": "",
                    "error": f"Unexpected error: {str(e)}",
                    "status": "exception",
                    "created_files": {},
                    "other_files": {}
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
        # 実行ごとに一時ディレクトリを初期化（削除）
        shutil.rmtree(temp_dir)