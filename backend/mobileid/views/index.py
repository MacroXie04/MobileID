from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required(login_url="/login")
def index(request):
    """
    首页视图 - 主要逻辑已移至 AccountTypeRoutingMiddleware 中间件
    这个视图现在主要作为fallback，正常情况下不应该被调用到
    因为中间件会拦截并处理根路径的请求
    """
    # 如果到达这里，说明中间件没有处理请求，可能出现了异常
    # 作为fallback，重定向到登录页面
    return redirect("mobileid:web_login")
