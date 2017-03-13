$(document).ready(function(){
	function generate_download_btn(type , id, operationcol){
		$.ajax($SCRIPT_ROOT + '/_get_'+type+'_result', {
                method: 'get',
                dataType: 'json',
                data: {id: id},
        }).done(function(data){
        	var json_data = "text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data));
        	download_name = data.IP.split(".")[3] + '-' + data.deployTime.split("-")[3] + '-' + data.type;
        	var a = document.createElement('a');
			a.href = 'data:' + json_data;
			a.download = download_name+'.json';
			a.class = "btn btn-xs btn-download";
			a.innerHTML = '<i class="material-icons">get_app</i>';
			$(operationcol).append(a);
        }).fail(function(xhr, status) {
            console.log("Failed: " + xhr.status + ', Result: ' + status)
        })
	}


	$('tbody tr').each(function(index){
		if ($(this).find("td:eq(2)").text() === "cpu") {
            id = parseInt($(this).attr('id').substring(4));
            generate_download_btn("cpu", id, $(this).children("td:last-child"));      
            }
        else if ($(this).find("td:eq(2)").text() === "mem") {
            id = parseInt($(this).attr('id').substring(4));
            generate_download_btn("mem", id, $(this).children("td:last-child"));           
            }
        else if ($(this).find("td:eq(2)").text() === "io") {
            id = parseInt($(this).attr('id').substring(3));
            generate_download_btn("io", id, $(this).children("td:last-child"));           
            }
        else
            alert("wrong type when draw download button in the table!")
	})
})