$(document).ready(function(){
    function draw_chart(data, chart){
        var option = {
            title: {
                text: data.type+" test@"+data.deployTime
            },
            toolbox: {
                show: true,
                feature: {
                    saveAsImage: {
                        show: true
                        }
                }
            },
            tooltip: {},
            legend: {
                data: ['pmresult', 'vmresult'],
                y: "bottom"
            },
            xAxis: {
                data: ["run time"]
            },
            yAxis: {},
            series: [{
                "name": "pmresult",
                "type": "bar",
                barWidth: 40, 
                "itemStyle": {
                    normal: {
                        label: {
                        show : true,
                        position: 'top',
                        textStyle: {
                            fontSize : '10',
                            fontFamily : '微软雅黑',
                            fontWeight : 'bold'
                            }
                        }
                    }
                },
                "data": [data.pmresult]
            },
            {
                "name": "vmresult",
                "type": "bar",
                barWidth: 40, 
                "itemStyle": {
                    normal: {
                        label: {
                        show : true,
                        position: 'top',
                        textStyle: {
                            fontSize : '10',
                            fontFamily : '微软雅黑',
                            fontWeight : 'bold'
                            }
                        }
                    }
                },
                "data": [data.vmresult]
            }
            ]
         };
        chart.setOption(option);
    }

   function draw_chart_on_panel(type, id,  panel_id){
        console.log(type)
        $.ajax($SCRIPT_ROOT + '/_get_'+type+'_result', {
                method: 'get',
                dataType: 'json',
                data: {id: id},
        }).done(function(data){
            var myChart = echarts.init(document.getElementById('panel'+panel_id));
           draw_chart(data, myChart) 
        }).fail(function(xhr, status) {
            console.log("Failed: " + xhr.status + ', Result: ' + status)
        })
    }
    // draw first three results' charts
    first_three_results = $('tbody tr').filter(function(){
        return $(this).find("td:eq(4) i").text() === "offline_pin"
    }).slice(0,3);
    first_three_results.each(function(index){
        if ($(this).find("td:eq(2)").text() === "cpu") {
            id = parseInt($(this).attr('id').substring(3));
            draw_chart_on_panel("cpu", id, index);      
            }
        else if ($(this).find("td:eq(2)").text() === "mem") {
            id = parseInt($(this).attr('id').substring(3));
            draw_chart_on_panel("mem", id, index);           
            }
        else if ($(this).find("td:eq(2)").text() === "io") {
            id = parseInt($(this).attr('id').substring(2));
            draw_chart_on_panel("io", id, index);           
            }
        else
            alert("wrong type when draw chart on panel!")
    })
})
