$(document).ready(function(){
    namespace = '/hostinfo'
    // var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
    socket.on('connect', function() {
        console.log('connected to the server')
    });
    /* test websocket connect
    socket.on('my_response', function(msg){
        $('#log').append('<br>' + $('<div/>').text(msg.data).html());
    });
    */
    
    // Interval function that tests message latency by sending a "ping"
    // message. The server then responds with a "pong" message and the
    // round trip time is measured.
    var ping_pong_times = [];
    var start_time;
    window.setInterval(function() {
        start_time = (new Date).getTime();
        socket.emit('my_ping');
    }, 1000);

    // Handler for the "pong" message. When the pong is received, the
    // time from the ping is stored, and the average of the last 30
    // samples is average and displayed.
    socket.on('my_pong', function() {
        var latency = (new Date).getTime() - start_time;
        ping_pong_times.push(latency);
        ping_pong_times = ping_pong_times.slice(-30); // keep last 30 samples
        var sum = 0;
        for (var i = 0; i < ping_pong_times.length; i++)
            sum += ping_pong_times[i];
        $('#ping-pong').text(Math.round(10 * sum / ping_pong_times.length) / 10);
    });

    socket.on('update_host', function(all_hosts){
        $('#dataTables-hosts tbody tr').each(function(index){
            //$(this).children().eq(2).text( "233" )
            // console.log($(this).attr('id'),   all_hosts[$(this).attr('id')])
            $(this).children().eq(2).text(all_hosts[$(this).attr('id')]);
        });
    })
})
