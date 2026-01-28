import requests

from src.post_parser import _get_post_and_blog_id
from src.config import DEFAULT_LOGIN_AUTH, LOGIN_KEY

url = "https://akamisam.lofter.com/post/757f0567_2b97a5421"
post_id, blog_id = _get_post_and_blog_id(url, DEFAULT_LOGIN_AUTH)
print("post_id =", post_id, "blog_id =", blog_id)

support_url = "https://api.lofter.com/v1.1/trade/gift/post/newSupportInfo"
params = {
    "postId": post_id,
    "blogId": blog_id,
    "vipFans": 0,
    "openFansVipPlan": 0,
    "scene": "note",
}

session = requests.Session()
# 用项目里的 LOGIN_KEY 和 DEFAULT_LOGIN_AUTH 设置 Cookie
session.cookies.set(LOGIN_KEY, DEFAULT_LOGIN_AUTH)

r = session.get(support_url, params=params, timeout=30)
print("newSupportInfo raw:")
print(r.text)