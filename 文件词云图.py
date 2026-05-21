import wordcloud
import jieba
f='文件地址'
with open(f,'r',encoding='utf-8') as q:
    txt=q.read()
words=jieba.lcut(txt)
for item in reversed(words):
    if len(item)==1:
        words.remove(item)
w=wordcloud.WordCloud( \
    width=1000,height=700,\
        background_color='white',\
            font_path="msyh.ttc"\
                )
txt_1=" ".join(words)
w.generate(txt_1)
w.to_file("词云图.png")