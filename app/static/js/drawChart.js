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
            yAxis: {}
        };

        if (data.type === "cpu" || data.type === "mem"){
            if (data.type === "cpu"){
            option.xAxis = { data: ["run time(s)"]};
            }
            else if (data.type === "mem"){
            option.xAxis = { data: ["Throughput(MB/s)"]};
            }
            option.series = [{
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
            ];
        } else if (data.type === "io"){
            option.xAxis = { data: ["Write", "Rewrite", "Read", "ReRead"]};
            option.series = [{
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
                "data": [data.pmInitialWrite, data.pmRewrite, data.pmRead, data.pmReRead]
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
                "data": [data.vmInitialWrite, data.vmRewrite, data.vmRead, data.vmReRead]
            }
            ];

        
        }
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

    function draw_first_three_charts() {
    // draw first three results' charts
    first_three_results = $('tbody tr').filter(function(){
        return $(this).find("td:eq(4) i").text() === "offline_pin"
    }).slice(0,3);
    first_three_results.each(function(index){
        if ($(this).find("td:eq(2)").text() === "cpu") {
            id = parseInt($(this).attr('id').substring(4));
            draw_chart_on_panel("cpu", id, index);      
            }
        else if ($(this).find("td:eq(2)").text() === "mem") {
            id = parseInt($(this).attr('id').substring(4));
            draw_chart_on_panel("mem", id, index);           
            }
        else if ($(this).find("td:eq(2)").text() === "io") {
            id = parseInt($(this).attr('id').substring(3));
            draw_chart_on_panel("io", id, index);           
            }
        else
            alert("wrong type when draw chart on panel!")
    })
    }

    // when the page load, draw first three charts
    draw_first_three_charts()
    // when the refresh button triggerred, refresh the newest first three charts
    $("#refresh-btn").click(draw_first_three_charts);

    // button used to draw chart on panel0
    $(".btn-panel0").click(function(){
        var type = $(this).parent().parent().find("td:eq(2)").text();
        if (type === "cpu" || type === "mem")
            var id = parseInt($(this).parent().parent().attr('id').substring(4))
        else if (type === "io")
            var id = parseInt($(this).parent().parent().attr('id').substring(3))
        draw_chart_on_panel(type, id, 0)
    });
     // button used to draw chart on panel1
    $(".btn-panel1").click(function(){
        var type = $(this).parent().parent().find("td:eq(2)").text();
        if (type === "cpu" || type === "mem")
            var id = parseInt($(this).parent().parent().attr('id').substring(4))
        else if (type === "io")
            var id = parseInt($(this).parent().parent().attr('id').substring(3))
        draw_chart_on_panel(type, id, 1)
    });
     // button used to draw chart on panel2
    $(".btn-panel2").click(function(){
        var type = $(this).parent().parent().find("td:eq(2)").text();
        if (type === "cpu" || type === "mem")
            var id = parseInt($(this).parent().parent().attr('id').substring(4))
        else if (type === "io")
            var id = parseInt($(this).parent().parent().attr('id').substring(3))
        draw_chart_on_panel(type, id, 2)
    });


})

