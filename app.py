import os
import json
from flask import Flask, request, jsonify, session, redirect, render_template_string

app = Flask(__name__)

# === 强制从环境变量读取密钥和凭证，无默认值！===
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
USERNAME = os.environ.get("LOGIN_USER")
PASSWORD = os.environ.get("LOGIN_PASS")
STUDENT_DATA_RAW = os.environ.get("STUDENT_DATA")

# 启动前校验必要环境变量
required_vars = {
    "FLASK_SECRET_KEY": SECRET_KEY,
    "LOGIN_USER": USERNAME,
    "LOGIN_PASS": PASSWORD,
    "STUDENT_DATA": STUDENT_DATA_RAW,
}

missing = [k for k, v in required_vars.items() if not v]
if missing:
    raise EnvironmentError(
        f"❌ 缺少必要的环境变量，请在部署平台设置以下变量: {', '.join(missing)}"
    )

app.secret_key = SECRET_KEY

# 尝试解析学生数据（启动时校验）
try:
    all_data = json.loads(STUDENT_DATA_RAW)
    if not isinstance(all_data, list):
        raise ValueError("STUDENT_DATA 必须是 JSON 数组")
except Exception as e:
    raise ValueError(f"❌ STUDENT_DATA 格式错误: {e}")

# ========== 路由逻辑 ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user == USERNAME and pwd == PASSWORD:
            session['logged_in'] = True
            return redirect('/')
        else:
            return render_template_string(login_page, error="用户名或密码错误")
    return render_template_string(login_page, error="")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

@app.route('/api/data')
def api_data():
    if not session.get('logged_in'):
        return jsonify({"error": "未授权"}), 401

    page = int(request.args.get('page', 1))
    ROWS_PER_PAGE = 30
    start = (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE

    return jsonify({
        "total": len(all_data),
        "difficulty": len([x for x in all_data if x.get("困难等级") not in [None, "", "null"]]),
        "psych": len([x for x in all_data if x.get("心里疑问") == "是"]),
        "data": all_data[start:end],
        "page": page,
        "total_pages": (len(all_data) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
    })

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    return render_template_string(main_page)

# ========== HTML 页面（同前，略作精简）==========
login_page = '''
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>登录</title></head>
<body style="font-family: Arial; text-align: center; margin-top: 100px;">
  <h2>🔒 学生信息管理系统</h2>
  {% if error %}<p style="color:red">{{ error }}</p>{% endif %}
  <form method="post" style="display:inline-block; text-align:left;">
    <p><label>用户名：<input name="username" required autofocus></label></p>
    <p><label>密码：<input name="password" type="password" required></label></p>
    <p><button type="submit">登录</button></p>
  </form>
</body></html>
'''

main_page = '''
<!DOCTYPE html>
<html lang="zh-CN"><head>
  <meta charset="UTF-8"><title>学生统计</title>
  <style>body{font-family:"Microsoft YaHei",sans-serif;margin:20px;background:#f9f9f9;}
  .summary{background:#e6f7ff;padding:15px;margin-bottom:20px;border-radius:8px;}
  table{width:100%;border-collapse:collapse;background:white;}
  th,td{border:1px solid #ddd;padding:10px;text-align:left;}
  th{background:#f0f8ff;}
  .pagination{text-align:center;margin-top:15px;}
  button{margin:0 5px;padding:6px 12px;}
  .active{background:#1890ff;color:white;}</style>
</head><body>
<div class="summary">
  <h2>📊 统计概览</h2>
  <p>总人数：<span id="total">-</span></p>
  <p>困难人数：<span id="difficulty">-</span></p>
  <p>心理疑问人数：<span id="psych">-</span></p>
</div>
<table><thead><tr id="header"></tr></thead><tbody id="tbody"></tbody></table>
<div class="pagination" id="pagination"></div>
<p><a href="/logout">退出登录</a></p>
<script>
let currentPage=1;
async function loadData(page=1){
  const res=await fetch(`/api/data?page=${page}`);
  if(res.status===401){alert("登录已过期");location.href="/login";return;}
  const d=await res.json();
  document.getElementById("total").textContent=d.total;
  document.getElementById("difficulty").textContent=d.difficulty;
  document.getElementById("psych").textContent=d.psych;
  const headers=d.data.length?Object.keys(d.data[0]):[];
  document.getElementById("header").innerHTML=headers.map(h=>`<th>${h}</th>`).join("");
  document.getElementById("tbody").innerHTML=d.data.map(row=>
    `<tr>${headers.map(h=>`<td>${row[h]||''}</td>`).join('')}</tr>`
  ).join("");
  currentPage=page;
  let html='';
  for(let i=1;i<=d.total_pages;i++){
    html+=`<button onclick="loadData(${i})"${i===currentPage?' class="active"':''}>${i}</button>`;
  }
  document.getElementById("pagination").innerHTML=html;
}
loadData();
</script>
</body></html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))

<!-- b9n24VM78hkPIuwFh_Z082tLYaQl_RPpsQGB9n0SmI0 -->