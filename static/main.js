/**
 * Created by denis on 3/8/16.
 */
var socket = io('http://25.81.215.212:3000/');

socket.on('news', function (data) {
    console.log(data);
    socket.emit('my other event', { my: 'data' });
});

socket.on('connect', function(){
    socket.emit('authentication', {token: "62b8e1df-4806-4d01-ad00-7dfbf123ef02"});
    socket.on('authenticated', function() {
        console.log('Yo!')
    });
    socket.on('unauthorized', function(err){
        console.log("Noooo!: ", err.message);
    });
});