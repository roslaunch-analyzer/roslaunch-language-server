import typer
import os
import sys

cli = typer.Typer()

def set_pythonpath():
    current_path = os.getenv('PYTHONPATH', '')
    new_path = os.path.abspath('./src')

    # Update the python path to use the launch launch_ros packages from src directory
    # Because the current implementaiton of launch is slow.
    os.environ['PYTHONPATH'] = f"{new_path}:{current_path}"
    sys.path.insert(0,new_path)

@cli.command()
def run(port: int = None):
    set_pythonpath()
    from roslaunch_language_server.sever import server
    
    print(f"Starting roslaunch-language-server on port {port}")
    server.start_tcp("localhost", port)

if __name__ == "__main__":
    run()
