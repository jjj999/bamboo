import pytest
from peewee import SqliteDatabase

from . import ROOT, load_example


EXAMPLE_MODULES = (
    "examples/heroku_deployment/hello.py",
    "examples/image_traffic/image_traffic.py",
    "examples/tweets/app.py",
    "examples/upsidedown/request.py",
    "examples/upsidedown/serve.py",
)


@pytest.mark.parametrize("relative_path", EXAMPLE_MODULES)
def test_example_module_loads(relative_path: str) -> None:
    module_name = "example_" + relative_path.replace("/", "_").replace(".", "_")
    load_example(relative_path, module_name)


def test_heroku_configuration_matches_supported_python() -> None:
    directory = ROOT / "examples/heroku_deployment"

    assert (directory / ".python-version").read_text().strip() == "3.15"
    assert not (directory / "runtime.txt").exists()
    assert (directory / "Procfile").read_text().strip() == (
        "web: gunicorn hello:app --log-file=-"
    )

    requirements = (directory / "requirements.txt").read_text().splitlines()
    assert "bamboo-core" in requirements
    assert "gunicorn" in requirements


def test_tweets_controllers_with_sqlite() -> None:
    module = load_example("examples/tweets/app.py", "example_tweets_sqlite")
    database = SqliteDatabase(":memory:")
    models = [module.UserModel, module.TweetModel]

    with database.bind_ctx(models), database:
        database.create_tables(models)
        users = module.UserController(module.UserModel)
        tweets = module.TweetController(module.TweetModel)

        users.register("Alice", "alice@example.com")
        tweet_id = tweets.post("alice@example.com", "hello")
        assert [(tweet.id, tweet.content) for tweet in tweets.get_tweets()] == [
            (tweet_id, "hello")
        ]

        tweets.update(tweet_id, "updated")
        assert [tweet.content for tweet in tweets.get_tweets("alice@example.com")] == [
            "updated"
        ]

        tweets.delete(tweet_id, "alice@example.com")
        assert tweets.get_tweets() == []
        users.delete("alice@example.com")
