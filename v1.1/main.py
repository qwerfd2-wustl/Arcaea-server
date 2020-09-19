from flask import Flask, request, jsonify, make_response
import configparser
import base64
import auth
import info
import setme
import arcscore

app = Flask(__name__)
wsgi_app = app.wsgi_app


def error_return(error_code):  # 错误返回
    # 100 无法在此ip地址下登录游戏
    # 101 用户名占用
    # 102 电子邮箱已注册
    # 103 已有一个账号由此设备创建
    # 104 用户名密码错误
    # 105 24小时内登入两台设备
    # 106 账户冻结
    # 107 你没有足够的体力
    # 401 用户不存在
    # 403 无法连接至服务器
    # 501 502 此物品目前无法获取
    # 504 无效的序列码
    # 505 此序列码已被使用
    # 506 你已拥有了此物品
    # 601 好友列表已满
    # 602 此用户已是好友
    # 604 你不能加自己为好友
    # 其它 发生未知错误
    return jsonify({
        "success": False,
        "error_code": error_code
    })


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/coffee/12/auth/login', methods=['POST'])  # 登录接口
def login():
    headers = request.headers
    id_pwd = headers['Authorization']
    id_pwd = base64.b64decode(id_pwd[6:]).decode()
    name, password = id_pwd.split(':', 1)

    try:
        token = auth.arc_login(name, password)
        if token is not None:
            r = {"success": True, "token_type": "Bearer"}
            r['access_token'] = token
            return jsonify(r)
        else:
            return error_return(104)  # 用户名或密码错误
    except:
        return error_return(108)


@app.route('/coffee/12/user/', methods=['POST'])  # 注册接口
def register():
    name = request.form['name']
    password = request.form['password']
    try:
        user_id, token, error_code = auth.arc_register(name, password)
        if user_id is not None:
            r = {"success": True, "value": {
                'user_id': user_id, 'access_token': token}}
            return jsonify(r)
        else:
            return error_return(error_code)  # 应该是101，用户名被占用，毕竟电子邮箱、设备号没记录
    except:
        return error_return(108)


@app.route('/coffee/12/compose/aggregate', methods=['GET'])  # 用户信息获取
def aggregate():
    calls = request.args.get('calls')
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            if calls == '[{ "endpoint": "/user/me", "id": 0 }]':  # 极其沙雕的判断，我猜get的参数就两种
                r = info.arc_aggregate_small(user_id)
            else:
                r = info.arc_aggregate_big(user_id)
            return jsonify(r)
        else:
            return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/user/me/character', methods=['POST'])  # 角色切换
def character_change():
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    character_id = request.form['character']
    skill_sealed = request.form['skill_sealed']
    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            flag = setme.change_char(user_id, character_id, skill_sealed)
            if flag:
                return jsonify({
                    "success": True,
                    "value": {
                        "user_id": user_id,
                        "character": character_id
                    }
                })
            else:
                return error_return(108)
        else:
            return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/<path:path>/toggle_uncap', methods=['POST'])  # 角色觉醒切换
def character_uncap(path):
    character_id = int(path[22:])
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            r = setme.change_char_uncap(user_id, character_id)
            if r is not None:
                return jsonify({
                    "success": True,
                    "value": {
                        "user_id": user_id,
                        "character": [r]
                    }
                })
            else:
                return error_return(108)
        else:
            return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/friend/me/add', methods=['POST'])  # 加好友
def add_friend():
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    friend_code = request.form['friend_code']
    try:
        user_id = auth.token_get_id(token)
        friend_id = auth.code_get_id(friend_code)
        if user_id is not None and friend_id is not None:
            r = setme.arc_add_friend(user_id, friend_id)
            if r is not None and r != 602 and r != 604:
                return jsonify({
                    "success": True,
                    "value": {
                        "user_id": user_id,
                        "updatedAt": "2020-09-07T07:32:12.740Z",
                        "createdAt": "2020-09-06T10:05:18.471Z",
                        "friends": r
                    }
                })
            else:
                if r is not None:
                    return error_return(r)
                else:
                    return error_return(108)
        else:
            if friend_id is None:
                return error_return(401)
            else:
                return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/friend/me/delete', methods=['POST'])  # 删好友
def delete_friend():
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    friend_id = int(request.form['friend_id'])
    try:
        user_id = auth.token_get_id(token)
        if user_id is not None and friend_id is not None:
            r = setme.arc_delete_friend(user_id, friend_id)
            if r is not None:
                return jsonify({
                    "success": True,
                    "value": {
                        "user_id": user_id,
                        "updatedAt": "2020-09-07T07:32:12.740Z",
                        "createdAt": "2020-09-06T10:05:18.471Z",
                        "friends": r
                    }
                })
            else:
                return error_return(108)
        else:
            if friend_id is None:
                return error_return(401)
            else:
                return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/score/song/friend', methods=['GET'])  # 好友排名，默认最多50
def song_score_friend():
    song_id = request.args.get('song_id')
    difficulty = request.args.get('difficulty')
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            r = arcscore.arc_score_friend(user_id, song_id, difficulty)
            if r is not None:
                return jsonify({
                    "success": True,
                    "value": r
                })
            else:
                return error_return(108)
        else:
            return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/score/song/me', methods=['GET'])  # 我的排名，默认最多20
def song_score_me():
    song_id = request.args.get('song_id')
    difficulty = request.args.get('difficulty')
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            r = arcscore.arc_score_me(user_id, song_id, difficulty)
            if r is not None:
                return jsonify({
                    "success": True,
                    "value": r
                })
            else:
                return error_return(108)
        else:
            return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/score/song', methods=['GET'])  # TOP20
def song_score_top():
    song_id = request.args.get('song_id')
    difficulty = request.args.get('difficulty')
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            r = arcscore.arc_score_top(song_id, difficulty)
            if r is not None:
                return jsonify({
                    "success": True,
                    "value": r
                })
            else:
                return error_return(108)
        else:
            return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/score/song', methods=['POST'])  # 成绩上传
def song_score_post():
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    song_id = request.form['song_id']
    difficulty = int(request.form['difficulty'])
    score = int(request.form['score'])
    shiny_perfect_count = int(request.form['shiny_perfect_count'])
    perfect_count = int(request.form['perfect_count'])
    near_count = int(request.form['near_count'])
    miss_count = int(request.form['miss_count'])
    health = int(request.form['health'])
    modifier = int(request.form['modifier'])
    beyond_gauge = int(request.form['beyond_gauge'])
    clear_type = int(request.form['clear_type'])

    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            r = arcscore.arc_score_post(user_id, song_id, difficulty, score, shiny_perfect_count,
                                        perfect_count, near_count, miss_count, health, modifier, beyond_gauge, clear_type)
            if r is not None:
                return jsonify({
                    "success": True,
                    "value": {"user_rating": r}
                })
            else:
                return error_return(108)
        else:
            return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/score/token', methods=['GET'])  # 成绩上传所需的token，显然我不想验证
def score_token():
    return jsonify({
        "success": True,
        "value": {
            "token": "1145141919810"
        }
    })


@app.route('/coffee/12/user/me/save', methods=['GET'])  # 从云端同步
def cloud_get():
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            r = arcscore.arc_all_get(user_id)
            if r is not None:
                return jsonify({
                    "success": True,
                    "value": r
                })
            else:
                return error_return(108)
        else:
            return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/user/me/save', methods=['POST'])  # 向云端同步
def cloud_post():
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    scores_data = request.form['scores_data']
    clearlamps_data = request.form['clearlamps_data']
    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            arcscore.arc_all_post(user_id, scores_data, clearlamps_data)
            return jsonify({
                "success": True,
                "value": {
                    "user_id": user_id
                }
            })
        else:
            return error_return(108)
    except:
        return error_return(108)


@app.route('/coffee/12/purchase/me/redeem', methods=['POST'])  # 兑换码，自然没有用
def redeem():
    return error_return(504)


@app.route('/coffee/<path:path>', methods=['POST'])  # 三个设置，写在最后降低优先级
def sys_set(path):
    set_arg = path[10:]
    headers = request.headers
    token = headers['Authorization']
    token = token[7:]
    value = request.form['value']

    try:
        user_id = auth.token_get_id(token)
        if user_id is not None:
            setme.arc_sys_set(user_id, value, set_arg)
            r = info.arc_aggregate_small(user_id)
            r['value'] = r['value'][0]['value']
            return jsonify(r)
        else:
            return error_return(108)
    except:
        return error_return(108)


def main():
    config = configparser.ConfigParser()
    path = r'setting.ini'
    config.read(path, encoding="utf-8")
    HOST = config.get('CONFIG','HOST')
    PORT = config.get('CONFIG','PORT')
    app.run(HOST, PORT)


if __name__ == '__main__':
    main()


## Made By Lost  2020.9.11
