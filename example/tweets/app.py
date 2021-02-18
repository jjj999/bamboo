
from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
import json
from typing import List, Optional, Tuple, Type

from bamboo import App, Endpoint, data_format
from bamboo.api import JsonApiData
from bamboo.endpoint import Callback_t
from bamboo.base import HTTPStatus
from bamboo.error import ErrInfoBase
from bamboo.request import http
from bamboo.test import ServerForm, TestExecutor
from peewee import (
    BigAutoField, CharField, DateTimeField, ForeignKeyField, 
    IntegrityError, Model, PostgresqlDatabase, TextField
)


Flag_t = int
db = PostgresqlDatabase("tutrials")

class ModelBase(Model):
    """The model inherited by all models.
    """
            
    @classmethod
    def get_fields(cls) -> Tuple[str]:
        return tuple(cls._meta.fields.keys())
    
    
class ControllerBase(metaclass=ABCMeta):
    
    def __init__(self, modelclass: Type[ModelBase], *args, **kwargs) -> None:
        self.modelclass = modelclass
        
        if not modelclass.table_exists():
            modelclass.create_table()
            

# User Model    ------------------------------------------------------------------

class UserModel(ModelBase):
    
    email = CharField(primary_key=True)
    name = CharField()
    
    class Meta:
        database = db


class UserController(ControllerBase):
    
    FLAG_REGISTER_GOOD              = 100
    FLAG_REGISTER_FAILED            = 101
    FLAG_REGISTER_ALREADY_EXIST     = 102
    FLAG_DELETE_GOOD                = 200
    FLAG_DELETE_FAILED              = 201
    FLAG_DELETE_NOT_EXIST           = 202
    
    LEN_SERIAL_STRING = 16
    
    def __init__(self, modelclass: Type[UserModel], *args, **kwargs) -> None:
        super().__init__(modelclass, *args, **kwargs)
        
        self.modelclass = modelclass
        
    def register(self, name: str, email: str) -> Flag_t:
        try:            
            data = {"name": name, "email": email}
            self.modelclass.create(**data)
            
            return self.FLAG_REGISTER_GOOD
        except IntegrityError:
            return self.FLAG_REGISTER_ALREADY_EXIST
        except:
            return self.FLAG_REGISTER_FAILED
        
    def delete(self, email: str) -> Flag_t:
        try:
            model = self.modelclass.get_by_id(email)
            model.delete_instance()
            
            return self.FLAG_DELETE_GOOD
        except self.modelclass.DoesNotExist:
            return self.FLAG_DELETE_NOT_EXIST
        except:
            return self.FLAG_DELETE_FAILED
                
# --------------------------------------------------------------------------------

# Tweet Model   ------------------------------------------------------------------
        
class TweetModel(ModelBase):
    
    id = BigAutoField(primary_key=True)
    user = ForeignKeyField(UserModel, backref="tweets")
    content = TextField()
    datetime = DateTimeField(default=datetime.now)
    
    class Meta:
        database = db
        
        
@dataclass
class Tweet:
    id: int
    content: str
    datetime: str
    
    
class TweetController(ControllerBase):
    
    FLAG_POST_GOOD              = 100
    FLAG_POST_FAILED            = 101
    FLAG_POST_NOT_EXIST         = 102
    FLAG_UPDATE_GOOD            = 200
    FLAG_UDPATE_FAILED          = 201
    FLAG_UPDATE_NOT_EXIST       = 202
    FLAG_DELETE_GOOD            = 300
    FLAG_DELETE_FAILED          = 301
    FLAG_DELETE_NOT_EXIST       = 302
    FLAG_DELETE_FORBIDDEN       = 303
    FLAG_GET_TWEETS_GOOD        = 400
    FLAG_GET_TWEETS_FAIELD      = 401
    FLAG_GET_TWEETS_NOT_EXIST   = 402
    
    
    def __init__(self, modelclass: TweetModel, *args, **kwargs) -> None:
        super().__init__(modelclass, *args, **kwargs)

        self.modelclass = modelclass
        
    def post(self, email: str, content: str) -> Tuple[Flag_t, Optional[int]]:
        try:
            data = {"user": email, "content": content}
            model = self.modelclass.create(**data)
            
            return (self.FLAG_POST_GOOD, model.id)
        except IntegrityError:
            return (self.FLAG_POST_NOT_EXIST, None)
        except:
            return (self.FLAG_POST_FAILED, None)
        
    def update(self, id: int, new_content: str) -> Flag_t:
        try:
            model = self.modelclass.get_by_id(id)
            model.content = new_content
            model.save()
            
            return self.FLAG_UPDATE_GOOD
        except self.modelclass.DoesNotExist:
            return self.FLAG_UPDATE_NOT_EXIST
        except:
            return self.FLAG_UDPATE_FAILED
        
    def delete(self, id: int, email: str) -> Flag_t:
        try:
            model = self.modelclass.get_by_id(id)
            if email != model.user:
                return self.FLAG_DELETE_FORBIDDEN
            
            return self.FLAG_DELETE_GOOD
        except self.modelclass.DoesNotExist:
            return self.FLAG_DELETE_NOT_EXIST
        except:
            return self.FLAG_DELETE_FAILED
        
    def get_tweets(self, email: Optional[str] = None) -> Tuple[Flag_t, List[Tweet]]:
        try:
            if email is None:
                query = self.modelclass.select()
            else:
                query = self.modelclass.select().where(self.modelclass.user == email)
            tweets = []
            for model in query:
                tweets.append(Tweet(model.id, model.content, model.datetime.ctime()))
                
            return (self.FLAG_GET_TWEETS_GOOD, tweets)
        except self.modelclass.DoesNotExist:
            return (self.FLAG_GET_TWEETS_NOT_EXIST, [])
        except:
            return (self.FLAG_GET_TWEETS_FAIELD, [])

# --------------------------------------------------------------------------------

# Errors    ----------------------------------------------------------------------

# User

class UserRegsiterAlreadyExistErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.BAD_REQUEST
    
    def get_body(self) -> bytes:
        return b"User already exists."
    
    
class UserRegisterFailedErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    
    def get_body(self) -> bytes:
        return b"Registration failed because of internal error."
    
    
class UserDeleteNotExistErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.BAD_REQUEST
    
    def get_body(self) -> bytes:
        return b"User not found."
    
    
class UserDeleteFailedErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    
    def get_body(self) -> bytes:
        return b"Deleting user failed because of internal error."
    
   
# Tweet
 
class TweetsGetFailedErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    
    def get_body(self) -> bytes:
        return b"Getting tweets failed because of internal error."
    
    
class TweetsGetNotExistErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.BAD_REQUEST
    
    def get_body(self) -> bytes:
        return b"Tweets not found."
        
        
class TweetPostFailedErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    
    def get_body(self) -> bytes:
        return b"Posting tweet failed because of internal error."
    
    
class TweetPostNotExistErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.BAD_REQUEST
    
    def get_body(self) -> bytes:
        return b"User not found. Sign up first."
    
    
class TweetUpdateFailedErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    
    def get_body(self) -> bytes:
        return b"Updating tweet failed because of internal error."
    
    
class TweetUpdateNotExistErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.BAD_REQUEST
    
    def get_body(self) -> bytes:
        return b"Tweet not found."
    
    
class TweetDeleteFailedErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    
    def get_body(self) -> bytes:
        return b"Deleting tweet failed because of internal error."
    
    
class TweetDeleteNotExistErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.BAD_REQUEST
    
    def get_body(self) -> bytes:
        return b"Tweet not found."
    
    
class TweetDeleteForbiddenErrInfo(ErrInfoBase):
    
    http_status = HTTPStatus.FORBIDDEN
    
    def get_body(self) -> bytes:
        return b"Deleting tweet was forbidden. Delete your own tweets."

# --------------------------------------------------------------------------------

# Endpoitns ----------------------------------------------------------------------

app = App()

user_controller = UserController(UserModel)
tweet_controller = TweetController(TweetModel)


def print_request_body(callback: Callback_t) -> Callback_t:
    
    def printer(self: Endpoint) -> None:
        if len(self.body):
            data = json.loads(self.body)
            print("Requested")
            print("---------")
            print(json.dumps(data, indent=4))

        callback(self)
        
    printer.__dict__ = callback.__dict__
    return printer

# User

class UserRegisterInput(JsonApiData):
    
    email: str
    name: str
    
    
class UserDeleteInput(JsonApiData):

    email: str
            

@app.route("user", parcel=(user_controller,))
class UserEndpoint(Endpoint):
    
    def setup(self, controller: UserController, *parcel) -> None:
        self.controller = controller
        
    @print_request_body
    @data_format(input=UserRegisterInput, output=None)
    def do_POST(self, req_body: UserRegisterInput) -> None:
        flag = self.controller.register(req_body.name, req_body.email)
        if flag == self.controller.FLAG_REGISTER_ALREADY_EXIST:
            self.send_err(UserRegsiterAlreadyExistErrInfo())
            return
        elif flag == self.controller.FLAG_REGISTER_FAILED:
            self.send_err(UserRegisterFailedErrInfo())
            return
        
        self.send_only_status(HTTPStatus.OK)
        
    @print_request_body
    @data_format(input=UserDeleteInput, output=None)
    def do_DELETE(self, req_body: UserDeleteInput) -> None:
        flag = self.controller.delete(req_body.email)
        if flag == self.controller.FLAG_DELETE_NOT_EXIST:
            self.send_err(UserDeleteNotExistErrInfo())
            return
        elif flag == self.controller.FLAG_DELETE_FAILED:
            self.send_err(UserDeleteFailedErrInfo())
            return
        
        self.send_only_status(HTTPStatus.OK)
        

# Tweet

class TweetsGetInput(JsonApiData):
    
    email: Optional[str] = None


class SingleTweet(JsonApiData):
    
    id: int
    content: str
    datetime: str
    
    
class TweetsGetOutput(JsonApiData):
    
    tweets: List[SingleTweet]
        

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
    
    
@app.route("tweet", parcel=(tweet_controller,))
class TweetsEndpoint(Endpoint):
    
    def setup(self, controller: TweetController, *parcel) -> None:
        self.controller = controller
    
    @print_request_body
    @data_format(input=TweetsGetInput, output=TweetsGetOutput)
    def do_GET(self, rec_body: TweetsGetInput) -> None:
        flag, tweets = self.controller.get_tweets(rec_body.email)
        if flag == self.controller.FLAG_GET_TWEETS_NOT_EXIST:
            self.send_err(TweetsGetNotExistErrInfo())
            return
        elif flag == self.controller.FLAG_GET_TWEETS_FAIELD:
            self.send_err(TweetsGetFailedErrInfo())
            return
        
        tweets = [tweet.__dict__ for tweet in tweets]
        data = {"tweets": tweets}
        self.send_json(data)
        
    @print_request_body
    @data_format(input=TweetPostInput, output=TweetPostOutput)
    def do_POST(self, rec_body: TweetPostInput) -> None:
        flag, id = self.controller.post(rec_body.email, rec_body.content)
        if flag == self.controller.FLAG_POST_NOT_EXIST:
            self.send_err(TweetPostNotExistErrInfo())
            return
        elif flag == self.controller.FLAG_POST_FAILED:
            self.send_err(TweetPostFailedErrInfo())
            return
        
        body = {"id": id}
        self.send_json(body)
        
    @print_request_body
    @data_format(input=TweetUpdateInput, output=None)
    def do_PUT(self, rec_body: TweetUpdateInput) -> None:
        flag = self.controller.update(rec_body.id, rec_body.new_content)
        if flag == self.controller.FLAG_UPDATE_NOT_EXIST:
            self.send_err(TweetUpdateNotExistErrInfo())
            return
        elif flag == self.controller.FLAG_UDPATE_FAILED:
            self.send_err(TweetUpdateFailedErrInfo())
            return
        
        self.send_only_status(HTTPStatus.OK)
        
    @print_request_body
    @data_format(input=TweetDeleteInput, output=None)
    def do_DELETE(self, rec_body: TweetDeleteInput) -> None:
        flag = self.controller.delete(rec_body.id, rec_body.email)
        if flag == self.controller.FLAG_DELETE_NOT_EXIST:
            self.send_err(TweetDeleteNotExistErrInfo())
            return
        elif flag == self.controller.FLAG_DELETE_FAILED:
            self.send_err(TweetDeleteFailedErrInfo())
            return
        elif flag == self.controller.FLAG_DELETE_FORBIDDEN:
            self.send_err(TweetDeleteForbiddenErrInfo())
            return
        
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

    res = http.post(uris.user, json={"email": email, "name": name})
    if res.ok:
        print("ユーザー登録が完了しました．\n")
        return email
    else:
        print(res.body.decode(), end="\n\n")
    
    
def request_user_delete(uris: Uris, email: str) -> None:
    if not confirm_yes_no("本当に削除しますか？"):
        print("削除を中止します．\n")
        return
    
    res = http.delete(uris.user, json={"email": email})
    if res.ok:
        print("削除が完了しました．\n")
    else:
        print(res.body.decode(), end="\n\n")
    
    
def print_tweets(tweets: List[SingleTweet]) -> None:
    for tweet in tweets:
            print("-" * 30)
            print()
            print(f"ID: {tweet.id}")
            print(f"Datetime: {tweet.datetime}")
            print(f"Content: {tweet.content}")
            print()
        
        
def request_tweets_all(uris: Uris, email: str) -> None:
    res = http.get(uris.tweet, json={"email": None}, datacls=TweetsGetOutput)
    if res.ok:
        data = res.attach()
        print_tweets(data.tweets)
    else:
        print(res.body.decode(), end="\n\n")
        
        
def request_tweets_history(uris: Uris, email: str) -> None:
    res = http.get(uris.tweet, json={"email": email}, datacls=TweetsGetOutput)
    if res.ok:
        data = res.attach()
        print_tweets(data.tweets)
    else:
        print(res.body.decode(), end="\n\n")


def request_tweet_post(uris: Uris, email: str) -> None:
    content = input("ツイート内容 >> ")
    res = http.post(uris.tweet, json={"email": email, "content": content}, datacls=TweetPostOutput)
    if res.ok:
        data = res.attach()
        print(f"投稿が完了しました．ID: {data.id}\n")
    else:
        print(res.body.decode(), end="\n\n")


def request_tweet_update(uris: Uris, email: str) -> None:
    id = int(input("編集したいツイートID: "))
    content = input("新しいツイート内容 >> ")
    res = http.put(uris.tweet, json={"id": id, "new_content": content})
    if res.ok:
        print(f"投稿が完了しました．\n")
    else:
        print(res.body.decode(), end="\n\n")


def request_tweet_delete(uris: Uris, email: str) -> None:
    id = int(input("削除したいツイートID: "))
    res = http.delete(uris.tweet, json={"id": id, "email": email})
    if res.ok:
        print("削除が完了しました．\n")
    elif res.status == 403:
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
        "http://localhost:8000/tweet"
    )
    
    
    if len(sys.argv) == 1:
        form = ServerForm("", 8000, app, "app.log")
        executor = TestExecutor(request_interact, args=(uris,))
        executor.add_forms(form)
        executor.exec()
    elif sys.argv[1] == "client":
        request_interact(uris)
