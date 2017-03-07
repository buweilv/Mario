$(document).ready(function(){
    var table = $('#dataTables-hosts').DataTable({
    "scrollY": "600px",
    "scrollCollapse": "true",
    'columnDefs':[
        {
        'targets': 0,
        'checkboxes': {
            'selectRow': true
            }
        }
    ],
        'select': {
            'style': 'multi'
        },
        'order': [[1, 'asc']]
    });

    $.func = {
        notification: function(info, text) {
            var nof = document.createElement('div');
            nof.setAttribute('class','alert alert-dismissable ' + info);
            nof.innerHTML = '<button type="button" class="close" data-dismiss="alert">&times;</button>' + text;
            $('#notification').append(nof);
        }
    }

    $("#addhost-btn").click(function(){
        console.log('send to /_add_host')
        $.ajax($SCRIPT_ROOT + '/_add_host', {
            //method: 'get',
            method: 'post',
      //      data: {
      //          ip: $('#ip-addr').val(),
      //          passwd: $('#passwd').val()
      //      },
            data: $('#add-host-form').serialize(),
            // revieve data format
            dataType: 'json'
            }).done(function(data){
                if (data.input_ok === 'invalid hostname') {
                    $.func.notification('alert-danger', 'invalid hostname');
                    console.log('invalid hostname.');
                } else if (data.input_ok === 'auth failed'){
                    $.func.notification('alert-danger', 'auth fialed');
                    console.log('auth failed.');
                } else if (data.input_ok === 'database failed'){
                    $.func.notification('alert-danger', 'database failed');
                    console.log('database failed.');
                } else if (data.input_ok === 'host already added'){
                    $.func.notification('alert-danger', 'Host Already added');
                    console.log('host already added.');
                } else if (data.input_ok === 'empty field'){
                    $.func.notification('alert-danger', 'Empty Field!');
                    console.log('empty field.');
                } else if(data.input_ok === 'check the machine if ready') {
                    $.func.notification('alert-danger', 'Check the machine, it should be ready for SSH connection')
                    console.log('check the machine if ready')
                } else if(data.input_ok === 'host added success') {
                    var rowNode = table.row.add( [
                        data.id,
                        data.IP,
                        data.status
                    ] ).draw( false )
                        .node();
                    $(rowNode).attr('id', data.id)
                    childNode = $(rowNode).children('td').eq(1)
                    childNode.attr('name', 'ip')
                    $.func.notification('alert-success', 'Host added successfully!')
                    console.log('host added success')
                } else {
                    console.log('input successfully handled!'); // for debug
                }
            }).fail(function(xhr, status) {
                console.log('Failed: '+ xhr.status + ', Result: ' + status);
            });
    });


    $("#delhost-btn").click(function(){
        var form = $("#form-hosts");
//        var rows_selected = table.column(0).checkboxes.selected();
        var rows_selected = $('tr.selected');
        var rows_arr = [];

        // Iterate over all selected checkboxes
        $('tr.selected').each(function(index) {
        // Create a hidden element
        $(form).append(
             $('<input>')
                .attr('type', 'hidden')
                .attr('name', 'id'+index)
                .val(this.id)
         );
        rows_arr.push(this.id);
        });

        // check the rows_arr get right rowIds
        //console.log('rows_arr len: ' + rows_arr.length + ' Elements: ');
        //console.log(rows_arr);
        //for (var i in rows_arr)
        //   console.log(rows_arr[i] + ' ');


        // post the selected host ids to the server side
        $.ajax($SCRIPT_ROOT + '/_del_hosts', {
            method: 'post',
            data: form.serialize(),
            dataType: 'json'
            }).done(function(data){
                if (data.ok === true) {
                    for (var index in rows_arr) {
                        table.row($('#'+rows_arr[index])).remove().draw();
                    }
                 //   table.draw();
                }
                else {
                    alert('Database delete failed!');
                }
            }).fail(function(xhr, status) {
                console.log('Failed: '+ xhr.status + ', Result: ' + status);
            });

        // Remove added input elements
        $('input[name^=id]').remove();
    });

    $("#cpu-btn").click(function(){
        var form = $("#form-hosts")
        var rows_selected = $('tr.selected')
        var rows_arr = [];
        var ips_arr = [];

        //Iterate over all selected checkboxes
        $('tr.selected').each(function(index) {
        // create a hidden element
        $(form).append(
            $('<input>')
                .attr('type', 'hidden')
                .attr('name', 'id'+index)
                .val(this.id)
         );
         // end of function append
         rows_arr.push(this.id);
         ips_arr.push($(this).children('td[name=ip]').text());
        });
        // end of function each
        // check the rows_arr get right rowIds
        /*
        console.log('rows_arr len: ' + rows_arr.length + ' Elements: ');
        console.log(rows_arr);
        for (var i in rows_arr)
            console.log(rows_arr[i] + ' ');
        */
        // end of log
        // post the selected host ids to the server side
         $.ajax($SCRIPT_ROOT + '/_cpu_test', {
            method: 'post',
            data: form.serialize(),
            dataType: 'json'
         }).done(function(data) {
            console.log(data)
            console.log(ips_arr)
            var message = {
                status: "error",
                info: ""
            };
            for (var i in ips_arr){
                console.log(ips_arr[i])
                if (data[ips_arr[i]] != 'success')
                    if (data[ips_arr[i]] === 'no one')
                        message['info'] += data[ips_arr[i]] +' is listening ' + 'channel ' + ips_arr[i] + '\n';
                    else
                        message['info'] += data[ips_arr[i]] +' are listening ' + 'channel ' + ips_arr[i] + '\n';
            }
            if (!message['info'])
            {
                message['info'] = "All hosts deploy successfully!"
                message['status'] = "success"
            }
            swal({
                title: "CPU test deploy info",
                text: message['info'],
                type: message['status'],
                confirmButtonText: "Got it!"
            })
         }).fail(function(xhr, status) {
            console.log('Failed: '+ xhr.status + ', Result: ' + status);
         });

         // Remove added input elements
        $('input[name^=id]').remove();
    });
    // the end of the cpu-btn click

    $("#mem-btn").click(function(){
        var form = $("#form-hosts")
        var rows_selected = $('tr.selected')
        var rows_arr = [];
        var ips_arr = [];

        //Iterate over all selected checkboxes
        $('tr.selected').each(function(index) {
        // create a hidden element
        $(form).append(
            $('<input>')
                .attr('type', 'hidden')
                .attr('name', 'id'+index)
                .val(this.id)
         );
         // end of function append
         rows_arr.push(this.id);
         ips_arr.push($(this).children('td[name=ip]').text());
        });
        // end of function each
        // check the rows_arr get right rowIds
        /*
        console.log('rows_arr len: ' + rows_arr.length + ' Elements: ');
        console.log(rows_arr);
        for (var i in rows_arr)
            console.log(rows_arr[i] + ' ');
        */
        // end of log
        // post the selected host ids to the server side
         $.ajax($SCRIPT_ROOT + '/_mem_test', {
            method: 'post',
            data: form.serialize(),
            dataType: 'json'
         }).done(function(data) {
            console.log(data)
            console.log(ips_arr)
            var message = {
                status: "error",
                info: ""
            };
            for (var i in ips_arr){
                console.log(ips_arr[i])
                if (data[ips_arr[i]] != 'success')
                    if (data[ips_arr[i]] === 'no one')
                        message['info'] += data[ips_arr[i]] +' is listening ' + 'channel ' + ips_arr[i] + '\n';
                    else
                        message['info'] += data[ips_arr[i]] +' are listening ' + 'channel ' + ips_arr[i] + '\n';
            }
            if (!message['info'])
            {
                message['info'] = "All hosts deploy successfully!"
                message['status'] = "success"
            }
            swal({
                title: "Mem test deploy info",
                text: message['info'],
                type: message['status'],
                confirmButtonText: "Got it!"
            })
         }).fail(function(xhr, status) {
            console.log('Failed: '+ xhr.status + ', Result: ' + status);
         });

         // Remove added input elements
        $('input[name^=id]').remove();
    });
    // the end of the mem-btn click


    $("#io-btn").click(function(){
        var form = $("#form-hosts")
        var rows_selected = $('tr.selected')
        var rows_arr = [];
        var ips_arr = [];

        //Iterate over all selected checkboxes
        $('tr.selected').each(function(index) {
        // create a hidden element
        $(form).append(
            $('<input>')
                .attr('type', 'hidden')
                .attr('name', 'id'+index)
                .val(this.id)
         );
         // end of function append
         rows_arr.push(this.id);
         ips_arr.push($(this).children('td[name=ip]').text());
        });
        // end of function each
        // check the rows_arr get right rowIds
        /*
        console.log('rows_arr len: ' + rows_arr.length + ' Elements: ');
        console.log(rows_arr);
        for (var i in rows_arr)
            console.log(rows_arr[i] + ' ');
        */
        // end of log
        // post the selected host ids to the server side
         $.ajax($SCRIPT_ROOT + '/_io_test', {
            method: 'post',
            data: form.serialize(),
            dataType: 'json'
         }).done(function(data) {
            console.log(data)
            console.log(ips_arr)
            var message = {
                status: "error",
                info: ""
            };
            for (var i in ips_arr){
                console.log(ips_arr[i])
                if (data[ips_arr[i]] != 'success')
                    if (data[ips_arr[i]] === 'no one')
                        message['info'] += data[ips_arr[i]] +' is listening ' + 'channel ' + ips_arr[i] + '\n';
                    else
                        message['info'] += data[ips_arr[i]] +' are listening ' + 'channel ' + ips_arr[i] + '\n';
            }
            if (!message['info'])
            {
                message['info'] = "All hosts deploy successfully!"
                message['status'] = "success"
            }
            swal({
                title: "I/O test deploy info",
                text: message['info'],
                type: message['status'],
                confirmButtonText: "Got it!"
            })
         }).fail(function(xhr, status) {
            console.log('Failed: '+ xhr.status + ', Result: ' + status);
         });

         // Remove added input elements
        $('input[name^=id]').remove();
    });
    // the end of the io-btn click



});
