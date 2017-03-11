$(document).ready(function(){
    var sidebar_tabs = $('ul.nav li')
    sidebar_tabs.on('click', function(){
        $('ul.nav li.active').removeClass('active')
        $(this).addClass('active')
    })
})
