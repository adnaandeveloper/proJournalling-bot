import json,os
_cache={}
def t(lang,key,**kw):
    if lang not in _cache:
        with open(os.path.join(os.path.dirname(__file__),"locales",f"{lang}.json"),encoding="utf-8") as f:
            _cache[lang]=json.load(f)
    return _cache[lang].get(key,key).format(**kw)
