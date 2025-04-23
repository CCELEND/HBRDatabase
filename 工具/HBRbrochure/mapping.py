
from tools import load_json

style_id_brochure_id = {}
# 加载资源文件
def load_resources():
    global style_id_brochure_id
    if style_id_brochure_id:
        return
    style_id_brochure_id = load_json("./工具/HBRbrochure/style_id_brochure_id.json")

def GetBrochureIdByStyleId(style_id):
    brochure_id = style_id_brochure_id[style_id]
    return brochure_id
