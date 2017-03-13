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
})
