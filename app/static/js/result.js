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
        }
    ],
        'select': {
            'style': 'multi'
        },
        'order': [[1, 'asc']]
    });
})
