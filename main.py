from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.get("/scrap")
def scrap_kavak():
    try:
        result = subprocess.run(
            ["poetry", "run", "scrap"],
            check=True,
            capture_output=True,
            text=True
        )
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "returncode": e.returncode,
            "stdout": e.stdout,
            "stderr": e.stderr
        }
