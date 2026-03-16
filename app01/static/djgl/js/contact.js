(function ($, window, document, undefined) {
    'use strict';

    var $form = $('#contact-form');

    $form.on("submit", function (e) {
        
        $(".preloader").show();
        
        var firstname = $("#firstname").val(),
            lastname = $("#lastname").val(),
            email = $("#email").val(),
            subject = $("#subject").val(),
            msg = $("#msg").val();
        
        Email.send({
            SecureToken: "547f57f5-53f8-45cb-8dd4-f712386e572d",
            To : "emailto@gmail.com",
            From : "emailfrom@gmail.com",
            Subject : "Message from Aurpa",
            Body : "<p><b>Message:</b>" + msg + "</p><br><b>Subject:</b>" + subject + "<br><b>Email:</b>" + email
        }).then(
          function(){
              $(".preloader").hide();
              alert("Your message successfully sent");
              $("#firstname").val(null);
              $("#lastname").val(null);
              $("#email").val(null);
              $("#subject").val(null);
              $("#msg").val(null);
          }
        );
        
        e.preventDefault();
    });
}(jQuery, window, document));