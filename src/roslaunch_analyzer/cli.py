import typer

cli = typer.Typer()


@cli.command()
def run(cmds: str):
    import json

    from roslaunch_analyzer import command_to_tree, parse_command_line

    command = parse_command_line(cmds)

    tree = command_to_tree(command)

    tree.build()

    print(json.dumps(tree.serialize(), indent=2))


if __name__ == "__main__":
    run()
