# README #

- First, you should create user at `/api/users/me/` [POST]
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
Also you'll get X-Token in header which you will have to send to get authenticated in websockets.

- Then watch this code sample (your code will be similar):
```
// Got this event on connecting to server
socket.on('connect', function(){
    // Trigger authentication event with data (token)
    socket.emit('authentication', {token: "your X-Token"});

    // Some code on success or fail
    socket.on('authenticated', function() {
        console.log('Yo!')
    });
    socket.on('unauthorized', function(err){
        console.log("Noooo!: ", err.message);
    });
});
```