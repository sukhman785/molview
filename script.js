$(document).ready( 
    /* this defines a function that gets called after the document is in memory */
    function()
    {
      $("#add").click(
        /* this defines a function that gets called after someone clicks 
         * the button */
        
        function()
        {
          let elementnumber = $("#element-number").val()
          let elementcode = $("#element-code").val()
          let elementname = $("#element-name").val()
          let color1 = $("#color-1").val()
          let color2 = $("#color-2").val()
          let color3 = $("#color-3").val()
          let elementradius = $("#element-radius").val()
        $.ajax({
            type:"post", 
            url: "/add",
            data: {
                elementnumber,
                elementcode,
                elementname,
                color1,
                color2,
                color3,
                elementradius
            },
            success: function(res)
            {
                $("tablebody").append("<tr><td>"+ elementnumber + 
                "</td><td>" + elementcode + 
                "</td><td>" + elementname + 
                "</td><td>" + color1 + 
                "</td><td>" + color2 + 
                "</td><td>" + color3 + 
                "</td><td>" + elementradius + 
                "</td></tr>")
            }
        })
        } );

    } );
  