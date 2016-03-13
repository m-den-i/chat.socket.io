# README #


## Technologies ##
This project was created as example of websocket's using. The project is multi-user single-room chat. The technology stack was used to make this project is:

### *Python*   
The main part (*Login page*, *login/signup for phones*, *main page*, *admin site*) was very quickly written in Python using libraries below:

- **Django** - popular blocking web-framework in Python. All information can be found at
official pages which are written very well. [Official Django pages are here.](https://www.djangoproject.com/)

- **Django REST framework** - powerful and flexible toolkit for building Web APIs for Django.
[http://www.django-rest-framework.org/](http://www.django-rest-framework.org/)   

### *Javascript* 
Websocket part was written in Javascript.

- **Node.js** - Node.js® is a JavaScript runtime built on Chrome's V8 JavaScript engine. Node.js uses an event-driven, non-blocking I/O model that makes it lightweight and efficient. Node.js' package ecosystem, npm, is the largest ecosystem of open source libraries in the world. This runtime uses JIT and it is blazingly fast.     [https://nodejs.org/en/](https://nodejs.org/en/)

- **Express** - Fast, unopinionated, minimalist web framework for Node.js.  
[http://expressjs.com/](http://expressjs.com/)

- **Socket.IO** - websocket solution. As official pages are claiming: *THE FASTEST AND MOST RELIABLE REAL-TIME ENGINE. Socket.IO enables real-time bidirectional event-based communication. It works on every platform, browser or device, focusing equally on reliability and speed.* [http://socket.io/](http://socket.io/) 

- **socketio-auth** - authentication module for socket.io. [https://github.com/facundoolano/socketio-auth](https://github.com/facundoolano/socketio-auth)

- *Sequelize.js* - *Sequelize* is a promise-based ORM for Node.js and io.js. It supports the dialects PostgreSQL, MySQL, MariaDB, SQLite and MSSQL and features solid transaction support, relations, read replication and more.


## Structure and description
As was mentioned before the main part was written in Python. All models and according database structure is generated with it:

- It generates login page (and authenticates, using *http sessions*), main page with chat window and client JS script to communicate with socket server. Below you may see code samples:

`base/views.py`
```python
# As you may see in studytracker/urls.py this view placed under /
# Here you just get index.html page placed in base/static
# You can reach main page only if authenticated, otherwise you are redirected at /login
@login_required(login_url='/login/')
def index(request):
    return render(request, 'index.html')


# This is login view, generating(!) page with login form
# Forms in Django are classes that describes http forms and translating into http markdown later
# So, here you may see Login form in base/forms.py
# If you sent valid form you'll be authenticated using http sessions and redirected to /
class LoginView(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = '/'

    def form_valid(self, form):
        user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user is not None:
            login(self.request, user)
            return redirect('/')
        else:
            return HttpResponse('Please register.')
```

`base/forms.py`
```python
# Only two fields are going to be translated
class LoginForm(forms.Form):
    username = forms.CharField(max_length=256)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=256)
```

- Using *django-rest-framework* it allows to authenticate mobile clients and JS single-page application with Token-based authentication. Also, there is worth to notice, that Token will be used in websocket's authentication.

`base/views.py`
```python
# Here we create user instance and it is placed under /api/users/:id/ or /api/users/me/
# Serializers - allows to encode/decode information from JSON
# How API are created you may check in django-rest-framework (DRF) docs
class UserViewSet(RetrieveSelfMixin,
                  ResetPasswordViewMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = UserSerializer
    queryset = get_user_model().objects
    permission_classes = [IsSelfOrReadOnly, POSTOnlyIfAnonymous]

    def update(self, request, *args, **kwargs):
        kwargs.update({'partial': True})
        return super(UserViewSet, self).update(request, *args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        response = super(UserViewSet, self).create(request, *args, **kwargs)
        response.data = None
        return response

    def perform_create(self, serializer):
        obj = serializer.save()


# Here we generate Token on login and delete Token on logout, 
# connected with user instance in db as FK. 
# According to Token-based authentication client should send 
# in HTTP header field: Authorization
# with value: Token `some value`
# How token authentication works exactly you may check in DRF 
# docs and source code of drf-secure-token lib.
# In two words, we take Token from header and try to get it from db. 
# If it exists and connected with user instance,
# we know which user is going to request.
# All this placed under /api/auth/:url_path
class UserAuthViewSet(viewsets.ViewSet):
    NEW_TOKEN_HEADER = 'X-Token'

    login_serializer_class = UsernameLoginSerializer

    @decorators.list_route(methods=['post'], permission_classes=[permissions.AllowAny], url_path='signin')
    def basic_login(self, request):
        serializer = self.get_login_serializer()
        serializer.is_valid(raise_exception=True)
        self.user = serializer.authenticate()
        headers = self.get_success_headers()
        request.session['X-Token'] = headers[self.NEW_TOKEN_HEADER].key
        resp = Response(status=status.HTTP_201_CREATED,
                        headers=headers,
                        data=UserSerializer(instance=self.user).data)
        return resp

    def get_login_serializer(self, **kwargs):
        return self.login_serializer_class(data=self.request.data, **kwargs)

    def get_success_headers(self):
        return {self.NEW_TOKEN_HEADER: self.user.user_auth_tokens.create()}

    @decorators.list_route(methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='token')
    def token(self, request):
        tok = Token.objects.filter(user=request.user).first()
        return Response(data={'X-Token': tok.key if tok else Token.objects.create(user=request.user).key})

    @decorators.list_route(methods=['delete'], permission_classes=[permissions.IsAuthenticated], url_path='logout')
    def logout(self, request):
        auth_token = request._request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        request.user.user_auth_tokens.filter(key=auth_token).delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)

```  

Node.js is responsible for websocket part. This part of project is placed in path `node`.

- First, we create Object relational mapping with sequelize.js on top of Django-created tables to use db.

`node/models/index.js`
```js
// This main file which is responsible for exporting
// module `models`. Here we export one-file-described models.
'use strict';

var fs        = require('fs');
var path      = require('path');
var Sequelize = require('sequelize');
var basename  = path.basename(module.filename);
var config = require(__dirname + '/../config/config.json')["pg_db"];
var db        = {};

var sequelize = new Sequelize('postgres://postgres:Cruelworld@localhost:5432/studytracker');

fs
  .readdirSync(__dirname)
  .filter(function(file) {
    return (file.indexOf('.') !== 0) && (file !== basename) && (file.slice(-3) === '.js');
  })
  .forEach(function(file) {
    var model = sequelize['import'](path.join(__dirname, file));
    db[model.name] = model;
  });

Object.keys(db).forEach(function(modelName) {
  if (db[modelName].associate) {
    db[modelName].associate(db);
  }
});

db.sequelize = sequelize;
db.Sequelize = Sequelize;


module.exports = db;
```

`node/models/user.js`
```js
// Other files are similar - we describe model (and relations too, for sure).
// And explicitly points to SQL table, already generated by django's ORM
module.exports = function(sequelize, DataTypes) {
  Message = sequelize.import(__dirname + '/message');
  var User = sequelize.define("User", {
    email: DataTypes.STRING,
    username: DataTypes.STRING
  }, {
    tableName: 'base_member',
    timestamps: false
  });
  User.hasMany(Message, {as: 'messages'});
  return User;
};
```
- Second, we create Express server isntance and socket.io instance on top of it. 

`node/bin/www`
```js
// Settings for Express server
var app = require('../app');
// http - instance of server
var http = require('http').Server(app);
// Here we create socket.io server on top of http server
var io = require('socket.io')(http);
// And also let's import models
var models = require('../models');

...


http.listen(3000, function(){
  console.log('listening on *:3000');
});

```

- Also using socket.io server we must authenticate user that is going to communicate with other members.

`node/bin/www`
```js
// Here we create hook to implement authentication in socket.io
// without using querystrings to send credentials with module `socketio-auth`
// We get socket instance of user trying to authenticate.
// Also we get data, sent by client: there should be token. See index.html
require('socketio-auth')(io, {
  authenticate: function (socket, data, callback) {
    //get credentials sent by the client and log them (for debugging purposes)
    console.log('DATA: ' + data.token);
    var token = data.token;
    models.sequelize.sync().then(function () {
      // Trying to find token, using ORM
      models.Token.findOne({where: {key: token}}).then(function(tokenObj){
        if (!tokenObj) return callback(new Error("Token not found."));
        // If token is found let's found user with this token
        models.User.findOne({where: {id: tokenObj.user_id}}).then(function(userObj){
          if (!userObj) return callback(new Error("User by token not found."));
          // Then set user to socket instance 
          socket.client.user = userObj;
          return callback(null, true);
        });
      })
    });
  }
});
```

- Last step to setup events of socket.io

`node/bin/www`
```js
// This event is triggered on user connection
io.on('connection', function(socket){
  // We get socket instance here

  // Let's log date of connection
  console.log('a user connected', new Date().toLocaleTimeString());
  // Then send hello from server
  socket.emit('news', { message: 'Hello, at localhost:3000' });
  // if we get from any client message
  socket.on('client-sent-message', function (data) {
    // we should send it to others (all) sockets
    io.sockets.emit('server-got-message', {message: socket.client.user.email + ': ' + data.message})
  })

});
```

- Client library is quite simple in use. See `static/index.html`

## Quick installation (all actions is from main project folder `/studytracker`)
- Make sure you've installed Python, Node.js (PIP and NPM package managements as well, for sure)
- Optionally install virtualenv for python to isolate your libs from main libs of python. [http://docs.python-guide.org/en/latest/dev/virtualenvs/](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
- Create Postgresql database named `studytracker`.
- In `studytracker/settings.py` find dict *DATABASES*. Insert there your credentials. This will be used to connect to database.
- Run `pip install -r requirements.txt` to install python requirements listed in requirements.txt.
- Run `./manage.py migrate` to apply model changes in base/models.py
- Go to folder `node` and run `npm install`.
- Run node.js server on localhost with `node bin/www`
- Go back (one folder up) and run Django server on localhost with `./manage.py runserver`
- On page [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) you may fill database with some info.


## Using project ##
### Mobile phone or Javascript single-page app
- First, you should create user at `/api/users/` [POST]
```
{
"email": "mail@mail.com",
"password": "qwerty"
}
```


- Second, you should login at `/api/auth/signin/` [POST]
```
{
"username": "mail@mail.com",
"password": "qwerty"
}
```
You'll get X-Token in header which you will have to send to get authenticated in websockets.

- Then watch this code sample (your code will be similar):
```
// Got this event on connecting to server
socket.on('connect', function(){
    // Trigger authentication event with data (token)
    socket.emit('authentication', {token: "your X-Token"});

    // Some code on successful authorization
    socket.on('authenticated', function() {
        console.log('Yo!')
    });
    // Or failed...
    socket.on('unauthorized', function(err){
        console.log("Noooo!: ", err.message);
    });
});
```

### Usual web-client
- Visit `/`, you'll be redirected to login page.
- Log in and you are ready to talk!