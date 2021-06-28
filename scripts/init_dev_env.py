import subprocess


def init_dev_env() -> None:
    cmds = [
        ["pipenv", "install"],
        ["pipenv", "install", "--dev"],
        ["git", "config", "commit.message", ".gitmessage"],
    ]
    for cmd in cmds:
        subprocess.run(cmd)


if __name__ == "__main__":
    init_dev_env()
