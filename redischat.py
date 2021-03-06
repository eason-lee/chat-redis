import flask
from flask import request
import redis
import time
import json


'''
# 安装redis
sudo apt-get install redis-server
sudo pip3 install redis
# 启动redis服务器
(redis-server &) 用括号可以使这个服务器一直在后台运行
# 使用 gunicorn 启动
gunicorn --worker-class=gevent -t 9999 wsgi --bind '0.0.0.0:3000'
# 开启 debug 输出
gunicorn --log-level debug --worker-class=gevent -t 999 redis_chat81:app
# 把 gunicorn 输出写入到 gunicorn.log 文件中
gunicorn --log-level debug --access-logfile gunicorn.log --worker-class=gevent -t 999 redis_chat81:app
'''

# 连接上本机的 redis 服务器
# 所以要先打开 redis 服务器
red = redis.Redis(host='localhost', port=6379, db=0)
print('redis', red)

app = flask.Flask(__name__)
app.secret_key = 'chat-key'

# 发布聊天广播的 redis 频道
chat_channel = 'chat'

#监听 redis 广播并 yield data 到客户端
def stream():
    # 对每一个用户 创建一个[发布订阅]对象
    pubsub = red.pubsub()
    # 订阅广播频道
    pubsub.subscribe(chat_channel)
    # 监听订阅的广播
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = message['data'].decode('utf-8')
            # 用 sse 返回给前端
            yield 'data: {}\n\n'.format(data)


@app.route('/chat/subscribe')
def subscribe():
    return flask.Response(stream(), mimetype="text/event-stream")


@app.route('/chat')
def index_view():
    return flask.render_template('index.html')


def current_time():
    return int(time.time())


@app.route('/chat/add', methods=['POST'])
def chat_add():
    msg = request.get_json()
    name = msg.get('name', '')
    if name == '':
        name = '无名'
    content = msg.get('content', '')
    channel = msg.get('channel', '')
    r = {
        'name': name,
        'content': content,
        'channel': channel,
        'created_time': current_time(),
    }
    message = json.dumps(r, ensure_ascii=False)
    # 用 redis 发布消息
    red.publish(chat_channel, message)
    return 'OK'


