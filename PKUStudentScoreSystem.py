import requests
import getpass
import random
import os

def login(username, password):
    params = {
        'appid': 'portal2017',
        'userName': username,
        'password': password,
        'randCode': None,
        'smsCode': None,
        'otpCode': None,
        'redirUrl': 'https://portal.pku.edu.cn/portal2017/ssoLogin.do'
    }
    req = requests.post('https://iaaa.pku.edu.cn/iaaa/oauthlogin.do', data= params)
    responsedata = req.json()
    if 'token'  not in responsedata:
        return None
    token = responsedata['token']
    params = {
        '_rand': random.random(),
        'token': token
    }
    req = requests.get('http://portal.pku.edu.cn/portal2017/ssoLogin.do', params= params)
    return req.history[1].cookies

def get_gpa(x) -> float:
    d = {
        'A+': 4.0,
        'A': 4.0,
        'A-': 3.7,
        'B+': 3.3,
        'B': 3.0,
        'B-': 2.7,
        'C+': 2.3,
        'C': 2.0,
        'C-': 1.5,
        'D': 1.0,
        'F': 0.0
    }
    assert type(x) is int or type(x) is str or type(x) is float
    if type(x) is int:
        x = float(x)
    if type(x) is str:
        try:
            x = float(x)
        except ValueError:
            try:
                return d[x]
            except KeyError:
                return float('nan')
    return float('%.2f' % (4 - 3 * (100 - x) ** 2 / 1600)) if x >= 60.0 else 0.0

def get_scores(cookies):
    req = requests.get('https://portal.pku.edu.cn/portal2017/bizcenter/score/retrScores.do', cookies= cookies)
    if req.json()['success']:
        return req.json()
    return None

def pass_grade_point(s: str) -> tuple[bool, float] :
    ss = get_gpa(s)
    if ss != ss:
        if s in ('合格', 'EX', 'P'):
            return (True, ss)
        if s in ('不合格', 'NP', 'I', 'IP', 'W'):
            return (False, ss)
    if ss != 0.0:
        return (True, ss)
    return (False, 0.0)

def analyse_scores(scores: dict, xndxq= None, color_mode= 0) -> tuple:
    result = tuple()
    for i in scores['cjxx']:
        if xndxq:
            if '%s-%s' % (i['xnd'], i['xq']) != xndxq:
                continue
        result += ('%s-%s:\n' % (i['xnd'], i['xq']), )
        for j in i['list']:
            _tmpstr = "%s"
            specialresult = ""
            # Pass, Exempted: green, other: red
            if color_mode == 1:
                if pass_grade_point(j['xqcj'])[0]:
                    #Special process
                    if pass_grade_point(j['xqcj'])[1] == 4.00:
                        for i in '    Course No.: %s; Credit:%s; Course name: %s' % (j['kch'], j['xf'], j['kcmc']):
                            specialresult += "\033[%dm%s\033[0m" % (random.randint(31, 36), i)
                    _tmpstr = "\033[32m%s\033[0m"
                else:
                    _tmpstr = "\033[31m%s\033[0m"
            # >=98.5: rainbow, >= 85: green, >= 75: yellow, >= 60: red, < 60: default with red background, Nan: default
            elif color_mode == 2:
                if pass_grade_point(j['xqcj'])[1] == pass_grade_point(j['xqcj'])[1]:
                    #Special process
                    if pass_grade_point(j['xqcj'])[1] == 4.00:
                        for i in '    Course No.: %s; Credit:%s; Course name: %s' % (j['kch'], j['xf'], j['kcmc']):
                            specialresult += "\033[%dm%s\033[0m" % (random.randint(31, 36), i)
                    elif pass_grade_point(j['xqcj'])[1] >= 3.58:
                        _tmpstr = "\033[32m%s\033[0m"
                    elif pass_grade_point(j['xqcj'])[1] >= 2.83:
                        _tmpstr = "\033[33m%s\033[0m"
                    elif pass_grade_point(j['xqcj'])[1] >= 1.00:
                        _tmpstr = "\033[31m%s\033[0m"
                    else:
                        _tmpstr = "\033[41m%s\033[0m"
            result += (_tmpstr % ('    Course No.: %s; Credit:%s; Course name: %s' % (j['kch'], j['xf'], j['kcmc'])), ) if not specialresult else (specialresult, )
    return result

def analyse_credit(scores: dict, xndxq= None) -> str:
    result = 0.0
    for i in scores['cjxx']:
        if xndxq:
            if '%s-%s' % (i['xnd'], i['xq']) != xndxq:
                continue
        for j in i['list']:
            if pass_grade_point(j['xqcj'])[0]:
                result += float(j['xf'])
    return '%.1f' % result

def query_scores(scores: dict, course_no: str, one_hundred= False, eval_expression= None):
    for i in scores['cjxx']:
        for j in i['list']:
            header = 'Credit: %s; Course name: %s; Score: %%s.' % (j['xf'], j['kcmc'])
            if j['kch'] == course_no:
                if one_hundred:
                    return header % j['xqcj']
                elif eval_expression:
                    while (_t := input("Eval is dangerous, please make sure that you know what you do!(y/n)")) not in ('y', 'n'):
                        pass
                    if _t == 'y':
                        return str(eval(eval_expression%j['xqcj']))
                    else:
                        return "Operation canceled by user."
                else:
                    try:
                        score = int(float(j['xqcj']) * 10)
                        if (score >= 600):
                            return header % 'Pass'
                        else:
                            return header % 'Fail'
                    except ValueError:
                        return header % j['xqcj']
    return 'Not found!'

def main():
    print("Peking University Student Score System")
    login_status = {
        'status': False, 
        'username': None, 
        'password': None, 
        'cookie': None
    }
    scores = {}
    while 1:
        inp = input(str(login_status['username']) + '>').strip().split()
        try:
            if inp[0] == 'login':
                if '-n' in inp[1:]:
                    login_status['username'] = None
                    login_status['password'] = None
                if (not login_status['username'] or not login_status['password']):
                    login_status['username'] = input('Username:')
                    login_status['password'] = getpass.getpass('Password:')
                result = login(login_status['username'], login_status['password'])
                if result:
                    login_status['status'] = True
                    login_status['cookie'] = result
                    print('Success')
                else:
                    login_status['status'] = False
                    print('Failed')
            elif inp[0] == 'get':
                if not login_status['status']:
                    print('Please login first!')
                    continue
                scores = get_scores(login_status['cookie'])
                print('Success! You may list courses then')
            elif inp[0] == 'list':
                color_mode: int = 0
                if not scores:
                    print('Get scores first!')
                    continue
                if '-c2' in inp:
                    color_mode = 2
                    inp.remove('-c2')
                if '-c1' in inp:
                    color_mode = 1
                    inp.remove('-c1')
                if len(inp) == 2:
                    for _i in analyse_scores(scores, xndxq= inp[1], color_mode= color_mode):
                        os.system("echo %s" % _i)
                else:
                    for _i in analyse_scores(scores, color_mode= color_mode):
                        os.system("echo %s" % _i)
            elif inp[0] == 'query':
                if not scores:
                    print('Get scores first!')
                    continue
                one_hundred = False
                eval_expression = None
                if '-h' in inp[1:]:
                    one_hundred = True
                    inp.remove('-h')
                if '-p' in inp[1:]:
                    inp.remove('-p')
                if '-e' in inp[1:]:
                    eval_expression = inp[-1]
                    inp.remove(eval_expression)
                    inp.remove('-e')
                course_no = inp[1] if inp[1].isalnum() else '0'
                print(query_scores(scores, course_no, one_hundred= one_hundred, eval_expression= eval_expression))
            elif inp[0] == 'credit':
                if len(inp) == 2:
                    print(inp[1], ' got credit(s): ', analyse_credit(scores, xndxq= inp[1]))
                else:
                    print('Total credit(s): ', analyse_credit(scores))
                pass
            elif inp[0] == 'help':
                print('Usage:\nlogin [-n]\nget\nlist [-c1 | -c2] [xndxq]\nquery [-h | -p | -e] courseNo [eval expression]\ncredit [xndxq]\nhelp\nquit')
            elif inp[0] == 'quit':
                return 0
            else :
                print('Unknown command!')
        except:
            pass
    return 1

if __name__ == "__main__":
    exit(main())