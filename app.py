#!/usr/bin/env python
import os
import PIL.Image
import sanic
import sanic_jinja2
import aionotify


app = sanic.Sanic(__name__)
jinja = sanic_jinja2.SanicJinja2(app)

app.static('/images', './images')
app.static('/thumbnails', './thumbnails')


@app.websocket('/update')
async def update(request, ws):
    # TODO: Fix this stupid method of creating a new watcher on every request
    watcher = aionotify.Watcher()
    watcher.watch('images/', aionotify.Flags.CREATE | aionotify.Flags.DELETE
                  | aionotify.Flags.MOVED_FROM | aionotify.Flags.MOVED_TO)
    await watcher.setup(app.loop)
    while True:
        event = await watcher.get_event()
        await ws.send(b'')


@app.route('/upload', methods=['GET', 'POST'])
async def upload(request):
    if request.method == 'POST':
        for f in request.files['f']:
            with open(os.path.join('images/', f.name), 'wb') as file:
                file.write(f.body)
    return await sanic.response.file('templates/upload.html')


@app.route('/')
async def root(request):
    for f in os.listdir('images'):
        if not os.path.exists(os.path.join('thumbnails', f)):
            img = PIL.Image.open(os.path.join('images', f))
            img.thumbnail((128, 128))
            img.save(os.path.join('thumbnails', f), optimize=True)
    return jinja.render('index.html', request, pics=os.listdir('images'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8000')
