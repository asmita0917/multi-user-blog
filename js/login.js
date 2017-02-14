function click1() {

    documents.getelementbyid('#login-form-link').click(function(e) {
        documents.getelementbyid("#login-form").delay(100).fadeIn(100);
        documents.getelementbyid("#register-form").fadeOut(100);
        documents.getelementbyid('#register-form-link').removeClass('active');
        documents.getelementbyid(this).addClass('active');
        e.preventDefault();
    });
    documents.getelementbyid('#register-form-link').click(function(e) {
        documents.getelementbyid("#register-form").delay(100).fadeIn(100);
        documents.getelementbyid("#login-form").fadeOut(100);
        documents.getelementbyid('#login-form-link').removeClass('active');
        documents.getelementbyid(this).addClass('active');
        e.preventDefault();
    });

};
