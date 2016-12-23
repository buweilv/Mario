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

    // modify datatable-checkboxes plugin --> show selected items num correctly


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
        console.log('rows_arr len: ' + rows_arr.length + ' Elements: ');
        console.log(rows_arr);
        for (var i in rows_arr)
            console.log(rows_arr[i] + ' ');


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
});
