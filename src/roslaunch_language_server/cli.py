import typer

cli = typer.Typer()


@cli.command()
def run(port: int = None):
    from roslaunch_language_server.server import server
    import roslaunch_language_server.feature  # noqa
    
    print(f"Starting roslaunch-language-server on port {port}")
    server.start_tcp("localhost", port)


if __name__ == "__main__":
    run()