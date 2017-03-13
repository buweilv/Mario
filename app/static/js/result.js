$(document).ready(function(){
    var result_table = $('#dataTables-results').DataTable({
    "scrollY": "600px",
    "scrollCollapse": "true",
    'columnDefs':[
        {
        'targets': 0,
        'checkboxes': {
            'selectRow': true
            }
        },
        { "width": "20%", "targets": 5}
    ],
        'select': {
            'style': 'multi'
        },
        'order': [[3, 'desc']]
    });

        // button used to delete results
    $("#delresult-btn").click(function(){
        var form = $("#form-results")
        var rows_selected = $('tr.selected')
        var rows_arr = [];
        //Iterate over all selected checkboxes
        $('tr.selected').each(function(index) {
        // create a hidden element
        $(form).append(
            $('<input>')
                .attr('type', 'hidden')
                .attr('name', 'rid'+index)
                .val(this.id)
         );
         rows_arr.push(this.id);
        });

        // post the selected host ids to the server side
        $.ajax($SCRIPT_ROOT + '/_del_results', {
            method: 'post',
            data: form.serialize(),
            dataType: 'json'
            }).done(function(data){
                if (data.ok === true) {
                    for (var index in rows_arr) {
                        result_table.row($('#'+rows_arr[index])).remove().draw();
                    }
                 //   table.draw();
                }
                else {
                    alert('Result Database delete failed!');
                }
            }).fail(function(xhr, status) {
                console.log('Failed: '+ xhr.status + ', Result: ' + status);
            });

        // Remove added input elements
        $('input[name^=rid]').remove();
    })
})
