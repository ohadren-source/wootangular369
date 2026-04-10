import base64

b64 = open('static/solar8_face.b64').read().strip()
src = f'data:image/png;base64,{b64}'

html = open('static/solar8.html', encoding='utf-8').read()
html = html.replace('/static/android-chrome-512x512.png', src)

open('static/solar8.html', 'w', encoding='utf-8').write(html)
print('Done.')