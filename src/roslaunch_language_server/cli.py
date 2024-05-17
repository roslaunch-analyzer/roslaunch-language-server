import typer

# from roslaunch_language_server.logger import logger

cli = typer.Typer()


@cli.command()
def run(port: int = None):
    from roslaunch_language_server.sever import server

    print(f"Starting roslaunch-language-server on port {port}")
    server.start_tcp("localhost", port)


if __name__ == "__main__":
    run()
