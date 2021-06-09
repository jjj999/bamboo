from dataclasses import dataclass
from datetime import datetime
import functools
import json
import traceback
import typing as t

from bamboo import (
    ErrInfo,
    HTTPStatus,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.api import JsonApiData
from bamboo.request import Response, http
from bamboo.sticky.http import data_format
from peewee import (
    BigAutoField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegrityError,
    Model,
    PostgresqlDatabase,
    TextField,
)


# For the MVC architecture  ------------------------------------------------------

db = PostgresqlDatabase("bamboo-tutorials")


class ModelBase(Model):

    class Meta:

        database = db

    @classmethod
    def get_fields(cls) -> t.Tuple[str]:
        return tuple(cls._meta.fields.keys())


class ControllerBase:

    def __init__(self, model: t.Type[ModelBase]) -> None:
        self.model = model

        if not model.table_exists():
            model.create_table()

# --------------------------------------------------------------------------------

# Errors    ----------------------------------------------------------------------

class CustomErrInfo(ErrInfo):

    msg: str

    def get_body(self) -> t.Union[bytes, t.Iterable[bytes]]:
        return self.msg.encode()


class InternalErrInfo(ErrInfo):

    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    msg = "Some errors occured in the server."

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

        traceback.print_exc()

# User

class UserAlreadyExistErrInfo(ErrInfo):

    http_status = HTTPStatus.BAD_REQUEST
    msg = "User already exists."


class UserNotExistErrInfo(ErrInfo):

    http_status = HTTPStatus.BAD_REQUEST
    msg = "User not found."

# Tweet

class TweetNotExistErrInfo(ErrInfo):

    http_status = HTTPStatus.BAD_REQUEST
    msg = "Tweets not found."


class TweetForbiddenErrInfo(ErrInfo):

    http_status = HTTPStatus.FORBIDDEN
    msg = "Deleting tweet was forbidden. Delete your own tweets."

# ----------------------------------------------------------------------------

# APIs  ----------------------------------------------------------------------

class UserRegisterInput(JsonApiData):

    email: str
    name: str


class UserDeleteInput(JsonApiData):

    email: str


class TweetsGetInput(JsonApiData):

    email: t.Optional[str] = None


class SingleTweet(JsonApiData):

    id: int
    content: str
    datetime: str


class TweetsGetOutput(JsonApiData):

    tweets: t.List[SingleTweet]


class TweetPostInput(JsonApiData):

    email: str
    content: str


class TweetPostOutput(JsonApiData):

    id: int


class TweetUpdateInput(JsonApiData):

    id: int
    new_content: str


class TweetDeleteInput(JsonApiData):

    id: int
    email: str

# --------------------------------------------------------------------------------

# User Model    ------------------------------------------------------------------

class UserModel(ModelBase):

    email = CharField(primary_key=True)
    name = CharField()


class UserController(ControllerBase):

    LEN_SERIAL_STRING = 16

    def __init__(self, model: t.Type[UserModel]) -> None:
        super().__init__(model)

        self.model = model

    def register(self, name: str, email: str) -> None:
        try:
            data = {"name": name, "email": email}
            self.model.create(**data)
        except IntegrityError as e:
            raise UserAlreadyExistErrInfo() from e
        except Exception as e:
            raise InternalErrInfo() from e

    def delete(self, email: str) -> None:
        try:
            model = self.model.get_by_id(email)
            model.delete_instance()
        except self.model.DoesNotExist as e:
            raise UserNotExistErrInfo() from e
        except Exception as e:
            raise InternalErrInfo() from e

# --------------------------------------------------------------------------------

# Tweet Model   ------------------------------------------------------------------

class TweetModel(ModelBase):

    id = BigAutoField(primary_key=True)
    user = ForeignKeyField(UserModel, backref="tweets")
    content = TextField()
    datetime = DateTimeField(default=datetime.now)


@dataclass
class Tweet:

    id: int
    content: str
    datetime: str


class TweetController(ControllerBase):

    def __init__(self, model: TweetModel) -> None:
        super().__init__(model)

        self.model = model

    def post(self, email: str, content: str) -> int:
        data = {"user": email, "content": content}
        try:
            model = self.model.create(**data)
        except IntegrityError as e:
            raise TweetNotExistErrInfo() from e
        except Exception as e:
            raise InternalErrInfo() from e
        else:
            return model.id

    def update(self, id: int, new_content: str) -> None:
        try:
            model = self.model.get_by_id(id)
            model.content = new_content
            model.save()
        except self.model.DoesNotExist as e:
            raise TweetNotExistErrInfo() from e
        except Exception as e:
            raise InternalErrInfo() from e

    def delete(self, id: int, email: str) -> None:
        try:
            model = self.model.get_by_id(id)
        except self.model.DoesNotExist as e:
            raise TweetNotExistErrInfo from e
        except Exception as e:
            raise InternalErrInfo() from e
        else:
            if email != model.user.email:
                raise TweetForbiddenErrInfo()
            model.delete_instance()

    def get_tweets(
        self,
        email: t.Optional[str] = None,
    ) -> t.List[SingleTweet]:
        try:
            if email is None:
                query = self.model.select()
            else:
                query = self.model.select().where(self.model.user == email)
        except self.model.DoesNotExist as e:
            raise TweetNotExistErrInfo() from e
        except Exception as e:
            raise InternalErrInfo() from e
        else:
            tweets = [
                SingleTweet(
                    id=m.id,
                    content=m.content,
                    datetime=m.datetime.ctime(),
                )
                for m in query
            ]
            return tweets

# --------------------------------------------------------------------------------

# Endpoitns ----------------------------------------------------------------------

app = WSGIApp()
Callback_t = t.Callable[[WSGIEndpoint], None]


def print_request_body(callback: Callback_t) -> Callback_t:

    @functools.wraps(callback)
    def printer(self: WSGIEndpoint) -> None:
        if len(self.body):
            data = json.loads(self.body)
            print("Requested")
            print("---------")
            print(json.dumps(data, indent=4))

        callback(self)

    return printer


@app.route("user")
class UserEndpoint(WSGIEndpoint):

    def setup(self, controller: UserController) -> None:
        self.controller = controller

    @print_request_body
    @data_format(input=UserRegisterInput, output=None)
    def do_POST(self, req: UserRegisterInput) -> None:
        self.controller.register(req.name, req.email)
        self.send_only_status(HTTPStatus.OK)

    @print_request_body
    @data_format(input=UserDeleteInput, output=None)
    def do_DELETE(self, req: UserDeleteInput) -> None:
        self.controller.delete(req.email)
        self.send_only_status(HTTPStatus.OK)


@app.route("tweet")
class TweetsEndpoint(WSGIEndpoint):

    def setup(self, controller: TweetController) -> None:
        self.controller = controller

    @print_request_body
    @data_format(input=TweetsGetInput, output=TweetsGetOutput)
    def do_GET(self, req: TweetsGetInput) -> None:
        tweets = self.controller.get_tweets(req.email)
        self.send_json(TweetsGetOutput(tweets=tweets))

    @print_request_body
    @data_format(input=TweetPostInput, output=TweetPostOutput)
    def do_POST(self, req: TweetPostInput) -> None:
        id = self.controller.post(req.email, req.content)
        self.send_json(TweetPostOutput(id=id))

    @print_request_body
    @data_format(input=TweetUpdateInput, output=None)
    def do_PUT(self, req: TweetUpdateInput) -> None:
        self.controller.update(req.id, req.new_content)
        self.send_only_status(HTTPStatus.OK)

    @print_request_body
    @data_format(input=TweetDeleteInput, output=None)
    def do_DELETE(self, req: TweetDeleteInput) -> None:
        self.controller.delete(req.id, req.email)
        self.send_only_status(HTTPStatus.OK)

# --------------------------------------------------------------------------------

# Client App    ------------------------------------------------------------------

@dataclass
class Uris:

    user: str
    tweet: str


def confirm_yes_no(msg: str) -> bool:
    is_yes = True
    while True:
        answer = input(msg + " [yes/no] : ")
        if answer == "yes":
            break
        elif answer == "no":
            is_yes = False
            break
        else:
            print("yes か no で答えてください．")

    return is_yes


def request_user_register(uris: Uris) -> str:
    print("ユーザー登録をします．")
    email = input("メールアドレスを入力してください : ")
    name = input("お好きなユーザー名を登録してください : ")

    with http.post(
        uris.user,
        json=UserRegisterInput(email=email, name=name),
    ) as res:
        if res.ok:
            print("ユーザー登録が完了しました．\n")
            return email
        else:
            print(res.body.decode(), end="\n\n")


def request_user_delete(uris: Uris, email: str) -> None:
    if not confirm_yes_no("本当に削除しますか？"):
        print("削除を中止します．\n")
        return

    with http.delete(uris.user, json=UserDeleteInput(email=email)) as res:
        if res.ok:
            print("削除が完了しました．\n")
        else:
            print(res.body.decode(), end="\n\n")


def print_tweets(tweets: t.List[SingleTweet]) -> None:
    for tweet in tweets:
        print("-" * 30)
        print()
        print(f"ID: {tweet.id}")
        print(f"Datetime: {tweet.datetime}")
        print(f"Content: {tweet.content}")
        print()


def request_tweets_all(uris: Uris, email: str) -> None:
    with http.get(
        uris.tweet,
        json=TweetsGetInput(email=None),
        datacls=TweetsGetOutput,
    ) as res:
        if res.ok:
            data = res.attach()
            print_tweets(data.tweets)
        else:
            print(res.body.decode(), end="\n\n")


def request_tweets_history(uris: Uris, email: str) -> None:
    with http.get(
        uris.tweet,
        json=TweetsGetInput(email=email),
        datacls=TweetsGetOutput,
    ) as res:
        if res.ok:
            data = res.attach()
            print_tweets(data.tweets)
        else:
            print(res.body.decode(), end="\n\n")


def request_tweet_post(uris: Uris, email: str) -> None:
    content = input("ツイート内容 >> ")
    with http.post(
        uris.tweet,
        json=TweetPostInput(email=email, content=content),
        datacls=TweetPostOutput,
    ) as res:
        if res.ok:
            data = res.attach()
            print(f"投稿が完了しました．ID: {data.id}\n")
        else:
            print(res.body.decode(), end="\n\n")


def request_tweet_update(uris: Uris, email: str) -> None:
    id = int(input("編集したいツイートID: "))
    content = input("新しいツイート内容 >> ")
    with http.put(
        uris.tweet,
        json=TweetUpdateInput(id=id, new_content=content),
    ) as res:
        if res.ok:
            print(f"投稿が完了しました．\n")
        else:
            print(res.body.decode(), end="\n\n")


def request_tweet_delete(uris: Uris, email: str) -> None:
    id = int(input("削除したいツイートID: "))
    with http.delete(
        uris.tweet,
        json=TweetDeleteInput(id=id, email=email),
    ) as res:
        if res.ok:
            print("削除が完了しました．\n")
        elif res.status == HTTPStatus.FORBIDDEN:
            print("あなたのツイートではありません．\n")
        else:
            print(res.body.decode(), end="\n\n")


COMMANDS = (
    (1,     "exit",     "ユーザーを削除します",         request_user_delete),
    (2,     "all",      "全てのツイートを表示します",   request_tweets_all),
    (3,     "history",  "ツイート履歴を表示します",     request_tweets_history),
    (4,     "post",     "新規ツイートをします",         request_tweet_post),
    (5,     "update",   "ツイート内容を編集します",     request_tweet_update),
    (6,     "delete",   "ツイートを削除します",         request_tweet_delete),
)


def display_commands():
    print("-" * 60)
    for no, command, explain, _ in COMMANDS:
        print(f"{no:>4} : {command:^10} : {explain:<30}")
    print("-" * 60)


def request_interact(uris: Uris):
    is_registered = confirm_yes_no("ユーザー登録はしていますか？")
    if is_registered:
        email = input("メールアドレスを入力してください: ")
    else:
        email = request_user_register(uris)

    display_commands()
    print("上のコマンド一覧から実行したいコマンドを選んでください．No でも コマンド名でも構いません．"
          "終了したい場合は 'q'，コマンド一覧を表示したい場合は 'd' を入力してください．\n")

    while True:
        request = input("No または コマンド名 >> ")
        if request == "q":
            break
        if request == "d":
            display_commands()
            continue
        if request.isdigit():
            request = int(request)
        print()

        for no, command, _, func in COMMANDS:
            if request in (no, command):
                func(uris, email)
                break
        else:
            print("一致するコマンドが存在しません．\n")

# --------------------------------------------------------------------------------

if __name__ == "__main__":

    import sys

    uris = Uris(
        "http://localhost:8000/user",
        "http://localhost:8000/tweet",
    )

    user_controller = UserController(UserModel)
    tweet_controller = TweetController(TweetModel)
    app.set_parcel(UserEndpoint, user_controller)
    app.set_parcel(TweetsEndpoint, tweet_controller)

    if len(sys.argv) == 1:
        form = WSGIServerForm("", 8000, app, "app.log")
        executor = WSGITestExecutor(form)
        executor.exec(request_interact, args=(uris,))
    elif sys.argv[1] == "client":
        request_interact(uris)
