import tempfile
import subprocess
import os
import shutil

def run_c_code_safely(code_str, input_data_list=[""], wait_time=1, compile_timeout=1e5):
    if len(input_data_list) == 0:
        input_data_list = [""]
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Cソースを一時ファイルに書き込み
        code_file = os.path.join(temp_dir, "program.c")
        with open(code_file, "w") as f:
            f.write(code_str)

        # 2. コンパイル
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
                "compile_error": compile_result.stderr.decode()
            }

        # 3. テストケースごとの実行
        results = []
        for i, input_data in enumerate(input_data_list):
            try:

                run_cmd = [
                    "docker", "run", "-i", "--rm", "--init", "--network", "none",
                    "-v", f"{temp_dir}:/app", "c_runner_base",
                    "bash", "-c", f"/app/program"
                ]
                run_result = subprocess.run(
                    run_cmd,
                    input=input_data.encode(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=wait_time + 1  # 余裕を持たせる
                )
                results.append({
                    "input": input_data,
                    "returncode": run_result.returncode,
                    "output": run_result.stdout.decode(),
                    "error": run_result.stderr.decode(),
                    "status": "ok" if run_result.returncode == 0 else "runtime_error"
                })

            except subprocess.TimeoutExpired as e:
                results.append({
                    "input": input_data,
                    "returncode": None,
                    "output": e.stdout.decode() if e.stdout else "",
                    "error": "Timeout: execution took too long.",
                    "status": "timeout"
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
