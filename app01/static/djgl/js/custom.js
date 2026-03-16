(function($){
    $(window).on("load", function(){
		$(".preloader").fadeOut();
	});
    
    $(document).ready(function(){
        // Sticky Navigation Bar
		$(window).scroll(function(){
			var scrollHeight = $(document).scrollTop();
			if(scrollHeight > 50){
				$('.primary-header').addClass('navigation-fixed');
			}else{
				$('.primary-header').removeClass('navigation-fixed');
			}

            // Scroll to Top
            if(scrollHeight > 106){
                $('.scrolltotop').fadeIn();
            }else{
                $('.scrolltotop').fadeOut();
            }
		});
        
        $(".primary-navigation").meanmenu({
            meanMenuContainer       : '.mobile-menu',
            meanScreenWidth         : 992,
            meanMenuOpen            : '<span></span><span></span><span></span>',
            meanMenuClose           : '<i class="fas fa-times"></i>',
        });

        $(".home-slider").owlCarousel({
            items                   : 1,
            dots                    : false,
            loop                    : true,
            mouseDrag               : false,
            touchDrag               : false,
            navText                 : ['<i class="fas fa-chevron-left"></i>','<i class="fas fa-chevron-right"></i>'],
            animateIn               : 'fadeIn',
            animateOut              : 'fadeOut',
            autoplay                : true,
            responsive              : {
                768                 : {                    
                    nav                     : true,
                }
            }
        });

        $(".testimonial-slider").owlCarousel({
            margin                  : 50,
            loop                    : true,
            dots                    : false,
            autoplay                : true,
            autoplaySpeed           : 1000,
            navSpeed                : 1000,
            mouseDrag               : false,
            responsive              : {
                0                   : {
                    items           : 1,
                },
                992                 : {
                    items           : 2,
                },
                1100                : {                    
                    nav             : true,
                    navText         : ['<i class="fas fa-chevron-left"></i>','<i class="fas fa-chevron-right"></i>'],
                    items           : 2,
                }
            }
        });

        $('.counter-info .number span').counterUp({
            delay: 10,
            time: 1000,
        });
    });
}(jQuery))